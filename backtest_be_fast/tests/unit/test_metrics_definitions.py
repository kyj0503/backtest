"""통계 정의 회귀 테스트: DCA 연환산 수익률(A-19), 경로별 Win_Rate/Profit_Factor 정의 통일(A-09)

A-19: `Annual_Return`이 `총 납입액 대비 최종 평가금`을 전 기간 복리로 연환산해,
DCA는 마지막 납입금이 거의 투자되지 않았는데도 첫날 전액 투자한 것처럼 계산됐다.
상승장에서 연환산 수익률이 실제 가격 상승률보다 크게 눌린다. 결정: 시간가중(TWR)
기준 — 당일 납입금을 뺀 `Daily_Return`의 누적곱으로 CAGR을 구한다(낙폭과 같은 정의).
`Total_Return`(총 납입 대비 손익률)은 그대로 둔다.

A-09: 같은 응답 필드가 실행 경로마다 다른 의미였다.
- `Win_Rate`: 전략 경로는 종목별 거래 승률의 금액 가중평균, buy&hold는 상승일 비율
- `Profit_Factor`(손실일 0): 전략 경로 0.0, buy&hold 2.0(이익 있음)/1.0(없음)
결정: 두 경로 모두 일 기준(상승일 비율, 일간 수익 합/손실 합)으로 통일하고,
계산 불가(손실일 없음)면 폴백 상수 대신 None. 거래 기준 승률은 `Trade_Win_Rate`로 따로 준다.
"""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio.portfolio_metrics import PortfolioMetrics
from app.services.portfolio_calculator_service import PortfolioCalculator
from app.services.portfolio_manager_service import PortfolioManagerService
from app.utils.metrics_math import (
    daily_profit_factor,
    time_weighted_annual_return,
)
from app.utils.serializers import recursive_serialize

pytestmark = pytest.mark.unit

START, END = '2022-01-03', '2023-12-29'

IMPLEMENTATIONS = [
    pytest.param(PortfolioMetrics.calculate_portfolio_statistics, id='PortfolioMetrics'),
    pytest.param(PortfolioCalculator.calculate_portfolio_statistics, id='PortfolioCalculator'),
]


def _geometric_frame(daily_growth: float, start: str = START, end: str = END,
                     first: float = 100.0) -> pd.DataFrame:
    """영업일마다 같은 비율(daily_growth)로 움직이는 가격 프레임."""
    index = pd.bdate_range(start=start, end=end)
    prices = first * (1.0 + daily_growth) ** np.arange(len(index))
    return pd.DataFrame({'Close': prices}, index=index)


def _zigzag_frame(start: str = START, end: str = END) -> pd.DataFrame:
    """상승일과 하락일이 섞인 가격 프레임 (+1%, +1%, -1.5% 반복)."""
    index = pd.bdate_range(start=start, end=end)
    pattern = [0.01, 0.01, -0.015]
    prices = [100.0]
    for i in range(1, len(index)):
        prices.append(prices[-1] * (1 + pattern[i % 3]))
    return pd.DataFrame({'Close': prices}, index=index)


def _flat_frame(price: float = 100.0, start: str = START, end: str = END) -> pd.DataFrame:
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


def _request(portfolio, **overrides) -> PortfolioBacktestRequest:
    params = dict(
        portfolio=portfolio,
        start_date=START,
        end_date=END,
        commission=0.0,
        rebalance_frequency='none',
        strategy='buy_hold_strategy',
    )
    params.update(overrides)
    return PortfolioBacktestRequest(**params)


def _run_buy_hold(request: PortfolioBacktestRequest, frames: dict) -> dict:
    service = PortfolioManagerService()
    with patch.object(
        service.data_loader, 'load_stock_data_parallel', new=AsyncMock(return_value=frames)
    ), patch.object(
        service.data_loader, 'load_ticker_currencies',
        new=AsyncMock(return_value={symbol: 'USD' for symbol in frames})
    ), patch.object(
        service.data_loader, 'load_exchange_rates', new=AsyncMock(return_value={})
    ):
        return asyncio.run(service.run_buy_and_hold_portfolio_backtest(request))


