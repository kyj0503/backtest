"""
EMA Strategy Requirements-based Testing (Black-box Testing)
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import EmaStrategy

class TestEmaRequirements:

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

    @pytest.fixture
    def standard_setup(self):
        return {
            'fast_window': 5,
            'slow_window': 10,
            'cash': 100000
        }

    def test_req_ema_02_golden_cross_buy(self, standard_setup):
        """
        [REQ-EMA-02] EMA 골든크로스 발생 시 매수
        """
        # 1. Down trend (Fast < Slow)
        p1 = np.linspace(120, 80, 40).tolist()
        
        # 2. Up trend (Fast > Slow cross)
        p2 = np.linspace(80, 120, 40).tolist()
        
        data = p1 + p2
        df = self.create_fixture_data(data)

        bt = Backtest(df, EmaStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(fast_window=5, slow_window=10)
        
        trades = stats['_trades']
        assert len(trades) > 0, "골든크로스 매수 발생"

    def test_req_ema_03_dead_cross_sell(self, standard_setup):
        """
        [REQ-EMA-03] EMA 데드크로스 발생 시 매도
        """
        # 0. Setup Phase (Down trend) to ensure indicators start Low
        p0 = np.linspace(120, 80, 20).tolist()

        # 1. Up trend (Golden Cross -> Buy)
        p1 = np.linspace(80, 120, 40).tolist()
        # 2. Down trend (Dead Cross -> Sell)
        p2 = np.linspace(120, 80, 40).tolist()
        
        data = p0 + p1 + p2
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, EmaStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(fast_window=5, slow_window=10)
        
        trades = stats['_trades']
        assert len(trades) > 0
        assert pd.notna(trades.iloc[-1]['ExitTime']), "데드크로스 청산 발생"
