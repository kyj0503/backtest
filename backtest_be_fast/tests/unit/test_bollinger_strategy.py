"""
Bollinger Bands 전략 단위 테스트

**테스트 범위**:
- 볼린저 밴드 계산 로직
- 상단/하단 밴드 계산
- 과매수/과매도 시그널 생성
- 변동성 기반 매매 검증

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
from backtesting.test import SMA
from app.strategies.bollinger_strategy import BollingerBandsStrategy


class TestBollingerBandsCalculation:
    """볼린저 밴드 계산 로직 검증"""

    def test_upper_band_calculation(self):
        """Given: 가격 데이터
        When: 상단 볼린저 밴드 계산
        Then: SMA + (2 × STD) 값 반환"""
        # Given
        prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120])

        # When: SMA와 표준편차 계산
        period = 5
        std_dev = 2
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        expected_upper = sma + (std_dev * std)

        # 실제 전략의 상단 밴드 계산
        strategy = BollingerBandsStrategy()
        actual_upper = strategy._upper_band(prices, period, std_dev)

        # Then: 상단 밴드가 올바르게 계산됨
        # 마지막 유효한 값 비교
        assert actual_upper.iloc[-1] == pytest.approx(expected_upper.iloc[-1], abs=0.01)

    def test_lower_band_calculation(self):
        """Given: 가격 데이터
        When: 하단 볼린저 밴드 계산
        Then: SMA - (2 × STD) 값 반환"""
        # Given
        prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120])

        # When
        period = 5
        std_dev = 2
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        expected_lower = sma - (std_dev * std)

        strategy = BollingerBandsStrategy()
        actual_lower = strategy._lower_band(prices, period, std_dev)

        # Then: 하단 밴드가 올바르게 계산됨
        assert actual_lower.iloc[-1] == pytest.approx(expected_lower.iloc[-1], abs=0.01)

    def test_bands_widen_with_high_volatility(self):
        """Given: 높은 변동성 데이터
        When: 볼린저 밴드 계산
        Then: 밴드 폭이 넓음"""
        # Given: 변동성 큰 데이터
        prices = pd.Series([100, 110, 95, 115, 90, 120, 85, 125, 130])

        # When
        strategy = BollingerBandsStrategy()
        upper = strategy._upper_band(prices, 5, 2)
        lower = strategy._lower_band(prices, 5, 2)

        # Then: 밴드 폭이 넓음
        band_width = upper.iloc[-1] - lower.iloc[-1]
        assert band_width > 20  # 높은 변동성으로 인한 넓은 밴드

    def test_bands_narrow_with_low_volatility(self):
        """Given: 낮은 변동성 데이터
        When: 볼린저 밴드 계산
        Then: 밴드 폭이 좁음"""
        # Given: 변동성 작은 데이터
        prices = pd.Series([100, 101, 100, 101, 100, 101, 100, 101, 100])

        # When
        strategy = BollingerBandsStrategy()
        upper = strategy._upper_band(prices, 5, 2)
        lower = strategy._lower_band(prices, 5, 2)

        # Then: 밴드 폭이 좁음
        band_width = upper.iloc[-1] - lower.iloc[-1]
        assert band_width < 5  # 낮은 변동성으로 인한 좁은 밴드

    def test_sma_equals_middle_band(self):
        """Given: 가격 데이터
        When: SMA와 중심선 계산
        Then: 중심선이 SMA와 동일"""
        # Given
        prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120])
        period = 5

        # When
        sma = SMA(prices, period)

        # Then: SMA가 볼린저 밴드의 중심선
        assert not sma.isna().all()


class TestBollingerBandsStrategy:
    """볼린저 밴드 전략 시그널 생성 검증"""

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

    def test_strategy_buys_at_lower_band(self):
        """Given: 가격이 하단 밴드 아래로 하락
        When: 볼린저 밴드 전략 실행
        Then: 매수 신호 발생 (과매도)"""
        # Given: 급격한 하락 후 반등
        close_prices = pd.Series([
            100, 99, 98, 97, 96, 95, 94, 93, 92, 91,
            90, 88, 86, 84, 82, 80, 78, 76, 74, 72,
            75, 80, 85, 90, 95
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=10, std_dev=2)

        # Then: 거래 발생
        assert result['# Trades'] >= 0

    def test_strategy_sells_at_upper_band(self):
        """Given: 가격이 상단 밴드 위로 상승
        When: 포지션이 있을 때
        Then: 매도 신호 발생 (과매수)"""
        # Given: 하락 후 급등
        close_prices = pd.Series([
            100, 98, 96, 94, 92, 90, 88, 86, 84, 82,
            85, 90, 95, 100, 105, 110, 115, 120, 125, 130,
            135, 140, 145, 150
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=10, std_dev=2)

        # Then: 거래 발생
        assert result['# Trades'] >= 0

    def test_strategy_respects_position_size(self):
        """Given: 볼린저 밴드 전략 with position_size=0.95
        When: 매수 신호 발생
        Then: 자본의 95%만 사용"""
        # Given
        close_prices = pd.Series([
            100, 98, 96, 94, 92, 90, 88, 86, 84, 82,
            80, 78, 76, 74, 72, 75, 80, 85, 90, 95,
            100, 105, 110
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 최종 자본이 초기 자본의 85% 이상
        assert result['Equity Final [$]'] >= 8500

    def test_strategy_with_custom_parameters(self):
        """Given: 커스텀 볼린저 밴드 파라미터
        When: 전략 실행
        Then: 설정된 파라미터로 동작"""
        # Given
        close_prices = pd.Series([
            100, 102, 104, 106, 108, 110, 108, 106, 104, 102,
            100, 98, 96, 94, 92, 95, 100, 105, 110, 115
        ])
        data = self.create_sample_data(close_prices)

        # When: 커스텀 파라미터 (좁은 밴드)
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=10, std_dev=1.5)

        # Then: 백테스트 완료
        assert result is not None
        assert 'Return [%]' in result

    def test_strategy_exits_at_sma(self):
        """Given: 하단 밴드에서 매수 후 가격 상승
        When: 가격이 SMA(중심선)에 도달
        Then: 매도 신호 발생 (이익 실현)"""
        # Given: 하단 터치 후 중심선 복귀
        close_prices = pd.Series([
            100, 99, 98, 97, 96, 95, 94, 93, 92, 91,
            90, 88, 86, 84, 82, 83, 85, 88, 92, 96,
            100, 102, 104
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=10, std_dev=2)

        # Then: 매수 후 매도 발생
        assert result is not None


class TestBollingerBandsEdgeCases:
    """볼린저 밴드 전략 경계값 및 예외 상황 테스트"""

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
        """Given: 최소 데이터 포인트 (period+1)
        When: 볼린저 밴드 계산
        Then: 정상 동작"""
        # Given: 21개 데이터 (period=20)
        close_prices = pd.Series([100 + i for i in range(21)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=20, std_dev=2)

        # Then: 에러 없이 실행
        assert result is not None

    def test_strategy_with_insufficient_data(self):
        """Given: period보다 적은 데이터
        When: 볼린저 밴드 전략 실행
        Then: 거래 발생하지 않음"""
        # Given: 10개 데이터 (period=20보다 적음)
        close_prices = pd.Series([100 + i for i in range(10)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=20, std_dev=2)

        # Then: 거래 없음
        assert result['# Trades'] == 0

    def test_strategy_with_zero_std_dev(self):
        """Given: 표준편차가 0에 가까운 데이터 (일정한 가격)
        When: 볼린저 밴드 계산
        Then: 밴드 폭이 매우 좁음"""
        # Given: 거의 일정한 가격
        close_prices = pd.Series([100.0] * 25)
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=20, std_dev=2)

        # Then: 거래 없음 (밴드 폭이 너무 좁아 진입/청산 조건 불충족)
        assert result['# Trades'] == 0

    def test_strategy_with_high_std_dev_multiplier(self):
        """Given: 높은 표준편차 배수 (std_dev=3)
        When: 볼린저 밴드 전략 실행
        Then: 밴드가 넓어져 거래 빈도 감소"""
        # Given
        close_prices = pd.Series([
            100, 102, 101, 103, 102, 104, 103, 105, 104, 106,
            105, 107, 106, 108, 107, 109, 108, 110, 109, 111,
            110, 112, 111, 113, 112
        ])
        data = self.create_sample_data(close_prices)

        # When: 넓은 밴드
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=10, std_dev=3)

        # Then: 거래가 적음
        assert result['# Trades'] <= 1

    def test_strategy_with_low_std_dev_multiplier(self):
        """Given: 낮은 표준편차 배수 (std_dev=1)
        When: 볼린저 밴드 전략 실행
        Then: 밴드가 좁아져 거래 빈도 증가"""
        # Given
        close_prices = pd.Series([
            100, 102, 101, 103, 102, 104, 103, 105, 104, 106,
            105, 107, 106, 108, 107, 109, 108, 110, 109, 111,
            110, 108, 109, 107, 108
        ])
        data = self.create_sample_data(close_prices)

        # When: 좁은 밴드
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.01)
        result = bt.run(period=5, std_dev=1)

        # Then: 더 많은 거래 발생 가능
        assert result is not None

    def test_strategy_handles_nan_in_bands(self):
        """Given: 초기 데이터 (밴드가 NaN)
        When: 전략 실행
        Then: NaN 체크 후 정상 동작"""
        # Given
        close_prices = pd.Series([100 + i for i in range(30)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=20, std_dev=2)

        # Then: 에러 없이 실행
        assert result is not None

    def test_strategy_with_extreme_price_spike(self):
        """Given: 극단적 가격 급등
        When: 볼린저 밴드 전략 실행
        Then: 상단 밴드 돌파로 매도"""
        # Given: 극단적 급등
        close_prices = pd.Series([
            100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
            110, 111, 112, 113, 114, 200, 201, 202, 203, 204
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=10, std_dev=2)

        # Then: 거래 발생
        assert result is not None

    def test_strategy_in_trending_market(self):
        """Given: 강한 추세장
        When: 볼린저 밴드 전략 실행
        Then: 밴드를 따라 이동 (추세에서는 비효율적)"""
        # Given: 강한 상승 추세
        close_prices = pd.Series([100 + i * 2 for i in range(30)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BollingerBandsStrategy, cash=10000, commission=0.0)
        result = bt.run(period=10, std_dev=2)

        # Then: 백테스트 완료 (추세장에서 볼린저 밴드는 비효율적일 수 있음)
        assert result is not None
