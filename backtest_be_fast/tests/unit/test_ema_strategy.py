"""
EMA Strategy Requirements-based Testing (Black-box Testing)

**Test Strategy**:
- **Spec-based**: Validate REQ-EMA-xx from `requirements.md`
- **Equivalence Partitioning**: Golden Cross (Buy), Dead Cross (Sell)
- **Consistency**: Similar logic to SMA but verifies EMA specific behavior implicit in calculation.
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import EmaStrategy

class TestEmaRequirements:
    """
    [REQ-EMA-01 ~ REQ-EMA-03] EMA 크로스 전략 요구사항 검증
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
            'fast_window': 5,
            'slow_window': 10,
            'cash': 10000
        }

    # ============================================================================
    # REQ-EMA-02 (매수 - 골든크로스)
    # ============================================================================
    def test_req_ema_02_golden_cross_buy(self, standard_setup):
        """
        [REQ-EMA-02] EMA 골든크로스 발생 시 매수
        """
        # 하락하다가 상승 -> Short EMA가 Long EMA 돌파
        p1 = [100 - i for i in range(20)] # 하락 (100 -> 80)
        p2 = [80 + i*2 for i in range(20)] # 급반등 (80 -> 120)
        
        data = p1 + p2
        df = self.create_fixture_data(data)

        bt = Backtest(df, EmaStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(fast_window=5, slow_window=10)
        
        assert len(stats['_trades']) > 0, "골든크로스 매수 발생"

    # ============================================================================
    # REQ-EMA-03 (매도 - 데드크로스)
    # ============================================================================
    def test_req_ema_03_dead_cross_sell(self, standard_setup):
        """
        [REQ-EMA-03] EMA 데드크로스 발생 시 매도
        """
        # 상승하다가 하락
        p1 = [100 + i for i in range(20)] # 상승
        p2 = [120 - i*2 for i in range(20)] # 급락
        
        data = p1 + p2
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, EmaStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(fast_window=5, slow_window=10)
        
        trades = stats['_trades']
        assert len(trades) > 0
        assert pd.notna(trades.iloc[-1]['ExitTime']), "데드크로스 청산 발생"
