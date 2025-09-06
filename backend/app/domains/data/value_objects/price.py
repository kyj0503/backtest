"""
Data domain - Price value objects

Price와 관련된 핵심 값 객체들을 정의합니다.
값 객체는 불변성을 보장하고 비즈니스 규칙을 캡슐화합니다.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Price:
    """
    가격을 나타내는 값 객체
    
    특징:
    - 불변성: frozen=True로 객체 생성 후 수정 불가
    - 정밀도: Decimal 타입으로 부동소수점 오차 방지
    - 검증: 음수 가격 방지 및 유효성 검사
    """
    value: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        """객체 생성 후 유효성 검사"""
        if self.value < 0:
            raise ValueError(f"Price cannot be negative: {self.value}")
        
        if not self.currency or len(self.currency) != 3:
            raise ValueError(f"Invalid currency code: {self.currency}")
    
    @classmethod
    def from_float(cls, value: float, currency: str = "USD") -> "Price":
        """float 값으로부터 Price 객체 생성"""
        return cls(Decimal(str(value)), currency)
    
    @classmethod
    def zero(cls, currency: str = "USD") -> "Price":
        """0 가격 객체 생성"""
        return cls(Decimal("0"), currency)
    
    def to_float(self) -> float:
        """float 값으로 변환"""
        return float(self.value)
    
    def add(self, other: "Price") -> "Price":
        """가격 더하기 (같은 통화만 허용)"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} vs {other.currency}")
        return Price(self.value + other.value, self.currency)
    
    def subtract(self, other: "Price") -> "Price":
        """가격 빼기 (같은 통화만 허용)"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} vs {other.currency}")
        result_value = self.value - other.value
        if result_value < 0:
            raise ValueError(f"Subtraction result cannot be negative: {result_value}")
        return Price(result_value, self.currency)
    
    def multiply(self, factor: Decimal) -> "Price":
        """가격에 배수 적용"""
        if factor < 0:
            raise ValueError(f"Factor cannot be negative: {factor}")
        return Price(self.value * factor, self.currency)
    
    def percentage_change(self, other: "Price") -> Decimal:
        """다른 가격 대비 변화율 계산 (백분율)"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} vs {other.currency}")
        if other.value == 0:
            raise ValueError("Cannot calculate percentage change from zero price")
        return ((self.value - other.value) / other.value) * 100
    
    def __str__(self) -> str:
        return f"{self.currency} {self.value:.2f}"
    
    def __lt__(self, other: "Price") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} vs {other.currency}")
        return self.value < other.value
    
    def __le__(self, other: "Price") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} vs {other.currency}")
        return self.value <= other.value
    
    def __gt__(self, other: "Price") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} vs {other.currency}")
        return self.value > other.value
    
    def __ge__(self, other: "Price") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} vs {other.currency}")
        return self.value >= other.value


@dataclass(frozen=True)
class Volume:
    """
    거래량을 나타내는 값 객체
    
    특징:
    - 정수형 거래량으로 주식 거래의 특성 반영
    - 음수 거래량 방지
    - 거래량 연산 지원
    """
    value: int
    
    def __post_init__(self):
        """객체 생성 후 유효성 검사"""
        if self.value < 0:
            raise ValueError(f"Volume cannot be negative: {self.value}")
    
    @classmethod
    def zero(cls) -> "Volume":
        """0 거래량 객체 생성"""
        return cls(0)
    
    def add(self, other: "Volume") -> "Volume":
        """거래량 더하기"""
        return Volume(self.value + other.value)
    
    def is_high_volume(self, threshold: int = 1000000) -> bool:
        """고거래량 여부 판단 (기본값: 100만주)"""
        return self.value >= threshold
    
    def __str__(self) -> str:
        if self.value >= 1000000:
            return f"{self.value / 1000000:.1f}M"
        elif self.value >= 1000:
            return f"{self.value / 1000:.1f}K"
        else:
            return str(self.value)
    
    def __lt__(self, other: "Volume") -> bool:
        return self.value < other.value
    
    def __le__(self, other: "Volume") -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: "Volume") -> bool:
        return self.value > other.value
    
    def __ge__(self, other: "Volume") -> bool:
        return self.value >= other.value


@dataclass(frozen=True)
class PriceRange:
    """
    가격 범위를 나타내는 값 객체 (일일 고가/저가 등)
    
    특징:
    - 고가가 저가보다 낮을 수 없음을 보장
    - 가격 범위 내 여부 확인 기능
    - 변동폭 계산 기능
    """
    low: Price
    high: Price
    
    def __post_init__(self):
        """객체 생성 후 유효성 검사"""
        if self.low.currency != self.high.currency:
            raise ValueError(f"Low and high prices must have same currency: {self.low.currency} vs {self.high.currency}")
        
        if self.low > self.high:
            raise ValueError(f"Low price cannot be higher than high price: {self.low} > {self.high}")
    
    @classmethod
    def from_floats(cls, low: float, high: float, currency: str = "USD") -> "PriceRange":
        """float 값들로부터 PriceRange 객체 생성"""
        return cls(
            Price.from_float(low, currency),
            Price.from_float(high, currency)
        )
    
    def contains(self, price: Price) -> bool:
        """주어진 가격이 범위 내에 있는지 확인"""
        return self.low <= price <= self.high
    
    def range_width(self) -> Price:
        """가격 범위의 폭 계산"""
        return self.high.subtract(self.low)
    
    def range_percentage(self) -> Decimal:
        """저가 대비 고가의 변동폭 (백분율)"""
        if self.low.value == 0:
            raise ValueError("Cannot calculate range percentage with zero low price")
        return ((self.high.value - self.low.value) / self.low.value) * 100
    
    def midpoint(self) -> Price:
        """중간 가격 계산"""
        mid_value = (self.low.value + self.high.value) / 2
        return Price(mid_value, self.low.currency)
    
    def __str__(self) -> str:
        return f"{self.low} - {self.high}"
