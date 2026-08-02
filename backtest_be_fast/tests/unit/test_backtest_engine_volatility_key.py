"""backtesting.py 통계 키 이름 정합성 테스트

`backtesting==0.3.3`의 `compute_stats`는 연환산 변동성을
`'Volatility (Ann.) [%]'` 키로 내보내는데, 응답 변환 코드는
`'Volatility [%]'`를 읽고 있었다. `.get(key, 0.0)` 기본값 때문에 조용히
0.0이 되어, 전략 백테스트의 변동성이 항상 0으로 보고됐다.
"""
import pytest

from app.services.backtest_engine import BacktestEngine

pytestmark = pytest.mark.unit


class TestVolatilityKeyMatchesLibraryOutput:
    def test_library_emits_annualized_volatility_key(self):
        """설치된 backtesting.py가 실제로 쓰는 키 이름을 고정한다.

        라이브러리를 올리면서 키가 바뀌면 이 테스트가 먼저 실패해,
        변환 코드가 조용히 0.0을 반환하는 상황을 막는다.
        """
        import pandas as pd
        from backtesting import Backtest, Strategy
        from backtesting.test import GOOG, SMA
        from backtesting.lib import crossover

        class _Sma(Strategy):
            def init(self):
                self.fast = self.I(SMA, self.data.Close, 10)
                self.slow = self.I(SMA, self.data.Close, 20)

            def next(self):
                if crossover(self.fast, self.slow):
                    self.buy()

        stats = Backtest(GOOG.iloc[:200], _Sma, cash=10_000, commission=0).run()

        assert 'Volatility (Ann.) [%]' in stats.index
        assert isinstance(stats['Volatility (Ann.) [%]'], float)
        assert not pd.isna(stats['Volatility (Ann.) [%]'])

    def test_converted_response_carries_nonzero_volatility(self):
        """실제 통계에서 변환하면 변동성이 0이 아니어야 한다.

        수정 전에는 존재하지 않는 키를 읽어 항상 0.0이 나왔다.
        """
        from datetime import date
        from unittest.mock import Mock
        from backtesting import Backtest, Strategy
        from backtesting.test import GOOG, SMA
        from backtesting.lib import crossover

        class _Sma(Strategy):
            def init(self):
                self.fast = self.I(SMA, self.data.Close, 10)
                self.slow = self.I(SMA, self.data.Close, 20)

            def next(self):
                if crossover(self.fast, self.slow):
                    self.buy()

        data = GOOG.iloc[:200]
        stats = Backtest(data, _Sma, cash=10_000, commission=0).run()
        assert stats['Volatility (Ann.) [%]'] > 0, "픽스처 전제: 변동성이 0보다 커야 의미 있는 검증"

        request = Mock()
        request.ticker = 'GOOG'
        request.initial_cash = 10_000.0
        request.strategy = 'sma_strategy'
        request.start_date = date(2004, 8, 19)
        request.end_date = date(2005, 6, 8)

        response = BacktestEngine()._convert_result_to_response(stats=stats, request=request)

        assert response.volatility_pct == pytest.approx(
            float(stats['Volatility (Ann.) [%]']), rel=1e-9
        )
        assert response.volatility_pct > 0
