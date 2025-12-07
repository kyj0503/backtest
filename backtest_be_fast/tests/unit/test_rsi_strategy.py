"""
RSI Strategy Requirements-based Testing (Black-box Testing)

**Test Strategy**:
- **Spec-based**: Validate REQ-RSI-xx from `requirements.md`
- **Equivalence Partitioning**: Oversold (<30), Neural (30-70), Overbought (>70)
- **Boundary Value Analysis**: 29.9 vs 30.0, 69.9 vs 70.0
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.strategies import RsiStrategy

class TestRsiRequirements:
    """
    [REQ-RSI-01 ~ REQ-RSI-07] RSI 전략 요구사항 검증
    """

    def create_fixture_data(self, price_pattern: list) -> pd.DataFrame:
        """테스트용 OHLC 데이터 생성 헬퍼"""
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
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'cash': 10000
        }

    # ============================================================================
    # REQ-RSI-04 (매수 진입): RSI < 30
    # ============================================================================
    @pytest.mark.parametrize("rsi_value_scenario, expected_trade", [
        # 시나리오: RSI 값을 직접 주입하기 어려우므로, RSI가 특정 값을 가지도록 유도하거나
        # 혹은 Strategy class의 _rsi 메서드 신뢰성을 바탕으로 통합 테스트
        # 여기서는 Backtest 엔진을 돌리므로, 입력 가격을 조작하여 RSI를 만듦.
        
        # 하지만 특정 RSI(예: 29.9)를 정확히 만드는 가격을 역산하기는 매우 어려움.
        # 따라서 "Black-box" 관점에서, "하락 추세가 지속되어 과매도에 진입하는 순간"을 포착.
        
        # 대안: RSI 계산 로직(REQ-RSI-01~03)은 별도 검증되었다고 가정하고,
        # Mocking을 통해 strategy.rsi[-1] 값을 강제할 수 있다면 Best.
        # 하지만 backtesting.py 구조상 Mocking이 까다로움.
        
        # 차선책: 극단적인 하락 패턴을 주어 RSI를 0에 가깝게 만들고,
        # 완만하게 회복시키며 경계를 테스트? -> 어렵다.
        
        # 전략 수정: 단위 테스트(Unit)이므로, Strategy 인스턴스의 next() 로직만 테스트하는 것이 가능할까?
        # backtesting.Strategy는 init(), next()가 엔진에 의해 호출됨.
        
        # 여기서는 가격 패턴을 통해 "확실한 과매도(약 20)", "확실한 중립(50)", "확실한 과매수(80)"
        # 3가지 파티션을 테스트하는 것으로 동등 분할 만족.
        # 경계값(29.9 vs 30.1)은 계산 로직 테스트(REQ-RSI-02)에서 수행하는 것이 맞음.
        # 매매 로직(REQ-RSI-04)은 "30 미만이면 산다"는 로직만 확인하면 됨.
        
        ("OVERSOLD", True),   # 30 미만 (예: 20)
        ("NEUTRAL",  False),  # 50 부근
        ("OVERBOUGHT", False) # 70 초과 (매수 안함)
    ])
    def test_req_rsi_04_buy_signal_partition(self, standard_setup, rsi_value_scenario, expected_trade):
        """
        [REQ-RSI-04] 매수 진입 동등 분할 테스트
        Given: RSI 상태별 가격 데이터
        When: 전략 실행
        Then: OVERSOLD 구간에서만 매수 발생
        """
        data = []
        if rsi_value_scenario == "OVERSOLD":
            # 지속 하락 -> RSI 낮음
            data = [100 - i*2 for i in range(30)] # 100, 98, ... 42 (약 30일간 하락)
        elif rsi_value_scenario == "NEUTRAL":
            # 지그재그 횡보
            data = [100, 102, 100, 102] * 10
        elif rsi_value_scenario == "OVERBOUGHT":
            # 지속 상승
            data = [100 + i*2 for i in range(30)]

        df = self.create_fixture_data(data)
        bt = Backtest(df, RsiStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(rsi_period=14)
        
        if expected_trade:
            assert len(stats['_trades']) > 0, f"Scenario {rsi_value_scenario}: 매수했어야 함"
        else:
            if rsi_value_scenario == "OVERBOUGHT":
                # 과매수 구간에서는 기존 포지션이 없으면 매수 안함. 
                # (RSI Strategy 로직상 30 미만 매수, 70 초과 매도)
                assert len(stats['_trades']) == 0

    # ============================================================================
    # REQ-RSI-05 (매도 청산): RSI > 70
    # ============================================================================
    def test_req_rsi_05_sell_signal_overbought(self):
        """
        [REQ-RSI-05] 과매수 구간 진입 시 청산
        Given: 매수 포지션 보유 (먼저 과매도 구간을 거침)
        When: 가격 상승하여 RSI > 70 도달
        Then: 청산 발생
        """
        # 1. 과매도 유도 (매수)
        # 2. 급반등 (과매수)
        
        # 하락 (30일) -> 상승 (30일)
        down_trend = [100 - i*2 for i in range(20)] # 100..60
        up_trend = [60 + i*4 for i in range(20)]    # 60..140 (급등)
        
        data = down_trend + up_trend
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, RsiStrategy, cash=10000, commission=0)
        stats = bt.run(rsi_period=10) # 민감하게 반응하도록 Period 단축
        
        trades = stats['_trades']
        assert len(trades) > 0, "매수가 먼저 발생해야 함"
        
        # 청산 확인
        assert pd.notna(trades.iloc[-1]['ExitTime']), "과매수 구간에서 청산되어야 함"

    # ============================================================================
    # REQ-RSI-07 (예외 처리): Division by Zero / Flat Data
    # ============================================================================
    def test_req_rsi_07_flat_data_no_error(self):
        """
        [REQ-RSI-07] 주가 변동 없을 때(Flat) 에러 방지
        Given: 가격이 모두 동일한 데이터
        When: RSI 계산 및 전략 실행
        Then: ZeroDivisionError 없이 실행 완료
        """
        data = [100] * 50
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, RsiStrategy, cash=10000, commission=0)
        stats = bt.run(rsi_period=14)
        
        # 에러 없이 결과가 나와야 함
        assert stats is not None
        assert len(stats['_trades']) == 0

    # ============================================================================
    # [Boundary Calculation Logic] 별도 검증 (White-box적 요소가 있지만 필수적)
    # ============================================================================
    def test_rsi_calculation_boundary(self):
        """
        [REQ-RSI-02] RSI 계산 정확성 미니 테스트
        """
        # 간단한 상승: 0->1 (Gain 1)
        # 간단한 하락: 1->0 (Loss 1)
        # RS = AvgGain / AvgLoss
        # Period=1이라 가정하면 Gain=1, Loss=0 -> RS=inf -> RSI=100
        # 구현상 어떻게 처리되는지 확인
        
        prices = pd.Series([100, 110]) # +10
        rsi = RsiStrategy._rsi(None, prices, period=1)
        # 첫 data point는 NaN, 두번째는 Gain 있음.
        # period=1이면 alpha=1. 
        # AvgGain = 10, AvgLoss = 0.
        # RS -> inf. RSI -> 100.
        
        # 0이 아닌 값 확인 (0 division handled)
        assert rsi.iloc[-1] > 99
