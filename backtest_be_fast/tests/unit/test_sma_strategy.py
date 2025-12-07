"""
SMA Strategy Requirements-based Testing (Black-box Testing)
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import SmaCrossStrategy

class TestSmaRequirements:

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
            'sma_short': 5,
            'sma_long': 10,
            'cash': 100000 
        }

    # ============================================================================
    # REQ-SMA-02 (매수 - 골든크로스): Short > Long (상향 돌파)
    # ============================================================================
    def test_req_sma_02_golden_cross_buy(self, standard_setup):
        """
        [REQ-SMA-02] 골든크로스 발생 시 매수
        """
        # Using Linear Trend to guarantee smooth crossover
        
        # 1. Downward trend (Short < Long)
        # Start high, go low.
        # 120 -> 80 over 40 days.
        p1 = np.linspace(120, 80, 40).tolist()
        
        # 2. Upward trend (Short > Long)
        # 80 -> 120 over 40 days.
        # Crossover should happen around the inflection point.
        p2 = np.linspace(80, 120, 40).tolist()
        
        data = p1 + p2
        df = self.create_fixture_data(data)

        # Run with short=5, long=10
        bt = Backtest(df, SmaCrossStrategy, cash=standard_setup['cash'], commission=0, finalize_trades=True)
        stats = bt.run(sma_short=5, sma_long=10)
        
        trades = stats['_trades']
        
        # Debugging
        # print("Trades:", trades)
        
        assert len(trades) > 0, "골든크로스에서 매수가 발생해야 함"
        # Entry should be Buy
        assert trades.iloc[0]['Size'] > 0


    # Boundary / No Cross
    # ============================================================================
    def test_sma_no_cross_no_trade(self, standard_setup):
        """
        [Boundary] 교차 없음 (지속 상승)
        """
        # Continuous Linear growth
        data = np.linspace(100, 200, 60).tolist()
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, SmaCrossStrategy, cash=standard_setup['cash'], commission=0, finalize_trades=True)
        stats = bt.run(sma_short=5, sma_long=10)
        
        trades = stats['_trades']
        
        # Should buy at start if conditions allow (wait, SmaCrossStrategy ONLY buys on Crossover)
        # If it's pure uptrend, Short is always > Long?
        # Initialization: SMA5 needs 5 days, SMA10 needs 10 days.
        # Day 10: SMA5 (avg of 6-10) vs SMA10 (avg of 1-10).
        # Linear uptrend: SMA5 is always > SMA10.
        # But crossover() requires Short was < Long previously.
        # Since it starts Short > Long, crossover never triggers.
        
        assert len(trades) == 0, "이미 정배열 상태에서는 골든크로스가 발생하지 않으므로 매수 없어야 함"
