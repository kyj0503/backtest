"""
자산 엔티티

포트폴리오를 구성하는 개별 자산을 나타내는 도메인 엔티티입니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid

from ..value_objects.weight import Weight


class AssetType(Enum):
    """자산 타입"""
    STOCK = "stock"
    CASH = "cash"
    BOND = "bond"
    ETF = "etf"
    CRYPTO = "crypto"
    COMMODITY = "commodity"


@dataclass
class AssetEntity:
    """자산 엔티티"""
    
    # 식별자
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 기본 정보
    symbol: str = ""
    name: str = ""
    asset_type: AssetType = AssetType.STOCK
    
    # 시장 정보
    exchange: str = ""
    currency: str = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # 포트폴리오 내 정보
    target_weight: Weight = field(default_factory=Weight.zero)
    current_weight: Weight = field(default_factory=Weight.zero)
    
    # 시장 데이터
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    # 추가 속성
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.symbol:
            raise ValueError("심볼은 필수입니다.")
        
        if not self.name:
            self.name = self.symbol
        
        if self.current_price is not None and self.current_price < 0:
            raise ValueError("가격은 음수일 수 없습니다.")
    
    @classmethod
    def create_stock(cls,
                    symbol: str,
                    name: str = None,
                    target_weight: Weight = None,
                    exchange: str = "",
                    sector: str = None,
                    **kwargs) -> "AssetEntity":
        """주식 자산 생성"""
        return cls(
            symbol=symbol,
            name=name or symbol,
            asset_type=AssetType.STOCK,
            target_weight=target_weight or Weight.zero(),
            exchange=exchange,
            sector=sector,
            **kwargs
        )
    
    @classmethod
    def create_cash(cls,
                   currency: str = "USD",
                   target_weight: Weight = None,
                   **kwargs) -> "AssetEntity":
        """현금 자산 생성"""
        symbol = f"CASH_{currency}"
        return cls(
            symbol=symbol,
            name=f"현금 ({currency})",
            asset_type=AssetType.CASH,
            target_weight=target_weight or Weight.zero(),
            currency=currency,
            current_price=1.0,  # 현금은 항상 1.0
            **kwargs
        )
    
    @classmethod
    def create_etf(cls,
                  symbol: str,
                  name: str = None,
                  target_weight: Weight = None,
                  **kwargs) -> "AssetEntity":
        """ETF 자산 생성"""
        return cls(
            symbol=symbol,
            name=name or symbol,
            asset_type=AssetType.ETF,
            target_weight=target_weight or Weight.zero(),
            **kwargs
        )
    
    def update_price(self, new_price: float):
        """가격 업데이트"""
        if new_price < 0:
            raise ValueError("가격은 음수일 수 없습니다.")
        
        self.current_price = new_price
        self.updated_at = datetime.now()
    
    def update_weight(self, new_weight: Weight):
        """현재 비중 업데이트"""
        self.current_weight = new_weight
        self.updated_at = datetime.now()
    
    def set_target_weight(self, target_weight: Weight):
        """목표 비중 설정"""
        self.target_weight = target_weight
        self.updated_at = datetime.now()
    
    def get_weight_deviation(self) -> Weight:
        """목표 비중과 현재 비중의 차이"""
        return self.current_weight.subtract(self.target_weight)
    
    def needs_rebalancing(self, threshold: float = 0.05) -> bool:
        """리밸런싱 필요 여부 (기본: 5% 임계값)"""
        deviation = abs(self.get_weight_deviation().value)
        return deviation >= threshold
    
    def is_overweight(self) -> bool:
        """목표 대비 과다 보유 여부"""
        return self.current_weight > self.target_weight
    
    def is_underweight(self) -> bool:
        """목표 대비 과소 보유 여부"""
        return self.current_weight < self.target_weight
    
    def is_cash_asset(self) -> bool:
        """현금 자산 여부"""
        return self.asset_type == AssetType.CASH
    
    def is_equity_asset(self) -> bool:
        """주식성 자산 여부"""
        return self.asset_type in [AssetType.STOCK, AssetType.ETF]
    
    def get_market_value(self, total_portfolio_value: float) -> float:
        """시장가치 계산"""
        return total_portfolio_value * self.current_weight.value
    
    def get_target_value(self, total_portfolio_value: float) -> float:
        """목표가치 계산"""
        return total_portfolio_value * self.target_weight.value
    
    def get_rebalancing_amount(self, total_portfolio_value: float) -> float:
        """리밸런싱 필요 금액 (양수: 매수, 음수: 매도)"""
        current_value = self.get_market_value(total_portfolio_value)
        target_value = self.get_target_value(total_portfolio_value)
        return target_value - current_value
    
    def add_metadata(self, key: str, value: Any):
        """메타데이터 추가"""
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        return self.metadata.get(key, default)
    
    def deactivate(self):
        """자산 비활성화"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def activate(self):
        """자산 활성화"""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type.value,
            "current_weight": self.current_weight.to_percentage(),
            "target_weight": self.target_weight.to_percentage(),
            "weight_deviation": self.get_weight_deviation().to_percentage(),
            "needs_rebalancing": self.needs_rebalancing(),
            "current_price": self.current_price,
            "is_active": self.is_active
        }
    
    def to_detailed_dict(self) -> Dict[str, Any]:
        """상세 정보 딕셔너리"""
        return {
            "identification": {
                "id": self.id,
                "symbol": self.symbol,
                "name": self.name,
                "asset_type": self.asset_type.value
            },
            "market_info": {
                "exchange": self.exchange,
                "currency": self.currency,
                "sector": self.sector,
                "industry": self.industry,
                "current_price": self.current_price,
                "market_cap": self.market_cap
            },
            "portfolio_info": {
                "target_weight": self.target_weight.to_dict(),
                "current_weight": self.current_weight.to_dict(),
                "weight_deviation": self.get_weight_deviation().to_dict(),
                "is_overweight": self.is_overweight(),
                "is_underweight": self.is_underweight(),
                "needs_rebalancing": self.needs_rebalancing()
            },
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "is_active": self.is_active,
                "additional_data": self.metadata
            }
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return (f"Asset({self.symbol}, {self.asset_type.value}, "
                f"목표: {self.target_weight}, 현재: {self.current_weight})")
