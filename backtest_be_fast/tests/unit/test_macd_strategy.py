"""
MACD Strategy Requirements-based Testing (Black-box Testing)
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import MacdStrategy

class TestMacdRequirements:

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

    def test_req_macd_03_buy_signal(self):
        """
        [REQ-MACD-03] MACD Line > Signal Line 교차 시 매수
        """
        # MACD(12, 26). Signal(9).
        # Need long periods.
        
        # 1. Strong Down trend
        p1 = np.linspace(200, 100, 60).tolist()
        
        # 2. Strong Up trend
        p2 = np.linspace(100, 200, 60).tolist()
        
        data = p1 + p2
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, MacdStrategy, cash=100000, commission=0)
        stats = bt.run(fast_period=12, slow_period=26, signal_period=9)
        
        assert len(stats['_trades']) > 0, "MACD 골든크로스 매수"

    def test_req_macd_04_sell_signal(self):
        """
        [REQ-MACD-04] MACD Line < Signal Line 교차 시 매도
        """
        # 0. Setup Phase (Down)
        p0 = np.linspace(200, 100, 40).tolist()

        # 1. Up trend (Buy)
        p1 = np.linspace(100, 200, 60).tolist()
        # 2. Down trend (Sell)
        p2 = np.linspace(200, 100, 60).tolist()
        
        data = p0 + p1 + p2
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, MacdStrategy, cash=100000, commission=0)
        stats = bt.run()
        
        trades = stats['_trades']
        assert len(trades) > 0
        assert pd.notna(trades.iloc[-1]['ExitTime']), "MACD 데드크로스 청산"
