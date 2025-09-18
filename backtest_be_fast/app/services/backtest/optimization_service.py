"""
최적화 서비스
"""
import time
import signal
import logging
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4
import pandas as pd

from backtesting import Backtest
from app.models.requests import OptimizationRequest
from app.models.responses import OptimizationResult, BacktestResult
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.core.config import settings


class OptimizationService:
    """파라미터 최적화 전담 서비스"""
    
    def __init__(self, data_repository=None, strategy_service_instance=None):
        self.data_repository = data_repository
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service_instance or strategy_service
        self.logger = logging.getLogger(__name__)
    
    async def optimize_strategy(self, request: OptimizationRequest) -> OptimizationResult:
        """
        전략 파라미터 최적화
        
        Args:
            request: 최적화 요청
            
        Returns:
            최적화 결과
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"최적화 시작: {request.ticker}, {request.strategy}")
            
            # 1. 데이터 수집
            data = await self._get_price_data(
                request.ticker, request.start_date, request.end_date
            )
            
            # 2. 전략 클래스 준비
            strategy_class = self._clone_strategy(
                self.strategy_service.get_strategy_class(request.strategy)
            )
            
            # 3. 백테스트 설정
            bt = Backtest(
                data=data,
                strategy=strategy_class,
                cash=request.initial_cash,
                commission=request.commission,
                exclusive_orders=True,
            )
            
            # 4. 최적화 파라미터 범위 변환
            param_ranges = self._convert_param_ranges(request.param_ranges)
            
            # 5. 최적화 실행 (타임아웃 적용)
            stats, best_params = self._run_optimization_with_timeout(
                bt, param_ranges, request
            )
            
            # 6. 최적 파라미터로 최종 백테스트 실행
            final_stats = self._run_final_backtest(bt, best_params)
            
            # 7. 결과 변환
            execution_time = time.time() - start_time
            backtest_result = self._convert_stats_to_backtest_result(
                final_stats, request, execution_time
            )
            
            # 최적화된 성능 지표 값 추출
            best_score = float(stats.get(request.maximize, 0))
            if best_score == 0:
                best_score = float(final_stats.get(request.maximize, 0))
            
            result = OptimizationResult(
                ticker=request.ticker,
                strategy=request.strategy,
                method=request.method.value,
                total_iterations=request.max_tries or 100,
                best_params=best_params,
                best_score=best_score,
                optimization_target=request.maximize,
                backtest_result=backtest_result,
                execution_time_seconds=execution_time,
                timestamp=datetime.now()
            )
            
            self.logger.info(f"최적화 완료: {request.ticker}, 실행시간: {execution_time:.2f}초")
            return result
            
        except Exception as e:
            self.logger.error(f"최적화 실행 실패: {str(e)}")
            raise
    
    def _convert_param_ranges(self, param_ranges: Dict[str, list]) -> Dict[str, range]:
        """최적화 파라미터 범위를 range 객체로 변환"""
        converted = {}
        for param, value_list in param_ranges.items():
            if isinstance(value_list, list) and len(value_list) >= 2:
                try:
                    start = int(value_list[0])
                    end = int(value_list[-1])
                    step = int(value_list[1] - value_list[0]) if len(value_list) > 2 else 1
                    converted[param] = range(start, end + 1, step)
                except (ValueError, IndexError):
                    self.logger.warning(f"파라미터 {param}의 범위 변환 실패, 건너뜀")
                    continue
        return converted
    
    def _run_optimization_with_timeout(self, bt: Backtest, param_ranges: Dict, request: OptimizationRequest):
        """타임아웃을 적용한 최적화 실행"""
        try:
            # 타임아웃 설정
            def timeout_handler(signum, frame):
                raise TimeoutError(f"최적화가 {settings.optimization_timeout_seconds}초 내에 완료되지 않았습니다.")
            
            # Windows에서는 signal.SIGALRM이 지원되지 않으므로 조건부 적용
            timeout_applied = False
            try:
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(settings.optimization_timeout_seconds)
                    timeout_applied = True
            except (AttributeError, OSError):
                self.logger.warning("신호 기반 타임아웃을 설정할 수 없습니다 (Windows 환경)")
            
            # 최적화 실행
            stats = bt.optimize(
                **param_ranges,
                maximize=request.maximize,
                method=request.method.value,
                max_tries=request.max_tries or settings.max_optimization_iterations,
                random_state=42
            )
            
            # 타임아웃 해제
            if timeout_applied:
                signal.alarm(0)
            
            # 최적 파라미터 추출
            best_params = {}
            for param in param_ranges.keys():
                if hasattr(stats._strategy, param):
                    best_params[param] = getattr(stats._strategy, param)
            
            return stats, best_params
            
        except TimeoutError as e:
            self.logger.warning(f"최적화 타임아웃: {str(e)}")
            # 타임아웃 시 기본 파라미터로 백테스트 실행
            default_params = self.strategy_service.validate_strategy_params(
                request.strategy, {}
            )
            try:
                safe_params = {k: v for k, v in default_params.items() if k != 'optimize'}
                stats = bt.run(**safe_params)
                return stats, default_params
            except Exception as run_e:
                self.logger.error(f"기본 파라미터 실행도 실패: {str(run_e)}")
                raise
        except Exception as e:
            self.logger.error(f"최적화 중 오류: {str(e)}")
            raise
    
    def _run_final_backtest(self, bt: Backtest, best_params: Dict[str, Any]):
        """최적 파라미터로 최종 백테스트 실행"""
        try:
            # 최적 파라미터로 백테스트 재실행
            final_stats = bt.run(**best_params)
            return final_stats
        except Exception as e:
            self.logger.warning(f"최적 파라미터 실행 오류, 기본 실행으로 대체: {str(e)}")
            try:
                final_stats = bt.run()
                return final_stats
            except Exception as e2:
                self.logger.warning(f"기본 실행도 실패: {str(e2)}")
                # 마지막 수단: 더미 통계 생성
                return self._create_fallback_stats()
    
    def _convert_stats_to_backtest_result(self, stats: pd.Series, request: OptimizationRequest, execution_time: float = 0.0) -> BacktestResult:
        """백테스트 통계를 BacktestResult로 변환"""
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
            # duration_days 계산 (request의 날짜 타입은 date/str 가능)
            import pandas as _pd
            start_date = _pd.to_datetime(request.start_date)
            end_date = _pd.to_datetime(request.end_date)
            duration_days = (end_date - start_date).days

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
                cagr_pct=safe_float('Return (Ann.) [%]'),
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
                alpha_pct=None,
                beta=None,
                kelly_criterion=None,
                sqn=safe_float('SQN') if 'SQN' in stats else None,
                execution_time_seconds=execution_time,
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"결과 변환 실패: {str(e)}")
            # 간단한 폴백 BacktestResult 반환
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
                execution_time_seconds=execution_time,
                timestamp=datetime.now()
            )

    async def _get_price_data(self, ticker, start_date, end_date) -> pd.DataFrame:
        """캐시 우선 데이터 조회"""
        if self.data_repository:
            data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
        else:
            data = self.data_fetcher.get_stock_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )

        if data is None or data.empty:
            raise ValueError("최적화에 사용할 가격 데이터를 찾지 못했습니다.")

        return data

    def _clone_strategy(self, base_strategy):
        """전략 클래스를 복제해 최적화 시 전역 상태 오염 방지.

        multiprocessing 환경에서 동적 타입을 pickling할 수 없어서 에러가 발생합니다.
        이를 피하기 위해 모듈 레벨에 이름이 있는 클래스를 생성하고 반환합니다.
        """
        # 안전한 이름 생성
        clone_name = f"{base_strategy.__name__}Optim_{uuid4().hex[:8]}"

        # 모듈 globals에 클래스를 추가하면 pickle이 이름으로 참조할 수 있습니다.
        if clone_name in globals():
            return globals()[clone_name]

        NewClass = type(clone_name, (base_strategy,), {})
        # 명시적으로 모듈을 현재 모듈로 설정하면 pickle이 이름으로 클래스를 찾을 수 있습니다.
        try:
            NewClass.__module__ = __name__
        except Exception:
            pass
        globals()[clone_name] = NewClass
        return NewClass
    
    def _create_fallback_stats(self):
        """폴백용 기본 통계"""
        return {
            'Equity Final [$]': 10000,
            'Return [%]': 0.0,
            '# Trades': 0,
            'Win Rate [%]': 0.0,
            'Best Trade [%]': 0.0,
            'Worst Trade [%]': 0.0,
            'Max. Drawdown [%]': 0.0,
            'Sharpe Ratio': 0.0,
            'Volatility [%]': 0.0
        }


# 글로벌 인스턴스
optimization_service = OptimizationService()
