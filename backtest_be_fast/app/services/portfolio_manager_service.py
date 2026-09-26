"""포트폴리오 백테스트 관리 서비스 (Manager)

포트폴리오 백테스트의 전체 흐름(입력 변환 → 실행 → 통계 조립 → 응답 구성)을
조율하고 메트릭·오류 계약을 책임진다. 단계별 규칙은 app/services/portfolio/에 있다.

- portfolio_inputs: 요청 → 종목별 금액·DCA 정보 (weight→금액 환산 공통 규칙)
- portfolio_execution: 전략 종목별 백테스트, buy&hold 시뮬레이션 준비·위임
- portfolio_statistics_builder: portfolio_statistics 조립
- portfolio_response_builder: 경로별 응답 딕셔너리 (키 순서가 API 계약)

통화 정책:
- DB 저장: 원본 통화 (KRW, JPY, EUR 등)
- 백테스트 계산: 모든 가격을 USD로 변환
- 프론트엔드: 개별 종목은 원본 통화, 결과는 USD
"""
import logging
import time
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from app.schemas.schemas import PortfolioBacktestRequest
# backtest_service는 portfolio_execution이 쓰지만 이 모듈에서도 import해 둔다 —
# 테스트가 "app.services.portfolio_manager_service.backtest_service.run_backtest"를
# patch한다(같은 전역 인스턴스의 속성이라 portfolio_execution에도 적용된다).
from app.services.backtest_service import backtest_service  # noqa: F401
from app.repositories.stock_repository import get_stock_repository
from app.services.portfolio_calculator_service import portfolio_calculator
from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager
from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine
from app.services.portfolio.portfolio_data_loader import PortfolioDataLoader
from app.services.portfolio.portfolio_metrics import PortfolioMetrics
from app.services.portfolio.portfolio_inputs import (
    BuyHoldAllocationBuilder,
    drop_unloaded_symbols,
    resolve_strategy_amounts,
)
from app.services.portfolio.portfolio_execution import (
    run_strategy_per_symbol,
    simulate_buy_hold,
)
from app.services.portfolio.portfolio_statistics_builder import (
    build_strategy_statistics,
    calculate_true_portfolio_stats,
    calculate_weighted_stats,
    strategy_headline_returns,
)
from app.services.portfolio.portfolio_response_builder import (
    build_buy_hold_individual_returns,
    build_buy_hold_response,
    build_cash_only_response,
    build_strategy_response,
    format_individual_results_list,
)
from app.utils.serializers import recursive_serialize
from app.domain.portfolio_domain import DcaStrategyInfo
from app.utils.currency_converter import currency_converter
from app.monitoring.custom_metrics import (
    BACKTEST_EXECUTION_TOTAL,
    BACKTEST_PROCESSING_SECONDS,
    observe_stage,
    record_ticker_popularity,
)

logger = logging.getLogger(__name__)

