"""
전략 레지스트리 - 단순화된 전략 관리
"""
from typing import Dict, Any, Type, Optional
import logging

from app.strategies.sma_strategy import SMAStrategy
from app.strategies.rsi_strategy import RSIStrategy
from app.strategies.bollinger_strategy import BollingerBandsStrategy
from app.strategies.macd_strategy import MACDStrategy
from app.strategies.ema_strategy import EMAStrategy
from app.strategies.buy_hold_strategy import BuyAndHoldStrategy


logger = logging.getLogger(__name__)


# 전략 레지스트리 정의
STRATEGY_REGISTRY: Dict[str, Dict[str, Any]] = {
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


def get_strategy_class(strategy_name: str, **params) -> Type:
    """전략 클래스 반환 (파라미터 적용)"""
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"지원하지 않는 전략: {strategy_name}")
    
    strategy_info = STRATEGY_REGISTRY[strategy_name]
    strategy_class = strategy_info['class']
    
    if not params:
        return strategy_class
    
    # 파라미터 검증
    if not validate_strategy_params(strategy_name, params):
        raise ValueError(f"잘못된 파라미터: {params}")
    
    # 파라미터를 클래스 속성으로 설정한 서브클래스 생성
    class ConfiguredStrategy(strategy_class):
        pass
    
    for key, value in params.items():
        if hasattr(strategy_class, key):
            setattr(ConfiguredStrategy, key, value)
    
    return ConfiguredStrategy


def get_available_strategies() -> Dict[str, Dict[str, Any]]:
    """사용 가능한 전략 목록 반환"""
    result = {}
    for name, info in STRATEGY_REGISTRY.items():
        result[name] = {
            'name': info['name'],
            'description': info['description'],
            'parameters': info['parameters'],
            'constraints': info['constraints']
        }
    return result


def validate_strategy_params(strategy_name: str, params: Dict[str, Any]) -> bool:
    """전략 파라미터 검증"""
    if strategy_name not in STRATEGY_REGISTRY:
        return False
    
    strategy_info = STRATEGY_REGISTRY[strategy_name]
    param_definitions = strategy_info['parameters']
    
    # 파라미터 타입 및 범위 검증
    for param_name, param_value in params.items():
        if param_name not in param_definitions:
            continue
        
        param_def = param_definitions[param_name]
        param_type = param_def['type']
        
        # 타입 검증
        if not isinstance(param_value, param_type):
            logger.warning(f"파라미터 타입 불일치: {param_name}")
            return False
        
        # 범위 검증
        if 'min' in param_def and param_value < param_def['min']:
            logger.warning(f"파라미터 범위 초과: {param_name} < {param_def['min']}")
            return False
        
        if 'max' in param_def and param_value > param_def['max']:
            logger.warning(f"파라미터 범위 초과: {param_name} > {param_def['max']}")
            return False
    
    # 제약 조건 검증
    final_params = _apply_defaults(strategy_name, params)
    for constraint in strategy_info['constraints']:
        if not _check_constraint(constraint, final_params):
            logger.warning(f"제약 조건 위반: {constraint}")
            return False
    
    return True


def _apply_defaults(strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """기본값 적용"""
    strategy_info = STRATEGY_REGISTRY[strategy_name]
    param_definitions = strategy_info['parameters']
    
    final_params = {}
    for param_name, param_def in param_definitions.items():
        if param_name in params:
            final_params[param_name] = params[param_name]
        elif 'default' in param_def:
            final_params[param_name] = param_def['default']
    
    return final_params


def _check_constraint(constraint: str, params: Dict[str, Any]) -> bool:
    """제약 조건 검증"""
    try:
        if '<' in constraint:
            left, right = constraint.split('<')
            left_param = left.strip()
            right_param = right.strip()
            
            if left_param in params and right_param in params:
                return params[left_param] < params[right_param]
        
        return True
    except Exception:
        return False
