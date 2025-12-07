"""
MACD Strategy Requirements-based Testing (Black-box Testing)

**Test Strategy**:
- **Spec-based**: Validate REQ-MACD-xx from `requirements.md`
- **Equivalence Partitioning**: MACD > Signal (Buy), MACD < Signal (Sell)
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import MacdStrategy

class TestMacdRequirements:
    """
    [REQ-MACD-01 ~ REQ-MACD-04] MACD 전략 요구사항 검증
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

    # ============================================================================
    # REQ-MACD-03 (매수): MACD 상향 돌파
    # ============================================================================
    def test_req_macd_03_buy_signal(self):
        """
        [REQ-MACD-03] MACD Line > Signal Line 교차 시 매수
        Given: 하락 추세 (MACD < Signal)
        When: 상승 반전 (MACD > Signal)
        Then: 매수 발생
        """
        # 하락 -> 상승 패턴
        # 100 -> 80 (20일), 80 -> 120 (20일)
        p1 = [100 - i for i in range(20)]
        p2 = [80 + i*2 for i in range(20)]
        
        data = p1 + p2
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, MacdStrategy, cash=10000, commission=0)
        stats = bt.run(fast_period=12, slow_period=26, signal_period=9)
        
        assert len(stats['_trades']) > 0, "MACD 골든크로스 매수"

    # ============================================================================
    # REQ-MACD-04 (매도): MACD 하향 돌파
    # ============================================================================
    def test_req_macd_04_sell_signal(self):
        """
        [REQ-MACD-04] MACD Line < Signal Line 교차 시 매도
        """
        # 상승 -> 하락 패턴
        p1 = [100 + i for i in range(30)]
        p2 = [130 - i*2 for i in range(20)]
        
        data = p1 + p2
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, MacdStrategy, cash=10000, commission=0)
        stats = bt.run()
        
        trades = stats['_trades']
        assert len(trades) > 0
        assert pd.notna(trades.iloc[-1]['ExitTime']), "MACD 데드크로스 청산"
