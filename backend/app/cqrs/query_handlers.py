"""
CQRS 쿼리 핸들러들
"""
from typing import Any, Dict, Optional, List
import asyncio

from app.cqrs import QueryHandler
from app.cqrs.queries import (
    GetBacktestResultQuery, GetBacktestHistoryQuery, GetChartDataQuery,
    GetPortfolioAnalyticsQuery, GetPortfolioPerformanceQuery,
    GetOptimizationResultsQuery, GetMarketDataQuery,
    GetStrategiesQuery, GetSystemMetricsQuery
)
from app.services.enhanced_backtest_service import EnhancedBacktestService
from app.services.enhanced_portfolio_service import EnhancedPortfolioService
from app.repositories.backtest_repository import BacktestRepository
from app.repositories.data_repository import DataRepository


class GetBacktestResultQueryHandler(QueryHandler[GetBacktestResultQuery]):
    """백테스트 결과 조회 쿼리 핸들러"""
    
    def __init__(self, backtest_service: EnhancedBacktestService, 
                 backtest_repository: BacktestRepository):
        self.backtest_service = backtest_service
        self.backtest_repository = backtest_repository
    
    async def handle(self, query: GetBacktestResultQuery) -> Dict[str, Any]:
        """백테스트 결과 조회"""
        try:
            # 백테스트 결과 조회
            result = await asyncio.to_thread(
                self.backtest_repository.get_backtest_result,
                query.backtest_id
            )
            
            if not result:
                return {
                    'success': False,
                    'error': 'Backtest result not found',
                    'backtest_id': query.backtest_id
                }
            
            # 차트 데이터 포함 여부
            if query.include_chart_data:
                chart_data = await asyncio.to_thread(
                    self.backtest_service.get_chart_data,
                    query.backtest_id
                )
                result['chart_data'] = chart_data
            
            # 분석 데이터 포함 여부
            if query.include_analysis:
                analysis = await asyncio.to_thread(
                    self.backtest_service.get_enhanced_analysis,
                    query.backtest_id
                )
                result['analysis'] = analysis
            
            return {
                'success': True,
                'backtest_id': query.backtest_id,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'backtest_id': query.backtest_id
            }


