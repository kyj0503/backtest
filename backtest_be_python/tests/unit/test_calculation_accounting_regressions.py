"""Independent accounting oracles; market data I/O only is replaced."""
import asyncio
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService
from app.services.portfolio.portfolio_metrics import PortfolioMetrics
from app.services.portfolio_calculator_service import PortfolioCalculator

pytestmark = pytest.mark.unit


def run_portfolio(frames, start, end, *, dca=False, fee=0, rebalance='none', currencies=None, rates=None):
    request = PortfolioBacktestRequest(
        portfolio=[dict(symbol=s, amount=1000 / len(frames),
                        investment_type='dca' if dca else 'lump_sum', dca_frequency='monthly_1')
                   for s in frames], start_date=start, end_date=end,
        commission=fee, rebalance_frequency=rebalance, strategy='buy_hold_strategy',
        include_stock_data=False, include_exchange_rates=False, include_benchmarks=False,
        include_news=False, include_volatility_events=False,
    )
    service = PortfolioManagerService()
    with patch.object(service.data_loader, 'load_stock_data_parallel', AsyncMock(return_value=frames)), \
         patch.object(service.data_loader, 'load_ticker_currencies', AsyncMock(return_value=currencies or {s: 'USD' for s in frames})), \
         patch.object(service.data_loader, 'load_exchange_rates', AsyncMock(return_value=rates or {})):
        return asyncio.run(service.run_buy_and_hold_portfolio_backtest(request))['data']


@pytest.mark.parametrize('start,end,holiday,expected,dates', [
    ('2024-01-03', '2024-03-06', '2024-02-07', 3000, ['2024-01-03', '2024-02-08', '2024-03-06']),
    ('2024-01-03', '2024-03-06', '2024-03-06', 2000, ['2024-01-03', '2024-02-07']),
    ('2024-01-01', '2024-12-02', '2024-01-01', 12000, None),
])
def test_holidays_do_not_shift_dca_calendar_or_create_losses(start, end, holiday, expected, dates):
    index = pd.bdate_range(start, end).difference(pd.DatetimeIndex([holiday]))
    data = run_portfolio({'AAA': pd.DataFrame({'Close': 100.0}, index=index)}, start, end, dca=True)
    stats = data['portfolio_statistics']
    assert stats['Initial_Value'] == expected
    assert stats['Final_Value'] == pytest.approx(expected)
    assert stats['Total_Return'] == pytest.approx(0)
    assert data['individual_results'][0]['final_equity'] == pytest.approx(expected)
    assert data['individual_results'][0]['trades'] == expected / 1000
    if dates:
        assert [t['EntryTime'][:10] for t in data['strategy_details']['AAA']['trade_log']] == dates


@pytest.mark.parametrize('fee,currency,expected', [(0.01, 'USD', 990), (0, 'KRW', 500)])
def test_individual_results_use_executed_usd_values(fee, currency, expected):
    index = pd.bdate_range('2024-01-01', '2024-03-29')
    frame = pd.DataFrame({'Close': 100 if currency == 'USD' else 100000}, index=index)
    rates = {'KRW': {day.date(): 1000 if pos == 0 else 2000 for pos, day in enumerate(index)}}
    data = run_portfolio({'AAA': frame}, '2024-01-01', '2024-03-29', fee=fee,
                         currencies={'AAA': currency}, rates=rates)
    assert data['portfolio_statistics']['Final_Value'] == pytest.approx(expected)
    assert data['individual_results'][0]['final_equity'] == pytest.approx(expected)
    assert data['individual_returns']['AAA']['return'] == pytest.approx((expected / 1000 - 1) * 100)
    assert data['individual_returns']['AAA']['end_price'] == pytest.approx(100 if currency == 'USD' else 50)
    assert data['strategy_details']['AAA']['trade_log'][0]['Size'] == pytest.approx(10 * (1 - fee))


def test_rebalanced_individual_final_equities_reconcile_with_portfolio():
    index = pd.bdate_range('2023-01-02', '2023-02-03')
    frames = {'AAA': pd.DataFrame({'Close': 100 * 2.0 ** (np.arange(len(index)) // 5)}, index=index),
              'BBB': pd.DataFrame({'Close': 100.0}, index=index)}
    data = run_portfolio(frames, '2023-01-02', '2023-02-03', rebalance='weekly_1')
    assert data['portfolio_statistics']['Final_Value'] == pytest.approx(1000 * 1.5 ** 4)
    assert sum(row['final_equity'] for row in data['individual_results']) == pytest.approx(1000 * 1.5 ** 4)
    # Flat BBB earns no price profit even though rebalance sales fund its holdings.
    assert data['individual_returns']['BBB']['return'] == pytest.approx(0)
    assert data['individual_results'][0]['trades'] > 1


def test_holiday_delays_rebalance_execution_but_not_the_next_due_date():
    index = pd.bdate_range('2024-01-03', '2024-03-06').difference(pd.DatetimeIndex(['2024-02-07']))
    frames = {'AAA': pd.DataFrame({'Close': 100 + np.arange(len(index))}, index=index),
              'BBB': pd.DataFrame({'Close': 100.0}, index=index)}
    data = run_portfolio(frames, '2024-01-03', '2024-03-06', fee=.01, rebalance='monthly_1')
    assert [event['date'] for event in data['rebalance_history']] == ['2024-02-08', '2024-03-06']
    stats = data['portfolio_statistics']
    assert sum(row['final_equity'] for row in data['individual_results']) == pytest.approx(stats['Final_Value'])
    attributed_profit = sum(row['amount'] * row['return'] / 100 for row in data['individual_returns'].values())
    assert attributed_profit == pytest.approx(stats['Final_Value'] - stats['Initial_Value'])


@pytest.mark.parametrize('calculator', [PortfolioMetrics, PortfolioCalculator])
def test_flat_days_break_loss_streaks_and_sharpe_uses_arithmetic_returns(calculator):
    returns = pd.Series([0.0] + [0.1, -0.1] * 126, index=pd.bdate_range('2023-01-02', periods=253))
    frame = pd.DataFrame({'Portfolio_Value': (1 + returns).cumprod(), 'Daily_Return': returns})
    stats = calculator.calculate_portfolio_statistics(frame, 1000)
    assert stats['Sharpe_Ratio'] == pytest.approx(0, abs=1e-12)
    flat = frame.assign(Portfolio_Value=1.0, Daily_Return=0.0)
    assert calculator.calculate_portfolio_statistics(flat, 1000)['Max_Consecutive_Losses'] == 0
