"""
Buy & Hold Strategy Requirements-based Testing (Black-box Testing)
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import BuyAndHoldStrategy

class TestBuyHoldRequirements:

    def create_fixture_data(self, price_pattern: list) -> pd.DataFrame:
        dates = pd.date_range(start='2024-01-01', periods=len(price_pattern), freq='D')
        prices = np.array(price_pattern, dtype=float)
        return pd.DataFrame({
            'Open': prices,
            'High': prices * 1.001,
            'Low': prices * 0.999,
            'Close': prices,
            'Volume': [1000] * len(prices)
        }, index=dates)

    def test_req_bh_01_buy_at_start(self):
        """
        [REQ-BH-01] 시작 시점 전액 매수
        """
        data = [100, 101, 102, 103, 104, 105, 106, 107]
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BuyAndHoldStrategy, cash=100000, commission=0)
        stats = bt.run()
        
        trades = stats['_trades']
        assert len(trades) >= 1, "최소 1건의 거래가 있어야 함"
        # Backtesting engine might execute trade on bar 2 or 3 depending on Open/Close logic
        assert trades.iloc[0]['EntryBar'] < 5, "초반에 진입해야 함"

    def test_req_bh_02_never_sell(self):
        """
        [REQ-BH-02] 종료 시까지 매도 없음 (ExitTime is NaN or End of Data)
        """
        # Volatile data
        data = [100, 200, 50, 300, 20, 100, 150, 80]
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BuyAndHoldStrategy, cash=100000, commission=0)
        stats = bt.run()
        
        trades = stats['_trades']
        
        if len(trades) > 0:
            last_trade = trades.iloc[-1]
            exit_bar = last_trade['ExitBar']
            
            # Check if it was forced closed at the end of data
            is_end_of_data = (exit_bar == len(data) - 1)
            is_not_closed = pd.isna(last_trade['ExitTime'])
            
            assert is_not_closed or is_end_of_data, "중간에 의도치 않게 청산되면 안 됨"
