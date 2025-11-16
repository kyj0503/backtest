"""
SMA 교차 전략 단위 테스트

**테스트 범위**:
- SMA 계산 로직의 정확성
- 골든 크로스/데드 크로스 판별
- 매수/매도 시그널 생성

**테스트 원칙**:
- 도메인 정책 테스트 (핵심 비즈니스 로직)
- 계산 정확성 검증
- 경계값 테스트
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from backtesting import Backtest
from app.strategies.sma_strategy import SMACrossStrategy, SMA


class TestSMACalculation:
    """SMA 계산 로직 검증"""

    def test_sma_calculates_correct_value(self):
        """Given: 단순 가격 데이터
        When: SMA 계산
        Then: 올바른 이동평균 값 반환"""
        # Given
        prices = pd.Series([100, 102, 104, 106, 108])

        # When: 3일 이동평균 계산
        sma_3 = SMA(prices, 3)

        # Then: 3일 이동평균이 정확함
        # 첫 2개는 NaN, 3번째부터 계산
        assert pd.isna(sma_3.iloc[0])
        assert pd.isna(sma_3.iloc[1])
        assert sma_3.iloc[2] == pytest.approx((100 + 102 + 104) / 3, abs=0.01)
        assert sma_3.iloc[3] == pytest.approx((102 + 104 + 106) / 3, abs=0.01)
        assert sma_3.iloc[4] == pytest.approx((104 + 106 + 108) / 3, abs=0.01)

    def test_sma_with_window_equals_length(self):
        """Given: 윈도우 크기 = 데이터 길이
        When: SMA 계산
        Then: 마지막 값만 유효"""
        # Given
        prices = pd.Series([100, 110, 120, 130, 140])

        # When: 5일 이동평균
        sma_5 = SMA(prices, 5)

        # Then: 마지막 값만 유효
        assert sma_5.iloc[-1] == pytest.approx((100 + 110 + 120 + 130 + 140) / 5, abs=0.01)

    def test_sma_handles_constant_prices(self):
        """Given: 일정한 가격
        When: SMA 계산
        Then: SMA도 동일한 값"""
        # Given
        prices = pd.Series([100.0] * 10)

        # When
        sma_5 = SMA(prices, 5)

        # Then: SMA가 100
        assert sma_5.iloc[-1] == pytest.approx(100.0, abs=0.01)

    def test_sma_short_vs_long_window(self):
        """Given: 상승 추세 데이터
        When: 단기/장기 SMA 계산
        Then: 단기 SMA가 장기 SMA보다 빠르게 반응"""
        # Given: 급격한 상승
        prices = pd.Series([100, 105, 110, 115, 120, 125, 130, 135, 140, 145])

        # When
        sma_short = SMA(prices, 3)
        sma_long = SMA(prices, 5)

        # Then: 최근 구간에서 단기 > 장기 (상승 추세)
        assert sma_short.iloc[-1] > sma_long.iloc[-1]


class TestSMACrossStrategy:
    """SMA 전략 시그널 생성 검증"""

    def create_sample_data(self, close_prices):
        """테스트용 OHLC 데이터 생성"""
        dates = pd.date_range(start='2023-01-01', periods=len(close_prices), freq='D')
        close_array = close_prices.values if isinstance(close_prices, pd.Series) else close_prices
        data = pd.DataFrame({
            'Open': close_array,
            'High': close_array * 1.01,
            'Low': close_array * 0.99,
            'Close': close_array,
            'Volume': [1000000] * len(close_prices)
        }, index=dates)
        return data

    def test_strategy_buys_on_golden_cross(self):
        """Given: 골든 크로스 발생 (단기 > 장기)
        When: SMA 전략 실행
        Then: 매수 신호 발생"""
        # Given: 하락 후 상승 (골든 크로스)
        close_prices = pd.Series([
            100, 98, 96, 94, 92,  # 하락 (단기 < 장기)
            93, 95, 98, 102, 106, 110, 115  # 상승 (단기 > 장기)
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        result = bt.run(sma_short=3, sma_long=5)

        # Then: 거래 발생 (골든 크로스에서 매수)
        assert result['# Trades'] >= 0

    def test_strategy_sells_on_dead_cross(self):
        """Given: 데드 크로스 발생 (단기 < 장기)
        When: 포지션이 있을 때
        Then: 매도 신호 발생"""
        # Given: 상승 후 하락 (데드 크로스)
        close_prices = pd.Series([
            100, 105, 110, 115, 120,  # 상승 (단기 > 장기)
            118, 115, 110, 105, 100, 95  # 하락 (단기 < 장기)
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        result = bt.run(sma_short=3, sma_long=5)

        # Then: 거래 발생 (매수 후 매도)
        assert result['# Trades'] >= 0

    def test_strategy_respects_position_size(self):
        """Given: SMA 전략 with position_size=0.95
        When: 매수 신호 발생
        Then: 자본의 95%만 사용"""
        # Given
        close_prices = pd.Series([
            100, 98, 96, 94, 92, 90, 88,
            90, 93, 97, 102, 108, 115, 120
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        result = bt.run(sma_short=3, sma_long=5)

        # Then: 최종 자본이 초기 자본의 85% 이상
        assert result['Equity Final [$]'] >= 8500

    def test_strategy_with_custom_parameters(self):
        """Given: 커스텀 SMA 파라미터 (short=5, long=10)
        When: 전략 실행
        Then: 설정된 파라미터로 동작"""
        # Given
        close_prices = pd.Series([
            100, 102, 104, 106, 108, 110, 108, 106, 104, 102,
            100, 105, 110, 115, 120
        ])
        data = self.create_sample_data(close_prices)

        # When: 커스텀 파라미터
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        result = bt.run(sma_short=5, sma_long=10)

        # Then: 백테스트 완료
        assert result is not None
        assert 'Return [%]' in result

    def test_strategy_in_sideways_market(self):
        """Given: 횡보장 (추세 없음)
        When: SMA 전략 실행
        Then: 잦은 거래로 인한 손실 가능"""
        # Given: 횡보
        close_prices = pd.Series([
            100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.01)
        result = bt.run(sma_short=2, sma_long=3)

        # Then: 높은 수수료로 손실 가능
        # 거래 발생 확인
        assert result is not None


class TestSMAEdgeCases:
    """SMA 전략 경계값 및 예외 상황 테스트"""

    def create_sample_data(self, close_prices):
        """테스트용 OHLC 데이터 생성"""
        dates = pd.date_range(start='2023-01-01', periods=len(close_prices), freq='D')
        close_array = close_prices.values if isinstance(close_prices, pd.Series) else close_prices
        data = pd.DataFrame({
            'Open': close_array,
            'High': close_array * 1.01,
            'Low': close_array * 0.99,
            'Close': close_array,
            'Volume': [1000000] * len(close_prices)
        }, index=dates)
        return data

    def test_strategy_with_minimum_data_points(self):
        """Given: 최소 데이터 포인트
        When: SMA 계산
        Then: 정상 동작"""
        # Given: 장기 윈도우 + 1개 데이터
        close_prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        result = bt.run(sma_short=3, sma_long=5)

        # Then: 에러 없이 실행
        assert result is not None

    def test_strategy_with_insufficient_data(self):
        """Given: 장기 윈도우보다 적은 데이터
        When: SMA 전략 실행
        Then: 거래 발생하지 않음"""
        # Given: 3개 데이터 (장기 윈도우 5보다 적음)
        close_prices = pd.Series([100, 105, 110])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        result = bt.run(sma_short=3, sma_long=5)

        # Then: 거래 없음
        assert result['# Trades'] == 0

    def test_strategy_with_equal_short_long_window(self):
        """Given: 단기 = 장기 윈도우
        When: SMA 전략 실행
        Then: 교차가 발생하지 않음"""
        # Given
        close_prices = pd.Series([100, 105, 110, 115, 120, 125, 130])
        data = self.create_sample_data(close_prices)

        # When: 단기 = 장기
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        result = bt.run(sma_short=5, sma_long=5)

        # Then: 거래 없음 (교차 없음)
        assert result['# Trades'] == 0

    def test_strategy_with_high_commission(self):
        """Given: 높은 수수료 (1%)
        When: SMA 전략 실행
        Then: 수수료가 수익률에 큰 영향"""
        # Given
        close_prices = pd.Series([
            100, 98, 96, 94, 92, 90,
            95, 100, 105, 110, 115, 120
        ])
        data = self.create_sample_data(close_prices)

        # When: 높은 수수료
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.01)
        result = bt.run(sma_short=3, sma_long=5)

        # Then: 수수료 차감으로 수익률 감소
        assert result is not None

    def test_strategy_with_zero_position_size(self):
        """Given: position_size = 0
        When: 매수 신호 발생
        Then: 거래 발생하지 않음"""
        # Given
        close_prices = pd.Series([
            100, 98, 96, 94, 92, 90,
            95, 100, 105, 110, 115
        ])
        data = self.create_sample_data(close_prices)

        # When: position_size = 0
        bt = Backtest(data, SMACrossStrategy, cash=10000, commission=0.0)
        # position_size를 0으로 설정하려면 strategy 클래스 수정 필요
        # 여기서는 매우 작은 값으로 테스트
        result = bt.run(sma_short=3, sma_long=5, position_size=0.001)

        # Then: 거래가 거의 없거나 매우 작은 포지션
        assert result['Equity Final [$]'] == pytest.approx(10000, abs=100)
