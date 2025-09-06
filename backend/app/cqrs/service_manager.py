"""
CQRS 서비스 통합 매니저
Enhanced 서비스와 CQRS 시스템을 통합하여 관리하는 매니저
"""
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

from app.cqrs import CQRSBus
from app.cqrs.commands import (
    RunBacktestCommand, RunPortfolioBacktestCommand, OptimizeStrategyCommand,
    OptimizePortfolioCommand, RebalancePortfolioCommand, CreatePortfolioCommand
)
from app.cqrs.queries import (
    GetBacktestResultQuery, GetBacktestHistoryQuery, GetChartDataQuery,
    GetPortfolioAnalyticsQuery, GetPortfolioPerformanceQuery,
    GetOptimizationResultsQuery, GetMarketDataQuery,
    GetStrategiesQuery, GetSystemMetricsQuery
)
from app.cqrs.command_handlers import (
    RunBacktestCommandHandler, RunPortfolioBacktestCommandHandler,
    OptimizeStrategyCommandHandler, OptimizePortfolioCommandHandler,
    RebalancePortfolioCommandHandler, CreatePortfolioCommandHandler
)
from app.cqrs.query_handlers import (
    GetBacktestResultQueryHandler, GetBacktestHistoryQueryHandler,
    GetChartDataQueryHandler, GetPortfolioAnalyticsQueryHandler,
    GetPortfolioPerformanceQueryHandler, GetOptimizationResultsQueryHandler,
    GetMarketDataQueryHandler, GetStrategiesQueryHandler,
    GetSystemMetricsQueryHandler
)
from app.services.enhanced_backtest_service import EnhancedBacktestService
from app.services.enhanced_portfolio_service import EnhancedPortfolioService
from app.repositories.backtest_repository import BacktestRepository
from app.repositories.data_repository import DataRepository
from app.events import EventBus


class CQRSServiceManager:
    """CQRS 서비스 통합 매니저"""
    
    def __init__(self):
        self.cqrs_bus = CQRSBus()
        self.event_bus = EventBus()
        self._services = {}
        self._repositories = {}
        self._handlers_registered = False
    
    def initialize_services(self, 
                          backtest_service: EnhancedBacktestService,
                          portfolio_service: EnhancedPortfolioService,
                          backtest_repository: BacktestRepository,
                          data_repository: DataRepository):
        """서비스 및 리포지토리 초기화"""
        self._services['backtest'] = backtest_service
        self._services['portfolio'] = portfolio_service
        self._repositories['backtest'] = backtest_repository
        self._repositories['data'] = data_repository
        
        self._register_handlers()
    
    def _register_handlers(self):
        """커맨드 및 쿼리 핸들러 등록"""
        if self._handlers_registered:
            return
        
        # 커맨드 핸들러 등록
        self.cqrs_bus.register_command_handler(
            RunBacktestCommand,
            RunBacktestCommandHandler(
                self._services['backtest'],
                self.event_bus
            )
        )
        
        self.cqrs_bus.register_command_handler(
            RunPortfolioBacktestCommand,
            RunPortfolioBacktestCommandHandler(
                self._services['portfolio'],
                self.event_bus
            )
        )
        
        self.cqrs_bus.register_command_handler(
            OptimizeStrategyCommand,
            OptimizeStrategyCommandHandler(
                self._services['backtest'],
                self.event_bus
            )
        )
        
        self.cqrs_bus.register_command_handler(
            OptimizePortfolioCommand,
            OptimizePortfolioCommandHandler(
                self._services['portfolio'],
                self.event_bus
            )
        )
        
        self.cqrs_bus.register_command_handler(
            RebalancePortfolioCommand,
            RebalancePortfolioCommandHandler(
                self._services['portfolio'],
                self.event_bus
            )
        )
        
        self.cqrs_bus.register_command_handler(
            CreatePortfolioCommand,
            CreatePortfolioCommandHandler(
                self._services['portfolio'],
                self.event_bus
            )
        )
        
        # 쿼리 핸들러 등록
        self.cqrs_bus.register_query_handler(
            GetBacktestResultQuery,
            GetBacktestResultQueryHandler(
                self._services['backtest'],
                self._repositories['backtest']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetBacktestHistoryQuery,
            GetBacktestHistoryQueryHandler(
                self._repositories['backtest']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetChartDataQuery,
            GetChartDataQueryHandler(
                self._services['backtest']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetPortfolioAnalyticsQuery,
            GetPortfolioAnalyticsQueryHandler(
                self._services['portfolio']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetPortfolioPerformanceQuery,
            GetPortfolioPerformanceQueryHandler(
                self._services['portfolio']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetOptimizationResultsQuery,
            GetOptimizationResultsQueryHandler(
                self._services['backtest']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetMarketDataQuery,
            GetMarketDataQueryHandler(
                self._repositories['data']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetStrategiesQuery,
            GetStrategiesQueryHandler(
                self._services['backtest']
            )
        )
        
        self.cqrs_bus.register_query_handler(
            GetSystemMetricsQuery,
            GetSystemMetricsQueryHandler()
        )
        
        self._handlers_registered = True
    
    # 백테스트 관련 메서드들
    async def run_backtest(self, symbol: str, strategy: str, start_date: str, 
                          end_date: str, strategy_params: Dict[str, Any],
                          commission: float = 0.002, initial_cash: float = 10000.0,
                          use_enhanced_analysis: bool = False) -> Dict[str, Any]:
        """백테스트 실행"""
        command = RunBacktestCommand(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params,
            commission=commission,
            initial_cash=initial_cash,
            use_enhanced_analysis=use_enhanced_analysis
        )
        return await self.cqrs_bus.execute_command(command)
    
    async def run_portfolio_backtest(self, portfolio_name: str, stocks: List[Dict[str, Any]],
                                   start_date: str, end_date: str, total_investment: float,
                                   rebalancing_frequency: str = 'none', commission: float = 0.002,
                                   use_enhanced_analysis: bool = False) -> Dict[str, Any]:
        """포트폴리오 백테스트 실행"""
        command = RunPortfolioBacktestCommand(
            portfolio_name=portfolio_name,
            stocks=stocks,
            start_date=start_date,
            end_date=end_date,
            total_investment=total_investment,
            rebalancing_frequency=rebalancing_frequency,
            commission=commission,
            use_enhanced_analysis=use_enhanced_analysis
        )
        return await self.cqrs_bus.execute_command(command)
    
    async def optimize_strategy(self, symbol: str, strategy: str, start_date: str,
                              end_date: str, parameter_ranges: Dict[str, Any],
                              optimization_metric: str = 'SQN',
                              max_combinations: int = 1000) -> Dict[str, Any]:
        """전략 최적화"""
        command = OptimizeStrategyCommand(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            parameter_ranges=parameter_ranges,
            optimization_metric=optimization_metric,
            max_combinations=max_combinations
        )
        return await self.cqrs_bus.execute_command(command)
    
    # 포트폴리오 관련 메서드들
    async def create_portfolio(self, name: str, assets: List[Dict[str, Any]],
                             total_value: float, creator_id: Optional[str] = None) -> Dict[str, Any]:
        """포트폴리오 생성"""
        command = CreatePortfolioCommand(
            name=name,
            assets=assets,
            total_value=total_value,
            creator_id=creator_id
        )
        return await self.cqrs_bus.execute_command(command)
    
    async def optimize_portfolio(self, portfolio_id: str, assets: List[Dict[str, Any]],
                               risk_tolerance: float, optimization_method: str = 'risk_adjusted',
                               constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """포트폴리오 최적화"""
        command = OptimizePortfolioCommand(
            portfolio_id=portfolio_id,
            assets=assets,
            risk_tolerance=risk_tolerance,
            optimization_method=optimization_method,
            constraints=constraints
        )
        return await self.cqrs_bus.execute_command(command)
    
    async def rebalance_portfolio(self, portfolio_id: str, target_weights: Dict[str, float],
                                rebalancing_trigger: str, transaction_cost_limit: float = 1000.0) -> Dict[str, Any]:
        """포트폴리오 리밸런싱"""
        command = RebalancePortfolioCommand(
            portfolio_id=portfolio_id,
            target_weights=target_weights,
            rebalancing_trigger=rebalancing_trigger,
            transaction_cost_limit=transaction_cost_limit
        )
        return await self.cqrs_bus.execute_command(command)
    
    # 조회 관련 메서드들
    async def get_backtest_result(self, backtest_id: str, include_chart_data: bool = False,
                                include_analysis: bool = False) -> Dict[str, Any]:
        """백테스트 결과 조회"""
        query = GetBacktestResultQuery(
            backtest_id=backtest_id,
            include_chart_data=include_chart_data,
            include_analysis=include_analysis
        )
        return await self.cqrs_bus.execute_query(query)
    
    async def get_portfolio_analytics(self, portfolio_id: str, analysis_type: str = 'full',
                                    include_correlation: bool = False,
                                    include_optimization: bool = False) -> Dict[str, Any]:
        """포트폴리오 분석 데이터 조회"""
        query = GetPortfolioAnalyticsQuery(
            portfolio_id=portfolio_id,
            analysis_type=analysis_type,
            include_correlation=include_correlation,
            include_optimization=include_optimization
        )
        return await self.cqrs_bus.execute_query(query)
    
    async def get_portfolio_performance(self, portfolio_id: str, period: str = 'all',
                                      benchmark: Optional[str] = None,
                                      include_breakdown: bool = False) -> Dict[str, Any]:
        """포트폴리오 성과 조회"""
        query = GetPortfolioPerformanceQuery(
            portfolio_id=portfolio_id,
            period=period,
            benchmark=benchmark,
            include_breakdown=include_breakdown
        )
        return await self.cqrs_bus.execute_query(query)
    
    async def get_chart_data(self, backtest_id: str, chart_type: str = 'portfolio',
                           include_indicators: bool = True, include_trades: bool = True) -> Dict[str, Any]:
        """차트 데이터 조회"""
        query = GetChartDataQuery(
            backtest_id=backtest_id,
            chart_type=chart_type,
            include_indicators=include_indicators,
            include_trades=include_trades
        )
        return await self.cqrs_bus.execute_query(query)
    
    async def get_market_data(self, symbols: List[str], start_date: str, end_date: str,
                            data_type: str = 'daily', include_volume: bool = True) -> Dict[str, Any]:
        """시장 데이터 조회"""
        query = GetMarketDataQuery(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            data_type=data_type,
            include_volume=include_volume
        )
        return await self.cqrs_bus.execute_query(query)
    
    async def get_strategies(self, category: Optional[str] = None, include_parameters: bool = True,
                           active_only: bool = True, user_id: Optional[str] = None) -> Dict[str, Any]:
        """전략 목록 조회"""
        query = GetStrategiesQuery(
            category=category,
            include_parameters=include_parameters,
            active_only=active_only,
            user_id=user_id
        )
        return await self.cqrs_bus.execute_query(query)
    
    async def get_system_metrics(self, metric_type: str = 'all', time_range: str = '1h',
                               include_detailed: bool = False) -> Dict[str, Any]:
        """시스템 메트릭 조회"""
        query = GetSystemMetricsQuery(
            metric_type=metric_type,
            time_range=time_range,
            include_detailed=include_detailed
        )
        return await self.cqrs_bus.execute_query(query)
    
    # 상태 조회 메서드들
    def get_event_bus_status(self) -> Dict[str, Any]:
        """이벤트 버스 상태 조회"""
        return self.event_bus.get_status()
    
    def get_cqrs_bus_status(self) -> Dict[str, Any]:
        """CQRS 버스 상태 조회"""
        return self.cqrs_bus.get_status()
    
    def get_command_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """커맨드 실행 히스토리 조회"""
        return self.cqrs_bus.get_command_history(limit)
    
    def get_query_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """쿼리 실행 히스토리 조회"""
        return self.cqrs_bus.get_query_history(limit)


# 글로벌 CQRS 매니저 인스턴스
cqrs_manager = CQRSServiceManager()
