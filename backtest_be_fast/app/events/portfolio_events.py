"""
포트폴리오 도메인 이벤트들
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from app.events import DomainEvent


class PortfolioCreatedEvent(DomainEvent):
    """포트폴리오 생성 이벤트"""
    
    def __init__(self, portfolio_id: str, name: str, assets: List[Dict[str, Any]],
                 total_value: float, creator_id: Optional[str] = None,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.portfolio_id = portfolio_id
        self.name = name
        self.assets = assets
        self.total_value = total_value
        self.creator_id = creator_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'portfolio_id': self.portfolio_id,
            'name': self.name,
            'assets': self.assets,
            'total_value': self.total_value,
            'creator_id': self.creator_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioCreatedEvent':
        return cls(
            portfolio_id=data['portfolio_id'],
            name=data['name'],
            assets=data['assets'],
            total_value=data['total_value'],
            creator_id=data.get('creator_id'),
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class PortfolioRebalancedEvent(DomainEvent):
    """포트폴리오 리밸런싱 이벤트"""
    
    def __init__(self, portfolio_id: str, old_weights: Dict[str, float],
                 new_weights: Dict[str, float], rebalancing_trigger: str,
                 transaction_cost: float, diversification_change: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.portfolio_id = portfolio_id
        self.old_weights = old_weights
        self.new_weights = new_weights
        self.rebalancing_trigger = rebalancing_trigger
        self.transaction_cost = transaction_cost
        self.diversification_change = diversification_change
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'portfolio_id': self.portfolio_id,
            'old_weights': self.old_weights,
            'new_weights': self.new_weights,
            'rebalancing_trigger': self.rebalancing_trigger,
            'transaction_cost': self.transaction_cost,
            'diversification_change': self.diversification_change
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioRebalancedEvent':
        return cls(
            portfolio_id=data['portfolio_id'],
            old_weights=data['old_weights'],
            new_weights=data['new_weights'],
            rebalancing_trigger=data['rebalancing_trigger'],
            transaction_cost=data['transaction_cost'],
            diversification_change=data['diversification_change'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class PortfolioOptimizedEvent(DomainEvent):
    """포트폴리오 최적화 이벤트"""
    
    def __init__(self, portfolio_id: str, original_weights: Dict[str, float],
                 optimized_weights: Dict[str, float], optimization_method: str,
                 risk_tolerance: float, expected_improvement: Dict[str, float],
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.portfolio_id = portfolio_id
        self.original_weights = original_weights
        self.optimized_weights = optimized_weights
        self.optimization_method = optimization_method
        self.risk_tolerance = risk_tolerance
        self.expected_improvement = expected_improvement
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'portfolio_id': self.portfolio_id,
            'original_weights': self.original_weights,
            'optimized_weights': self.optimized_weights,
            'optimization_method': self.optimization_method,
            'risk_tolerance': self.risk_tolerance,
            'expected_improvement': self.expected_improvement
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioOptimizedEvent':
        return cls(
            portfolio_id=data['portfolio_id'],
            original_weights=data['original_weights'],
            optimized_weights=data['optimized_weights'],
            optimization_method=data['optimization_method'],
            risk_tolerance=data['risk_tolerance'],
            expected_improvement=data['expected_improvement'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class AssetAddedToPortfolioEvent(DomainEvent):
    """포트폴리오에 자산 추가 이벤트"""
    
    def __init__(self, portfolio_id: str, asset_symbol: str, asset_type: str,
                 target_weight: float, added_value: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.portfolio_id = portfolio_id
        self.asset_symbol = asset_symbol
        self.asset_type = asset_type
        self.target_weight = target_weight
        self.added_value = added_value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'portfolio_id': self.portfolio_id,
            'asset_symbol': self.asset_symbol,
            'asset_type': self.asset_type,
            'target_weight': self.target_weight,
            'added_value': self.added_value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssetAddedToPortfolioEvent':
        return cls(
            portfolio_id=data['portfolio_id'],
            asset_symbol=data['asset_symbol'],
            asset_type=data['asset_type'],
            target_weight=data['target_weight'],
            added_value=data['added_value'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class AssetRemovedFromPortfolioEvent(DomainEvent):
    """포트폴리오에서 자산 제거 이벤트"""
    
    def __init__(self, portfolio_id: str, asset_symbol: str, asset_type: str,
                 previous_weight: float, removed_value: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.portfolio_id = portfolio_id
        self.asset_symbol = asset_symbol
        self.asset_type = asset_type
        self.previous_weight = previous_weight
        self.removed_value = removed_value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'portfolio_id': self.portfolio_id,
            'asset_symbol': self.asset_symbol,
            'asset_type': self.asset_type,
            'previous_weight': self.previous_weight,
            'removed_value': self.removed_value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssetRemovedFromPortfolioEvent':
        return cls(
            portfolio_id=data['portfolio_id'],
            asset_symbol=data['asset_symbol'],
            asset_type=data['asset_type'],
            previous_weight=data['previous_weight'],
            removed_value=data['removed_value'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class RiskToleranceChangedEvent(DomainEvent):
    """리스크 허용도 변경 이벤트"""
    
    def __init__(self, portfolio_id: str, old_risk_tolerance: float,
                 new_risk_tolerance: float, change_reason: str,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.portfolio_id = portfolio_id
        self.old_risk_tolerance = old_risk_tolerance
        self.new_risk_tolerance = new_risk_tolerance
        self.change_reason = change_reason
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'portfolio_id': self.portfolio_id,
            'old_risk_tolerance': self.old_risk_tolerance,
            'new_risk_tolerance': self.new_risk_tolerance,
            'change_reason': self.change_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskToleranceChangedEvent':
        return cls(
            portfolio_id=data['portfolio_id'],
            old_risk_tolerance=data['old_risk_tolerance'],
            new_risk_tolerance=data['new_risk_tolerance'],
            change_reason=data['change_reason'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )
