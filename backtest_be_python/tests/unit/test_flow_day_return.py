"""납입일(외부 유입일) 일간 수익률의 수수료 귀속 회귀 테스트

과거 공식: `Daily_Return = (V - P - F) / P` (V=당일 평가금, P=전일 평가금, F=당일 납입금).
새 납입금을 매수하며 낸 수수료가 분자에는 들어가지만 분모는 기존 자본 P뿐이라,
기존 자본이 작을수록 수수료가 손실률로 부풀었다. 재현: 10달러어치 종목을 먼저
사고(다른 시장 종목 휴장 등으로) 990달러어치 종목의 첫 매수가 며칠 늦어지면,
가격이 전혀 움직이지 않는데도 그날 수익률이 -19.84%로 기록돼 MDD·시간가중
연환산 수익률(A-19/A-20)을 오염시켰다.

수정: 유입 시점에 포트폴리오를 재평가하는 시간가중 수익률의 정의를 따른다.
시뮬레이션은 납입금을 당일 종가로 체결하므로 하루를 두 구간으로 나눈다.
- 구간 1: 전일 평가금 P → 납입 직전 평가금 V_pre (당일 가격 변동, 기존 자본만 노출)
- 구간 2: 납입 직후 자본 V_pre + F → 당일 최종 평가금 V (매수 수수료·리밸런싱 비용)
`Daily_Return = (V_pre / P) * (V / (V_pre + F)) - 1`

`P + F`를 분모로 쓰는 "기간 시작 유입" 근사는 쓰지 않았다. 당일 가격 변동을 새
납입금에도 나눠 주므로, 종가에 체결되는 이 시뮬레이션에서는 납입일의 시장 수익률을
희석한다(일정 상승률 DCA의 연환산 = 가격 연환산 불변식이 깨진다).
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio.portfolio_metrics import PortfolioMetrics
from app.services.portfolio_manager_service import PortfolioManagerService

pytestmark = pytest.mark.unit

START, END = '2022-01-03', '2022-12-30'
COMMISSION = 0.002


def _flat_frame(price: float, start: str = START, end: str = END) -> pd.DataFrame:
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


def _run_buy_hold(portfolio, frames, **overrides) -> dict:
    params = dict(
        portfolio=portfolio,
        start_date=START,
        end_date=END,
        commission=COMMISSION,
        rebalance_frequency='none',
        strategy='buy_hold_strategy',
    )
    params.update(overrides)
    request = PortfolioBacktestRequest(**params)
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


def _stock_info(symbol: str) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=1.0, asset_type='stock',
        investment_type='lump_sum', monthly_amount=0.0,
    )


class TestFlowDayReturnFormula:
    def test_purchase_fee_on_new_money_is_spread_over_post_flow_capital(self):
        """기존 자본 10, 납입 990, 수수료 1.98, 가격 불변.
        V_pre = 10, V = 10 + 988.02 = 998.02 → 수익률 = 998.02 / 1000 - 1 = -0.198%.
        과거 공식은 -1.98 / 10 = -19.8%."""
        _normalized, daily_return, _weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-08'),
            shares={'A': 0.1, 'B': 990 * (1 - COMMISSION) / 50.0},
            available_cash=0.0,
            current_prices={'A': 100.0, 'B': 50.0},
            cash_holdings={},
            prev_portfolio_value=10.0,
            daily_cash_inflow=990.0,
            total_amount=1000.0,
            dca_info={'A': _stock_info('AAA'), 'B': _stock_info('BBB')},
            pre_flow_value=10.0,
        )

        assert daily_return == pytest.approx(998.02 / 1000.0 - 1)

    def test_market_move_before_flow_counts_only_for_existing_capital(self):
        """기존 자본 100이 당일 +10%(→110)가 된 뒤 종가에 100을 수수료 없이 납입.
        V = 210. 새 납입금은 당일 가격 변동에 노출되지 않았으므로 수익률은 정확히 10%.
        (P + F 분모 근사라면 10/200 = 5%로 희석된다.)"""
        _normalized, daily_return, _weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-08'),
            shares={'A': 21.0},
            available_cash=0.0,
            current_prices={'A': 10.0},
            cash_holdings={},
            prev_portfolio_value=100.0,
            daily_cash_inflow=100.0,
            total_amount=200.0,
            dca_info={'A': _stock_info('AAA')},
            pre_flow_value=110.0,
        )

        assert daily_return == pytest.approx(0.10)

    def test_without_pre_flow_value_the_no_flow_formula_is_unchanged(self):
        _normalized, daily_return, _weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-08'),
            shares={'A': 11.0},
            available_cash=0.0,
            current_prices={'A': 10.0},
            cash_holdings={},
            prev_portfolio_value=100.0,
            daily_cash_inflow=0.0,
            total_amount=100.0,
            dca_info={'A': _stock_info('AAA')},
        )

        assert daily_return == pytest.approx(0.10)


class TestDelayedFirstPurchase:
    """작은 선행 자본 + 첫 매수가 늦어진 큰 종목 (혼합 시장 휴장 시작 등)."""

    def _run(self):
        late_start = pd.bdate_range(START, END)[5]
        frames = {
            'AAA': _flat_frame(100.0),
            'BBB': _flat_frame(50.0, start=late_start.strftime('%Y-%m-%d')),
        }
        portfolio = [
            {'symbol': 'AAA', 'amount': 10.0},
            {'symbol': 'BBB', 'amount': 990.0},
        ]
        return _run_buy_hold(portfolio, frames)['data']

    def test_no_fake_loss_on_the_delayed_purchase_day(self):
        data = self._run()

        worst_day = min(data['daily_returns'].values())
        # 가격이 전혀 움직이지 않으므로 손실은 BBB 매수 수수료(1.98)를
        # 납입 직후 자본(9.98 + 990)으로 나눈 값뿐이다. 과거: -19.84%
        expected = (998.0 / 999.98 - 1) * 100
        assert worst_day == pytest.approx(expected, rel=1e-9)

        stats = data['portfolio_statistics']
        assert stats['Max_Drawdown'] == pytest.approx(expected, rel=1e-9)

    def test_time_weighted_annual_return_uses_the_corrected_day(self):
        data = self._run()
        stats = data['portfolio_statistics']

        # 첫날 AAA 수수료(시작 비율 0.998) × BBB 매수일 수익률
        growth = 0.998 * (998.0 / 999.98)
        duration = (pd.Timestamp(END) - pd.Timestamp(START)).days
        expected = (growth ** (365.25 / duration) - 1) * 100
        assert stats['Annual_Return'] == pytest.approx(expected, rel=1e-9)
        # 총 납입 대비 손익률은 정의가 달라 그대로다: 998 / 1000 - 1
        assert stats['Total_Return'] == pytest.approx(-0.2, rel=1e-9)


class TestFlatPriceDcaWithCommission:
    def test_each_payment_fee_is_divided_by_post_flow_capital(self):
        """고정가, 월 적립 A, 수수료 c. k번째 납입일(k≥2):
        V_pre = (k-1)·A·(1-c), V = k·A·(1-c) → r_k = V / (V_pre + A) - 1.
        과거 공식: r_k = -c·A / ((k-1)·A·(1-c)) — 두 번째 납입일에 -0.2%로
        새 납입금 수수료가 기존 자본 전체의 손실처럼 잡혔다."""
        amount, c = 1000.0, COMMISSION
        data = _run_buy_hold(
            [{'symbol': 'AAA', 'amount': amount, 'investment_type': 'dca',
              'dca_frequency': 'monthly_1'}],
            {'AAA': _flat_frame(100.0)},
        )['data']

        flow_day_returns = sorted(r for r in data['daily_returns'].values() if r < 0)
        payments = data['individual_returns']['AAA']['dca_periods']
        expected = sorted(
            (k * amount * (1 - c) / ((k - 1) * amount * (1 - c) + amount) - 1) * 100
            for k in range(2, payments + 1)
        )
        assert flow_day_returns == pytest.approx(expected, rel=1e-9)

        index = 1.0
        for r in expected:
            index *= 1 + r / 100
        stats = data['portfolio_statistics']
        assert stats['Max_Drawdown'] == pytest.approx((index - 1) * 100, rel=1e-9)
        # 총 납입 대비 손익률은 모든 납입금이 수수료 c만큼 잃은 것 그대로다
        assert stats['Total_Return'] == pytest.approx(-c * 100, rel=1e-9)

    def test_flat_price_dca_without_commission_stays_zero(self):
        data = _run_buy_hold(
            [{'symbol': 'AAA', 'amount': 1000.0, 'investment_type': 'dca',
              'dca_frequency': 'monthly_1'}],
            {'AAA': _flat_frame(100.0)},
            commission=0.0,
        )['data']
        stats = data['portfolio_statistics']

        assert stats['Annual_Return'] == pytest.approx(0.0, abs=1e-9)
        assert stats['Total_Return'] == pytest.approx(0.0, abs=1e-9)
        assert stats['Max_Drawdown'] == pytest.approx(0.0, abs=1e-9)
