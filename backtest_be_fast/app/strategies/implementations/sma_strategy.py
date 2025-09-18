"""
단순 이동평균 교차 전략 (SMA Crossover Strategy)
"""
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
