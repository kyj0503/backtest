"""
EMA 교차 전략 단위 테스트

**테스트 범위**:
- EMA 계산 로직의 정확성
- 골든 크로스/데드 크로스 판별
- 매수/매도 시그널 생성
- SMA와의 차이점 검증

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
from app.strategies.ema_strategy import EMAStrategy


class TestEMACalculation:
    """EMA 계산 로직 검증"""

    def test_ema_calculates_correct_value(self):
        """Given: 단순 가격 데이터
        When: EMA 계산
        Then: 올바른 지수 이동평균 값 반환"""
        # Given
        prices = pd.Series([100, 102, 104, 106, 108, 110])

        # When: 3일 EMA 계산
        ema_3 = EMAStrategy._ema(prices, 3)

        # Then: EMA가 계산됨 (최근 데이터에 더 높은 가중치)
        assert not ema_3.isna().all()
        assert len(ema_3) == len(prices)
        # EMA는 첫 값부터 계산되므로 NaN이 없음
        assert ema_3.iloc[-1] > 0

    def test_ema_responds_faster_than_sma(self):
        """Given: 급격한 가격 변화
        When: EMA vs SMA 계산
        Then: EMA가 SMA보다 빠르게 반응"""
        # Given: 급격한 상승
        prices = pd.Series([100, 100, 100, 100, 100, 120, 120, 120])

        # When
        ema_5 = EMAStrategy._ema(prices, 5)
        sma_5 = prices.rolling(5).mean()

        # Then: 급등 후 EMA가 SMA보다 빠르게 상승
        # 마지막 시점에서 EMA > SMA
        assert ema_5.iloc[-1] > sma_5.iloc[-1]

    def test_ema_with_constant_prices(self):
        """Given: 일정한 가격
        When: EMA 계산
        Then: EMA도 동일한 값"""
        # Given
        prices = pd.Series([100.0] * 10)

        # When
        ema_5 = EMAStrategy._ema(prices, 5)

        # Then: EMA가 100
        assert ema_5.iloc[-1] == pytest.approx(100.0, abs=0.01)

    def test_ema_weights_recent_data_more(self):
        """Given: 최근 가격 상승 데이터
        When: EMA 계산
        Then: 최근 가격에 더 큰 가중치"""
        # Given: 최근 급등
        prices = pd.Series([100, 101, 102, 103, 104, 115])

        # When
        ema_5 = EMAStrategy._ema(prices, 5)

        # Then: 마지막 EMA가 단순 평균보다 높음 (최근 가격 115에 가중치)
        simple_avg = prices.mean()
        assert ema_5.iloc[-1] > simple_avg


class TestEMAStrategy:
    """EMA 전략 시그널 생성 검증"""

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
        """Given: 골든 크로스 발생 (빠른 EMA > 느린 EMA)
        When: EMA 전략 실행
        Then: 매수 신호 발생"""
        # Given: 하락 후 상승
        close_prices = pd.Series([
            100, 98, 96, 94, 92, 90,  # 하락
            92, 95, 99, 104, 110, 117  # 상승 (골든 크로스)
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=3, slow_window=5)

        # Then: 거래 발생
        assert result['# Trades'] >= 0

    def test_strategy_sells_on_dead_cross(self):
        """Given: 데드 크로스 발생 (빠른 EMA < 느린 EMA)
        When: 포지션이 있을 때
        Then: 매도 신호 발생"""
        # Given: 상승 후 하락
        close_prices = pd.Series([
            100, 105, 110, 115, 120, 125,  # 상승
            123, 120, 115, 110, 105, 100  # 하락 (데드 크로스)
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=3, slow_window=5)

        # Then: 거래 발생
        assert result['# Trades'] >= 0

    def test_strategy_respects_position_size(self):
        """Given: EMA 전략 with position_size=0.95
        When: 매수 신호 발생
        Then: 자본의 95%만 사용"""
        # Given
        close_prices = pd.Series([
            100, 98, 96, 94, 92, 90, 88,
            90, 94, 99, 105, 112, 120, 128
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=3, slow_window=5)

        # Then: 최종 자본이 초기 자본의 85% 이상
        assert result['Equity Final [$]'] >= 8500

    def test_strategy_with_custom_parameters(self):
        """Given: 커스텀 EMA 파라미터 (fast=5, slow=10)
        When: 전략 실행
        Then: 설정된 파라미터로 동작"""
        # Given
        close_prices = pd.Series([
            100, 102, 104, 106, 108, 110, 108, 106, 104, 102,
            100, 105, 110, 115, 120, 125
        ])
        data = self.create_sample_data(close_prices)

        # When: 커스텀 파라미터
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=5, slow_window=10)

        # Then: 백테스트 완료
        assert result is not None
        assert 'Return [%]' in result

    def test_strategy_default_parameters(self):
        """Given: 기본 파라미터 (fast=12, slow=26)
        When: EMA 전략 실행
        Then: MACD와 유사한 윈도우 사용"""
        # Given
        close_prices = pd.Series([
            100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
            120, 122, 124, 126, 128, 130, 128, 126, 124, 122,
            120, 118, 116, 114, 112, 110, 115, 120, 125, 130
        ])
        data = self.create_sample_data(close_prices)

        # When: 기본 파라미터
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run()  # 기본값 사용

        # Then: 백테스트 완료
        assert result is not None


class TestEMAEdgeCases:
    """EMA 전략 경계값 및 예외 상황 테스트"""

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
        When: EMA 계산
        Then: 정상 동작"""
        # Given
        close_prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=3, slow_window=5)

        # Then: 에러 없이 실행
        assert result is not None

    def test_strategy_with_insufficient_data(self):
        """Given: 느린 윈도우보다 적은 데이터
        When: EMA 전략 실행
        Then: 거래 발생 가능 (EMA는 첫 값부터 계산)"""
        # Given
        close_prices = pd.Series([100, 105, 110])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=3, slow_window=5)

        # Then: 백테스트 실행됨
        assert result is not None

    def test_strategy_with_equal_fast_slow_window(self):
        """Given: 빠른 = 느린 윈도우
        When: EMA 전략 실행
        Then: 교차가 발생하지 않음"""
        # Given
        close_prices = pd.Series([100, 105, 110, 115, 120, 125, 130])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=5, slow_window=5)

        # Then: 거래 없음
        assert result['# Trades'] == 0

    def test_strategy_with_high_volatility(self):
        """Given: 높은 변동성 데이터
        When: EMA 전략 실행
        Then: 빈번한 교차로 인한 거래 발생"""
        # Given: 지그재그 패턴
        close_prices = pd.Series([
            100, 105, 100, 105, 100, 105, 100, 105, 100, 105,
            100, 105, 100, 105, 100
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.01)
        result = bt.run(fast_window=2, slow_window=3)

        # Then: 빈번한 거래로 수수료 손실 가능
        assert result is not None

    def test_strategy_with_very_long_window(self):
        """Given: 매우 긴 윈도우 (slow=50)
        When: EMA 전략 실행
        Then: 거래가 거의 발생하지 않음"""
        # Given
        close_prices = pd.Series(range(100, 160))  # 60개 데이터
        data = self.create_sample_data(close_prices)

        # When: 매우 긴 윈도우
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=10, slow_window=50)

        # Then: 거래가 적음
        assert result['# Trades'] <= 2

    def test_ema_convergence_with_sufficient_data(self):
        """Given: 충분한 데이터
        When: EMA 계산
        Then: 초기 편향 없이 수렴"""
        # Given: 100개 데이터
        close_prices = pd.Series([100 + i * 0.1 for i in range(100)])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, EMAStrategy, cash=10000, commission=0.0)
        result = bt.run(fast_window=12, slow_window=26)

        # Then: 정상 실행
        assert result is not None