def _hold_backtest_result(frame: pd.DataFrame, amount: float, *, total_trades: int,
                          win_rate_pct: float) -> SimpleNamespace:
    """개별 종목 전략 백테스트 결과를 흉내 낸다: 첫날 전액 매수 후 보유한 equity curve."""
    shares = amount / frame['Close'].iloc[0]
    equity_curve = {
        date.strftime('%Y-%m-%d'): float(shares * price)
        for date, price in frame['Close'].items()
    }
    return SimpleNamespace(
        final_equity=float(shares * frame['Close'].iloc[-1]),
        equity_curve=equity_curve,
        total_trades=total_trades,
        win_rate_pct=win_rate_pct,
        max_drawdown_pct=0.0,
        sharpe_ratio=0.0,
    )


def _run_strategy(request: PortfolioBacktestRequest, results_by_symbol: dict) -> dict:
    """개별 종목 백테스트(backtesting.py)를 mock한 채 전략 경로를 실행한다."""
    async def fake_run_backtest(backtest_req):
        return results_by_symbol[backtest_req.ticker]

    service = PortfolioManagerService()
    with patch(
        'app.services.portfolio_manager_service.backtest_service.run_backtest',
        new=AsyncMock(side_effect=fake_run_backtest),
    ):
        return asyncio.run(service.run_strategy_portfolio_backtest(request))


def _duration_days(frame: pd.DataFrame) -> int:
    return (frame.index[-1] - frame.index[0]).days


# ---------------------------------------------------------------------------
# A-19: 연환산 수익률(TWR)
# ---------------------------------------------------------------------------

class TestTimeWeightedAnnualReturnHelper:
    def test_compounds_daily_returns_over_calendar_duration(self):
        returns = pd.Series([0.0, 0.10, -0.05])
        expected = ((1.10 * 0.95) ** (365.25 / 30) - 1) * 100

        assert time_weighted_annual_return(returns, 30) == pytest.approx(expected)

    def test_start_ratio_scales_the_growth(self):
        """첫날 수수료처럼 Daily_Return에 잡히지 않는 첫날 손실을 반영한다."""
        returns = pd.Series([0.0, 0.10])
        expected = ((0.998 * 1.10) ** (365.25 / 365) - 1) * 100

        assert time_weighted_annual_return(returns, 365, start_ratio=0.998) == pytest.approx(expected)

    def test_zero_duration_is_zero(self):
        assert time_weighted_annual_return(pd.Series([0.0, 0.5]), 0) == 0.0

    def test_total_loss_is_minus_100_not_nan(self):
        assert time_weighted_annual_return(pd.Series([0.0, -1.0]), 365) == pytest.approx(-100.0)


class TestDcaAnnualReturnIsTimeWeighted:
    def test_flat_price_dca_without_commission_is_zero(self):
        request = _request([{
            'symbol': 'AAPL', 'amount': 1000.0,
            'investment_type': 'dca', 'dca_frequency': 'monthly_1',
        }])
        result = _run_buy_hold(request, {'AAPL': _flat_frame()})

        stats = result['data']['portfolio_statistics']
        assert stats['Annual_Return'] == pytest.approx(0.0, abs=1e-9)
        assert stats['Total_Return'] == pytest.approx(0.0, abs=1e-9)

    def test_dca_into_constant_growth_matches_price_cagr(self):
        """매 영업일 0.05%씩 오르는 종목에 월 적립: 항상 전액 투자 상태이므로
        시간가중 연환산 수익률은 가격 자체의 연환산 상승률과 같아야 한다.

        수정 전: 총 납입액 대비 최종 평가금을 전 기간 복리로 연환산해, 늦게 넣은
        납입금이 전 기간 투자된 것처럼 분모에 잡혀 약 1/2 수준으로 눌렸다.
        """
        frame = _geometric_frame(0.0005)
        request = _request([{
            'symbol': 'AAPL', 'amount': 1000.0,
            'investment_type': 'dca', 'dca_frequency': 'monthly_1',
        }])
        result = _run_buy_hold(request, {'AAPL': frame})

        stats = result['data']['portfolio_statistics']
        price_ratio = frame['Close'].iloc[-1] / frame['Close'].iloc[0]
        expected = (price_ratio ** (365.25 / _duration_days(frame)) - 1) * 100
        assert stats['Annual_Return'] == pytest.approx(expected, rel=1e-9)
        # Total_Return은 총 납입 대비 손익률 그대로다 (시간가중 수익률보다 작다)
        assert 0 < stats['Total_Return'] < (price_ratio - 1) * 100

    def test_sharpe_uses_the_time_weighted_annual_return(self):
        frame = _zigzag_frame()
        request = _request([{
            'symbol': 'AAPL', 'amount': 1000.0,
            'investment_type': 'dca', 'dca_frequency': 'monthly_1',
        }])
        stats = _run_buy_hold(request, {'AAPL': frame})['data']['portfolio_statistics']

        assert stats['Sharpe_Ratio'] == pytest.approx(stats['Annual_Return'] / stats['Annual_Volatility'])


