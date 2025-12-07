"""
Bollinger Bands 전략 요구사항 기반 테스트 (Black-box Testing)
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import BollingerBandsStrategy

class TestBollingerBandsRequirements:
    """
    [REQ-BB-01 ~ REQ-BB-09] 볼린저 밴드 전략 요구사항 검증
    """

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
            'period': 20,
            'std_dev': 2,
            'cash': 100000
        }

    # ============================================================================
    # REQ-BB-05 (매수 진입): 주가 < 하단 밴드
    # ============================================================================
    @pytest.mark.parametrize("price_offset, expected_trade", [
        (-5.0, True),   # 하단 밴드보다 확실히 낮음
        (5.0, False),   # 하단 밴드보다 확실히 높음
    ])
    def test_req_bb_05_buy_signal_boundary(self, standard_setup, price_offset, expected_trade):
        """
        [REQ-BB-05] 하단 밴드 하향 돌파 테스트
        """
        # 1. Stable Phase: Constant 100 for 30 days.
        # Band = 100 (Std Dev = 0 theoretically, but practically small noise might be needed if lib handles 0 badly)
        # Using slight oscillation to ensure Std Dev > 0
        p1 = [100, 101] * 20 # 40 days, mean ~100.5, std ~0.5.
        # Lower band approx 100.5 - 2*0.5 = 99.5
        
        # 2. Test Price
        # If offset -5 -> 95. Should be well below 99.5. Buy.
        # If offset +5 -> 105. Should be above. No Buy.
        
        last_price = 100 + price_offset
        
        # Add extra bars after signal for order execution
        extra_data = [last_price] * 5
        
        data = p1 + [last_price] + extra_data
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BollingerBandsStrategy, cash=standard_setup['cash'], commission=0, finalize_trades=True)
        stats = bt.run(period=20, std_dev=2)
        
        if expected_trade:
             assert len(stats['_trades']) > 0, f"매수했어야 함 (Price={last_price})"
        else:
             assert len(stats['_trades']) == 0, f"매수하지 말았어야 함 (Price={last_price})"

    # ============================================================================
    # REQ-BB-06 (매도 청산): 주가 > 상단 밴드
    # ============================================================================
    def test_req_bb_06_sell_signal_breakout(self, standard_setup):
        """
        [REQ-BB-06] 상단 밴드 돌파 시 청산
        """
        # 1. Buy Phase: Stable then Drop
        p1 = [100, 101] * 15 # Stable
        p2 = [90] * 5       # Drop below band -> Buy
        
        # 2. Recovery & Breakout
        p3 = [100, 101] * 10 # Recover
        p4 = [120] * 5       # Breakout above upper band -> Sell
        
        data = p1 + p2 + p3 + p4
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BollingerBandsStrategy, cash=standard_setup['cash'], commission=0, finalize_trades=True)
        stats = bt.run(period=20, std_dev=2)
        
        trades = stats['_trades']
        assert len(trades) > 0, "매수 진입 실패"
        assert pd.notna(trades.iloc[-1]['ExitTime']), "상단 돌파 시 청산되어야 함"

    # ============================================================================
    # REQ-BB-07 (중심선 청산)
    # ============================================================================
    def test_req_bb_07_exit_at_sma(self):
        """
        [REQ-BB-07] 중심선(SMA) 복귀 시 청산
        """
        # 1. Buy Phase
        p1 = [100, 101] * 15
        p2 = [90] * 3 # Buy
        
        # 2. Return to Mean (Mean is approx 100)
        p3 = [100] * 5 # Hits Mean -> Sell
        
        data = p1 + p2 + p3
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BollingerBandsStrategy, cash=100000, commission=0, finalize_trades=True)
        stats = bt.run(period=20, std_dev=2)
        
        trades = stats['_trades']
        assert len(trades) > 0
        assert pd.notna(trades.iloc[-1]['ExitTime']), "중심선 복귀 시 청산되어야 함"
