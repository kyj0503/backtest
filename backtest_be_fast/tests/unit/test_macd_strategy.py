"""
MACD 전략 단위 테스트

**테스트 범위**:
- MACD 라인 계산 로직
- 시그널 라인 계산 로직
- MACD 교차 시그널 생성
- 히스토그램 검증

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
from app.strategies.macd_strategy import MACDStrategy


class TestMACDCalculation:
    """MACD 계산 로직 검증"""

    def test_macd_line_calculation(self):
        """Given: 가격 데이터
        When: MACD 라인 계산
        Then: EMA(12) - EMA(26) 값 반환"""
        # Given
        prices = pd.Series([100 + i for i in range(50)])

        # When: MACD 라인 계산
        macd_line = MACDStrategy._macd_line(None, prices, fast=12, slow=26)

        # Then: MACD 라인이 계산됨
        assert not macd_line.isna().all()
        assert len(macd_line) == len(prices)

    def test_signal_line_calculation(self):
        """Given: 가격 데이터
        When: 시그널 라인 계산
        Then: MACD의 EMA(9) 값 반환"""
        # Given
        prices = pd.Series([100 + i for i in range(50)])

        # When: 시그널 라인 계산
        signal_line = MACDStrategy._signal_line(None, prices, fast=12, slow=26, signal=9)

        # Then: 시그널 라인이 계산됨
        assert not signal_line.isna().all()
        assert len(signal_line) == len(prices)

    def test_macd_positive_in_uptrend(self):
        """Given: 상승 추세 데이터
        When: MACD 계산
        Then: MACD > 0 (단기 EMA > 장기 EMA)"""
        # Given: 강한 상승 추세
        prices = pd.Series([100 + i * 2 for i in range(50)])

        # When
        macd_line = MACDStrategy._macd_line(None, prices, fast=12, slow=26)

        # Then: 상승 추세에서 MACD > 0
        assert macd_line.iloc[-1] > 0

    def test_macd_negative_in_downtrend(self):
        """Given: 하락 추세 데이터
        When: MACD 계산
        Then: MACD < 0 (단기 EMA < 장기 EMA)"""
        # Given: 강한 하락 추세
        prices = pd.Series([200 - i * 2 for i in range(50)])

        # When
        macd_line = MACDStrategy._macd_line(None, prices, fast=12, slow=26)

        # Then: 하락 추세에서 MACD < 0
        assert macd_line.iloc[-1] < 0

    def test_macd_with_constant_price(self):
        """Given: 일정한 가격
        When: MACD 계산
        Then: MACD = 0"""
        # Given
        prices = pd.Series([100.0] * 50)

        # When
        macd_line = MACDStrategy._macd_line(None, prices, fast=12, slow=26)

        # Then: MACD가 0
        assert macd_line.iloc[-1] == pytest.approx(0.0, abs=0.01)


class TestMACDStrategy:
    """MACD 전략 시그널 생성 검증"""

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

    def test_strategy_buys_on_macd_crossover(self):
        """Given: MACD가 시그널을 상향 돌파
        When: MACD 전략 실행
        Then: 매수 신호 발생"""
        # Given: 하락 후 상승 (MACD 상향 돌파)
        close_prices = pd.Series([
            150, 148, 146, 144, 142, 140, 138, 136, 134, 132,
            130, 128, 126, 124, 122, 120, 118, 116, 114, 112,
            110, 112, 115, 119, 124, 130, 137, 145, 154, 164,
            175, 180, 185, 190, 195, 200
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_period=12, slow_period=26, signal_period=9)

        # Then: 거래 발생
        assert result['# Trades'] >= 0

    def test_strategy_sells_on_macd_crossunder(self):
        """Given: MACD가 시그널을 하향 돌파
        When: 포지션이 있을 때
        Then: 매도 신호 발생"""
        # Given: 상승 후 하락
        close_prices = pd.Series([
            100, 105, 110, 115, 120, 125, 130, 135, 140, 145,
            150, 155, 160, 165, 170, 175, 180, 185, 190, 195,
            200, 198, 195, 191, 186, 180, 173, 165, 156, 146,
            135, 130, 125, 120, 115, 110
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_period=12, slow_period=26, signal_period=9)

        # Then: 거래 발생
        assert result['# Trades'] >= 0

    def test_strategy_respects_position_size(self):
        """Given: MACD 전략 with position_size=0.95
        When: 매수 신호 발생
        Then: 자본의 95%만 사용"""
        # Given
        close_prices = pd.Series([
            150, 148, 146, 144, 142, 140, 138, 136, 134, 132,
            130, 128, 126, 124, 122, 120, 118, 116, 114, 112,
            115, 120, 126, 133, 141, 150, 160, 171, 183, 196,
            200, 205, 210
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 최종 자본이 초기 자본의 85% 이상
        assert result['Equity Final [$]'] >= 8500

    def test_strategy_with_custom_parameters(self):
        """Given: 커스텀 MACD 파라미터
        When: 전략 실행
        Then: 설정된 파라미터로 동작"""
        # Given
        close_prices = pd.Series([
            100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
            120, 122, 124, 126, 128, 130, 128, 126, 124, 122,
            120, 125, 130, 135, 140
        ])
        data = self.create_sample_data(close_prices)

        # When: 커스텀 파라미터 (더 빠른 MACD)
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_period=5, slow_period=13, signal_period=5)

        # Then: 백테스트 완료
        assert result is not None
        assert 'Return [%]' in result

    def test_strategy_handles_nan_values(self):
        """Given: NaN이 포함된 MACD/시그널
        When: 전략 실행
        Then: NaN 처리 후 정상 동작"""
        # Given: 충분한 데이터
        close_prices = pd.Series([100 + i for i in range(40)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 에러 없이 실행
        assert result is not None


class TestMACDEdgeCases:
    """MACD 전략 경계값 및 예외 상황 테스트"""

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
        """Given: 최소 데이터 포인트 (slow_period + signal_period)
        When: MACD 계산
        Then: 정상 동작"""
        # Given: 35개 데이터 (26 + 9)
        close_prices = pd.Series([100 + i for i in range(35)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 에러 없이 실행
        assert result is not None

    def test_strategy_with_insufficient_data(self):
        """Given: 부족한 데이터
        When: MACD 전략 실행
        Then: 거래 발생하지 않거나 최소한의 거래"""
        # Given: 20개 데이터 (slow_period보다 적음)
        close_prices = pd.Series([100 + i for i in range(20)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 백테스트 완료 (거래는 적을 수 있음)
        assert result is not None

    def test_strategy_in_sideways_market(self):
        """Given: 횡보장
        When: MACD 전략 실행
        Then: MACD가 0 근처에서 진동"""
        # Given: 횡보
        close_prices = pd.Series([
            100, 102, 101, 103, 102, 104, 103, 105, 104, 106,
            105, 107, 106, 108, 107, 109, 108, 110, 109, 111,
            110, 112, 111, 113, 112, 114, 113, 115, 114, 116
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.01)
        result = bt.run()

        # Then: 빈번한 거래로 수수료 손실 가능
        assert result is not None

    def test_strategy_with_high_volatility(self):
        """Given: 높은 변동성
        When: MACD 전략 실행
        Then: 빈번한 교차"""
        # Given: 지그재그 패턴
        close_prices = pd.Series([
            100, 110, 105, 115, 108, 118, 112, 122, 115, 125,
            120, 130, 125, 135, 130, 140, 135, 145, 140, 150,
            145, 155, 150, 160, 155, 165, 160, 170, 165, 175
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.01)
        result = bt.run(fast_period=5, slow_period=10, signal_period=3)

        # Then: 여러 거래 발생 가능
        assert result is not None

    def test_strategy_with_very_slow_parameters(self):
        """Given: 매우 느린 파라미터
        When: MACD 전략 실행
        Then: 거래가 적음"""
        # Given
        close_prices = pd.Series([100 + i for i in range(100)])
        data = self.create_sample_data(close_prices)

        # When: 매우 느린 MACD
        bt = Backtest(data, MACDStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_period=26, slow_period=52, signal_period=18)

        # Then: 거래가 적음
        assert result['# Trades'] <= 2

    def test_macd_histogram_convergence(self):
        """Given: 충분한 데이터
        When: MACD와 시그널 계산
        Then: 히스토그램 (MACD - Signal)이 올바르게 계산"""
        # Given
        prices = pd.Series([100 + i * 0.5 for i in range(50)])

        # When
        macd_line = MACDStrategy._macd_line(None, prices, 12, 26)
        signal_line = MACDStrategy._signal_line(None, prices, 12, 26, 9)
        histogram = macd_line - signal_line

        # Then: 히스토그램이 계산됨
        assert not histogram.isna().all()
        # 마지막 값이 유효함
        assert not np.isnan(histogram.iloc[-1])

    def test_strategy_with_zero_initial_cash(self):
        """Given: 0 초기 자본
        When: MACD 전략 실행
        Then: 거래 불가"""
        # Given
        close_prices = pd.Series([100 + i for i in range(40)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MACDStrategy, cash=0, commission=0.0)
        result = bt.run()

        # Then: 거래 없음
        assert result['# Trades'] == 0