class TestLumpSumAnnualReturnIsUnchanged:
    """납입이 없으면 TWR과 기존 공식(최종 평가금/원금의 연환산)이 같아야 한다."""

    @pytest.mark.parametrize('commission', [0.0, 0.002])
    def test_lump_sum_matches_final_value_cagr_including_first_day_commission(self, commission):
        """첫날 매수 수수료는 평가금을 줄이지만 Daily_Return[0]은 0으로 기록된다.
        누적곱만 쓰면 수수료만큼 연환산 수익률이 부풀므로 첫날 비율을 반영해야 한다."""
        frame = _zigzag_frame()
        request = _request([{'symbol': 'AAPL', 'amount': 1000.0}], commission=commission)
        stats = _run_buy_hold(request, {'AAPL': frame})['data']['portfolio_statistics']

        legacy = ((stats['Final_Value'] / stats['Initial_Value']) ** (365.25 / _duration_days(frame)) - 1) * 100
        assert stats['Annual_Return'] == pytest.approx(legacy, rel=1e-9)

    def test_lump_sum_with_cash_matches_final_value_cagr(self):
        frame = _zigzag_frame()
        request = _request([
            {'symbol': 'AAPL', 'amount': 700.0},
            {'symbol': 'CASH', 'amount': 300.0, 'asset_type': 'cash'},
        ], commission=0.002)
        stats = _run_buy_hold(request, {'AAPL': frame})['data']['portfolio_statistics']

        legacy = ((stats['Final_Value'] / stats['Initial_Value']) ** (365.25 / _duration_days(frame)) - 1) * 100
        assert stats['Annual_Return'] == pytest.approx(legacy, rel=1e-9)

    @pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
    def test_frame_without_inflows_uses_first_value_as_start(self, calc_statistics):
        """engine 밖에서 만든 곡선(전략 경로)은 첫날 평가금/원금이 시작 비율이다."""
        values = [0.998, 1.05, 1.10]
        returns = pd.Series(values).pct_change().fillna(0.0).tolist()
        df = pd.DataFrame(
            {'Portfolio_Value': values, 'Daily_Return': returns},
            index=pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-31']),
        )
        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Annual_Return'] == pytest.approx((1.10 ** (365.25 / 30) - 1) * 100, rel=1e-9)

    @pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
    def test_explicit_start_ratio_attr_wins_over_first_value(self, calc_statistics):
        """DCA 곡선은 첫날 평가금이 총 납입액의 일부라 Portfolio_Value[0]을 쓸 수 없다."""
        df = pd.DataFrame(
            {'Portfolio_Value': [0.1, 0.22], 'Daily_Return': [0.0, 0.10]},
            index=pd.to_datetime(['2024-01-01', '2024-12-31']),
        )
        df.attrs['twr_start_ratio'] = 1.0
        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Annual_Return'] == pytest.approx((1.10 ** (365.25 / 365) - 1) * 100, rel=1e-9)


# ---------------------------------------------------------------------------
# A-09: Win_Rate / Profit_Factor 정의 통일
# ---------------------------------------------------------------------------

class TestDailyProfitFactorHelper:
    def test_ratio_of_gross_gain_to_gross_loss(self):
        assert daily_profit_factor(pd.Series([0.02, -0.01, 0.03, -0.02])) == pytest.approx(0.05 / 0.03)

    def test_no_losing_day_is_none(self):
        assert daily_profit_factor(pd.Series([0.01, 0.02])) is None

    def test_flat_is_none(self):
        assert daily_profit_factor(pd.Series([0.0, 0.0])) is None

    def test_all_losses_is_zero(self):
        assert daily_profit_factor(pd.Series([-0.01, -0.02])) == 0.0


