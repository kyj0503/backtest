"""
MACD 전략 (Moving Average Convergence Divergence Strategy)
"""
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover


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
            
            if crossover(self.macd_line, self.signal_line) and not self.position:
                self.buy()
            elif crossover(self.signal_line, self.macd_line) and self.position:
                self.position.close()
