"""
지수 이동평균(EMA) 교차 전략 (EMA Crossover Strategy)
"""
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover


class EMAStrategy(Strategy):
    """EMA 교차 전략"""

    fast_window = 12
    slow_window = 26

    def init(self):
        close = self.data.Close
        self.ema_fast = self.I(self._ema, close, self.fast_window)
        self.ema_slow = self.I(self._ema, close, self.slow_window)

    def next(self):
        if crossover(self.ema_fast, self.ema_slow):
            self.buy()
        elif crossover(self.ema_slow, self.ema_fast):
            self.sell()

    @staticmethod
    def _ema(values, period: int):
        series = pd.Series(values)
        return series.ewm(span=period, adjust=False).mean()
