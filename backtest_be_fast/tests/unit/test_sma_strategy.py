"""
SMA Strategy Requirements-based Testing (Black-box Testing)

**Test Strategy**:
- **Spec-based**: Validate REQ-SMA-xx from `requirements.md`
- **Equivalence Partitioning**: Golden Cross (Buy), Dead Cross (Sell), No Cross (Hold)
- **Boundary Value Analysis**: Signal line crossing
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import SmaCrossStrategy

class TestSmaRequirements:
    """
    [REQ-SMA-01 ~ REQ-SMA-03] SMA 크로스 전략 요구사항 검증
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
            'sma_short': 5,  # 테스트 속도를 위해 짧게 설정 (기본 10)
            'sma_long': 10,  # (기본 20)
            'cash': 10000
        }

    # ============================================================================
    # REQ-SMA-02 (매수 - 골든크로스): Short > Long (상향 돌파)
    # ============================================================================
    def test_req_sma_02_golden_cross_buy(self, standard_setup):
        """
        [REQ-SMA-02] 골든크로스 발생 시 매수
        Given: Short < Long 상태 유지하다가
        When: 가격 급등으로 Short > Long 전환
        Then: 매수 신호 발생
        """
        # 1. 초기: 100 유지 (Short=100, Long=100) -> 교차 없음
        # 2. 하락: 90 유지 (Short < Long) -> 준비
        # 3. 급등: 120 (Short > Long) -> 교차
        
        # 20일간 100
        p1 = [100] * 20
        # 10일간 90 (Short=90, Long=95->90) -> 확실히 Short < Long
        p2 = [90] * 10
        # 급등 (120) -> Short 상승
        p3 = [120] * 10
        
        data = p1 + p2 + p3
        df = self.create_fixture_data(data)

        # 테스트용 파라미터로 실행
        bt = Backtest(df, SmaCrossStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(sma_short=5, sma_long=10)
        
        assert len(stats['_trades']) > 0, "골든크로스에서 매수가 발생해야 함"
        # 매수 진입 확인
        assert stats['_trades'].iloc[0]['EntryBar'] > 20

    # ============================================================================
    # REQ-SMA-03 (매도 - 데드크로스): Short < Long (하향 돌파)
    # ============================================================================
    def test_req_sma_03_dead_cross_sell(self, standard_setup):
        """
        [REQ-SMA-03] 데드크로스 발생 시 매도
        Given: 매수 상태 (골든크로스 이후)
        When: 가격 급락으로 Short < Long 전환
        Then: 매도 신호 발생
        """
        # 1. 골든크로스 유도 (매수)
        # 100 -> 120 (상승)
        p1 = [100] * 20
        p2 = [120] * 10 # Golden Cross
        
        # 2. 데드크로스 유도 (매도)
        # 120 -> 80 (하락)
        p3 = [80] * 10 # Dead Cross
        
        data = p1 + p2 + p3
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, SmaCrossStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(sma_short=5, sma_long=10)
        
        trades = stats['_trades']
        assert len(trades) > 0, "진입 거래가 있어야 함"
        
        # 청산 확인 (ExitTime 존재)
        assert pd.notna(trades.iloc[-1]['ExitTime']), "데드크로스에서 청산되어야 함"

    # ============================================================================
    # Boundary / No Cross
    # ============================================================================
    def test_sma_no_cross_no_trade(self, standard_setup):
        """
        [Boundary] 교차 없음 (지속 상승)
        Given: Short > Long 상태 지속
        When: 교차 발생 안함
        Then: 추가 거래 없음 (Buy & Hold와 유사) or 진입 시점 1회 외엔 없음
        """
        # 계속 1씩 증가 (100, 101, 102...)
        # SMA Short > SMA Long 항상 유지 (Short가 더 빨리 오르므로)
        data = [100 + i for i in range(50)]
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, SmaCrossStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(sma_short=5, sma_long=10)
        
        # 시작할 때 100->105 구간에서 Short > Long 되면서 1번 살 수는 있음.
        # 혹은 초기 데이터 부족 구간 지나고 바로 살 수도.
        # 핵심: 샀다 팔았다 반복하지 않아야 함.
        
        trades = stats['_trades']
        if len(trades) > 0:
            # 매수 후 매도(청산)이 없어야 함 (계속 오르니까 데드크로스 없음)
            assert pd.isna(trades.iloc[0]['ExitTime']), "상승장에서는 청산되지 않아야 함"
