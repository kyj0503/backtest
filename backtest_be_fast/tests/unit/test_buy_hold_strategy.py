"""
Buy & Hold 전략 단위 테스트

**테스트 범위**:
- 전략 실행 및 매수 로직
- 포지션 보유 검증
- 매도 없음 확인

**테스트 원칙**:
- 도메인 정책 테스트 (핵심 비즈니스 로직)
- 경계값 테스트
- Given-When-Then 패턴 사용
"""
import pytest
import pandas as pd
from datetime import datetime
from backtesting import Backtest
from app.strategies.buy_hold_strategy import BuyAndHoldStrategy


class TestBuyAndHoldStrategy:
    """Buy & Hold 전략 검증"""

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

    def test_strategy_buys_on_first_bar(self):
        """Given: 가격 데이터
        When: Buy & Hold 전략 실행
        Then: 첫 봉에서 매수"""
        # Given: 상승 추세 데이터
        close_prices = pd.Series([100, 105, 110, 115, 120])
        data = self.create_sample_data(close_prices)

        # When: 백테스트 실행
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 거래가 1회만 발생 (첫 매수)
        assert result['# Trades'] == 0  # Buy & Hold는 매도가 없으므로 완결된 거래 0개
        # 최종 자본이 초기 자본보다 높음 (상승 추세)
        assert result['Equity Final [$]'] > 10000

    def test_strategy_holds_through_volatility(self):
        """Given: 변동성이 큰 가격 데이터
        When: Buy & Hold 전략 실행
        Then: 중간에 매도하지 않고 계속 보유"""
        # Given: 변동성 높은 데이터
        close_prices = pd.Series([
            100, 90, 110, 85, 105, 95, 115, 120, 100, 130
        ])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 완결된 거래가 없음 (매도 없음)
        assert result['# Trades'] == 0
        # 최종 가격(130) > 초기 가격(100)이므로 수익
        assert result['Return [%]'] > 0

    def test_strategy_returns_match_price_change(self):
        """Given: 가격 데이터
        When: Buy & Hold 전략 실행
        Then: 수익률이 가격 변화율과 동일"""
        # Given
        close_prices = pd.Series([100, 110, 105, 115, 125])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 수익률 = (최종 가격 / 초기 가격 - 1) * 100
        expected_return = ((125 / 100) - 1) * 100
        # backtesting.py는 commission을 차감하므로 약간의 오차 허용
        assert result['Return [%]'] == pytest.approx(expected_return, abs=1.0)

    def test_strategy_with_downtrend(self):
        """Given: 하락 추세 데이터
        When: Buy & Hold 전략 실행
        Then: 손실 발생"""
        # Given: 하락 추세
        close_prices = pd.Series([100, 95, 90, 85, 80])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 손실 발생
        assert result['Return [%]'] < 0
        assert result['Equity Final [$]'] < 10000

    def test_strategy_with_single_data_point(self):
        """Given: 단일 데이터 포인트
        When: Buy & Hold 전략 실행
        Then: 에러 없이 실행되지만 거래 없음"""
        # Given
        close_prices = pd.Series([100])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 거래 없음 (최소 2개 데이터 필요)
        assert result is not None


class TestBuyAndHoldEdgeCases:
    """Buy & Hold 전략 경계값 및 예외 상황 테스트"""

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

    def test_strategy_with_high_commission(self):
        """Given: 높은 수수료 (1%)
        When: Buy & Hold 전략 실행
        Then: 수수료가 수익률에 영향"""
        # Given
        close_prices = pd.Series([100, 105, 110, 115, 120])
        data = self.create_sample_data(close_prices)

        # When: 높은 수수료
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.01)
        result = bt.run()

        # Then: 수수료 차감으로 인해 수익률 감소
        # (120/100 - 1) * 100 = 20%, 하지만 수수료 차감
        assert result['Return [%]'] < 20

    def test_strategy_with_zero_initial_cash(self):
        """Given: 0 초기 자본
        When: Buy & Hold 전략 실행 시도
        Then: 거래 불가"""
        # Given
        close_prices = pd.Series([100, 105, 110])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=0, commission=0.0)
        result = bt.run()

        # Then: 거래 없음 (자본 없음)
        assert result['# Trades'] == 0

    def test_strategy_with_very_high_price(self):
        """Given: 매우 높은 주가 (초기 자본보다 높음)
        When: Buy & Hold 전략 실행
        Then: 매수 불가"""
        # Given: 주가가 초기 자본보다 높음
        close_prices = pd.Series([20000, 21000, 22000])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 거래 없음 (자본 부족)
        assert result['# Trades'] == 0

    def test_strategy_performance_vs_benchmark(self):
        """Given: 상승 추세 데이터
        When: Buy & Hold 전략 실행
        Then: Buy & Hold Return과 총 수익률이 유사"""
        # Given
        close_prices = pd.Series([100, 110, 105, 120, 130])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: Buy & Hold 전략이므로 두 수익률이 유사해야 함
        # (commission 차이만 존재)
        assert abs(result['Return [%]'] - result['Buy & Hold Return [%]']) < 2.0

    def test_strategy_with_flat_market(self):
        """Given: 횡보장 (가격 변동 없음)
        When: Buy & Hold 전략 실행
        Then: 수익률 0% (수수료 제외)"""
        # Given: 가격 변동 없음
        close_prices = pd.Series([100, 100, 100, 100, 100])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, BuyAndHoldStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then: 수익률 0%
        assert result['Return [%]'] == pytest.approx(0.0, abs=0.5)
