"""
백테스트 관련 쿼리들
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.cqrs import Query


class GetBacktestResultQuery(Query):
    """백테스트 결과 조회 쿼리"""
    
    def __init__(self, backtest_id: str, include_chart_data: bool = False,
                 include_analysis: bool = False,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.backtest_id = backtest_id
        self.include_chart_data = include_chart_data
        self.include_analysis = include_analysis
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        return bool(self.backtest_id)
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'backtest_id': self.backtest_id,
            'include_chart_data': self.include_chart_data,
            'include_analysis': self.include_analysis
        }


class GetBacktestHistoryQuery(Query):
    """백테스트 히스토리 조회 쿼리"""
    
    def __init__(self, user_id: Optional[str] = None, symbol: Optional[str] = None,
                 strategy: Optional[str] = None, date_from: Optional[str] = None,
                 date_to: Optional[str] = None, limit: int = 100, offset: int = 0,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.user_id = user_id
        self.symbol = symbol
        self.strategy = strategy
        self.date_from = date_from
        self.date_to = date_to
        self.limit = limit
        self.offset = offset
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        if self.limit <= 0 or self.offset < 0:
            return False
        
        if self.date_from and self.date_to:
            try:
                start = datetime.strptime(self.date_from, '%Y-%m-%d')
                end = datetime.strptime(self.date_to, '%Y-%m-%d')
                if start >= end:
                    return False
            except ValueError:
                return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'limit': self.limit,
            'offset': self.offset
        }


class GetChartDataQuery(Query):
    """차트 데이터 조회 쿼리"""
    
    def __init__(self, backtest_id: str, chart_type: str = 'portfolio',
                 include_indicators: bool = True, include_trades: bool = True,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.backtest_id = backtest_id
        self.chart_type = chart_type
        self.include_indicators = include_indicators
        self.include_trades = include_trades
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        if not self.backtest_id:
            return False
        
        if self.chart_type not in ['portfolio', 'equity', 'drawdown', 'trades']:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'backtest_id': self.backtest_id,
            'chart_type': self.chart_type,
            'include_indicators': self.include_indicators,
            'include_trades': self.include_trades
        }


class GetPortfolioAnalyticsQuery(Query):
    """포트폴리오 분석 데이터 조회 쿼리"""
    
    def __init__(self, portfolio_id: str, analysis_type: str = 'full',
                 include_correlation: bool = False, include_optimization: bool = False,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.portfolio_id = portfolio_id
        self.analysis_type = analysis_type
        self.include_correlation = include_correlation
        self.include_optimization = include_optimization
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        if not self.portfolio_id:
            return False
        
        if self.analysis_type not in ['full', 'basic', 'risk', 'performance']:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'portfolio_id': self.portfolio_id,
            'analysis_type': self.analysis_type,
            'include_correlation': self.include_correlation,
            'include_optimization': self.include_optimization
        }


class GetPortfolioPerformanceQuery(Query):
    """포트폴리오 성과 조회 쿼리"""
    
    def __init__(self, portfolio_id: str, period: str = 'all',
                 benchmark: Optional[str] = None, include_breakdown: bool = False,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.portfolio_id = portfolio_id
        self.period = period
        self.benchmark = benchmark
        self.include_breakdown = include_breakdown
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        if not self.portfolio_id:
            return False
        
        if self.period not in ['all', '1y', '6m', '3m', '1m', 'ytd']:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'portfolio_id': self.portfolio_id,
            'period': self.period,
            'benchmark': self.benchmark,
            'include_breakdown': self.include_breakdown
        }


class GetOptimizationResultsQuery(Query):
    """최적화 결과 조회 쿼리"""
    
    def __init__(self, optimization_id: str, include_parameters: bool = True,
                 include_metrics: bool = True, top_n: int = 10,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.optimization_id = optimization_id
        self.include_parameters = include_parameters
        self.include_metrics = include_metrics
        self.top_n = top_n
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        if not self.optimization_id:
            return False
        
        if self.top_n <= 0:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'optimization_id': self.optimization_id,
            'include_parameters': self.include_parameters,
            'include_metrics': self.include_metrics,
            'top_n': self.top_n
        }


class GetMarketDataQuery(Query):
    """시장 데이터 조회 쿼리"""
    
    def __init__(self, symbols: List[str], start_date: str, end_date: str,
                 data_type: str = 'daily', include_volume: bool = True,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.data_type = data_type
        self.include_volume = include_volume
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        if not self.symbols or not self.start_date or not self.end_date:
            return False
        
        if self.data_type not in ['daily', 'weekly', 'monthly']:
            return False
        
        try:
            start = datetime.strptime(self.start_date, '%Y-%m-%d')
            end = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start >= end:
                return False
        except ValueError:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'data_type': self.data_type,
            'include_volume': self.include_volume
        }


class GetStrategiesQuery(Query):
    """전략 목록 조회 쿼리"""
    
    def __init__(self, category: Optional[str] = None, include_parameters: bool = True,
                 active_only: bool = True, user_id: Optional[str] = None,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.category = category
        self.include_parameters = include_parameters
        self.active_only = active_only
        self.user_id = user_id
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        return True  # 모든 파라미터가 옵셔널
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'include_parameters': self.include_parameters,
            'active_only': self.active_only,
            'user_id': self.user_id
        }


class GetSystemMetricsQuery(Query):
    """시스템 메트릭 조회 쿼리"""
    
    def __init__(self, metric_type: str = 'all', time_range: str = '1h',
                 include_detailed: bool = False,
                 query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(query_id, timestamp)
        self.metric_type = metric_type
        self.time_range = time_range
        self.include_detailed = include_detailed
    
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        if self.metric_type not in ['all', 'performance', 'usage', 'errors']:
            return False
        
        if self.time_range not in ['1h', '6h', '24h', '7d', '30d']:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'metric_type': self.metric_type,
            'time_range': self.time_range,
            'include_detailed': self.include_detailed
        }
