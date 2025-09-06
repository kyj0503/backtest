"""
Data domain - MarketDataEntity

시장 데이터를 나타내는 엔티티입니다.
엔티티는 식별자를 가지며, 생명주기 동안 상태가 변할 수 있습니다.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..value_objects import Price, Volume, PriceRange, TickerInfo


@dataclass
class MarketDataPoint:
    """
    특정 날짜의 시장 데이터 포인트
    
    특징:
    - 일일 OHLCV 데이터 저장
    - 가격 범위 및 거래량 정보
    - 조정 가격 지원
    """
    ticker: TickerInfo
    date: date
    open_price: Price
    high_price: Price
    low_price: Price
    close_price: Price
    volume: Volume
    adjusted_close: Optional[Price] = None
    
    def __post_init__(self):
        """객체 생성 후 유효성 검사"""
        # 현금 자산은 가격 데이터 검증 제외
        if self.ticker.symbol.is_cash():
            return
        
        # 가격 순서 검증
        price_range = PriceRange(self.low_price, self.high_price)
        if not price_range.contains(self.open_price):
            raise ValueError(f"Open price {self.open_price} not in range {price_range}")
        if not price_range.contains(self.close_price):
            raise ValueError(f"Close price {self.close_price} not in range {price_range}")
    
    def get_price_range(self) -> PriceRange:
        """일일 가격 범위 반환"""
        return PriceRange(self.low_price, self.high_price)
    
    def get_price_change(self) -> Price:
        """일일 가격 변화량"""
        return self.close_price.subtract(self.open_price)
    
    def get_price_change_percentage(self) -> float:
        """일일 가격 변화율 (백분율)"""
        if self.open_price.value == 0:
            return 0.0
        return float(self.close_price.percentage_change(self.open_price))
    
    def is_up_day(self) -> bool:
        """상승일 여부"""
        return self.close_price > self.open_price
    
    def is_down_day(self) -> bool:
        """하락일 여부"""
        return self.close_price < self.open_price
    
    def get_effective_price(self) -> Price:
        """유효 가격 (조정가 우선, 없으면 종가)"""
        return self.adjusted_close if self.adjusted_close else self.close_price


@dataclass
class MarketDataEntity:
    """
    시장 데이터 엔티티
    
    특징:
    - 고유 식별자 보유
    - 여러 날짜의 데이터 포인트 관리
    - 데이터 무결성 보장
    - 시계열 데이터 분석 기능
    """
    id: UUID = field(default_factory=uuid4)
    ticker: TickerInfo = field(default=None)
    data_points: Dict[date, MarketDataPoint] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_data_point(self, data_point: MarketDataPoint) -> None:
        """데이터 포인트 추가"""
        if self.ticker and data_point.ticker != self.ticker:
            raise ValueError(f"Data point ticker {data_point.ticker} does not match entity ticker {self.ticker}")
        
        if not self.ticker:
            self.ticker = data_point.ticker
        
        self.data_points[data_point.date] = data_point
        self.updated_at = datetime.utcnow()
    
    def get_data_point(self, date: date) -> Optional[MarketDataPoint]:
        """특정 날짜의 데이터 포인트 조회"""
        return self.data_points.get(date)
    
    def get_date_range(self) -> Optional[Tuple[date, date]]:
        """데이터 날짜 범위 반환"""
        if not self.data_points:
            return None
        
        dates = sorted(self.data_points.keys())
        return dates[0], dates[-1]
    
    def get_data_in_range(self, start_date: date, end_date: date) -> List[MarketDataPoint]:
        """날짜 범위 내 데이터 포인트들 반환 (날짜 순 정렬)"""
        result = []
        for data_date, data_point in self.data_points.items():
            if start_date <= data_date <= end_date:
                result.append(data_point)
        
        return sorted(result, key=lambda x: x.date)
    
    def get_latest_price(self) -> Optional[Price]:
        """최신 종가 반환"""
        if not self.data_points:
            return None
        
        latest_date = max(self.data_points.keys())
        latest_point = self.data_points[latest_date]
        return latest_point.get_effective_price()
    
    def get_price_series(self, start_date: date, end_date: date) -> List[Tuple[date, Price]]:
        """날짜 범위의 가격 시계열 반환"""
        data_points = self.get_data_in_range(start_date, end_date)
        return [(point.date, point.get_effective_price()) for point in data_points]
    
    def calculate_volatility(self, start_date: date, end_date: date) -> Optional[float]:
        """기간 내 변동성 계산 (일일 수익률 표준편차)"""
        data_points = self.get_data_in_range(start_date, end_date)
        if len(data_points) < 2:
            return None
        
        # 일일 수익률 계산
        returns = []
        for i in range(1, len(data_points)):
            prev_price = data_points[i-1].get_effective_price()
            curr_price = data_points[i].get_effective_price()
            
            if prev_price.value > 0:
                daily_return = float(curr_price.percentage_change(prev_price))
                returns.append(daily_return)
        
        if not returns:
            return None
        
        # 표준편차 계산
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def has_data_for_period(self, start_date: date, end_date: date) -> bool:
        """지정 기간에 데이터가 있는지 확인"""
        return len(self.get_data_in_range(start_date, end_date)) > 0
    
    def get_data_count(self) -> int:
        """데이터 포인트 개수"""
        return len(self.data_points)
    
    def is_cash_asset(self) -> bool:
        """현금 자산 여부"""
        return self.ticker and self.ticker.symbol.is_cash()
    
    def __str__(self) -> str:
        if self.ticker:
            data_range = self.get_date_range()
            count = self.get_data_count()
            if data_range:
                return f"MarketData({self.ticker.symbol}) [{data_range[0]} to {data_range[1]}] ({count} points)"
            else:
                return f"MarketData({self.ticker.symbol}) (empty)"
        return f"MarketData(id={self.id})"
