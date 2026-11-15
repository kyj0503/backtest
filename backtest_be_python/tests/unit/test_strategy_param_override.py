"""전략 파라미터 오버라이드 회귀 테스트 (P1-02)

BacktestEngine._build_strategy()는 STRATEGIES 스펙(app/services/strategy_service.py)의
공개 파라미터 이름을 검증한 뒤 `hasattr(base_strategy, key)`로 실제 전략 클래스 속성에
매핑한다. 전략 클래스의 튜닝 가능한 클래스 속성 이름이 공개 파라미터 이름과 다르면
hasattr가 항상 False가 되어 오버라이드가 조용히 무시되고, 사용자가 어떤 값을 보내도
백테스트는 항상 기본값으로 실행된다 (예: SMA 전략의 `sma_short`/`sma_long` vs 공개
파라미터 `short_window`/`long_window`).

이 테스트는 StrategyService.validate_strategy_params를 목(mock)하지 않고 실제 검증
로직을 통과시켜, BacktestEngine._build_strategy()가 반환하는 클래스의 속성이 사용자가
전달한 값과 실제로 일치하는지 확인한다.
"""
import pytest

from app.services.backtest_engine import BacktestEngine


pytestmark = pytest.mark.unit


@pytest.fixture
def engine():
    """실제 StrategyService를 사용하는 BacktestEngine (파라미터 검증 목킹 없음)"""
    return BacktestEngine()


class TestSmaStrategyParamOverride:
    """sma_strategy 공개 파라미터: short_window, long_window"""

    def test_short_and_long_window_are_applied(self, engine):
        params = {'short_window': 7, 'long_window': 21}

        result = engine._build_strategy('sma_strategy', params)

        assert result.short_window == 7
        assert result.long_window == 21


class TestRsiStrategyParamOverride:
    """rsi_strategy 공개 파라미터: rsi_period, rsi_oversold, rsi_overbought"""

    def test_period_oversold_overbought_are_applied(self, engine):
        params = {'rsi_period': 21, 'rsi_oversold': 25, 'rsi_overbought': 75}

        result = engine._build_strategy('rsi_strategy', params)

        assert result.rsi_period == 21
        assert result.rsi_oversold == 25
        assert result.rsi_overbought == 75


class TestBollingerStrategyParamOverride:
    """bollinger_strategy 공개 파라미터: period, std_dev"""

    def test_period_and_std_dev_are_applied(self, engine):
        params = {'period': 30, 'std_dev': 2.5}

        result = engine._build_strategy('bollinger_strategy', params)

        assert result.period == 30
        assert result.std_dev == 2.5


class TestMacdStrategyParamOverride:
    """macd_strategy 공개 파라미터: fast_period, slow_period, signal_period"""

    def test_fast_slow_signal_periods_are_applied(self, engine):
        params = {'fast_period': 8, 'slow_period': 20, 'signal_period': 5}

        result = engine._build_strategy('macd_strategy', params)

        assert result.fast_period == 8
        assert result.slow_period == 20
        assert result.signal_period == 5


class TestEmaStrategyParamOverride:
    """ema_strategy 공개 파라미터: fast_window, slow_window"""

    def test_fast_and_slow_window_are_applied(self, engine):
        params = {'fast_window': 8, 'slow_window': 34}

        result = engine._build_strategy('ema_strategy', params)

        assert result.fast_window == 8
        assert result.slow_window == 34
