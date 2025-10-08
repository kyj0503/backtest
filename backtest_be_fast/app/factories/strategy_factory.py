"""
전략 인스턴스 생성 Factory
"""
from typing import Type, Dict, Any, Optional
import logging
from abc import ABC, abstractmethod
from uuid import uuid4

from app.strategies.sma_strategy import SMAStrategy
from app.strategies.rsi_strategy import RSIStrategy
from app.strategies.bollinger_strategy import BollingerBandsStrategy
from app.strategies.macd_strategy import MACDStrategy
from app.strategies.ema_strategy import EMAStrategy
from app.strategies.buy_hold_strategy import BuyAndHoldStrategy


class StrategyFactoryInterface(ABC):
    """전략 팩토리 인터페이스"""
    
    @abstractmethod
    def create_strategy(self, strategy_name: str, **params) -> Type:
        """전략 인스턴스 생성"""
        pass
    
    @abstractmethod
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 전략 목록"""
        pass
    
    @abstractmethod
    def validate_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """전략 파라미터 검증"""
        pass


class DefaultStrategyFactory(StrategyFactoryInterface):
    """기본 전략 팩토리 구현"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._strategies = {
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
                'constraints': [
                    'short_window < long_window'
                ]
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
                'constraints': [
                    'rsi_oversold < rsi_overbought'
                ]
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
                'constraints': [
                    'fast_period < slow_period'
                ]
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
                'constraints': [
                    'fast_window < slow_window'
                ]
            },
            'buy_and_hold': {
                'class': BuyAndHoldStrategy,
                'name': 'Buy and Hold Strategy',
                'description': '매수 후 보유 전략',
                'parameters': {},
                'constraints': []
            }
        }
    
    def create_strategy(self, strategy_name: str, **params) -> Type:
        """전략 인스턴스 생성"""
        try:
            if strategy_name not in self._strategies:
                raise ValueError(f"지원하지 않는 전략: {strategy_name}")
            
            strategy_info = self._strategies[strategy_name]
            strategy_class = strategy_info['class']

            # 파라미터 검증
            if not self.validate_strategy_params(strategy_name, params):
                raise ValueError(f"잘못된 파라미터: {params}")

            # 전달된 파라미터만 정규화하여 준비
            normalized_params = self._normalize_params(strategy_name, params)

            # 사용자 입력이 없다면 원본 클래스를 그대로 사용
            if not normalized_params:
                self.logger.info(f"전략 생성 완료(기본 파라미터 사용): {strategy_name}")
                return strategy_class

            # 사용자 파라미터만 오버라이드하는 임시 서브클래스 생성
            dynamic_attrs = {
                name: value
                for name, value in normalized_params.items()
                if hasattr(strategy_class, name)
            }

            configured_name = f"{strategy_class.__name__}Configured_{uuid4().hex[:8]}"
            configured_strategy = type(configured_name, (strategy_class,), dynamic_attrs)

            self.logger.info(
                "전략 생성 완료: %s, overrides=%s", strategy_name, dynamic_attrs
            )
            return configured_strategy
            
        except Exception as e:
            self.logger.error(f"전략 생성 실패: {strategy_name}, {str(e)}")
            raise
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 전략 목록"""
        # 클래스 정보 제외하고 반환
        result = {}
        for name, info in self._strategies.items():
            result[name] = {
                'name': info['name'],
                'description': info['description'],
                'parameters': info['parameters'],
                'constraints': info['constraints']
            }
        return result
    
    def validate_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """전략 파라미터 검증"""
        try:
            if strategy_name not in self._strategies:
                return False
            
            strategy_info = self._strategies[strategy_name]
            param_definitions = strategy_info['parameters']
            
            # 파라미터 타입 및 범위 검증
            for param_name, param_value in params.items():
                if param_name not in param_definitions:
                    continue  # 알 수 없는 파라미터는 무시
                
                param_def = param_definitions[param_name]
                param_type = param_def['type']
                
                # 타입 검증
                if not isinstance(param_value, param_type):
                    self.logger.warning(f"파라미터 타입 불일치: {param_name}, expected: {param_type}, got: {type(param_value)}")
                    return False
                
                # 범위 검증
                if 'min' in param_def and param_value < param_def['min']:
                    self.logger.warning(f"파라미터 범위 초과: {param_name} < {param_def['min']}")
                    return False
                
                if 'max' in param_def and param_value > param_def['max']:
                    self.logger.warning(f"파라미터 범위 초과: {param_name} > {param_def['max']}")
                    return False
            
            # 제약 조건 검증
            final_params = self._apply_default_params(strategy_name, params)
            for constraint in strategy_info['constraints']:
                if not self._validate_constraint(constraint, final_params):
                    self.logger.warning(f"제약 조건 위반: {constraint}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"파라미터 검증 실패: {str(e)}")
            return False
    
    def _apply_default_params(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """기본값 적용"""
        strategy_info = self._strategies[strategy_name]
        param_definitions = strategy_info['parameters']
        
        final_params = {}
        
        # 기본값 적용
        for param_name, param_def in param_definitions.items():
            if param_name in params:
                final_params[param_name] = params[param_name]
            elif 'default' in param_def:
                final_params[param_name] = param_def['default']
        
        return final_params

    def _normalize_params(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 입력 파라미터를 타입에 맞춰 정규화"""
        if not params:
            return {}

        strategy_info = self._strategies[strategy_name]
        param_definitions = strategy_info['parameters']

        normalized: Dict[str, Any] = {}
        for param_name, raw_value in params.items():
            if param_name not in param_definitions:
                continue

            param_type = param_definitions[param_name]['type']
            try:
                normalized[param_name] = param_type(raw_value)
            except (TypeError, ValueError):
                self.logger.warning(
                    "파라미터 타입 변환 실패: %s=%s (%s)",
                    param_name,
                    raw_value,
                    param_type,
                )
                raise

        return normalized
    
    def _validate_constraint(self, constraint: str, params: Dict[str, Any]) -> bool:
        """제약 조건 검증"""
        try:
            # 간단한 제약 조건 해석 (예: 'short_window < long_window')
            if '<' in constraint:
                left, right = constraint.split('<')
                left_param = left.strip()
                right_param = right.strip()
                
                if left_param in params and right_param in params:
                    return params[left_param] < params[right_param]
            
            # 추가 제약 조건 타입은 필요시 구현
            return True
            
        except Exception:
            return False
    
    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """특정 전략 정보 조회"""
        if strategy_name in self._strategies:
            info = self._strategies[strategy_name].copy()
            # 클래스 정보 제외
            del info['class']
            return info
        return None


# Factory 팩토리 (메타 팩토리)
class StrategyFactoryFactory:
    """전략 팩토리의 팩토리"""
    
    @staticmethod
    def create(factory_type: str = "default") -> StrategyFactoryInterface:
        """팩토리 인스턴스 생성"""
        if factory_type == "default":
            return DefaultStrategyFactory()
        else:
            raise ValueError(f"지원하지 않는 팩토리 타입: {factory_type}")


# 전역 인스턴스
StrategyFactory = StrategyFactoryFactory.create("default")
strategy_factory = StrategyFactory
