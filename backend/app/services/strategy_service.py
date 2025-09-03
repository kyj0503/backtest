"""
백테스팅 전략 서비스
"""
from typing import Dict, Any, Type
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.test import SMA


class SMAStrategy(Strategy):
    """단순 이동평균 교차 전략"""
    short_window = 10
    long_window = 20
    
    def init(self):
        close = self.data.Close
        self.sma_short = self.I(SMA, close, self.short_window)
        self.sma_long = self.I(SMA, close, self.long_window)
    
    def next(self):
        if crossover(self.sma_short, self.sma_long):
            self.buy()
        elif crossover(self.sma_long, self.sma_short):
            self.sell()


class RSIStrategy(Strategy):
    """RSI 전략 - 개선된 버전"""
    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30
    position_size = 0.95  # 95% 포지션 사용
    
    def init(self):
        close = self.data.Close
        self.rsi = self.I(self._rsi, close, self.rsi_period)
    
    def _rsi(self, close: pd.Series, period: int) -> pd.Series:
        """RSI 계산 - 안정성 개선"""
        close = pd.Series(close)
        delta = close.diff()
        
        # 상승분과 하락분 분리
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 지수 이동평균으로 평균 계산 (더 안정적)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        # 0으로 나누는 것 방지
        avg_loss = avg_loss.replace(0, np.finfo(float).eps)
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)  # NaN 값을 50으로 채움
    
    def next(self):
        if len(self.rsi) > self.rsi_period:  # 충분한 데이터가 있을 때만 실행
            current_rsi = self.rsi[-1]
            
            # 과매도 구간에서 매수
            if current_rsi < self.rsi_oversold and not self.position:
                self.buy(size=self.position_size)
            
            # 과매수 구간에서 매도
            elif current_rsi > self.rsi_overbought and self.position:
                self.sell(size=self.position.size)


class BollingerBandsStrategy(Strategy):
    """볼린저 밴드 전략"""
    period = 20
    std_dev = 2
    
    def init(self):
        close = self.data.Close
        self.sma = self.I(SMA, close, self.period)
        self.upper_band = self.I(self._upper_band, close, self.period, self.std_dev)
        self.lower_band = self.I(self._lower_band, close, self.period, self.std_dev)
    
    def _upper_band(self, close: pd.Series, period: int, std_dev: float) -> pd.Series:
        """상단 볼린저 밴드 계산"""
        close = pd.Series(close)
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        return sma + (std_dev * std)
    
    def _lower_band(self, close: pd.Series, period: int, std_dev: float) -> pd.Series:
        """하단 볼린저 밴드 계산"""
        close = pd.Series(close)
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        return sma - (std_dev * std)
    
    def next(self):
        if (len(self.upper_band) > 0 and len(self.lower_band) > 0 and 
            not np.isnan(self.upper_band[-1]) and not np.isnan(self.lower_band[-1])):
            
            current_price = self.data.Close[-1]
            
            if current_price < self.lower_band[-1] and not self.position:
                self.buy()
            elif current_price > self.upper_band[-1] and self.position:
                self.sell()


class MACDStrategy(Strategy):
    """MACD 전략"""
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    def init(self):
        close = self.data.Close
        self.macd_line = self.I(self._macd_line, close, self.fast_period, self.slow_period)
        self.signal_line = self.I(self._signal_line, close, self.fast_period, self.slow_period, self.signal_period)
    
    def _macd_line(self, close: pd.Series, fast: int, slow: int) -> pd.Series:
        """MACD 라인 계산"""
        close = pd.Series(close)
        exp1 = close.ewm(span=fast).mean()
        exp2 = close.ewm(span=slow).mean()
        return exp1 - exp2
    
    def _signal_line(self, close: pd.Series, fast: int, slow: int, signal: int) -> pd.Series:
        """시그널 라인 계산"""
        macd = self._macd_line(close, fast, slow)
        return macd.ewm(span=signal).mean()
    
    def next(self):
        if (len(self.macd_line) > 1 and len(self.signal_line) > 1 and
            not np.isnan(self.macd_line[-1]) and not np.isnan(self.signal_line[-1])):
            
            if crossover(self.macd_line, self.signal_line):
                self.buy()
            elif crossover(self.signal_line, self.macd_line):
                self.sell()


class BuyAndHoldStrategy(Strategy):
    """매수 후 보유 전략"""
    
    def init(self):
        self.bought = False
    
    def next(self):
        if not self.bought:
            self.buy()
            self.bought = True


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
            'rsi_strategy': {
                'class': RSIStrategy,
                'name': 'RSI Strategy',
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
            'macd_strategy': {
                'class': MACDStrategy,
                'name': 'MACD Strategy',
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
        
        return validated_params


# 글로벌 인스턴스
strategy_service = StrategyService() 