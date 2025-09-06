"""
자산 배분 값 객체 (Value Object)

포트폴리오의 자산 배분을 나타내는 불변 객체입니다.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Tuple
from .weight import Weight


@dataclass(frozen=True)
class Allocation:
    """자산 배분 값 객체"""
    
    weights: Dict[str, Weight] = field(default_factory=dict)
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.weights:
            raise ValueError("자산 배분이 비어있습니다.")
        
        # 총 비중 검증
        total = self.get_total_weight()
        if not (0.99 <= total.value <= 1.01):  # 부동소수점 오차 허용
            raise ValueError(f"총 비중이 100%가 아닙니다. 현재: {total.to_percentage():.2f}%")
        
        # 음수 비중 검증
        for symbol, weight in self.weights.items():
            if weight.value < 0:
                raise ValueError(f"음수 비중은 허용되지 않습니다: {symbol} = {weight}")
    
    @classmethod
    def equal_weight(cls, symbols: List[str]) -> "Allocation":
        """동일 가중 배분 생성"""
        if not symbols:
            raise ValueError("심볼 목록이 비어있습니다.")
        
        weight = Weight.equal_weight(len(symbols))
        weights = {symbol: weight for symbol in symbols}
        return cls(weights)
    
    @classmethod
    def from_percentages(cls, percentages: Dict[str, float]) -> "Allocation":
        """퍼센트값으로부터 Allocation 생성"""
        weights = {
            symbol: Weight.from_percentage(pct) 
            for symbol, pct in percentages.items()
        }
        return cls(weights)
    
    @classmethod
    def from_amounts(cls, amounts: Dict[str, float]) -> "Allocation":
        """금액으로부터 Allocation 생성"""
        total_amount = sum(amounts.values())
        if total_amount == 0:
            raise ValueError("총 금액이 0입니다.")
        
        weights = {
            symbol: Weight(amount / total_amount)
            for symbol, amount in amounts.items()
        }
        return cls(weights)
    
    @classmethod
    def market_cap_weighted(cls, market_caps: Dict[str, float]) -> "Allocation":
        """시가총액 가중 배분 생성"""
        return cls.from_amounts(market_caps)
    
    def get_weight(self, symbol: str) -> Weight:
        """특정 자산의 비중 조회"""
        return self.weights.get(symbol, Weight.zero())
    
    def get_total_weight(self) -> Weight:
        """총 비중 계산"""
        total = sum(weight.value for weight in self.weights.values())
        return Weight(total)
    
    def get_symbols(self) -> List[str]:
        """포함된 심볼 목록"""
        return list(self.weights.keys())
    
    def get_significant_assets(self, threshold: float = 0.01) -> Dict[str, Weight]:
        """유의미한 비중을 가진 자산들 (기본: 1% 이상)"""
        return {
            symbol: weight 
            for symbol, weight in self.weights.items()
            if weight.is_significant(threshold)
        }
    
    def get_largest_positions(self, count: int = 5) -> List[Tuple[str, Weight]]:
        """최대 비중 포지션들"""
        sorted_positions = sorted(
            self.weights.items(), 
            key=lambda x: x[1].value, 
            reverse=True
        )
        return sorted_positions[:count]
    
    def get_smallest_positions(self, count: int = 5) -> List[Tuple[str, Weight]]:
        """최소 비중 포지션들"""
        sorted_positions = sorted(
            self.weights.items(), 
            key=lambda x: x[1].value
        )
        return sorted_positions[:count]
    
    def rebalance_to_target(self, target: "Allocation") -> Dict[str, Weight]:
        """목표 배분으로 리밸런싱하기 위한 조정값"""
        adjustments = {}
        
        all_symbols = set(self.get_symbols()) | set(target.get_symbols())
        
        for symbol in all_symbols:
            current_weight = self.get_weight(symbol)
            target_weight = target.get_weight(symbol)
            adjustment = target_weight.subtract(current_weight)
            
            if not adjustment.is_zero():
                adjustments[symbol] = adjustment
        
        return adjustments
    
    def calculate_turnover(self, new_allocation: "Allocation") -> Weight:
        """회전율 계산 (변경된 비중의 합)"""
        total_change = 0.0
        
        all_symbols = set(self.get_symbols()) | set(new_allocation.get_symbols())
        
        for symbol in all_symbols:
            current_weight = self.get_weight(symbol)
            new_weight = new_allocation.get_weight(symbol)
            change = abs(current_weight.value - new_weight.value)
            total_change += change
        
        return Weight(total_change / 2)  # 한 방향 변화만 계산
    
    def is_concentrated(self, threshold: float = 0.5) -> bool:
        """집중도 검사 (특정 비중 이상이 하나의 자산에 집중되었는지)"""
        return any(weight.value >= threshold for weight in self.weights.values())
    
    def get_concentration_ratio(self, top_n: int = 5) -> Weight:
        """상위 N개 자산의 집중도"""
        top_positions = self.get_largest_positions(top_n)
        concentration = sum(weight.value for _, weight in top_positions)
        return Weight(concentration)
    
    def get_diversification_score(self) -> float:
        """다양화 점수 (0-1, 1이 최대 다양화)"""
        if len(self.weights) <= 1:
            return 0.0
        
        # 허핀달 지수의 역수를 이용한 다양화 점수
        herfindahl = sum(weight.value ** 2 for weight in self.weights.values())
        max_diversification = Decimal('1.0') / Decimal(str(len(self.weights)))  # 동일가중시 최대 다양화
        
        herfindahl_reciprocal = Decimal('1') / herfindahl
        max_div_reciprocal = Decimal('1') / max_diversification
        
        return float((herfindahl_reciprocal - 1) / (max_div_reciprocal - 1))
    
    def normalize(self) -> "Allocation":
        """비중 정규화 (총합이 100%가 되도록)"""
        total = self.get_total_weight()
        
        if total.is_zero():
            raise ValueError("총 비중이 0이므로 정규화할 수 없습니다.")
        
        normalized_weights = {
            symbol: weight.normalize_with(total)
            for symbol, weight in self.weights.items()
        }
        
        return Allocation(normalized_weights)
    
    def filter_by_minimum_weight(self, min_weight: Weight) -> "Allocation":
        """최소 비중 이상인 자산만 필터링"""
        filtered_weights = {
            symbol: weight
            for symbol, weight in self.weights.items()
            if weight >= min_weight
        }
        
        if not filtered_weights:
            raise ValueError("필터링 후 자산이 없습니다.")
        
        return Allocation(filtered_weights).normalize()
    
    def to_percentages(self) -> Dict[str, float]:
        """퍼센트 딕셔너리로 변환"""
        return {
            symbol: weight.to_percentage()
            for symbol, weight in self.weights.items()
        }
    
    def to_summary_dict(self) -> Dict[str, any]:
        """요약 정보 딕셔너리"""
        return {
            "total_assets": len(self.weights),
            "total_weight": self.get_total_weight().to_percentage(),
            "largest_position": {
                "symbol": self.get_largest_positions(1)[0][0],
                "weight": self.get_largest_positions(1)[0][1].to_percentage()
            } if self.weights else None,
            "concentration_top5": self.get_concentration_ratio(5).to_percentage(),
            "diversification_score": round(self.get_diversification_score(), 3),
            "is_concentrated": self.is_concentrated()
        }
    
    def to_detailed_dict(self) -> Dict[str, any]:
        """상세 정보 딕셔너리"""
        return {
            "weights": self.to_percentages(),
            "summary": self.to_summary_dict(),
            "largest_positions": [
                {"symbol": symbol, "weight": weight.to_percentage()}
                for symbol, weight in self.get_largest_positions()
            ],
            "significant_assets": {
                symbol: weight.to_percentage()
                for symbol, weight in self.get_significant_assets().items()
            }
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        top_3 = self.get_largest_positions(3)
        asset_strs = [f"{symbol}: {weight}" for symbol, weight in top_3]
        return f"Allocation({', '.join(asset_strs)}{'...' if len(self.weights) > 3 else ''})"
