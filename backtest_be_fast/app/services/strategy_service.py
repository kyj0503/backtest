"""
Strategy service - wrapper around strategy_registry for backward compatibility
"""

from typing import Dict, Any, Type
from backtesting import Strategy

from app import strategy_registry


class StrategyService:
    """Strategy management service - wrapper around strategy_registry"""

    def get_strategy_class(self, strategy_name: str) -> Type[Strategy]:
        """Return strategy class"""
        return strategy_registry.get_strategy_class(strategy_name)

    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """Return strategy information"""
        strategies = strategy_registry.get_available_strategies()
        if strategy_name not in strategies:
            raise ValueError(f"Unsupported strategy: {strategy_name}")
        return strategies[strategy_name]

    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Return all strategy information"""
        return strategy_registry.get_available_strategies()

    def validate_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate strategy parameters and apply defaults"""
        if not strategy_registry.validate_strategy_params(strategy_name, params):
            raise ValueError(f"Invalid parameters: {params}")
        
        # Return parameters with defaults applied
        return strategy_registry._apply_defaults(strategy_name, params)


# Global instance
strategy_service = StrategyService()
