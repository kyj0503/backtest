"""
서비스 인스턴스 생성 및 의존성 주입 Factory
"""
from typing import Dict, Any, Optional, Type
import logging
from abc import ABC, abstractmethod

from app.repositories.backtest_repository import BacktestRepositoryInterface, backtest_repository
from app.repositories.data_repository import DataRepositoryInterface, data_repository
from app.factories.strategy_factory import StrategyFactoryInterface, strategy_factory


class ServiceFactoryInterface(ABC):
    """서비스 팩토리 인터페이스"""
    
    @abstractmethod
    def create_backtest_engine(self, **kwargs):
        """백테스트 엔진 생성"""
        pass
    
    @abstractmethod
    def create_optimization_service(self, **kwargs):
        """최적화 서비스 생성"""
        pass
    
    @abstractmethod
    def create_chart_data_service(self, **kwargs):
        """차트 데이터 서비스 생성"""
        pass
    
    @abstractmethod
    def create_validation_service(self, **kwargs):
        """검증 서비스 생성"""
        pass
    
    @abstractmethod
    def create_backtest_service(self, **kwargs):
        """백테스트 서비스 생성"""
        pass


class DefaultServiceFactory(ServiceFactoryInterface):
    """기본 서비스 팩토리 구현"""
    
    def __init__(self, 
                 backtest_repo: Optional[BacktestRepositoryInterface] = None,
                 data_repo: Optional[DataRepositoryInterface] = None,
                 strategy_factory_instance: Optional[StrategyFactoryInterface] = None):
        self.logger = logging.getLogger(__name__)
        
        # 의존성 주입
        self.backtest_repository = backtest_repo or backtest_repository
        self.data_repository = data_repo or data_repository
        self.strategy_factory = strategy_factory_instance or strategy_factory
        
        # 싱글톤 인스턴스 캐시
        self._instances: Dict[str, Any] = {}
    
    def create_backtest_engine(self, **kwargs):
        """백테스트 엔진 생성 (의존성 주입)"""
        if 'backtest_engine' not in self._instances:
            from app.services.backtest.backtest_engine import BacktestEngine
            
            # 수정된 BacktestEngine (Repository 주입)
            class EnhancedBacktestEngine(BacktestEngine):
                def __init__(self, data_repo, strategy_factory, backtest_repo):
                    super().__init__()
                    self.data_repository = data_repo
                    self.strategy_factory_instance = strategy_factory
                    self.backtest_repository = backtest_repo
                
                async def get_stock_data_with_cache(self, ticker, start_date, end_date):
                    """캐시를 활용한 데이터 조회"""
                    return await self.data_repository.get_stock_data(ticker, start_date, end_date)
                
                def get_strategy_class_with_factory(self, strategy_name, **params):
                    """팩토리를 활용한 전략 생성"""
                    return self.strategy_factory_instance.create_strategy(strategy_name, **params)
                
                async def save_result(self, result, user_id=None):
                    """결과 저장"""
                    return await self.backtest_repository.save_result(result, user_id)
            
            self._instances['backtest_engine'] = EnhancedBacktestEngine(
                self.data_repository,
                self.strategy_factory,
                self.backtest_repository
            )
        
        return self._instances['backtest_engine']
    
    def create_optimization_service(self, **kwargs):
        """최적화 서비스 생성 (의존성 주입)"""
        if 'optimization_service' not in self._instances:
            from app.services.backtest.optimization_service import OptimizationService
            
            # 수정된 OptimizationService (Repository 주입)
            class EnhancedOptimizationService(OptimizationService):
                def __init__(self, data_repo, strategy_factory):
                    super().__init__()
                    self.data_repository = data_repo
                    self.strategy_factory_instance = strategy_factory
                
                async def get_stock_data_with_cache(self, ticker, start_date, end_date):
                    """캐시를 활용한 데이터 조회"""
                    return await self.data_repository.get_stock_data(ticker, start_date, end_date)
                
                def get_strategy_class_with_factory(self, strategy_name, **params):
                    """팩토리를 활용한 전략 생성"""
                    return self.strategy_factory_instance.create_strategy(strategy_name, **params)
            
            self._instances['optimization_service'] = EnhancedOptimizationService(
                self.data_repository,
                self.strategy_factory
            )
        
        return self._instances['optimization_service']
    
    def create_chart_data_service(self, **kwargs):
        """차트 데이터 서비스 생성 (의존성 주입)"""
        if 'chart_data_service' not in self._instances:
            from app.services.backtest.chart_data_service import ChartDataService
            
            # 수정된 ChartDataService (Repository 주입)
            class EnhancedChartDataService(ChartDataService):
                def __init__(self, data_repo):
                    super().__init__()
                    self.data_repository = data_repo
                
                async def get_stock_data_with_cache(self, ticker, start_date, end_date):
                    """캐시를 활용한 데이터 조회"""
                    return await self.data_repository.get_stock_data(ticker, start_date, end_date)
            
            self._instances['chart_data_service'] = EnhancedChartDataService(
                self.data_repository
            )
        
        return self._instances['chart_data_service']
    
    def create_validation_service(self, **kwargs):
        """검증 서비스 생성"""
        from app.services.backtest.validation_service import ValidationService
        return ValidationService()
    
    def create_backtest_service(self, **kwargs):
        """백테스트 서비스 생성 (Repository Pattern 적용)"""
        from app.services.backtest_service import BacktestService
        # 현재 BacktestService는 service_factory만 받도록 설계되어 있음
        # Repository는 전역 인스턴스를 통해 간접 주입됨
        return BacktestService(service_factory_instance=self)
    
    def create_portfolio_service(self, **kwargs):
        """포트폴리오 서비스 생성 (추후 리팩터링 시 사용)"""
        # TODO: PortfolioService 리팩터링 후 구현
        pass
    
    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 팩토리 통계"""
        return {
            'created_services': list(self._instances.keys()),
            'total_services': len(self._instances),
            'repository_stats': {
                'backtest_repo': 'injected' if self.backtest_repository else 'none',
                'data_repo': 'injected' if self.data_repository else 'none'
            }
        }
    
    def reset_instances(self):
        """인스턴스 캐시 초기화 (테스트용)"""
        self._instances.clear()
        self.logger.info("서비스 인스턴스 캐시 초기화 완료")


class TestServiceFactory(ServiceFactoryInterface):
    """테스트용 서비스 팩토리"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 테스트용 Mock Repository 사용
        from app.repositories.backtest_repository import BacktestRepositoryFactory
        from app.repositories.data_repository import DataRepositoryFactory
        
        self.backtest_repository = BacktestRepositoryFactory.create("memory")
        self.data_repository = DataRepositoryFactory.create("mock")
        self.strategy_factory = strategy_factory
    
    def create_backtest_engine(self, **kwargs):
        """테스트용 백테스트 엔진 생성"""
        # Mock 데이터와 Repository를 사용하는 테스트용 엔진
        return DefaultServiceFactory(
            self.backtest_repository,
            self.data_repository,
            self.strategy_factory
        ).create_backtest_engine(**kwargs)
    
    def create_optimization_service(self, **kwargs):
        """테스트용 최적화 서비스 생성"""
        return DefaultServiceFactory(
            self.backtest_repository,
            self.data_repository,
            self.strategy_factory
        ).create_optimization_service(**kwargs)
    
    def create_chart_data_service(self, **kwargs):
        """테스트용 차트 데이터 서비스 생성"""
        return DefaultServiceFactory(
            self.backtest_repository,
            self.data_repository,
            self.strategy_factory
        ).create_chart_data_service(**kwargs)
    
    def create_validation_service(self, **kwargs):
        """테스트용 검증 서비스 생성"""
        return DefaultServiceFactory().create_validation_service(**kwargs)


# Service Factory 팩토리
class ServiceFactoryFactory:
    """서비스 팩토리의 팩토리"""
    
    @staticmethod
    def create(factory_type: str = "default", **kwargs) -> ServiceFactoryInterface:
        """팩토리 인스턴스 생성"""
        if factory_type == "default":
            return DefaultServiceFactory(**kwargs)
        elif factory_type == "test":
            return TestServiceFactory()
        else:
            raise ValueError(f"지원하지 않는 팩토리 타입: {factory_type}")


# 전역 인스턴스 (클래스로 사용)
ServiceFactory = DefaultServiceFactory
service_factory = DefaultServiceFactory()
