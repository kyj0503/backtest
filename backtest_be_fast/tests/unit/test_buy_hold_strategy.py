"""
Buy & Hold Strategy Requirements-based Testing (Black-box Testing)

**Test Strategy**:
- **Spec-based**: Validate REQ-BH-xx from `requirements.md`
- **Logic**: Buy once at start, never sell.
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import BuyAndHoldStrategy

class TestBuyHoldRequirements:
    """
    [REQ-BH-01 ~ REQ-BH-02] 단순 보유 전략 검증
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

    def test_req_bh_01_buy_at_start(self):
        """
        [REQ-BH-01] 시작 시점 전액 매수
        """
        data = [100, 101, 102, 103, 104]
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BuyAndHoldStrategy, cash=10000, commission=0)
        stats = bt.run()
        
        trades = stats['_trades']
        assert len(trades) == 1, "정확히 1건의 거래만 있어야 함"
        assert trades.iloc[0]['EntryBar'] < 5, "초반에 진입해야 함"

    def test_req_bh_02_never_sell(self):
        """
        [REQ-BH-02] 종료 시까지 매도 없음 (ExitTime is NaN or End of Data)
        """
        # 등락이 심해도 팔지 않아야 함
        data = [100, 200, 50, 300, 20]
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BuyAndHoldStrategy, cash=10000, commission=0)
        stats = bt.run()
        
        trades = stats['_trades']
        # 백테스트 엔진은 마지막 날 강제 청산을 할 수도 있음.
        # 하지만 전략 로직상으로는 self.sell()을 호출하지 않아야 함.
        # backtesting.py는 마지막에 Open Position을 보여줌. ExitTime이 비어있어야 함 (혹은 마지막 봉)
        
        # 마지막 봉에서 강제 청산되는 경우는 backtesting.py의 report 메커니즘 차이임.
        # 우리가 검증할 건 중간에 로직에 의해 팔리지 않았는지.
        
        if len(trades) > 0:
            exit_bar = trades.iloc[0]['ExitBar']
            # 만약 청산되었다면 그것은 데이터 끝이어야 함 (len(data)-1)
            # 혹은 Open 상태여야 함
            is_open = pd.isna(trades.iloc[0]['ExitTime'])
            is_end = exit_bar == len(data) - 1
            
            assert is_open or is_end, "중간에 청산되면 안 됨"