class PortfolioManagerService:
    """
    포트폴리오 백테스트 관리 서비스 (Manager/Orchestrator Role)

    [역할 정의]
    이 서비스는 '사장님'과 같은 역할로, 직접 복잡한 계산을 수행하기보다 하위 모듈들을 조율하여 전체 업무를 완수합니다.
    API 요청을 받고, 데이터를 로드하고, 최종 결과를 포맷팅하는 **전체 흐름을 주관**합니다.

    주요 책임:
    1. Orchestration: 데이터 로딩, 시뮬레이션 실행, 결과 취합의 흐름 제어.
    2. Data Management: StockRepository 등을 통해 필요한 외부 데이터를 준비.
    3. Delegation: 실제 시뮬레이션 계산은 PortfolioSimulationEngine에 위임.
    """
    def __init__(self):
        """포트폴리오 서비스 초기화"""
        # 추출된 컴포넌트 초기화
        self.dca_manager = PortfolioDcaManager()
        self.rebalancer = PortfolioRebalancer()
        self.simulation_engine = PortfolioSimulationEngine(
            dca_manager=self.dca_manager,
            rebalancer=self.rebalancer
        )
        self.metrics = PortfolioMetrics()
        # Repository 초기화 (Repository 패턴)
        self.stock_repository = get_stock_repository()
        
        # Data Loader 초기화 (데이터 준비 역할)
        self.data_loader = PortfolioDataLoader(
            stock_repository=self.stock_repository,
            currency_converter=currency_converter
        )
        
        logger.info("포트폴리오 서비스가 초기화되었습니다")

    # 통계 조립 규칙은 portfolio_statistics_builder로 옮겼다. 기존 이름은 테스트와
    # 호출부 호환을 위해 그대로 둔다.
    _calculate_weighted_stats = staticmethod(calculate_weighted_stats)
    _calculate_true_portfolio_stats = staticmethod(calculate_true_portfolio_stats)
    _format_individual_results_list = staticmethod(format_individual_results_list)

    async def calculate_dca_portfolio_returns(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        amounts: Dict[str, float],
        dca_info: Dict[str, DcaStrategyInfo],
        start_date: str,
        end_date: str,
        rebalance_frequency: str = "weekly_4",
        commission: float = 0.0
    ) -> pd.DataFrame:
        """DCA와 리밸런싱을 고려한 포트폴리오 수익률 계산

        Note: last_rebalance_date는 예정일 추적용, rebalance_history는 실제 거래만 기록
        """
        return await simulate_buy_hold(
            self.data_loader,
            self.simulation_engine,
            portfolio_data,
            amounts,
            dca_info,
            start_date,
            end_date,
            rebalance_frequency,
            commission,
        )
    
    
    async def run_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """
        포트폴리오 백테스트 실행
        
        Args:
            request: 포트폴리오 백테스트 요청
            
        Returns:
            백테스트 결과
        """
        strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
        logger.info(f"포트폴리오 백테스트 시작: 전략={strategy_name}, 종목수={len(request.portfolio)}")

        # 예외를 잡지 않는다: API 레이어의 @handle_portfolio_errors가 HTTP 상태
        # 코드로 변환해야 하므로, 여기서 catch-all을 다시 넣으면 모든 실패가
        # 200 응답으로 위장된다.
        if strategy_name != "buy_hold_strategy":
            return await self.run_strategy_portfolio_backtest(request)
        else:
            return await self.run_buy_and_hold_portfolio_backtest(request)
    
    async def run_strategy_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """
        전략 기반 포트폴리오 백테스트 실행
        각 종목에 동일한 전략을 적용하고 투자 금액으로 결합
        """
        try:
            # --- [Custom Metrics] Start Timer ---
            start_time = time.time()
            # ------------------------------------

            # amount/weight 동시 지원: amount가 없고 weight만 있으면 환산
            amounts, total_amount = resolve_strategy_amounts(request.portfolio)

            # --- [Custom Metrics] Ticker Popularity (카디널리티 상한, P2-15) ---
            # 현금(asset_type='cash')은 "티커"가 아니므로 집계 대상에서 제외한다
            # -- 커스텀 현금 이름(예: "예금")이 라벨로 새어나가는 것도 막는다.
            for item in request.portfolio:
                if item.asset_type != 'cash':
                    record_ticker_popularity(item.symbol)
            # ------------------------------------------

            strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
            logger.info(f"전략 기반 백테스트: {strategy_name}, 총 투자금액: ${total_amount:,.2f}")

            # 각 종목별로 전략 백테스트 실행
            outcome = await run_strategy_per_symbol(request, amounts, total_amount, strategy_name)
            portfolio_results = outcome.portfolio_results
            total_portfolio_value = outcome.total_portfolio_value

            if not portfolio_results:
                raise ValueError("모든 종목의 백테스트가 실패했습니다.")

            # 포트폴리오 전체 통계 계산
            portfolio_return, duration_days, annual_return = strategy_headline_returns(
                request, total_amount, total_portfolio_value
            )
            weighted_stats = calculate_weighted_stats(portfolio_results)

            # equity curve, daily returns, weight history 계산
            equity_curve, daily_returns, weight_history = await portfolio_calculator._calculate_realistic_equity_curve(
                request, portfolio_results, total_amount
            )

            # 집계된 equity curve에서 실제 포트폴리오 지표(Sharpe/MDD/AvgDD/Peak/
            # 거래일수)를 계산한다. 종목별 지표의 가중평균은 상관관계와 하락 시점
            # 차이를 무시하므로 포트폴리오 전체의 진짜 지표가 아니다 (P2-08).
            # 일 기준 지표(변동성·상승/하락일·연속일·Win_Rate·Profit_Factor)도 모두
            # 여기서 가져와 buy&hold 경로와 같은 정의를 쓴다 (A-09). 과거에는
            # Win_Rate가 거래 승률의 금액 가중평균, Profit_Factor 폴백이 0.0이라
            # 전략만 바꿔도 같은 필드의 의미가 달라졌다.
            true_portfolio_stats = calculate_true_portfolio_stats(
                equity_curve, daily_returns, total_amount
            )

            # 포트폴리오 통계 (프론트엔드 호환)
            portfolio_statistics = build_strategy_statistics(
                request,
                duration_days=duration_days,
                total_amount=total_amount,
                total_portfolio_value=total_portfolio_value,
                portfolio_return=portfolio_return,
                annual_return=annual_return,
                weighted_stats=weighted_stats,
                true_portfolio_stats=true_portfolio_stats,
            )

            result = build_strategy_response(
                outcome=outcome,
                portfolio_statistics=portfolio_statistics,
                portfolio_return=portfolio_return,
                equity_curve=equity_curve,
                daily_returns=daily_returns,
                weight_history=weight_history,
            )

            logger.info(f"전략 포트폴리오 백테스트 완료: 총 수익률 {portfolio_return:.2f}%")
            
            # --- [Custom Metrics] Record Success ---
            duration = time.time() - start_time
            BACKTEST_PROCESSING_SECONDS.labels(strategy_type="strategy_portfolio").observe(duration)
            observe_stage("simulation", duration)  # A-08: 부가 데이터 단계와 나란히 비교
            logger.info(f"백테스트 단계 소요(초): simulation={duration:.3f}")
            BACKTEST_EXECUTION_TOTAL.labels(strategy_type="strategy_portfolio", status="success").inc()
            # ---------------------------------------
            
            return recursive_serialize(result)
            
        except Exception:
            # --- [Custom Metrics] Record Error ---
            BACKTEST_EXECUTION_TOTAL.labels(strategy_type="strategy_portfolio", status="error").inc()
            # -------------------------------------
            # 로깅만 하고 재발생시킨다 — 에러 dict로 변환하면 @handle_portfolio_errors가
            # 무력화되어 실패가 HTTP 200으로 나간다.
            logger.exception("전략 포트폴리오 백테스트 실행 중 오류 발생")
            raise
    
    async def run_buy_and_hold_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """
        Buy & Hold 포트폴리오 백테스트 실행 (투자 금액 기반)
        현금(CASH)과 주식을 함께 처리, 분할 매수(DCA) 지원
        """
        try:
            # --- [Custom Metrics] Start Timer ---
            start_time = time.time()
            # ------------------------------------

            # 백테스트 기간 계산 (주 수)
            start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')

            # 백테스트 기간을 주 단위로 계산
            backtest_days = (end_date_obj - start_date_obj).days
            backtest_weeks = backtest_days // 7  # 주 단위 (정수 나눗셈)

            logger.info(f"백테스트 기간: {request.start_date} ~ {request.end_date} ({backtest_days}일, {backtest_weeks}주)")

            # Phase 1: 종목별 투자 금액·DCA 정보 (입력 변환)
            builder = BuyHoldAllocationBuilder(start_date_obj, end_date_obj)
            for item in request.portfolio:
                # --- [Custom Metrics] Ticker Popularity (카디널리티 상한, P2-15) ---
                # 현금(asset_type='cash')은 "티커"가 아니므로 집계 대상에서 제외한다
                # -- 커스텀 현금 이름(예: "예금")이 라벨로 새어나가는 것도 막는다.
                if item.asset_type != 'cash':
                    record_ticker_popularity(item.symbol)
                # ------------------------------------------
                builder.add(item)
            allocation = builder.allocation
            amounts = allocation.amounts  # 실제 총 투자 금액 (DCA의 경우 회당 금액 × 횟수)
            dca_info = allocation.dca_info
            cash_amount = allocation.cash_amount

            # Phase 2: 모든 종목 데이터를 병렬로 로드 (Data Loader 위임)
            portfolio_data = {}
            if allocation.symbols_to_load:
                portfolio_data = await self.data_loader.load_stock_data_parallel(
                    symbols_to_load=allocation.symbols_to_load,
                    start_date=request.start_date,
                    end_date=request.end_date
                )

            # 데이터를 불러오지 못한 종목은 분모와 시뮬레이션에서 제외하고 경고로 알린다 (A-03)
            warnings = drop_unloaded_symbols(allocation, portfolio_data)

            # 총 투자 금액 계산
            total_amount = sum(amounts.values())

            # 현금만 있는 경우 처리
            if not portfolio_data and cash_amount > 0:
                logger.info("현금만 있는 포트폴리오로 백테스트 실행")

                result = build_cash_only_response(request, cash_amount, warnings)
                return recursive_serialize(result)
            
            # 주식과 현금이 모두 없는 경우
            if not portfolio_data and cash_amount == 0:
                raise ValueError("포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다.")
            
            # 분할 매수를 고려한 포트폴리오 수익률 계산
            logger.info("분할 매수 및 리밸런싱을 고려한 포트폴리오 수익률 계산 중...")
            portfolio_result = await self.calculate_dca_portfolio_returns(
                portfolio_data, amounts, dca_info, request.start_date, request.end_date,
                request.rebalance_frequency, request.commission
            )
            
            # 통계 계산
            logger.info("포트폴리오 통계 계산 중...")
            statistics = portfolio_calculator.calculate_portfolio_statistics(portfolio_result, total_amount)
            
            # 개별 종목 수익률 (참고용, 현금 포함)과 거래 로그
            individual_returns, strategy_details = build_buy_hold_individual_returns(
                amounts, dca_info, portfolio_data, cash_amount, total_amount, request.start_date
            )

            # 결과 포맷팅
            result = build_buy_hold_response(
                statistics=statistics,
                individual_returns=individual_returns,
                strategy_details=strategy_details,
                amounts=amounts,
                dca_info=dca_info,
                total_amount=total_amount,
                portfolio_result=portfolio_result,
                warnings=warnings,
            )

            logger.info(f"Buy & Hold 포트폴리오 백테스트 완료: 총 수익률 {statistics['Total_Return']:.2f}%")
            
            # --- [Custom Metrics] Record Success ---
            duration = time.time() - start_time
            BACKTEST_PROCESSING_SECONDS.labels(strategy_type="buy_and_hold").observe(duration)
            observe_stage("simulation", duration)  # A-08: 부가 데이터 단계와 나란히 비교
            logger.info(f"백테스트 단계 소요(초): simulation={duration:.3f}")
            BACKTEST_EXECUTION_TOTAL.labels(strategy_type="buy_and_hold", status="success").inc()
            # ---------------------------------------

            return recursive_serialize(result)
            
        except Exception:
            # --- [Custom Metrics] Record Error ---
            BACKTEST_EXECUTION_TOTAL.labels(strategy_type="buy_and_hold", status="error").inc()
            # -------------------------------------
            # 로깅만 하고 재발생시킨다 — 에러 dict로 변환하면 @handle_portfolio_errors가
            # 무력화되어 실패가 HTTP 200으로 나간다.
            logger.exception("Buy & Hold 포트폴리오 백테스트 실행 중 오류 발생")
            raise


# 전역 인스턴스 생성
portfolio_manager_service = PortfolioManagerService()
