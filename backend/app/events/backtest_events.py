"""
백테스트 도메인 이벤트들
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from app.events import DomainEvent


class BacktestStartedEvent(DomainEvent):
    """백테스트 시작 이벤트"""
    
    def __init__(self, backtest_id: str, symbol: str, strategy: str, 
                 start_date: str, end_date: str, parameters: Dict[str, Any],
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.backtest_id = backtest_id
        self.symbol = symbol
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.parameters = parameters
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'backtest_id': self.backtest_id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'parameters': self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestStartedEvent':
        return cls(
            backtest_id=data['backtest_id'],
            symbol=data['symbol'],
            strategy=data['strategy'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            parameters=data['parameters'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class BacktestCompletedEvent(DomainEvent):
    """백테스트 완료 이벤트"""
    
    def __init__(self, backtest_id: str, symbol: str, strategy: str,
                 total_return: float, annual_return: float, sharpe_ratio: float,
                 max_drawdown: float, trade_count: int, success: bool,
                 execution_time_seconds: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.backtest_id = backtest_id
        self.symbol = symbol
        self.strategy = strategy
        self.total_return = total_return
        self.annual_return = annual_return
        self.sharpe_ratio = sharpe_ratio
        self.max_drawdown = max_drawdown
        self.trade_count = trade_count
        self.success = success
        self.execution_time_seconds = execution_time_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'backtest_id': self.backtest_id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'trade_count': self.trade_count,
            'success': self.success,
            'execution_time_seconds': self.execution_time_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestCompletedEvent':
        return cls(
            backtest_id=data['backtest_id'],
            symbol=data['symbol'],
            strategy=data['strategy'],
            total_return=data['total_return'],
            annual_return=data['annual_return'],
            sharpe_ratio=data['sharpe_ratio'],
            max_drawdown=data['max_drawdown'],
            trade_count=data['trade_count'],
            success=data['success'],
            execution_time_seconds=data['execution_time_seconds'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class BacktestFailedEvent(DomainEvent):
    """백테스트 실패 이벤트"""
    
    def __init__(self, backtest_id: str, symbol: str, strategy: str,
                 error_message: str, error_type: str,
                 execution_time_seconds: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.backtest_id = backtest_id
        self.symbol = symbol
        self.strategy = strategy
        self.error_message = error_message
        self.error_type = error_type
        self.execution_time_seconds = execution_time_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'backtest_id': self.backtest_id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'execution_time_seconds': self.execution_time_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestFailedEvent':
        return cls(
            backtest_id=data['backtest_id'],
            symbol=data['symbol'],
            strategy=data['strategy'],
            error_message=data['error_message'],
            error_type=data['error_type'],
            execution_time_seconds=data['execution_time_seconds'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class StrategyOptimizationStartedEvent(DomainEvent):
    """전략 최적화 시작 이벤트"""
    
    def __init__(self, optimization_id: str, symbol: str, strategy: str,
                 parameter_ranges: Dict[str, Any], optimization_metric: str,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.optimization_id = optimization_id
        self.symbol = symbol
        self.strategy = strategy
        self.parameter_ranges = parameter_ranges
        self.optimization_metric = optimization_metric
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'optimization_id': self.optimization_id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'parameter_ranges': self.parameter_ranges,
            'optimization_metric': self.optimization_metric
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyOptimizationStartedEvent':
        return cls(
            optimization_id=data['optimization_id'],
            symbol=data['symbol'],
            strategy=data['strategy'],
            parameter_ranges=data['parameter_ranges'],
            optimization_metric=data['optimization_metric'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class StrategyOptimizationCompletedEvent(DomainEvent):
    """전략 최적화 완료 이벤트"""
    
    def __init__(self, optimization_id: str, symbol: str, strategy: str,
                 best_parameters: Dict[str, Any], best_metric_value: float,
                 total_combinations_tested: int, execution_time_seconds: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.optimization_id = optimization_id
        self.symbol = symbol
        self.strategy = strategy
        self.best_parameters = best_parameters
        self.best_metric_value = best_metric_value
        self.total_combinations_tested = total_combinations_tested
        self.execution_time_seconds = execution_time_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'optimization_id': self.optimization_id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'best_parameters': self.best_parameters,
            'best_metric_value': self.best_metric_value,
            'total_combinations_tested': self.total_combinations_tested,
            'execution_time_seconds': self.execution_time_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyOptimizationCompletedEvent':
        return cls(
            optimization_id=data['optimization_id'],
            symbol=data['symbol'],
            strategy=data['strategy'],
            best_parameters=data['best_parameters'],
            best_metric_value=data['best_metric_value'],
            total_combinations_tested=data['total_combinations_tested'],
            execution_time_seconds=data['execution_time_seconds'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )
