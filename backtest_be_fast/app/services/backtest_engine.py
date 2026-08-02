"""백테스트 실행 엔진

backtesting.py 라이브러리를 래핑하여 백테스트를 실행하고 결과를 표준 형식으로 변환합니다.
"""
import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List, Type
from uuid import uuid4
import pandas as pd
import numpy as np

from backtesting import Backtest, Strategy
from fastapi import HTTPException

from app.schemas.requests import BacktestRequest
from app.schemas.responses import BacktestResult
from app.utils.data_fetcher import data_fetcher
from app.repositories.data_repository import data_repository
from app.services.strategy_service import strategy_service
from app.services.validation_service import validation_service
from app.core.exceptions import ValidationError
from app.constants.currencies import SUPPORTED_CURRENCIES
from app.utils.currency_converter import currency_converter
from app.utils.type_converters import safe_float, safe_int


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
            self.validation_service.validate_backtest_request(request)

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

            data = await self._convert_to_usd(request.ticker, data, request.start_date, request.end_date)

            strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
            strategy_class = self._build_strategy(strategy_name, request.strategy_params)

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
            
            run_kwargs = self._build_run_kwargs(request)
            # FIXED: Wrap synchronous bt.run() with asyncio.to_thread() (async/sync boundary)
            result = await asyncio.to_thread(self._execute_backtest, bt, run_kwargs)
            self.logger.info("백테스트 실행 완료")
            self.logger.info(f"거래 수: {result['# Trades']}")
            self.logger.info(f"수익률: {result.get('Return [%]', 0):.2f}%")
            self.logger.info(f"Buy & Hold: {result.get('Buy & Hold Return [%]', 0):.2f}%")

            # 디버깅: 실제 stats 키들 출력
            self.logger.debug("=== 백테스트 결과 키들 ===")
            for key in result.index:
                self.logger.debug(f"  '{key}': {result.get(key)}")
            self.logger.debug("========================")

            # 참고: 위 83행의 `result['# Trades']`가 이미 이 키를 무조건 역참조한다.
            # 그 키가 없다면(또는 result가 None이라면) 83행에서 먼저 KeyError/TypeError가
            # 발생해 이 지점에 도달하기 전에 아래 except 블록으로 빠진다. 즉 이 시점에
            # 도달했다면 '# Trades' in result는 항상 참이다. 과거에는 이 사실이 없는
            # 것처럼 "무효한 결과" 분기를 두고 실제로 실행된 거래가 없는데도
            # `_create_fallback_result()`로 Win Rate 100%/거래 1건 같은 조작된 통계를
            # HTTP 200 성공으로 반환했다(P3-21). 그 분기는 도달 불가능한 죽은 코드였다.
            return self._convert_result_to_response(result, request)

        except Exception as e:
            self.logger.error(f"백테스트 전체 프로세스 오류: {e}")

            # 이미 HTTPException으로 만들어진 예외는 그대로 재발생시켜 호출자(엔드포인트)에서
            # 적절한 상태코드를 처리할 수 있도록 한다. ValidationError와
            # InvalidSymbolError는 모두 HTTPException의 서브클래스이므로 이 분기에서
            # 이미 처리된다 (별도의 isinstance 분기가 필요 없다 — 과거에는 아래에
            # 도달 불가능한 ValidationError/InvalidSymbolError 전용 분기가 있었는데,
            # 그중 ValidationError 분기는 `try: raise e / except Exception: pass`로
            # 자기 자신이 던진 예외를 즉시 삼켜버리는 자기 무력화 버그까지 있었다).
            if isinstance(e, HTTPException):
                raise

            # 그 외 에러는 500으로 처리
            raise HTTPException(status_code=500, detail=f"백테스트 실행 실패: {str(e)}")
    
    async def _get_price_data(
        self, ticker: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """캐시-우선 가격 데이터 조회"""
        if self.data_repository:
            data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
        else:
            # 동기 data_fetcher를 안전하게 async로 실행
            data = await asyncio.to_thread(
                self.data_fetcher.fetch_stock_data,
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )

        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"가격 데이터를 찾을 수 없습니다: {ticker}")

        return data

    async def _convert_to_usd(
        self, ticker: str, data: pd.DataFrame, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """비USD 통화의 가격 데이터를 USD로 변환"""
        return await currency_converter.convert_dataframe_to_usd(
            ticker=ticker,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

    def _build_strategy(
        self, strategy_name: str, params: Optional[Dict[str, Any]]
    ) -> Type[Strategy]:
        """요청 파라미터를 적용한 전략 클래스를 생성"""
        base_strategy = self.strategy_service.get_strategy_class(strategy_name)
        if not params:
            return base_strategy

        try:
            validated = self.strategy_service.validate_strategy_params(
                strategy_name,
                params,
            )
        except ValueError as exc:
            self.logger.warning(
                "전략 파라미터 검증 실패(%s): %s",
                strategy_name,
                exc,
            )
            raise ValidationError(str(exc)) from exc

        sanitized_params: Dict[str, Any] = {
            key: validated[key]
            for key in params.keys()
            if key in validated
        }

        overrides = {
            key: value
            for key, value in sanitized_params.items()
            if hasattr(base_strategy, key)
        }

        if not overrides:
            return base_strategy

        override_details = ", ".join([f"{k}={v}" for k, v in overrides.items()])
        self.logger.info(
            f"전략 파라미터 오버라이드 ({strategy_name}): {override_details}"
        )

        configured_name = f"{base_strategy.__name__}Configured_{uuid4().hex[:8]}"
        return type(configured_name, (base_strategy,), overrides)

    def _build_run_kwargs(self, request: BacktestRequest) -> Dict[str, Any]:
        """Backtest.run 호출 시 사용할 부가 인자 구성"""
        run_kwargs: Dict[str, Any] = {}
        if request.spread and request.spread > 0:
            run_kwargs["spread"] = request.spread
        return run_kwargs

    def _execute_backtest(self, bt: Backtest, run_kwargs: Dict[str, Any]) -> pd.Series:
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
                trade_log=[],
                execution_time_seconds=0.1,
                timestamp=datetime.now()
            )

    def _convert_result_to_response(self, stats: pd.Series, request: BacktestRequest) -> BacktestResult:
        """백테스트 결과를 API 응답 형식으로 변환"""
        try:
            # duration_days 계산
            start_date = pd.to_datetime(request.start_date)
            end_date = pd.to_datetime(request.end_date)
            duration_days = (end_date - start_date).days

            # 날짜를 문자열로 변환
            start_date_str = str(request.start_date)
            end_date_str = str(request.end_date)

            trade_log: List[Dict[str, Any]] = []
            trades_df = stats.get('_trades') if hasattr(stats, 'get') else None
            if isinstance(trades_df, pd.DataFrame) and not trades_df.empty:
                trade_log = trades_df.fillna(0).to_dict(orient='records')

            alpha_pct = None
            beta_value = None

            # equity_curve 추출 (전략 실행 결과)
            equity_curve_dict = None
            equity_curve_df = stats.get('_equity_curve') if hasattr(stats, 'get') else None
            if isinstance(equity_curve_df, pd.DataFrame) and not equity_curve_df.empty:
                try:
                    # DataFrame을 Dict[str, float]로 변환
                    equity_curve_dict = {}
                    for idx, row in equity_curve_df.iterrows():
                        date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
                        equity_curve_dict[date_str] = float(row['Equity'])
                except Exception as e:
                    self.logger.warning(f"equity curve 변환 실패: {e}")
                    equity_curve_dict = None

            if getattr(request, 'benchmark_ticker', None):
                try:
                    self.logger.info(f"벤치마크 데이터 로딩 중: {request.benchmark_ticker}")
                    benchmark = self.data_fetcher.fetch_stock_data(
                        ticker=request.benchmark_ticker,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if (
                        benchmark is not None and not benchmark.empty
                        and isinstance(equity_curve_df, pd.DataFrame) and not equity_curve_df.empty
                    ):
                        self.logger.debug(
                            f"벤치마크 데이터 로드 완료: {len(benchmark)} 포인트, "
                            f"전략 equity curve: {len(equity_curve_df)} 포인트"
                        )
                        strat_returns = equity_curve_df['Equity'].pct_change().dropna()
                        bench_returns = benchmark['Close'].pct_change().dropna()
                        strat_returns, bench_returns = strat_returns.align(bench_returns, join='inner')
                        if len(strat_returns) > 1 and bench_returns.var() != 0:
                            cov_matrix = np.cov(strat_returns, bench_returns)
                            cov = cov_matrix[0][1]
                            var_bench = bench_returns.var()
                            if var_bench != 0:
                                beta_value = cov / var_bench
                                mean_strat = strat_returns.mean()
                                mean_bench = bench_returns.mean()
                                alpha_pct = (mean_strat - beta_value * mean_bench) * 100
                                beta_value = float(beta_value)
                                alpha_pct = float(alpha_pct)
                                self.logger.info(
                                    f"Alpha/Beta 계산 완료: Alpha={alpha_pct:.2f}%, Beta={beta_value:.3f} "
                                    f"(전략 평균 수익률={mean_strat*100:.3f}%, 벤치마크 평균 수익률={mean_bench*100:.3f}%)"
                                )
                        else:
                            self.logger.warning("Alpha/Beta 계산 불가: 데이터 포인트 부족 또는 벤치마크 분산 0")
                    else:
                        self.logger.warning(f"벤치마크 데이터 없음 또는 equity curve 없음")
                except Exception as e:
                    self.logger.warning(f"Alpha/Beta 계산 실패: {e}")

            return BacktestResult(
                ticker=request.ticker,
                strategy=request.strategy,
                start_date=start_date_str,
                end_date=end_date_str,
                duration_days=duration_days,
                initial_cash=request.initial_cash,
                final_equity=safe_float(stats.get('Equity Final [$]', request.initial_cash)),
                total_return_pct=safe_float(stats.get('Return [%]', 0.0)),
                annualized_return_pct=safe_float(stats.get('Return (Ann.) [%]', 0.0)),
                buy_and_hold_return_pct=safe_float(stats.get('Buy & Hold Return [%]', 0.0)),
                cagr_pct=safe_float(stats.get('Return (Ann.) [%]', 0.0)),  # CAGR은 연간 수익률과 동일
                # backtesting.py 0.3.3은 연환산 변동성을 'Volatility (Ann.) [%]'로
                # 내보낸다. 과거에는 존재하지 않는 'Volatility [%]'를 읽어
                # .get 기본값 때문에 항상 0.0이 보고됐다.
                volatility_pct=safe_float(
                    stats.get('Volatility (Ann.) [%]', stats.get('Volatility [%]', 0.0))
                ),
                sharpe_ratio=safe_float(stats.get('Sharpe Ratio', 0.0)),
                sortino_ratio=safe_float(stats.get('Sortino Ratio', 0.0)),
                calmar_ratio=safe_float(stats.get('Calmar Ratio', 0.0)),
                max_drawdown_pct=safe_float(stats.get('Max. Drawdown [%]', 0.0)),
                avg_drawdown_pct=safe_float(stats.get('Avg. Drawdown [%]', 0.0)),
                total_trades=safe_int(stats.get('# Trades', 0)),
                win_rate_pct=safe_float(stats.get('Win Rate [%]', 0.0)),
                profit_factor=safe_float(stats.get('Profit Factor', 0.0)),
                avg_trade_pct=safe_float(stats.get('Avg. Trade [%]', 0.0)),
                best_trade_pct=safe_float(stats.get('Best Trade [%]', 0.0)),
                worst_trade_pct=safe_float(stats.get('Worst Trade [%]', 0.0)),
                alpha_pct=alpha_pct,
                beta=beta_value,
                kelly_criterion=None,  # 추후 계산 추가
                sqn=safe_float(stats.get('SQN', 0.0)) if 'SQN' in stats else None,
                trade_log=trade_log,
                equity_curve=equity_curve_dict,  # 일일 자산 가치
                execution_time_seconds=0.5,  # 추후 실제 시간 측정 추가
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"결과 변환 실패: {str(e)}")
            # 이전에는 여기서 _create_fallback_result(pd.DataFrame(), request)를 호출해
            # 완전히 조작된(전부 0인) 결과를 HTTP 200 성공으로 반환했다(P3-21). 실제
            # 백테스트는 성공했는데 결과를 응답 스키마로 변환하는 과정에서만 실패한
            # 것이므로, 실패를 성공으로 위장하지 않고 그대로 실패로 표면화한다 —
            # run_backtest()의 예외 처리기가 이를 500으로 매핑한다.
            raise HTTPException(
                status_code=500,
                detail=f"백테스트 결과 변환에 실패했습니다: {request.ticker}"
            ) from e


# 글로벌 인스턴스
backtest_engine = BacktestEngine(data_repository=data_repository)
