"""
백테스팅 전략 서비스
"""
from typing import Dict, Any, Type
from backtesting import Strategy
from ..strategies import (
    SMAStrategy,
    RSIStrategy,
    BollingerBandsStrategy,
    MACDStrategy,
    EMAStrategy,
    BuyAndHoldStrategy
)


class StrategyService:
    """전략 관리 서비스"""
    
    def __init__(self):
        self._strategies = {
            'sma_crossover': {
                'class': SMAStrategy,
                'name': 'Simple Moving Average Crossover',
                'description': '단순 이동평균 교차 전략',
                'parameters': {
                    'short_window': {
                        'type': 'int',
                        'default': 10,
                        'min': 5,
                        'max': 50,
                        'description': '단기 이동평균 기간'
                    },
                    'long_window': {
                        'type': 'int',
                        'default': 20,
                        'min': 10,
                        'max': 200,
                        'description': '장기 이동평균 기간'
                    }
                }
            },
            'rsi': {
                'class': RSIStrategy,
                'name': 'RSI',
                'description': 'RSI 과매수/과매도 기반 전략',
                'parameters': {
                    'rsi_period': {
                        'type': 'int',
                        'default': 14,
                        'min': 5,
                        'max': 30,
                        'description': 'RSI 계산 기간'
                    },
                    'rsi_overbought': {
                        'type': 'int',
                        'default': 70,
                        'min': 60,
                        'max': 90,
                        'description': 'RSI 과매수 기준'
                    },
                    'rsi_oversold': {
                        'type': 'int',
                        'default': 30,
                        'min': 10,
                        'max': 40,
                        'description': 'RSI 과매도 기준'
                    }
                }
            },
            'bollinger_bands': {
                'class': BollingerBandsStrategy,
                'name': 'Bollinger Bands Strategy',
                'description': '볼린저 밴드 기반 전략',
                'parameters': {
                    'period': {
                        'type': 'int',
                        'default': 20,
                        'min': 10,
                        'max': 50,
                        'description': '이동평균 기간'
                    },
                    'std_dev': {
                        'type': 'float',
                        'default': 2.0,
                        'min': 1.0,
                        'max': 3.0,
                        'description': '표준편차 배수'
                    }
                }
            },
            'macd': {
                'class': MACDStrategy,
                'name': 'MACD',
                'description': 'MACD 교차 기반 전략',
                'parameters': {
                    'fast_period': {
                        'type': 'int',
                        'default': 12,
                        'min': 5,
                        'max': 20,
                        'description': '빠른 EMA 기간'
                    },
                    'slow_period': {
                        'type': 'int',
                        'default': 26,
                        'min': 20,
                        'max': 50,
                        'description': '느린 EMA 기간'
                    },
                    'signal_period': {
                        'type': 'int',
                        'default': 9,
                        'min': 5,
                        'max': 15,
                        'description': '시그널 라인 기간'
                    }
                }
            },
            'ema_crossover': {
                'class': EMAStrategy,
                'name': 'EMA Crossover',
                'description': '지수 이동평균 교차 기반 전략',
                'parameters': {
                    'fast_window': {
                        'type': 'int',
                        'default': 12,
                        'min': 5,
                        'max': 50,
                        'description': '단기 EMA 기간'
                    },
                    'slow_window': {
                        'type': 'int',
                        'default': 26,
                        'min': 10,
                        'max': 200,
                        'description': '장기 EMA 기간'
                    }
                }
            },
            'buy_and_hold': {
                'class': BuyAndHoldStrategy,
                'name': 'Buy and Hold',
                'description': '매수 후 보유 전략',
                'parameters': {}
            }
        }
    
    def get_strategy_class(self, strategy_name: str) -> Type[Strategy]:
        """전략 클래스 반환"""
        if strategy_name not in self._strategies:
            raise ValueError(f"지원하지 않는 전략: {strategy_name}")
        return self._strategies[strategy_name]['class']
    
    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """전략 정보 반환"""
        if strategy_name not in self._strategies:
            raise ValueError(f"지원하지 않는 전략: {strategy_name}")
        
        strategy_data = self._strategies[strategy_name].copy()
        strategy_data.pop('class')  # 클래스는 제외
        return strategy_data
    
    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """모든 전략 정보 반환"""
        result = {}
        for name, data in self._strategies.items():
            result[name] = {
                'name': data['name'],
                'description': data['description'],
                'parameters': data['parameters']
            }
        return result
    
    def validate_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """전략 파라미터 유효성 검증 및 기본값 적용"""
        if strategy_name not in self._strategies:
            raise ValueError(f"지원하지 않는 전략: {strategy_name}")
        
        strategy_info = self._strategies[strategy_name]
        validated_params = {}
        
        for param_name, param_info in strategy_info['parameters'].items():
            if param_name in params:
                value = params[param_name]
                param_type = param_info['type']
                
                # 타입 변환
                if param_type == 'int':
                    value = int(value)
                elif param_type == 'float':
                    value = float(value)
                
                # 범위 검증
                if 'min' in param_info and value < param_info['min']:
                    raise ValueError(f"{param_name}의 값 {value}는 최소값 {param_info['min']}보다 작습니다")
                if 'max' in param_info and value > param_info['max']:
                    raise ValueError(f"{param_name}의 값 {value}는 최대값 {param_info['max']}보다 큽니다")
                
                validated_params[param_name] = value
            else:
                # 기본값 사용
                if 'default' in param_info:
                    validated_params[param_name] = param_info['default']
        
        # 전략별 특수 검증 로직
        if strategy_name == 'sma_crossover':
            short_window = validated_params.get('short_window', 10)
            long_window = validated_params.get('long_window', 20)
            if short_window >= long_window:
                raise ValueError(f"SMA 전략에서 short_window({short_window})는 long_window({long_window})보다 작아야 합니다")

        elif strategy_name == 'rsi':
            rsi_overbought = validated_params.get('rsi_overbought', 70)
            rsi_oversold = validated_params.get('rsi_oversold', 30)
            if rsi_oversold >= rsi_overbought:
                raise ValueError(f"RSI 전략에서 rsi_oversold({rsi_oversold})는 rsi_overbought({rsi_overbought})보다 작아야 합니다")

        elif strategy_name == 'ema_crossover':
            fast_window = validated_params.get('fast_window', 12)
            slow_window = validated_params.get('slow_window', 26)
            if fast_window >= slow_window:
                raise ValueError(f"EMA 전략에서 fast_window({fast_window})는 slow_window({slow_window})보다 작아야 합니다")

        return validated_params


# 글로벌 인스턴스
strategy_service = StrategyService() 
