"""백테스팅 실행 서비스

단일 종목 백테스트 실행 및 결과 변환을 담당합니다.
"""
from typing import Dict, Any
import logging

from app.services.strategy_service import strategy_service
from app.utils.data_fetcher import data_fetcher

# 참고(P3-21): 이 모듈은 과거 임포트 시점에 backtesting._stats.compute_stats를
# 몽키패치해, 특정 pandas Timedelta 비교 오류가 발생하면 원본 예외를 삼키고
# 하드코딩된 조작 통계(Win Rate 50%, Profit Factor 1.0 등)를 HTTP 200 성공으로
# 반환했다. backtesting._stats.compute_stats는 backtesting 패키지 전역에 공유되는
# 함수 객체이므로, 이 모듈이 (portfolio_manager_service의 모듈 최상단 임포트를 통해)
# 한 번이라도 로드되면 모든 백테스트 실행 경로에 영향을 미치는 실제 도달 가능한
# 패치였다. 실패를 조작된 성공으로 위장하지 않기 위해 패치를 제거했다 — 이제
# compute_stats 오류는 원본 그대로 전파되어 BacktestEngine.run_backtest()의
# 예외 처리기가 500으로 매핑한다.

from app.schemas.requests import BacktestRequest
from app.schemas.responses import BacktestResult

# 분리된 서비스들 import
from app.services.backtest_engine import backtest_engine
from app.services.validation_service import validation_service

logger = logging.getLogger(__name__)


class BacktestService:
    """백테스팅 서비스 - BacktestEngine, ValidationService에 작업 위임"""

    def __init__(self):
        # 서비스들 직접 임포트
        self.backtest_engine = backtest_engine
        self.validation_service = validation_service

        # 호환성을 위해 기존 속성들 유지
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service

        logger.info("백테스트 서비스가 초기화되었습니다")

    async def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        """백테스트 실행 - Repository Pattern이 적용된 BacktestEngine에 위임"""
        return await self.backtest_engine.run_backtest(request)

    def validate_backtest_request(self, request: BacktestRequest) -> None:
        """백테스트 요청 검증 - ValidationService에 위임"""
        return self.validation_service.validate_backtest_request(request)

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


# 전역 인스턴스
backtest_service = BacktestService()
