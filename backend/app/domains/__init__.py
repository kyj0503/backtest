"""
Domains

Domain-Driven Design (DDD) 아키텍처의 도메인 계층입니다.

포함된 도메인:
- backtest: 백테스트 실행, 전략 관리, 결과 분석
- portfolio: 자산 배분, 포트폴리오 관리, 리밸런싱  
- data: 시장 데이터 수집, 캐싱, 관리
"""

# 주요 도메인 서비스들
from .backtest import BacktestDomainService, StrategyDomainService
from .portfolio import PortfolioDomainService
from .data import DataDomainService

# 핵심 엔티티들
from .backtest import BacktestResultEntity, StrategyEntity
from .portfolio import PortfolioEntity, AssetEntity
from .data import MarketDataEntity, MarketDataPoint

# 주요 값 객체들
from .backtest import DateRange, PerformanceMetrics
from .portfolio import Weight, Allocation
from .data import Price, Volume, Symbol, TickerInfo

__all__ = [
    # Domain Services
    "BacktestDomainService",
    "StrategyDomainService", 
    "PortfolioDomainService",
    "DataDomainService",
    
    # Entities
    "BacktestResultEntity",
    "StrategyEntity",
    "PortfolioEntity", 
    "AssetEntity",
    "MarketDataEntity",
    "MarketDataPoint",
    
    # Value Objects
    "DateRange",
    "PerformanceMetrics",
    "Weight",
    "Allocation",
    "Price",
    "Volume",
    "Symbol", 
    "TickerInfo",
]

__version__ = "1.0.0"
__author__ = "Backtest Team"
