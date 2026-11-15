"""백테스팅 실행 서비스

단일 종목 백테스트 실행 및 결과 변환을 담당합니다.
"""
from typing import Dict, Any
import logging


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

logger = logging.getLogger(__name__)


class BacktestService:
    """백테스팅 서비스 - BacktestEngine, ValidationService에 작업 위임"""

    def __init__(self):
        # 실제 실행은 전부 엔진에 위임한다. 검증(validation_service)과 전략
        # 조회(strategy_service)는 엔진이 직접 호출하므로 여기서 들고 있을
        # 이유가 없다 — 위임 메서드가 사라지면서 함께 제거했다.
        self.backtest_engine = backtest_engine

        logger.info("백테스트 서비스가 초기화되었습니다")

    async def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        """백테스트 실행 - Repository Pattern이 적용된 BacktestEngine에 위임"""
        return await self.backtest_engine.run_backtest(request)





# 전역 인스턴스
backtest_service = BacktestService()
