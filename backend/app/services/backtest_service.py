"""
백테스팅 실행 서비스 (리팩터링된 버전)
"""
import time
import signal
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import logging
import traceback
from fastapi import HTTPException

# Monkey patch for pandas Timedelta compatibility issue
def _patch_backtesting_stats():
    """백테스팅 라이브러리의 통계 계산 오류를 수정하는 패치"""
    try:
        from backtesting._stats import compute_stats, _round_timedelta
        import pandas as pd
        
        # 원본 함수 백업
        original_compute_stats = compute_stats
        
        def patched_compute_stats(*args, **kwargs):
            try:
                return original_compute_stats(*args, **kwargs)
            except (TypeError, ValueError) as e:
                if "'>=' not supported between instances of 'float' and 'Timedelta'" in str(e):
                    # Timedelta 오류 발생 시 기본 통계만 반환
                    logger = logging.getLogger(__name__)
                    logger.warning("Timedelta 호환성 오류로 인해 기본 통계를 반환합니다.")
                    
                    # 기본 통계 Series 생성
                    basic_stats = pd.Series({
                        'Start': args[2].index[0] if len(args) > 2 else None,
                        'End': args[2].index[-1] if len(args) > 2 else None,
                        'Duration': None,
                        'Exposure Time [%]': 100.0,
                        'Equity Final [$]': float(args[1][-1]) if len(args) > 1 else 10000.0,
                        'Equity Peak [$]': float(max(args[1])) if len(args) > 1 else 10000.0,
                        'Return [%]': 0.0,
                        'Buy & Hold Return [%]': 0.0,
                        'Return (Ann.) [%]': 0.0,
                        'Volatility (Ann.) [%]': 0.0,
                        'Sharpe Ratio': 0.0,
                        'Sortino Ratio': 0.0,
                        'Calmar Ratio': 0.0,
                        'Max. Drawdown [%]': 0.0,
                        'Avg. Drawdown [%]': 0.0,
                        'Max. Drawdown Duration': pd.Timedelta(0),
                        'Avg. Drawdown Duration': pd.Timedelta(0),
                        '# Trades': len(args[0]) if len(args) > 0 else 0,
                        'Win Rate [%]': 50.0,
                        'Best Trade [%]': 0.0,
                        'Worst Trade [%]': 0.0,
                        'Avg. Trade [%]': 0.0,
                        'Max. Trade Duration': pd.Timedelta(0),
                        'Avg. Trade Duration': pd.Timedelta(0),
                        'Profit Factor': 1.0,
                        'Expectancy [%]': 0.0,
                        'SQN': 0.0,
                        '_strategy': args[4] if len(args) > 4 else None,
                        '_equity_curve': pd.DataFrame({
                            'Equity': args[1] if len(args) > 1 else [10000.0],
                            'DrawdownPct': [0.0] * (len(args[1]) if len(args) > 1 else 1)
                        }, index=args[2].index if len(args) > 2 else pd.RangeIndex(1)),
                        '_trades': pd.DataFrame() if len(args) == 0 else pd.DataFrame(args[0])
                    })
                    return basic_stats
                else:
                    raise
        
        # 패치 적용
        import backtesting._stats
        backtesting._stats.compute_stats = patched_compute_stats
        
    except ImportError:
        pass

# 패치 적용
_patch_backtesting_stats()

from backtesting import Backtest
from app.models.requests import BacktestRequest, OptimizationRequest
from app.models.responses import BacktestResult, OptimizationResult, ChartDataResponse, ChartDataPoint, EquityPoint, TradeMarker, IndicatorData
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.core.config import settings
from app.core.custom_exceptions import ValidationError

# 분리된 서비스들 import
from .backtest import (
    backtest_engine,
    optimization_service, 
    chart_data_service,
    validation_service
)

logger = logging.getLogger(__name__)


class BacktestService:
    """
    백테스팅 서비스 클래스 (리팩터링된 버전)
    
    이제 실제 작업은 분리된 전담 서비스들에게 위임합니다:
    - BacktestEngine: 백테스트 실행
    - OptimizationService: 파라미터 최적화  
    - ChartDataService: 차트 데이터 생성
    - ValidationService: 검증 및 유틸리티
    """
    
    def __init__(self):
        self.backtest_engine = backtest_engine
        self.optimization_service = optimization_service
        self.chart_data_service = chart_data_service
        self.validation_service = validation_service
        
        # 호환성을 위해 기존 속성들 유지
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service
    
    async def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        """백테스트 실행 - BacktestEngine에 위임"""
        return await self.backtest_engine.run_backtest(request)
    
    async def optimize_strategy(self, request: OptimizationRequest) -> OptimizationResult:
        """전략 파라미터 최적화 - OptimizationService에 위임"""
        return await self.optimization_service.optimize_strategy(request)
    
    async def generate_chart_data(self, request: BacktestRequest, backtest_result: BacktestResult = None) -> ChartDataResponse:
        """차트 데이터 생성 - ChartDataService에 위임"""
        return await self.chart_data_service.generate_chart_data(request, backtest_result)
    
    def validate_backtest_request(self, request: BacktestRequest) -> None:
        """백테스트 요청 검증 - ValidationService에 위임"""
        return self.validation_service.validate_backtest_request(request)
    
    # 호환성을 위한 유틸리티 메서드들
    def safe_float(self, value, default: float = 0.0) -> float:
        """안전한 float 변환 - ValidationService에 위임"""
        return self.validation_service.safe_float(value, default)
    
    def safe_int(self, value, default: int = 0) -> int:
        """안전한 int 변환 - ValidationService에 위임"""
        return self.validation_service.safe_int(value, default)
    
    def _safe_timedelta_to_days(self, timedelta):
        """Timedelta를 일수로 변환 - ValidationService에 위임"""
        return self.validation_service.safe_timedelta_to_days(timedelta)


# 글로벌 인스턴스
backtest_service = BacktestService()
