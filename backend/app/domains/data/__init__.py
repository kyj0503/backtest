"""
Data domain

시장 데이터 수집, 캐싱, 관리를 담당하는 도메인입니다.

주요 구성요소:
- Value Objects: Price, Volume, Symbol, TickerInfo 등
- Entities: MarketDataEntity, MarketDataPoint
- Services: DataDomainService
"""

from .value_objects import (
    Price, Volume, PriceRange,
    Symbol, AssetType, MarketInfo, TickerInfo
)
from .entities import MarketDataEntity, MarketDataPoint
from .services import DataDomainService

__all__ = [
    # Value Objects
    "Price",
    "Volume", 
    "PriceRange",
    "Symbol",
    "AssetType",
    "MarketInfo",
    "TickerInfo",
    
    # Entities
    "MarketDataEntity",
    "MarketDataPoint",
    
    # Services
    "DataDomainService",
]
