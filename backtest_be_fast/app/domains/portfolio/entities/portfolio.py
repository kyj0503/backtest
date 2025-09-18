"""
포트폴리오 엔티티

포트폴리오를 나타내는 도메인 엔티티입니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from .asset import AssetEntity
from ..value_objects.weight import Weight
from ..value_objects.allocation import Allocation


@dataclass
class PortfolioEntity:
    """포트폴리오 엔티티"""
    
    # 식별자
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 기본 정보
    name: str = ""
    description: str = ""
    
    # 자산 구성
    assets: List[AssetEntity] = field(default_factory=list)
    
    # 포트폴리오 설정
    total_value: float = 0.0
    currency: str = "USD"
    rebalancing_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    rebalancing_threshold: float = 0.05  # 5%
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.name:
            raise ValueError("포트폴리오명은 필수입니다.")
        
        if self.total_value < 0:
            raise ValueError("포트폴리오 가치는 음수일 수 없습니다.")
    
    def add_asset(self, asset: AssetEntity):
        """자산 추가"""
        # 중복 심볼 검사
        if any(a.symbol == asset.symbol for a in self.assets):
            raise ValueError(f"이미 존재하는 자산입니다: {asset.symbol}")
        
        self.assets.append(asset)
        self.updated_at = datetime.now()
    
    def remove_asset(self, symbol: str) -> bool:
        """자산 제거"""
        original_count = len(self.assets)
        self.assets = [a for a in self.assets if a.symbol != symbol]
        
        if len(self.assets) < original_count:
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_asset(self, symbol: str) -> Optional[AssetEntity]:
        """자산 조회"""
        return next((a for a in self.assets if a.symbol == symbol), None)
    
    def get_active_assets(self) -> List[AssetEntity]:
        """활성 자산 목록"""
        return [a for a in self.assets if a.is_active]
    
    def get_current_allocation(self) -> Allocation:
        """현재 자산 배분"""
        weights = {
            asset.symbol: asset.current_weight
            for asset in self.get_active_assets()
        }
        return Allocation(weights)
    
    def get_target_allocation(self) -> Allocation:
        """목표 자산 배분"""
        weights = {
            asset.symbol: asset.target_weight
            for asset in self.get_active_assets()
        }
        return Allocation(weights)
    
    def needs_rebalancing(self) -> bool:
        """리밸런싱 필요 여부"""
        return any(
            asset.needs_rebalancing(self.rebalancing_threshold)
            for asset in self.get_active_assets()
        )
    
    def get_rebalancing_orders(self) -> Dict[str, float]:
        """리밸런싱 주문 목록"""
        orders = {}
        
        for asset in self.get_active_assets():
            if asset.needs_rebalancing(self.rebalancing_threshold):
                amount = asset.get_rebalancing_amount(self.total_value)
                if abs(amount) > 1.0:  # 최소 거래 금액
                    orders[asset.symbol] = amount
        
        return orders
    
    def calculate_turnover(self) -> Weight:
        """회전율 계산"""
        current = self.get_current_allocation()
        target = self.get_target_allocation()
        return current.calculate_turnover(target)
    
    def update_asset_prices(self, prices: Dict[str, float]):
        """자산 가격 일괄 업데이트"""
        for symbol, price in prices.items():
            asset = self.get_asset(symbol)
            if asset:
                asset.update_price(price)
        
        self.updated_at = datetime.now()
    
    def rebalance_to_target(self):
        """목표 배분으로 리밸런싱"""
        target_allocation = self.get_target_allocation()
        
        for asset in self.get_active_assets():
            target_weight = target_allocation.get_weight(asset.symbol)
            asset.update_weight(target_weight)
        
        self.updated_at = datetime.now()
    
    def get_asset_count(self) -> int:
        """총 자산 개수"""
        return len(self.get_active_assets())
    
    def get_equity_assets(self) -> List[AssetEntity]:
        """주식성 자산들"""
        return [a for a in self.get_active_assets() if a.is_equity_asset()]
    
    def get_cash_assets(self) -> List[AssetEntity]:
        """현금 자산들"""
        return [a for a in self.get_active_assets() if a.is_cash_asset()]
    
    def get_largest_positions(self, count: int = 5) -> List[AssetEntity]:
        """최대 비중 포지션들"""
        active_assets = self.get_active_assets()
        sorted_assets = sorted(active_assets, key=lambda a: a.current_weight.value, reverse=True)
        return sorted_assets[:count]
    
    def get_concentration_ratio(self, top_n: int = 5) -> Weight:
        """상위 N개 자산 집중도"""
        top_assets = self.get_largest_positions(top_n)
        concentration = sum(asset.current_weight.value for asset in top_assets)
        return Weight(concentration)
    
    def is_well_diversified(self, max_single_weight: float = 0.3) -> bool:
        """충분히 분산되었는지 확인"""
        return all(
            asset.current_weight.value <= max_single_weight
            for asset in self.get_active_assets()
        )
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "total_value": self.total_value,
            "currency": self.currency,
            "asset_count": self.get_asset_count(),
            "needs_rebalancing": self.needs_rebalancing(),
            "concentration_top5": self.get_concentration_ratio(5).to_percentage(),
            "is_well_diversified": self.is_well_diversified(),
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }
    
    def to_detailed_dict(self) -> Dict[str, Any]:
        """상세 정보 딕셔너리"""
        return {
            "metadata": {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "is_active": self.is_active
            },
            "configuration": {
                "total_value": self.total_value,
                "currency": self.currency,
                "rebalancing_frequency": self.rebalancing_frequency,
                "rebalancing_threshold": self.rebalancing_threshold
            },
            "assets": [asset.to_summary_dict() for asset in self.get_active_assets()],
            "allocation": {
                "current": self.get_current_allocation().to_detailed_dict(),
                "target": self.get_target_allocation().to_detailed_dict()
            },
            "analytics": {
                "needs_rebalancing": self.needs_rebalancing(),
                "turnover": self.calculate_turnover().to_percentage(),
                "concentration_top5": self.get_concentration_ratio(5).to_percentage(),
                "is_well_diversified": self.is_well_diversified(),
                "rebalancing_orders": self.get_rebalancing_orders()
            }
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return (f"Portfolio({self.name}, {self.get_asset_count()}개 자산, "
                f"${self.total_value:,.2f})")
