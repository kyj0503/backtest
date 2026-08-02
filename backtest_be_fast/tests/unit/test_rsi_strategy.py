"""
RSI Strategy Requirements-based Testing (Black-box Testing)
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import RsiStrategy

pytestmark = pytest.mark.unit


class TestRsiRequirements:

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
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'cash': 10000
        }

    # ============================================================================
    # REQ-RSI-04 (매수 진입): RSI < 30 (과매도)
    # ============================================================================
    @pytest.mark.parametrize("rsi_value_scenario, expected_trade", [
        ("OVERSOLD", True),   # Drop prices hard to trigger RSI < 30
        ("NEUTRAL", False),   # Stable prices
        ("OVERBOUGHT", False), # Rising prices
    ])
    def test_req_rsi_04_buy_signal_partition(self, standard_setup, rsi_value_scenario, expected_trade):
        """
        [REQ-RSI-04] 과매도 구간 진입 테스트
        """
        # Initialization
        p1 = [100] * 20
        
        if rsi_value_scenario == "OVERSOLD":
            # Sharp drop to crash RSI
            p2 = np.linspace(100, 50, 10).tolist() # 50% drop in 10 days
        elif rsi_value_scenario == "NEUTRAL":
            p2 = [100] * 10
        elif rsi_value_scenario == "OVERBOUGHT":
            p2 = np.linspace(100, 200, 10).tolist() # Sharp rise
            
        data = p1 + p2
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, RsiStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(rsi_period=14)
        
        if expected_trade:
            assert len(stats['_trades']) > 0, f"Scenario {rsi_value_scenario}: 매수했어야 함"
        else:
            assert len(stats['_trades']) == 0, f"Scenario {rsi_value_scenario}: 매수하지 말았어야 함"

    # ============================================================================
    # REQ-RSI-05 (매도 청산): RSI > 70 (과매수)
    # ============================================================================
    def test_req_rsi_05_sell_signal_overbought(self, standard_setup):
        """
        [REQ-RSI-05] 과매수 구간 진입 시 청산
        """
        # 1. Buy: Drop
        p1 = [100] * 20
        p2 = np.linspace(100, 60, 10).tolist() # Buy
        
        # 2. Sell: Rise sharply
        p3 = np.linspace(60, 150, 15).tolist() # Sell
        
        data = p1 + p2 + p3
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, RsiStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(rsi_period=14)
        
        trades = stats['_trades']
        assert len(trades) > 0
        assert pd.notna(trades.iloc[-1]['ExitTime']), "과매수 시 청산되어야 함"

    # ============================================================================
    # Edge Cases
    # ============================================================================
    def test_req_rsi_07_flat_data_no_error(self, standard_setup):
        """
        [REQ-RSI-07] 데이터 변화가 없을 때 (RSI 계산 불가/0) 에러 없음 확인
        """
        data = [100] * 50
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, RsiStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(rsi_period=14)
        
        # Should finish without error
        assert len(stats) > 0

    def test_rsi_calculation_boundary(self):
        """
        최소 데이터 길이(Period)보다 적은 경우
        """
        data = [100] * 10 # < 14
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, RsiStrategy, cash=10000, commission=0)
        stats = bt.run(rsi_period=14)
        assert len(stats['_trades']) == 0
