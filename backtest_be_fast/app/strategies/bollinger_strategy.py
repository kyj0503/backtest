"""
볼린저 밴드 전략 (Bollinger Bands Strategy)
"""
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.test import SMA


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
