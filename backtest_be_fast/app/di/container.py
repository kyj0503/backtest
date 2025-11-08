"""
의존성 주입 컨테이너

**역할**:
- 모든 서비스의 의존성을 중앙에서 관리
- 서비스 인스턴스의 생성 및 주입
- 싱글톤 패턴으로 서비스 재사용
- 테스트 시 Mock 객체 주입 가능

**주요 서비스**:
1. DataSource: 주식 데이터 소스 (YFinanceDataSource)
2. BacktestEngine: 백테스트 실행 엔진
3. PortfolioService: 포트폴리오 백테스트
4. StrategyService: 전략 관리

**사용 예**:
```python
from app.di.container import service_container

# 싱글톤 서비스 조회
backtest_engine = service_container.get_backtest_engine()
portfolio_service = service_container.get_portfolio_service()

# 테스트용 Mock 주입
from unittest.mock import Mock
mock_data_source = Mock()
service_container.set_data_source(mock_data_source)
```

**의존성 그래프**:
```
DataSource (YFinanceDataSource)
    ↓
BacktestEngine, PortfolioService
    ↓
API Endpoints
```

**의존성**:
- app/interfaces/data_source.py: DataSource 인터페이스
- app/services/: 모든 서비스 구현

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/ (DI 사용)
- Backend: app/main.py (컨테이너 초기화)
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ServiceContainer:
    """의존성 주입 컨테이너 - Registry 패턴"""

    def __init__(self):
        """컨테이너 초기화"""
        self._data_source: Optional[object] = None
        self._backtest_engine: Optional[object] = None
        self._portfolio_service: Optional[object] = None
        self._strategy_service: Optional[object] = None
        self._validation_service: Optional[object] = None
        self._data_fetcher: Optional[object] = None

    # ==================== DataSource ====================
    def get_data_source(self):
        """데이터 소스 조회 (싱글톤)"""
        if self._data_source is None:
            from app.interfaces.data_source import YFinanceDataSource
            self._data_source = YFinanceDataSource()
            logger.info("데이터 소스 초기화: YFinanceDataSource")
        return self._data_source

    def set_data_source(self, data_source):
        """데이터 소스 설정 (테스트용)"""
        self._data_source = data_source
        logger.info(f"데이터 소스 설정: {type(data_source).__name__}")

    # ==================== BacktestEngine ====================
    def get_backtest_engine(self):
        """백테스트 엔진 조회 (싱글톤)"""
        if self._backtest_engine is None:
            from app.services.backtest_engine import BacktestEngine
            from app.repositories.data_repository import data_repository
            from app.services.strategy_service import strategy_service
            from app.services.validation_service import validation_service

            self._backtest_engine = BacktestEngine(
                data_repository=data_repository,
                strategy_service_instance=strategy_service,
                validation_service_instance=validation_service
            )
            logger.info("백테스트 엔진 초기화")
        return self._backtest_engine

    def set_backtest_engine(self, engine):
        """백테스트 엔진 설정 (테스트용)"""
        self._backtest_engine = engine
        logger.info(f"백테스트 엔진 설정: {type(engine).__name__}")

    # ==================== BacktestService ====================
    def get_backtest_service(self):
        """백테스트 서비스 조회 (싱글톤)"""
        from app.services.backtest_service import BacktestService
        # BacktestService는 상태를 유지하지 않으므로 매번 새로 생성
        return BacktestService()

    # ==================== PortfolioService ====================
    def get_portfolio_service(self):
        """포트폴리오 서비스 조회 (싱글톤)"""
        if self._portfolio_service is None:
            from app.services.portfolio_service import PortfolioService

            self._portfolio_service = PortfolioService()
            logger.info("포트폴리오 서비스 초기화")
        return self._portfolio_service

    def set_portfolio_service(self, service):
        """포트폴리오 서비스 설정 (테스트용)"""
        self._portfolio_service = service
        logger.info(f"포트폴리오 서비스 설정: {type(service).__name__}")

    # ==================== StrategyService ====================
    def get_strategy_service(self):
        """전략 서비스 조회 (싱글톤)"""
        if self._strategy_service is None:
            from app.services.strategy_service import StrategyService

            self._strategy_service = StrategyService()
            logger.info("전략 서비스 초기화")
        return self._strategy_service

    def set_strategy_service(self, service):
        """전략 서비스 설정 (테스트용)"""
        self._strategy_service = service
        logger.info(f"전략 서비스 설정: {type(service).__name__}")

    # ==================== ValidationService ====================
    def get_validation_service(self):
        """검증 서비스 조회 (싱글톤)"""
        if self._validation_service is None:
            from app.services.validation_service import ValidationService

            self._validation_service = ValidationService()
            logger.info("검증 서비스 초기화")
        return self._validation_service

    def set_validation_service(self, service):
        """검증 서비스 설정 (테스트용)"""
        self._validation_service = service
        logger.info(f"검증 서비스 설정: {type(service).__name__}")

    # ==================== DataFetcher ====================
    def get_data_fetcher(self):
        """데이터 페칭 유틸리티 조회 (싱글톤)"""
        if self._data_fetcher is None:
            from app.utils.data_fetcher import DataFetcher

            self._data_fetcher = DataFetcher()
            logger.info("데이터 페칭 유틸리티 초기화")
        return self._data_fetcher

    def set_data_fetcher(self, fetcher):
        """데이터 페칭 유틸리티 설정 (테스트용)"""
        self._data_fetcher = fetcher
        logger.info(f"데이터 페칭 유틸리티 설정: {type(fetcher).__name__}")

    # ==================== 컨테이너 관리 ====================
    def reset(self):
        """모든 서비스 초기화 (테스트용)"""
        self._data_source = None
        self._backtest_engine = None
        self._portfolio_service = None
        self._strategy_service = None
        self._validation_service = None
        self._data_fetcher = None
        logger.info("서비스 컨테이너 초기화됨")

    def health_check(self) -> dict:
        """컨테이너 상태 확인"""
        return {
            "data_source": self._data_source is not None,
            "backtest_engine": self._backtest_engine is not None,
            "portfolio_service": self._portfolio_service is not None,
            "strategy_service": self._strategy_service is not None,
            "validation_service": self._validation_service is not None,
            "data_fetcher": self._data_fetcher is not None,
        }


# 전역 싱글톤 컨테이너
service_container = ServiceContainer()

# 더 간단한 접근을 위한 헬퍼 함수
def get_service_container() -> ServiceContainer:
    """전역 서비스 컨테이너 조회"""
    return service_container


if __name__ == "__main__":
    # 컨테이너 테스트
    container = get_service_container()

    print("서비스 컨테이너 초기화 테스트")
    print(f"데이터 소스: {type(container.get_data_source()).__name__}")
    print(f"백테스트 엔진: {type(container.get_backtest_engine()).__name__}")
    print(f"포트폴리오 서비스: {type(container.get_portfolio_service()).__name__}")
    print(f"전략 서비스: {type(container.get_strategy_service()).__name__}")
    print("\n컨테이너 상태:")
    print(container.health_check())
