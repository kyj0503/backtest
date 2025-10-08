"""
매수 후 보유 전략 (Buy and Hold Strategy)
"""
from backtesting import Strategy


class BuyAndHoldStrategy(Strategy):
    """매수 후 보유 전략"""
    
    def init(self):
        self.bought = False
    
    def next(self):
        if not self.bought:
            self.buy()
            self.bought = True
