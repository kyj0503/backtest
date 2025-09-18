"""
가중치 값 객체 (Value Object)

포트폴리오에서 자산의 비중을 나타내는 불변 객체입니다.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Union
import math


@dataclass(frozen=True)
class Weight:
    """자산 비중 값 객체"""
    
    value: float  # 0.0 ~ 1.0 범위의 비중값
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(f"비중은 0.0-1.0 범위여야 합니다. 입력값: {self.value}")
        
        # 부동소수점 정밀도 문제 해결
        object.__setattr__(self, 'value', round(self.value, 6))
    
    @classmethod
    def from_percentage(cls, percentage: float) -> "Weight":
        """퍼센트값으로부터 Weight 생성"""
        return cls(percentage / 100.0)
    
    @classmethod
    def from_ratio(cls, numerator: Union[int, float], denominator: Union[int, float]) -> "Weight":
        """비율로부터 Weight 생성"""
        if denominator == 0:
            raise ValueError("분모는 0이 될 수 없습니다.")
        return cls(float(numerator) / float(denominator))
    
    @classmethod
    def equal_weight(cls, count: int) -> "Weight":
        """동일 가중치 생성"""
        if count <= 0:
            raise ValueError("자산 개수는 양수여야 합니다.")
        return cls(1.0 / count)
    
    @classmethod
    def zero(cls) -> "Weight":
        """0 비중"""
        return cls(0.0)
    
    @classmethod
    def full(cls) -> "Weight":
        """100% 비중"""
        return cls(1.0)
    
    def to_percentage(self) -> float:
        """백분율로 변환 (0.5 -> 50.0)"""
        return float(self.value) * 100.0
    
    def to_basis_points(self) -> int:
        """베이시스 포인트로 변환 (1% = 100bp)"""
        return int(self.value * 10000)
    
    def is_zero(self) -> bool:
        """0 비중 여부"""
        return abs(self.value) < 1e-6
    
    def is_full(self) -> bool:
        """100% 비중 여부"""
        return abs(self.value - 1.0) < 1e-6
    
    def is_significant(self, threshold: float = 0.01) -> bool:
        """유의미한 비중 여부 (기본: 1% 이상)"""
        return self.value >= threshold
    
    def add(self, other: "Weight") -> "Weight":
        """비중 합산"""
        return Weight(self.value + other.value)
    
    def subtract(self, other: "Weight") -> "Weight":
        """비중 차감"""
        return Weight(max(0.0, self.value - other.value))
    
    def multiply(self, factor: float) -> "Weight":
        """비중에 배수 적용"""
        return Weight(min(1.0, self.value * factor))
    
    def normalize_with(self, total_weight: "Weight") -> "Weight":
        """전체 비중으로 정규화"""
        if total_weight.is_zero():
            return Weight.zero()
        return Weight(self.value / total_weight.value)
    
    def compare_to(self, other: "Weight") -> str:
        """다른 비중과 비교"""
        diff = self.value - other.value
        if abs(diff) < 1e-6:
            return "equal"
        elif diff > 0:
            return "higher"
        else:
            return "lower"
    
    def difference_from(self, other: "Weight") -> "Weight":
        """다른 비중과의 차이"""
        return Weight(abs(self.value - other.value))
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "value": self.value,
            "percentage": round(self.to_percentage(), 2),
            "basis_points": self.to_basis_points()
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"{self.to_percentage():.2f}%"
    
    def __float__(self) -> float:
        """float 변환"""
        return self.value
    
    def __add__(self, other: "Weight") -> "Weight":
        """+ 연산자"""
        return self.add(other)
    
    def __sub__(self, other: "Weight") -> "Weight":
        """- 연산자"""
        return self.subtract(other)
    
    def __mul__(self, factor: float) -> "Weight":
        """* 연산자"""
        return self.multiply(factor)
    
    def __rmul__(self, factor: float) -> "Weight":
        """* 연산자 (역순)"""
        return self.multiply(factor)
    
    def __eq__(self, other) -> bool:
        """== 연산자"""
        if not isinstance(other, Weight):
            return False
        return abs(self.value - other.value) < 1e-6
    
    def __lt__(self, other: "Weight") -> bool:
        """< 연산자"""
        return self.value < other.value
    
    def __le__(self, other: "Weight") -> bool:
        """<= 연산자"""
        return self.value <= other.value
    
    def __gt__(self, other: "Weight") -> bool:
        """> 연산자"""
        return self.value > other.value
    
    def __ge__(self, other: "Weight") -> bool:
        """>= 연산자"""
        return self.value >= other.value