class GetBacktestHistoryQueryHandler(QueryHandler[GetBacktestHistoryQuery]):
    """백테스트 히스토리 조회 쿼리 핸들러"""
    
    def __init__(self, backtest_repository: BacktestRepository):
        self.backtest_repository = backtest_repository
    
    async def handle(self, query: GetBacktestHistoryQuery) -> Dict[str, Any]:
        """백테스트 히스토리 조회"""
        try:
            filters = {}
            if query.user_id:
                filters['user_id'] = query.user_id
            if query.symbol:
                filters['symbol'] = query.symbol
            if query.strategy:
                filters['strategy'] = query.strategy
            if query.date_from:
                filters['date_from'] = query.date_from
            if query.date_to:
                filters['date_to'] = query.date_to
            
            results = await asyncio.to_thread(
                self.backtest_repository.get_backtest_history,
                filters,
                query.limit,
                query.offset
            )
            
            return {
                'success': True,
                'results': results,
                'total_count': len(results),
                'limit': query.limit,
                'offset': query.offset
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class GetChartDataQueryHandler(QueryHandler[GetChartDataQuery]):
    """차트 데이터 조회 쿼리 핸들러"""
    
    def __init__(self, backtest_service: EnhancedBacktestService):
        self.backtest_service = backtest_service
    
    async def handle(self, query: GetChartDataQuery) -> Dict[str, Any]:
        """차트 데이터 조회"""
        try:
            chart_data = await asyncio.to_thread(
                self.backtest_service.get_chart_data,
                query.backtest_id,
                query.chart_type,
                query.include_indicators,
                query.include_trades
            )
            
            return {
                'success': True,
                'backtest_id': query.backtest_id,
                'chart_type': query.chart_type,
                'data': chart_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'backtest_id': query.backtest_id
            }


class GetPortfolioAnalyticsQueryHandler(QueryHandler[GetPortfolioAnalyticsQuery]):
    """포트폴리오 분석 데이터 조회 쿼리 핸들러"""
    
    def __init__(self, portfolio_service: EnhancedPortfolioService):
        self.portfolio_service = portfolio_service
    
    async def handle(self, query: GetPortfolioAnalyticsQuery) -> Dict[str, Any]:
        """포트폴리오 분석 데이터 조회"""
        try:
            analytics = await asyncio.to_thread(
                self.portfolio_service.get_portfolio_analytics,
                query.portfolio_id,
                query.analysis_type
            )
            
            # 상관관계 분석 포함
            if query.include_correlation:
                correlation = await asyncio.to_thread(
                    self.portfolio_service.get_correlation_matrix,
                    query.portfolio_id
                )
                analytics['correlation_matrix'] = correlation
            
            # 최적화 제안 포함
            if query.include_optimization:
                optimization = await asyncio.to_thread(
                    self.portfolio_service.get_optimization_suggestions,
                    query.portfolio_id
                )
                analytics['optimization_suggestions'] = optimization
            
            return {
                'success': True,
                'portfolio_id': query.portfolio_id,
                'analytics': analytics
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'portfolio_id': query.portfolio_id
            }


class GetPortfolioPerformanceQueryHandler(QueryHandler[GetPortfolioPerformanceQuery]):
    """포트폴리오 성과 조회 쿼리 핸들러"""
    
    def __init__(self, portfolio_service: EnhancedPortfolioService):
        self.portfolio_service = portfolio_service
    
    async def handle(self, query: GetPortfolioPerformanceQuery) -> Dict[str, Any]:
        """포트폴리오 성과 조회"""
        try:
            performance = await asyncio.to_thread(
                self.portfolio_service.get_portfolio_performance,
                query.portfolio_id,
                query.period,
                query.benchmark
            )
            
            # 성과 분해 분석 포함
            if query.include_breakdown:
                breakdown = await asyncio.to_thread(
                    self.portfolio_service.get_performance_breakdown,
                    query.portfolio_id,
                    query.period
                )
                performance['breakdown'] = breakdown
            
            return {
                'success': True,
                'portfolio_id': query.portfolio_id,
                'period': query.period,
                'performance': performance
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'portfolio_id': query.portfolio_id
            }


class GetOptimizationResultsQueryHandler(QueryHandler[GetOptimizationResultsQuery]):
    """최적화 결과 조회 쿼리 핸들러"""
    
    def __init__(self, backtest_service: EnhancedBacktestService):
        self.backtest_service = backtest_service
    
    async def handle(self, query: GetOptimizationResultsQuery) -> Dict[str, Any]:
        """최적화 결과 조회"""
        try:
            results = await asyncio.to_thread(
                self.backtest_service.get_optimization_results,
                query.optimization_id,
                query.top_n
            )
            
            # 파라미터 상세 정보 제외
            if not query.include_parameters:
                for result in results:
                    result.pop('parameters', None)
            
            # 메트릭 상세 정보 제외
            if not query.include_metrics:
                for result in results:
                    result.pop('detailed_metrics', None)
            
            return {
                'success': True,
                'optimization_id': query.optimization_id,
                'results': results,
                'total_results': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'optimization_id': query.optimization_id
            }


class GetMarketDataQueryHandler(QueryHandler[GetMarketDataQuery]):
    """시장 데이터 조회 쿼리 핸들러"""
    
    def __init__(self, data_repository: DataRepository):
        self.data_repository = data_repository
    
    async def handle(self, query: GetMarketDataQuery) -> Dict[str, Any]:
        """시장 데이터 조회"""
        try:
            market_data = {}
            
            for symbol in query.symbols:
                data = await asyncio.to_thread(
                    self.data_repository.get_price_data,
                    symbol,
                    query.start_date,
                    query.end_date
                )
                
                if data is not None:
                    # 볼륨 데이터 제외 옵션
                    if not query.include_volume and 'Volume' in data.columns:
                        data = data.drop(columns=['Volume'])
                    
                    market_data[symbol] = data.to_dict('index')
            
            return {
                'success': True,
                'symbols': query.symbols,
                'data_type': query.data_type,
                'market_data': market_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'symbols': query.symbols
            }


class GetStrategiesQueryHandler(QueryHandler[GetStrategiesQuery]):
    """전략 목록 조회 쿼리 핸들러"""
    
    def __init__(self, backtest_service: EnhancedBacktestService):
        self.backtest_service = backtest_service
    
    async def handle(self, query: GetStrategiesQuery) -> Dict[str, Any]:
        """전략 목록 조회"""
        try:
            strategies = await asyncio.to_thread(
                self.backtest_service.get_available_strategies,
                query.category,
                query.active_only
            )
            
            # 파라미터 정보 제외
            if not query.include_parameters:
                for strategy in strategies:
                    strategy.pop('parameters', None)
            
            # 사용자별 필터링
            if query.user_id:
                user_strategies = await asyncio.to_thread(
                    self.backtest_service.get_user_strategies,
                    query.user_id
                )
                strategies.extend(user_strategies)
            
            return {
                'success': True,
                'strategies': strategies,
                'total_count': len(strategies)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class GetSystemMetricsQueryHandler(QueryHandler[GetSystemMetricsQuery]):
    """시스템 메트릭 조회 쿼리 핸들러"""
    
    def __init__(self):
        pass
    
    async def handle(self, query: GetSystemMetricsQuery) -> Dict[str, Any]:
        """시스템 메트릭 조회"""
        try:
            # 시스템 메트릭 수집 (향후 모니터링 시스템과 연동)
            metrics = {
                'performance': {
                    'avg_response_time': 0.1,
                    'requests_per_second': 10.5,
                    'cpu_usage': 25.6,
                    'memory_usage': 42.3
                },
                'usage': {
                    'active_users': 15,
                    'total_backtests': 1250,
                    'total_portfolios': 89,
                    'cache_hit_rate': 85.4
                },
                'errors': {
                    'error_rate': 0.02,
                    'failed_backtests': 3,
                    'api_errors': 1,
                    'system_errors': 0
                }
            }
            
            # 메트릭 타입별 필터링
            if query.metric_type != 'all':
                metrics = {query.metric_type: metrics.get(query.metric_type, {})}
            
            return {
                'success': True,
                'metric_type': query.metric_type,
                'time_range': query.time_range,
                'metrics': metrics
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
