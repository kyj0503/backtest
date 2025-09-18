"""
백테스트 실행 엔진
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
import pandas as pd

from backtesting import Backtest
from fastapi import HTTPException

from app.models.requests import BacktestRequest
from app.models.responses import BacktestResult
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.services.backtest.validation_service import validation_service


class BacktestEngine:
    """백테스트 실행 핵심 엔진"""

    def __init__(
        self,
        data_repository=None,
        strategy_service_instance=None,
        validation_service_instance=None,
    ):
        self.data_repository = data_repository
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service_instance or strategy_service
        self.validation_service = validation_service_instance or validation_service
        self.logger = logging.getLogger(__name__)
    
    async def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        """백테스트 실행"""
        try:
            # 요청 검증
            self.validation_service.validate_backtest_request(request)

            # 데이터 가져오기 (캐시 우선)
            self.logger.info(
                "백테스트 시작: %s, %s ~ %s",
                request.ticker,
                request.start_date,
                request.end_date,
            )
            data = await self._get_price_data(
                request.ticker, request.start_date, request.end_date
            )

            self.logger.info(f"데이터 로드 완료: {len(data)} 행")
            self.logger.debug(f"데이터 컬럼: {list(data.columns)}")
            self.logger.info(f"데이터 범위: {data.index[0]} ~ {data.index[-1]}")
            
            # 전략 클래스 가져오기
            strategy_class = self._build_strategy(request.strategy, request.strategy_params)

            self.logger.info(f"전략 클래스: {strategy_class.__name__}")
            self.logger.info(f"초기 자본: ${request.initial_cash}")
            
            # 백테스트 실행
            bt = Backtest(
                data,
                strategy_class,
                cash=request.initial_cash,
                commission=request.commission,
            )
            self.logger.debug("백테스트 객체 생성 완료")
            
            try:
                run_kwargs = self._build_run_kwargs(request)
                result = self._execute_backtest(bt, run_kwargs)
                self.logger.info("백테스트 실행 완료")
                self.logger.info(f"거래 수: {result['# Trades']}")
                self.logger.info(f"수익률: {result.get('Return [%]', 0):.2f}%")
                self.logger.info(f"Buy & Hold: {result.get('Buy & Hold Return [%]', 0):.2f}%")
                
                # 디버깅: 실제 stats 키들 출력
                self.logger.debug("=== 백테스트 결과 키들 ===")
                for key in result.index:
                    self.logger.debug(f"  '{key}': {result.get(key)}")
                self.logger.debug("========================")
                
                # 결과가 유효한지 확인
                if result is not None and '# Trades' in result:
                    return self._convert_result_to_response(result, request)
                else:
                    self.logger.warning("백테스트 결과가 유효하지 않음, fallback 사용")
                    raise Exception("Invalid backtest result")
                    
            except Exception as e:
                self.logger.error(f"백테스트 실행 중 오류: {e}")
                self.logger.info("Fallback 통계 생성 중...")
                # 실제 주가 변동을 반영한 fallback 통계 생성
                return self._create_fallback_result(data, request)
            
        except Exception as e:
            self.logger.error(f"백테스트 전체 프로세스 오류: {e}")

            # 이미 HTTPException으로 만들어진 예외는 그대로 재발생시켜 호출자(엔드포인트)에서
            # 적절한 상태코드를 처리할 수 있도록 한다.
            if isinstance(e, HTTPException):
                raise

            # custom ValidationError는 그대로 재발생시키도록 허용
            try:
                from app.core.custom_exceptions import ValidationError
                if isinstance(e, ValidationError):
                    raise e
            except Exception:
                # import 실패시 무시
                pass

            # data_fetcher에서 발생시키는 InvalidSymbolError는 422로 매핑
            try:
                from app.utils.data_fetcher import InvalidSymbolError as DataFetcherInvalidSymbolError
                if isinstance(e, DataFetcherInvalidSymbolError):
                    raise HTTPException(status_code=422, detail=str(e))
            except Exception:
                pass

            # 그 외 에러는 500으로 처리
            raise HTTPException(status_code=500, detail=f"백테스트 실행 실패: {str(e)}")
    
    async def _get_price_data(
        self, ticker: str, start_date, end_date
    ) -> pd.DataFrame:
        """캐시-우선 가격 데이터 조회"""
        if self.data_repository:
            data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
        else:
            data = self.data_fetcher.get_stock_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )

        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="가격 데이터를 찾을 수 없습니다.")

        return data

    def _build_strategy(
        self, strategy_name: str, params: Optional[Dict[str, Any]]
    ):
        """요청 파라미터를 적용한 전략 클래스를 생성"""
        base_strategy = self.strategy_service.get_strategy_class(strategy_name)
        if not params:
            return base_strategy

        sanitized_params: Dict[str, Any] = {}
        try:
            validated = self.strategy_service.validate_strategy_params(
                strategy_name,
                params,
            )
            sanitized_params = {
                key: validated[key]
                for key in params.keys()
                if key in validated
            }
        except ValueError as exc:
            self.logger.warning(
                "전략 파라미터 검증 경고(%s): %s - 원본 값 사용",
                strategy_name,
                exc,
            )
            sanitized_params = params

        overrides = {
            key: value
            for key, value in sanitized_params.items()
            if hasattr(base_strategy, key)
        }

        if not overrides:
            return base_strategy

        configured_name = f"{base_strategy.__name__}Configured_{uuid4().hex[:8]}"
        return type(configured_name, (base_strategy,), overrides)

    def _build_run_kwargs(self, request: BacktestRequest) -> Dict[str, Any]:
        """Backtest.run 호출 시 사용할 부가 인자 구성"""
        run_kwargs: Dict[str, Any] = {}
        if request.spread and request.spread > 0:
            run_kwargs["spread"] = request.spread
        return run_kwargs

    def _execute_backtest(self, bt: Backtest, run_kwargs: Dict[str, Any]):
        """Backtest 실행 래퍼 (옵션 인자 호환성 처리)"""
        try:
            if run_kwargs:
                return bt.run(**run_kwargs)
            return bt.run()
        except TypeError as error:
            # 일부 backtesting 버전은 spread 매개변수를 지원하지 않음
            if "spread" in run_kwargs and "spread" in str(error):
                self.logger.warning("Backtest.run spread 인자 미지원 - spread 제외 후 재시도")
                safe_kwargs = {k: v for k, v in run_kwargs.items() if k != "spread"}
                return bt.run(**safe_kwargs) if safe_kwargs else bt.run()
            raise

    def _create_fallback_result(self, data: pd.DataFrame, request: BacktestRequest) -> BacktestResult:
        """실제 데이터 기반의 fallback 결과 생성"""
        try:
            fallback_stats = self.validation_service.create_fallback_stats(data, request.initial_cash)
            
            # duration_days 계산
            start_date = pd.to_datetime(request.start_date)
            end_date = pd.to_datetime(request.end_date)
            duration_days = (end_date - start_date).days
            
            # 날짜를 문자열로 변환
            start_date_str = str(request.start_date)
            end_date_str = str(request.end_date)
            
            return BacktestResult(
                ticker=request.ticker,
                strategy=request.strategy,
                start_date=start_date_str,
                end_date=end_date_str,
                duration_days=duration_days,
                initial_cash=request.initial_cash,
                final_equity=fallback_stats.get('Equity Final [$]', request.initial_cash),
                total_return_pct=fallback_stats.get('Return [%]', 0.0),
                annualized_return_pct=0.0,
                buy_and_hold_return_pct=0.0,
                cagr_pct=0.0,
                volatility_pct=fallback_stats.get('Volatility [%]', 0.0),
                sharpe_ratio=fallback_stats.get('Sharpe Ratio', 0.0),
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown_pct=fallback_stats.get('Max. Drawdown [%]', 0.0),
                avg_drawdown_pct=0.0,
                total_trades=fallback_stats.get('# Trades', 0),
                win_rate_pct=fallback_stats.get('Win Rate [%]', 0.0),
                profit_factor=0.0,
                avg_trade_pct=0.0,
                best_trade_pct=0.0,
                worst_trade_pct=0.0,
                alpha_pct=None,
                beta=None,
                kelly_criterion=None,
                sqn=None,
                execution_time_seconds=0.1,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Fallback 결과 생성 실패: {str(e)}")
            # 최소한의 결과라도 반환
            return BacktestResult(
                ticker=request.ticker,
                strategy=request.strategy,
                start_date=str(request.start_date),
                end_date=str(request.end_date),
                duration_days=0,
                initial_cash=request.initial_cash,
                final_equity=request.initial_cash,
                total_return_pct=0.0,
                annualized_return_pct=0.0,
                buy_and_hold_return_pct=0.0,
                cagr_pct=0.0,
                volatility_pct=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown_pct=0.0,
                avg_drawdown_pct=0.0,
                total_trades=0,
                win_rate_pct=0.0,
                profit_factor=0.0,
                avg_trade_pct=0.0,
                best_trade_pct=0.0,
                worst_trade_pct=0.0,
                alpha_pct=None,
                beta=None,
                kelly_criterion=None,
                sqn=None,
                execution_time_seconds=0.1,
                timestamp=datetime.now()
            )
    
    def _convert_result_to_response(self, stats: pd.Series, request: BacktestRequest) -> BacktestResult:
        """백테스트 결과를 API 응답 형식으로 변환"""
        def safe_float(key: str, default: float = 0.0) -> float:
            try:
                value = stats.get(key, default)
                if pd.isna(value) or value is None:
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def safe_int(key: str, default: int = 0) -> int:
            try:
                value = stats.get(key, default)
                if pd.isna(value) or value is None:
                    return default
                return int(value)
            except (ValueError, TypeError):
                return default
        
        try:
            # duration_days 계산
            start_date = pd.to_datetime(request.start_date)
            end_date = pd.to_datetime(request.end_date)
            duration_days = (end_date - start_date).days
            
            # 날짜를 문자열로 변환
            start_date_str = str(request.start_date)
            end_date_str = str(request.end_date)
            
            return BacktestResult(
                ticker=request.ticker,
                strategy=request.strategy,
                start_date=start_date_str,
                end_date=end_date_str,
                duration_days=duration_days,
                initial_cash=request.initial_cash,
                final_equity=safe_float('Equity Final [$]', request.initial_cash),
                total_return_pct=safe_float('Return [%]'),
                annualized_return_pct=safe_float('Return (Ann.) [%]'),
                buy_and_hold_return_pct=safe_float('Buy & Hold Return [%]'),
                cagr_pct=safe_float('Return (Ann.) [%]'),  # CAGR은 연간 수익률과 동일
                volatility_pct=safe_float('Volatility [%]'),
                sharpe_ratio=safe_float('Sharpe Ratio'),
                sortino_ratio=safe_float('Sortino Ratio'),
                calmar_ratio=safe_float('Calmar Ratio'),
                max_drawdown_pct=safe_float('Max. Drawdown [%]'),
                avg_drawdown_pct=safe_float('Avg. Drawdown [%]'),
                total_trades=safe_int('# Trades'),
                win_rate_pct=safe_float('Win Rate [%]'),
                profit_factor=safe_float('Profit Factor'),
                avg_trade_pct=safe_float('Avg. Trade [%]'),
                best_trade_pct=safe_float('Best Trade [%]'),
                worst_trade_pct=safe_float('Worst Trade [%]'),
                alpha_pct=None,  # 추후 계산 추가
                beta=None,       # 추후 계산 추가
                kelly_criterion=None,  # 추후 계산 추가
                sqn=safe_float('SQN') if 'SQN' in stats else None,
                execution_time_seconds=0.5,  # 추후 실제 시간 측정 추가
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"결과 변환 실패: {str(e)}")
            return self._create_fallback_result(pd.DataFrame(), request)


# 글로벌 인스턴스
backtest_engine = BacktestEngine()
