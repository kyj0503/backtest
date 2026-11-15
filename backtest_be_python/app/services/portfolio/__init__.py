"""
포트폴리오 서비스 서브패키지

포트폴리오 백테스트 관련 기능을 담당하는 모듈들:
- portfolio_inputs: 요청 → 종목별 금액·DCA 정보 (입력 변환)
- portfolio_execution: 전략 종목별 백테스트, buy&hold 시뮬레이션 준비 (실행)
- portfolio_statistics_builder: portfolio_statistics 조립 (통계)
- portfolio_response_builder: 경로별 응답 딕셔너리 (응답 구성)
- portfolio_data_loader: 주가·통화·환율 로드
- portfolio_simulation_engine: 일별 시뮬레이션 루프
- portfolio_dca_manager: DCA 투자 관리
- portfolio_rebalancer: 리밸런싱 로직
- portfolio_metrics: 일별 평가금·수익률 계산

Note:
- 오케스트레이터는 app/services/portfolio_manager_service.py에 있다.
"""

from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager
from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine
from app.services.portfolio.portfolio_data_loader import PortfolioDataLoader
from app.services.portfolio.portfolio_metrics import PortfolioMetrics

__all__ = [
    'PortfolioDcaManager',
    'PortfolioRebalancer',
    'PortfolioSimulationEngine',
    'PortfolioDataLoader',
    'PortfolioMetrics',
]
