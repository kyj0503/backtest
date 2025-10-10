"""
전략 관리 서비스
"""
from typing import Dict, Any, Type
import logging

from backtesting import Strategy

from app.strategies.sma_strategy import SMAStrategy
from app.strategies.rsi_strategy import RSIStrategy
from app.strategies.bollinger_strategy import BollingerBandsStrategy
from app.strategies.macd_strategy import MACDStrategy
from app.strategies.ema_strategy import EMAStrategy
from app.strategies.buy_hold_strategy import BuyAndHoldStrategy


logger = logging.getLogger(__name__)


STRATEGIES: Dict[str, Dict[str, Any]] = {
    'sma_crossover': {
        'class': SMAStrategy,
        'name': 'Simple Moving Average Crossover',
        'description': 'SMA 단기/장기 이동평균 교차 전략',
        'parameters': {
            'short_window': {
                'type': int,
                'default': 10,
                'min': 2,
                'max': 50,
                'description': '단기 이동평균 기간'
            },
            'long_window': {
                'type': int,
                'default': 20,
                'min': 10,
                'max': 200,
                'description': '장기 이동평균 기간'
            }
        },
        'constraints': ['short_window < long_window']
    },
    'rsi_strategy': {
        'class': RSIStrategy,
        'name': 'RSI Strategy',
        'description': 'RSI 과매수/과매도 기반 전략',
        'parameters': {
            'rsi_period': {
                'type': int,
                'default': 14,
                'min': 2,
                'max': 50,
                'description': 'RSI 계산 기간'
            },
            'rsi_oversold': {
                'type': int,
                'default': 30,
                'min': 10,
                'max': 40,
                'description': 'RSI 과매도 임계값'
            },
            'rsi_overbought': {
                'type': int,
                'default': 70,
                'min': 60,
                'max': 90,
                'description': 'RSI 과매수 임계값'
            }
        },
        'constraints': ['rsi_oversold < rsi_overbought']
    },
    'bollinger_bands': {
        'class': BollingerBandsStrategy,
        'name': 'Bollinger Bands Strategy',
        'description': '볼린저 밴드 기반 전략',
        'parameters': {
            'period': {
                'type': int,
                'default': 20,
                'min': 5,
                'max': 100,
                'description': '이동평균 기간'
            },
            'std_dev': {
                'type': float,
                'default': 2.0,
                'min': 0.5,
                'max': 4.0,
                'description': '표준편차 배수'
            }
        },
        'constraints': []
    },
    'macd_strategy': {
        'class': MACDStrategy,
        'name': 'MACD Strategy',
        'description': 'MACD 기반 전략',
        'parameters': {
            'fast_period': {
                'type': int,
                'default': 12,
                'min': 5,
                'max': 50,
                'description': '빠른 이동평균 기간'
            },
            'slow_period': {
                'type': int,
                'default': 26,
                'min': 10,
                'max': 100,
                'description': '느린 이동평균 기간'
            },
            'signal_period': {
                'type': int,
                'default': 9,
                'min': 2,
                'max': 20,
                'description': '시그널 이동평균 기간'
            }
        },
        'constraints': ['fast_period < slow_period']
    },
    'ema_crossover': {
        'class': EMAStrategy,
        'name': 'EMA Crossover Strategy',
        'description': 'EMA 단기/장기 이동평균 교차 전략',
        'parameters': {
            'fast_window': {
                'type': int,
                'default': 12,
                'min': 5,
                'max': 50,
                'description': '단기 EMA 기간'
            },
            'slow_window': {
                'type': int,
                'default': 26,
                'min': 10,
                'max': 200,
                'description': '장기 EMA 기간'
            }
        },
        'constraints': ['fast_window < slow_window']
    },
    'buy_and_hold': {
        'class': BuyAndHoldStrategy,
        'name': 'Buy and Hold Strategy',
        'description': '매수 후 보유 전략',
        'parameters': {},
        'constraints': []
    }
}


class StrategyService:
    """전략 관리 서비스"""
    
    def get_strategy_class(self, strategy_name: str) -> Type[Strategy]:
        """전략 클래스 반환"""
        if strategy_name not in STRATEGIES:
            raise ValueError(f"지원하지 않는 전략: {strategy_name}")
        return STRATEGIES[strategy_name]['class']
    
    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """전략 정보 반환"""
        if strategy_name not in STRATEGIES:
            raise ValueError(f"지원하지 않는 전략: {strategy_name}")
        
        strategy_data = STRATEGIES[strategy_name].copy()
        strategy_data.pop('class')
        return strategy_data
    
    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """모든 전략 정보 반환"""
        result = {}
        for name, info in STRATEGIES.items():
            # parameters의 type 필드를 문자열로 변환 (JSON 직렬화 가능하도록)
            serializable_params = {}
            for param_name, param_info in info['parameters'].items():
                param_copy = param_info.copy()
                if 'type' in param_copy and isinstance(param_copy['type'], type):
                    param_copy['type'] = param_copy['type'].__name__
                serializable_params[param_name] = param_copy
            
            result[name] = {
                'name': info['name'],
                'description': info['description'],
                'parameters': serializable_params
            }
        return result
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 전략 목록 반환 (get_all_strategies의 별칭)"""
        return self.get_all_strategies()
    
    def validate_strategy_params(
        self, 
        strategy_name: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """전략 파라미터 유효성 검증 및 기본값 적용"""
        if strategy_name not in STRATEGIES:
            raise ValueError(f"지원하지 않는 전략: {strategy_name}")
        
        strategy_info = STRATEGIES[strategy_name]
        validated_params = {}
        
        for param_name, param_info in strategy_info['parameters'].items():
            if param_name in params:
                value = params[param_name]
                param_type = param_info['type']
                
                try:
                    if param_type == int:
                        value = int(value)
                    elif param_type == float:
                        value = float(value)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"파라미터 {param_name}을(를) {param_type.__name__} 타입으로 변환할 수 없습니다"
                    )
                
                if 'min' in param_info and value < param_info['min']:
                    raise ValueError(
                        f"{param_name}의 값 {value}는 최소값 {param_info['min']}보다 작습니다"
                    )
                if 'max' in param_info and value > param_info['max']:
                    raise ValueError(
                        f"{param_name}의 값 {value}는 최대값 {param_info['max']}보다 큽니다"
                    )
                
                validated_params[param_name] = value
            else:
                if 'default' in param_info:
                    validated_params[param_name] = param_info['default']
        
        self._check_constraints(strategy_name, validated_params)
        
        return validated_params
    
    def _check_constraints(self, strategy_name: str, params: Dict[str, Any]) -> None:
        """제약 조건 검증"""
        strategy_info = STRATEGIES[strategy_name]
        
        for constraint in strategy_info.get('constraints', []):
            if '<' in constraint:
                left, right = constraint.split('<')
                left_param = left.strip()
                right_param = right.strip()
                
                if left_param in params and right_param in params:
                    if params[left_param] >= params[right_param]:
                        raise ValueError(
                            f"{strategy_name} 전략에서 {left_param}({params[left_param]})는 "
                            f"{right_param}({params[right_param]})보다 작아야 합니다"
                        )


strategy_service = StrategyService()
