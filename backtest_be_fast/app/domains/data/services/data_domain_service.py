"""
Data domain - DataDomainService

데이터 수집, 캐싱, 관리를 담당하는 도메인 서비스입니다.
도메인 서비스는 여러 엔티티나 값 객체에 걸친 비즈니스 로직을 처리합니다.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Set
from decimal import Decimal

from ..entities import MarketDataEntity, MarketDataPoint
from ..value_objects import Price, Volume, TickerInfo, Symbol


class DataDomainService:
    """
    데이터 도메인의 핵심 비즈니스 로직을 담당하는 서비스
    
    책임:
    - 시장 데이터 생성 및 관리
    - 현금 자산 데이터 생성
    - 데이터 유효성 검증
    - 데이터 변환 및 정규화
    """
    
    def __init__(self):
        self._market_data_cache: Dict[str, MarketDataEntity] = {}
    
    def create_market_data_entity(self, ticker: TickerInfo) -> MarketDataEntity:
        """새로운 시장 데이터 엔티티 생성"""
        entity = MarketDataEntity(ticker=ticker)
        self._market_data_cache[str(ticker.symbol)] = entity
        return entity
    
    def create_cash_data_point(self, 
                              ticker: TickerInfo,
                              date: date,
                              cash_value: Decimal = Decimal("1.0")) -> MarketDataPoint:
        """
        현금 자산용 데이터 포인트 생성
        현금은 변동성이 없으므로 모든 가격이 동일
        """
        if not ticker.symbol.is_cash():
            raise ValueError(f"Ticker {ticker.symbol} is not a cash asset")
        
        price = Price(cash_value, "USD")
        volume = Volume.zero()
        
        return MarketDataPoint(
            ticker=ticker,
            date=date,
            open_price=price,
            high_price=price,
            low_price=price,
            close_price=price,
            volume=volume,
            adjusted_close=price
        )
    
    def create_stock_data_point(self,
                               ticker: TickerInfo,
                               date: date,
                               open_price: float,
                               high_price: float,
                               low_price: float,
                               close_price: float,
                               volume: int,
                               adjusted_close: Optional[float] = None) -> MarketDataPoint:
        """주식 데이터 포인트 생성"""
        if ticker.symbol.is_cash():
            raise ValueError(f"Ticker {ticker.symbol} is a cash asset, use create_cash_data_point instead")
        
        currency = "USD"  # 기본 통화
        
        return MarketDataPoint(
            ticker=ticker,
            date=date,
            open_price=Price.from_float(open_price, currency),
            high_price=Price.from_float(high_price, currency),
            low_price=Price.from_float(low_price, currency),
            close_price=Price.from_float(close_price, currency),
            volume=Volume(volume),
            adjusted_close=Price.from_float(adjusted_close, currency) if adjusted_close else None
        )
    
    def generate_cash_data_series(self,
                                 ticker: TickerInfo,
                                 start_date: date,
                                 end_date: date,
                                 cash_value: Decimal = Decimal("1.0")) -> MarketDataEntity:
        """
        현금 자산용 데이터 시리즈 생성
        지정된 기간 동안 일정한 가치를 유지하는 데이터 생성
        """
        if not ticker.symbol.is_cash():
            raise ValueError(f"Ticker {ticker.symbol} is not a cash asset")
        
        entity = self.create_market_data_entity(ticker)
        
        current_date = start_date
        while current_date <= end_date:
            # 주말은 제외 (주식 시장 휴무)
            if current_date.weekday() < 5:  # 0=월요일, 4=금요일
                data_point = self.create_cash_data_point(ticker, current_date, cash_value)
                entity.add_data_point(data_point)
            
            current_date += timedelta(days=1)
        
        return entity
    
    def validate_data_consistency(self, entities: List[MarketDataEntity]) -> Dict[str, List[str]]:
        """
        여러 엔티티의 데이터 일관성 검증
        
        반환값: 엔티티별 오류 메시지 목록
        """
        errors = {}
        
        for entity in entities:
            entity_errors = []
            
            # 기본 검증
            if not entity.ticker:
                entity_errors.append("Missing ticker information")
                continue
            
            if entity.get_data_count() == 0:
                entity_errors.append("No data points found")
                continue
            
            # 현금 자산은 추가 검증 불필요
            if entity.is_cash_asset():
                continue
            
            # 주식 데이터 검증
            data_range = entity.get_date_range()
            if data_range:
                start_date, end_date = data_range
                data_points = entity.get_data_in_range(start_date, end_date)
                
                # 가격 연속성 검증
                for i, point in enumerate(data_points):
                    if point.open_price.value <= 0:
                        entity_errors.append(f"Invalid open price on {point.date}: {point.open_price}")
                    
                    if point.close_price.value <= 0:
                        entity_errors.append(f"Invalid close price on {point.date}: {point.close_price}")
                    
                    # 가격 범위 검증
                    try:
                        price_range = point.get_price_range()
                        if not price_range.contains(point.open_price):
                            entity_errors.append(f"Open price out of range on {point.date}")
                        if not price_range.contains(point.close_price):
                            entity_errors.append(f"Close price out of range on {point.date}")
                    except ValueError as e:
                        entity_errors.append(f"Price range error on {point.date}: {str(e)}")
            
            if entity_errors:
                errors[str(entity.ticker.symbol)] = entity_errors
        
        return errors
    
    def get_common_date_range(self, entities: List[MarketDataEntity]) -> Optional[tuple[date, date]]:
        """여러 엔티티의 공통 날짜 범위 계산"""
        if not entities:
            return None
        
        ranges = []
        for entity in entities:
            entity_range = entity.get_date_range()
            if entity_range:
                ranges.append(entity_range)
        
        if not ranges:
            return None
        
        # 가장 늦은 시작일과 가장 이른 종료일
        start_date = max(r[0] for r in ranges)
        end_date = min(r[1] for r in ranges)
        
        if start_date <= end_date:
            return start_date, end_date
        else:
            return None
    
    def align_data_to_common_dates(self, entities: List[MarketDataEntity]) -> Dict[str, List[MarketDataPoint]]:
        """
        여러 엔티티의 데이터를 공통 날짜에 맞춰 정렬
        
        반환값: 심볼별 정렬된 데이터 포인트 목록
        """
        common_range = self.get_common_date_range(entities)
        if not common_range:
            return {}
        
        start_date, end_date = common_range
        result = {}
        
        for entity in entities:
            symbol = str(entity.ticker.symbol)
            data_points = entity.get_data_in_range(start_date, end_date)
            result[symbol] = data_points
        
        return result
    
    def calculate_correlation_matrix(self, entities: List[MarketDataEntity]) -> Dict[tuple, Optional[float]]:
        """
        엔티티들 간의 가격 상관관계 매트릭스 계산
        
        반환값: (symbol1, symbol2) -> correlation 딕셔너리
        """
        aligned_data = self.align_data_to_common_dates(entities)
        symbols = list(aligned_data.keys())
        correlations = {}
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i <= j:  # 대칭 매트릭스이므로 상삼각만 계산
                    if symbol1 == symbol2:
                        correlations[(symbol1, symbol2)] = 1.0
                    else:
                        # 현금 자산은 상관관계 0
                        entity1 = next(e for e in entities if str(e.ticker.symbol) == symbol1)
                        entity2 = next(e for e in entities if str(e.ticker.symbol) == symbol2)
                        
                        if entity1.is_cash_asset() or entity2.is_cash_asset():
                            correlations[(symbol1, symbol2)] = 0.0
                        else:
                            corr = self._calculate_price_correlation(
                                aligned_data[symbol1], 
                                aligned_data[symbol2]
                            )
                            correlations[(symbol1, symbol2)] = corr
        
        return correlations
    
    def _calculate_price_correlation(self, 
                                   data1: List[MarketDataPoint], 
                                   data2: List[MarketDataPoint]) -> Optional[float]:
        """두 데이터 시리즈 간의 가격 상관관계 계산"""
        if len(data1) != len(data2) or len(data1) < 2:
            return None
        
        # 일일 수익률 계산
        returns1 = []
        returns2 = []
        
        for i in range(1, len(data1)):
            # 첫 번째 시리즈
            prev_price1 = data1[i-1].get_effective_price()
            curr_price1 = data1[i].get_effective_price()
            if prev_price1.value > 0:
                return1 = float(curr_price1.percentage_change(prev_price1))
                returns1.append(return1)
            
            # 두 번째 시리즈
            prev_price2 = data2[i-1].get_effective_price()
            curr_price2 = data2[i].get_effective_price()
            if prev_price2.value > 0:
                return2 = float(curr_price2.percentage_change(prev_price2))
                returns2.append(return2)
        
        if len(returns1) != len(returns2) or len(returns1) < 2:
            return None
        
        # 상관계수 계산
        n = len(returns1)
        mean1 = sum(returns1) / n
        mean2 = sum(returns2) / n
        
        numerator = sum((returns1[i] - mean1) * (returns2[i] - mean2) for i in range(n))
        
        var1 = sum((returns1[i] - mean1) ** 2 for i in range(n))
        var2 = sum((returns2[i] - mean2) ** 2 for i in range(n))
        
        denominator = (var1 * var2) ** 0.5
        
        if denominator == 0:
            return None
        
        return numerator / denominator
