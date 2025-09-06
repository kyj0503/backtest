"""
백테스트 관련 커맨드들
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.cqrs import Command


class RunBacktestCommand(Command):
    """백테스트 실행 커맨드"""
    
    def __init__(self, symbol: str, strategy: str, start_date: str, end_date: str,
                 strategy_params: Dict[str, Any], commission: float = 0.002,
                 initial_cash: float = 10000.0, use_enhanced_analysis: bool = False,
                 command_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(command_id, timestamp)
        self.symbol = symbol
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.strategy_params = strategy_params
        self.commission = commission
        self.initial_cash = initial_cash
        self.use_enhanced_analysis = use_enhanced_analysis
    
    def validate(self) -> bool:
        """커맨드 유효성 검증"""
        if not self.symbol or not self.strategy:
            return False
        
        if not self.start_date or not self.end_date:
            return False
        
        try:
            start = datetime.strptime(self.start_date, '%Y-%m-%d')
            end = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start >= end:
                return False
        except ValueError:
            return False
        
        if self.commission < 0 or self.initial_cash <= 0:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'strategy': self.strategy,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'strategy_params': self.strategy_params,
            'commission': self.commission,
            'initial_cash': self.initial_cash,
            'use_enhanced_analysis': self.use_enhanced_analysis
        }


class RunPortfolioBacktestCommand(Command):
    """포트폴리오 백테스트 실행 커맨드"""
    
    def __init__(self, portfolio_name: str, stocks: List[Dict[str, Any]], 
                 start_date: str, end_date: str, total_investment: float,
                 rebalancing_frequency: str = 'none', commission: float = 0.002,
                 use_enhanced_analysis: bool = False,
                 command_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(command_id, timestamp)
        self.portfolio_name = portfolio_name
        self.stocks = stocks
        self.start_date = start_date
        self.end_date = end_date
        self.total_investment = total_investment
        self.rebalancing_frequency = rebalancing_frequency
        self.commission = commission
        self.use_enhanced_analysis = use_enhanced_analysis
    
    def validate(self) -> bool:
        """커맨드 유효성 검증"""
        if not self.portfolio_name or not self.stocks:
            return False
        
        if not self.start_date or not self.end_date:
            return False
        
        try:
            start = datetime.strptime(self.start_date, '%Y-%m-%d')
            end = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start >= end:
                return False
        except ValueError:
            return False
        
        if self.total_investment <= 0:
            return False
        
        # 포트폴리오 가중치 합계 검증
        total_weight = sum(stock.get('weight', 0) for stock in self.stocks)
        if abs(total_weight - 100) > 0.01:  # 100%에서 0.01% 이내 허용
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'portfolio_name': self.portfolio_name,
            'stocks': self.stocks,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_investment': self.total_investment,
            'rebalancing_frequency': self.rebalancing_frequency,
            'commission': self.commission,
            'use_enhanced_analysis': self.use_enhanced_analysis
        }


class OptimizeStrategyCommand(Command):
    """전략 최적화 커맨드"""
    
    def __init__(self, symbol: str, strategy: str, start_date: str, end_date: str,
                 parameter_ranges: Dict[str, Any], optimization_metric: str = 'SQN',
                 max_combinations: int = 1000,
                 command_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(command_id, timestamp)
        self.symbol = symbol
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.parameter_ranges = parameter_ranges
        self.optimization_metric = optimization_metric
        self.max_combinations = max_combinations
    
    def validate(self) -> bool:
        """커맨드 유효성 검증"""
        if not self.symbol or not self.strategy:
            return False
        
        if not self.start_date or not self.end_date:
            return False
        
        if not self.parameter_ranges:
            return False
        
        if self.max_combinations <= 0:
            return False
        
        try:
            start = datetime.strptime(self.start_date, '%Y-%m-%d')
            end = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start >= end:
                return False
        except ValueError:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'strategy': self.strategy,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'parameter_ranges': self.parameter_ranges,
            'optimization_metric': self.optimization_metric,
            'max_combinations': self.max_combinations
        }


class OptimizePortfolioCommand(Command):
    """포트폴리오 최적화 커맨드"""
    
    def __init__(self, portfolio_id: str, assets: List[Dict[str, Any]], 
                 risk_tolerance: float, optimization_method: str = 'risk_adjusted',
                 constraints: Optional[Dict[str, Any]] = None,
                 command_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(command_id, timestamp)
        self.portfolio_id = portfolio_id
        self.assets = assets
        self.risk_tolerance = risk_tolerance
        self.optimization_method = optimization_method
        self.constraints = constraints or {}
    
    def validate(self) -> bool:
        """커맨드 유효성 검증"""
        if not self.portfolio_id or not self.assets:
            return False
        
        if not (0.0 <= self.risk_tolerance <= 1.0):
            return False
        
        if self.optimization_method not in ['risk_adjusted', 'equal_weight', 'min_variance']:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'portfolio_id': self.portfolio_id,
            'assets': self.assets,
            'risk_tolerance': self.risk_tolerance,
            'optimization_method': self.optimization_method,
            'constraints': self.constraints
        }


class RebalancePortfolioCommand(Command):
    """포트폴리오 리밸런싱 커맨드"""
    
    def __init__(self, portfolio_id: str, target_weights: Dict[str, float],
                 rebalancing_trigger: str, transaction_cost_limit: float = 1000.0,
                 command_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(command_id, timestamp)
        self.portfolio_id = portfolio_id
        self.target_weights = target_weights
        self.rebalancing_trigger = rebalancing_trigger
        self.transaction_cost_limit = transaction_cost_limit
    
    def validate(self) -> bool:
        """커맨드 유효성 검증"""
        if not self.portfolio_id or not self.target_weights:
            return False
        
        # 가중치 합계 검증
        total_weight = sum(self.target_weights.values())
        if abs(total_weight - 1.0) > 0.01:  # 1.0에서 0.01 이내 허용
            return False
        
        if self.transaction_cost_limit < 0:
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'portfolio_id': self.portfolio_id,
            'target_weights': self.target_weights,
            'rebalancing_trigger': self.rebalancing_trigger,
            'transaction_cost_limit': self.transaction_cost_limit
        }


class CreatePortfolioCommand(Command):
    """포트폴리오 생성 커맨드"""
    
    def __init__(self, name: str, assets: List[Dict[str, Any]], total_value: float,
                 creator_id: Optional[str] = None,
                 command_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(command_id, timestamp)
        self.name = name
        self.assets = assets
        self.total_value = total_value
        self.creator_id = creator_id
    
    def validate(self) -> bool:
        """커맨드 유효성 검증"""
        if not self.name or not self.assets:
            return False
        
        if self.total_value <= 0:
            return False
        
        # 자산 유효성 검증
        for asset in self.assets:
            if 'symbol' not in asset or 'weight' not in asset:
                return False
            if asset['weight'] < 0:
                return False
        
        # 가중치 합계 검증
        total_weight = sum(asset['weight'] for asset in self.assets)
        if abs(total_weight - 100) > 0.01:  # 100%에서 0.01% 이내 허용
            return False
        
        return True
    
    def _get_data(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'assets': self.assets,
            'total_value': self.total_value,
            'creator_id': self.creator_id
        }
