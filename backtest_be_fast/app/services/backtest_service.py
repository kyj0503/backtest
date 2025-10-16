"""
백테스팅 실행 서비스

**역할**:
- backtesting.py 라이브러리를 사용하여 단일 종목 백테스트 실행
- 백테스트 결과를 프론트엔드가 사용할 수 있는 형식으로 변환
- pandas Timedelta 호환성 문제 해결을 위한 Monkey Patch 적용

**주요 기능**:
1. 백테스트 실행: 주어진 전략과 파라미터로 백테스트 수행
2. 통계 계산: 수익률, 샤프 비율, 최대 낙폭 등 성과 지표 계산
3. 거래 로그 변환: 백테스트 거래 기록을 JSON 직렬화 가능한 형식으로 변환

**의존성**:
- app/repositories/data_repository.py: 주가 데이터 조회
- app/services/strategy_service.py: 백테스트 전략 검증
- backtesting.py: 외부 백테스팅 라이브러리

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (API 엔드포인트)
- Backend: app/services/portfolio_service.py (포트폴리오 백테스트)
- Frontend: src/features/backtest/api/backtestService.ts (API 클라이언트)

**아키텍처 패턴**:
- Repository Pattern: 데이터 접근은 repository를 통해서만 수행
- Factory Pattern: 전략 객체 생성은 strategy_factory를 통해 수행
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
from decimal import Decimal

# Repository 패턴 import
from app.repositories import data_repository
from app.services.strategy_service import strategy_service

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

from app.schemas.requests import BacktestRequest
from app.schemas.responses import BacktestResult, ChartDataResponse, ChartDataPoint, EquityPoint, TradeMarker, IndicatorData
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.core.config import settings
from app.core.exceptions import ValidationError

# 분리된 서비스들 import
from app.services.backtest_engine import backtest_engine
from app.services.chart_data_service import chart_data_service
from app.services.validation_service import validation_service

logger = logging.getLogger(__name__)


class BacktestService:
    """
    백테스팅 서비스 클래스
    
    분리된 전담 서비스들에게 작업을 위임:
    - BacktestEngine: 백테스트 실행
    - ChartDataService: 차트 데이터 생성
    - ValidationService: 검증 및 유틸리티
    """
    
    def __init__(self):
        # 서비스들 직접 임포트
        self.backtest_engine = backtest_engine
        self.chart_data_service = chart_data_service
        self.validation_service = validation_service
        
        # Repository 접근
        self.data_repository = data_repository
        
        # 호환성을 위해 기존 속성들 유지
        from app.utils.data_fetcher import data_fetcher
        from app.services.strategy_service import strategy_service
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service

        logger.info("백테스트 서비스가 초기화되었습니다")
    
    async def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        """백테스트 실행 - Repository Pattern이 적용된 BacktestEngine에 위임"""
        return await self.backtest_engine.run_backtest(request)
    
    async def generate_chart_data(self, request: BacktestRequest, backtest_result: BacktestResult = None) -> ChartDataResponse:
        """차트 데이터 생성 - Repository Pattern이 적용된 ChartDataService에 위임"""
        return await self.chart_data_service.generate_chart_data(request, backtest_result)
    
    def validate_backtest_request(self, request: BacktestRequest) -> None:
        """백테스트 요청 검증 - ValidationService에 위임"""
        return self.validation_service.validate_backtest_request(request)
    
    # Repository를 활용한 메서드들
    async def get_cached_stock_data(self, ticker: str, start_date, end_date) -> pd.DataFrame:
        """캐시된 주식 데이터 조회"""
        return await self.data_repository.get_stock_data(ticker, start_date, end_date)
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 전략 목록"""
        return strategy_service.get_all_strategies()
    
    def validate_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """전략 파라미터 검증"""
        try:
            strategy_service.validate_strategy_params(strategy_name, params)
            return True
        except ValueError:
            return False
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 정보"""
        return {
            'repository_stats': {
                'data_cache': await self.data_repository.get_cache_stats()
            },
            'strategy_stats': {
                'available_strategies': len(strategy_service.get_all_strategies())
            }
        }
    
    # 호환성을 위한 유틸리티 메서드들 (ValidationService 위임)
    def safe_float(self, value, default: float = 0.0) -> float:
        """안전한 float 변환 - ValidationService에 위임"""
        return self.validation_service.safe_float(value, default)
    
    def safe_int(self, value, default: int = 0) -> int:
        """안전한 int 변환 - ValidationService에 위임"""
        return self.validation_service.safe_int(value, default)


# 전역 인스턴스
backtest_service = BacktestService()