class TestStrategyAndBuyHoldShareDefinitions:
    """같은 가격·같은 보유(첫날 전액 매수 후 보유)를 두 경로에 넣으면
    Win_Rate/Profit_Factor가 같은 값이어야 한다 — 정의가 같다는 뜻이다."""

    def _both(self, frame: pd.DataFrame, *, total_trades: int = 1, win_rate_pct: float = 100.0):
        buy_hold = _run_buy_hold(
            _request([{'symbol': 'AAPL', 'amount': 1000.0}]), {'AAPL': frame}
        )['data']['portfolio_statistics']
        strategy = _run_strategy(
            _request([{'symbol': 'AAPL', 'amount': 1000.0}], strategy='sma_strategy'),
            {'AAPL': _hold_backtest_result(frame, 1000.0, total_trades=total_trades,
                                           win_rate_pct=win_rate_pct)},
        )['data']['portfolio_statistics']
        return buy_hold, strategy

    def test_mixed_days_give_identical_win_rate_and_profit_factor(self):
        buy_hold, strategy = self._both(_zigzag_frame())

        # 일 기준 승률: 상승일 비율 (+,+,- 반복이므로 약 2/3)
        assert buy_hold['Win_Rate'] == pytest.approx(strategy['Win_Rate'])
        assert 60 < buy_hold['Win_Rate'] < 70
        assert buy_hold['Profit_Factor'] == pytest.approx(strategy['Profit_Factor'], rel=1e-9)
        assert buy_hold['Positive_Days'] == strategy['Positive_Days']
        assert buy_hold['Negative_Days'] == strategy['Negative_Days']
        assert buy_hold['Max_Consecutive_Gains'] == strategy['Max_Consecutive_Gains'] == 2
        assert buy_hold['Max_Consecutive_Losses'] == strategy['Max_Consecutive_Losses'] == 1
        assert buy_hold['Annual_Volatility'] == pytest.approx(strategy['Annual_Volatility'], rel=1e-9)

    def test_no_losing_day_gives_none_on_both_paths(self):
        """수정 전: 전략 경로 0.0, buy&hold 2.0."""
        buy_hold, strategy = self._both(_geometric_frame(0.0005))

        assert buy_hold['Profit_Factor'] is None
        assert strategy['Profit_Factor'] is None

    def test_trade_win_rate_is_kept_as_a_separate_field(self):
        """거래 기준 승률은 Win_Rate를 덮어쓰지 않고 Trade_Win_Rate로 나간다."""
        _, strategy = self._both(_zigzag_frame(), total_trades=4, win_rate_pct=25.0)

        assert strategy['Trade_Win_Rate'] == pytest.approx(25.0)
        assert strategy['Win_Rate'] != pytest.approx(25.0)

    def test_trade_win_rate_is_pooled_over_trades_and_ignores_cash(self):
        """수정 전 가중치는 투자금 비중이라 현금 50%가 승률을 절반으로 깎았다.
        거래 기준 승률은 전 종목 거래를 합친 승률(거래 수 가중)이어야 한다."""
        frame_a, frame_b = _zigzag_frame(), _geometric_frame(0.0005)
        request = _request([
            {'symbol': 'AAPL', 'amount': 500.0},
            {'symbol': 'MSFT', 'amount': 250.0},
            {'symbol': 'CASH', 'amount': 250.0, 'asset_type': 'cash'},
        ], strategy='sma_strategy')
        stats = _run_strategy(request, {
            'AAPL': _hold_backtest_result(frame_a, 500.0, total_trades=3, win_rate_pct=100 / 3),
            'MSFT': _hold_backtest_result(frame_b, 250.0, total_trades=1, win_rate_pct=100.0),
        })['data']['portfolio_statistics']

        # (1 + 1) 승 / 4 거래 = 50%
        assert stats['Trade_Win_Rate'] == pytest.approx(50.0)

    def test_trade_win_rate_is_none_without_trades(self):
        request = _request([{'symbol': 'AAPL', 'amount': 1000.0}], strategy='sma_strategy')
        stats = _run_strategy(request, {
            'AAPL': _hold_backtest_result(_zigzag_frame(), 1000.0, total_trades=0, win_rate_pct=0.0),
        })['data']['portfolio_statistics']

        assert stats['Trade_Win_Rate'] is None

    def test_none_survives_json_serialization_as_null(self):
        _, strategy = self._both(_geometric_frame(0.0005))

        payload = json.loads(json.dumps(recursive_serialize({'s': strategy})))
        assert payload['s']['Profit_Factor'] is None
