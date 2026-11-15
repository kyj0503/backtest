from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from app.core.exceptions import YfinanceRateLimitError
from tests.unit.test_portfolio_manager_response_snapshot import (
    _frame, _request, _run_strategy, _strategy_result,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('failed_result', [RuntimeError('unavailable'), None, SimpleNamespace()])
def test_strategy_excludes_failed_amount_and_reports_warning(failed_result):
    stock = {'symbol': 'AAPL', 'amount': 1000.0}
    value = _strategy_result(_frame(2), 1000.0, total_trades=1,
                             win_rate_pct=100, sharpe=1, mdd=-1)
    baseline = _run_strategy(_request([stock], strategy='sma_strategy'), {'AAPL': value})['data']
    actual = _run_strategy(
        _request([stock, {'symbol': 'ZZZZ', 'amount': 1000.0}], strategy='sma_strategy'),
        {'AAPL': value, 'ZZZZ': failed_result},
    )['data']
    assert actual['portfolio_statistics']['Initial_Value'] == 1000.0
    assert actual['portfolio_statistics']['Total_Return'] == pytest.approx(
        baseline['portfolio_statistics']['Total_Return'])
    assert actual['individual_returns']['AAPL']['weight'] == 1.0
    assert len(actual['warnings']) == 1 and 'ZZZZ' in actual['warnings'][0]


@pytest.mark.parametrize('mode,values', [('amount', [1000., 500., 200., 100.]), ('weight', [60., 20., 15., 5.])])
def test_strategy_preserves_duplicate_cash_names_and_stock_collision(mode, values):
    request = _request([
        {'symbol': 'A', mode: values[0]},
        {'symbol': 'A', mode: values[1], 'asset_type': 'cash'},
        {'symbol': 'A', mode: values[2], 'asset_type': 'cash'},
        {'symbol': 'A__cash_2', mode: values[3], 'asset_type': 'cash'},
    ], strategy='sma_strategy')
    actual = _run_strategy(request, {'A': lambda amount: _strategy_result(
        _frame(2), amount, total_trades=1, win_rate_pct=100, sharpe=1, mdd=-1)})['data']
    items = actual['individual_returns']
    assert len(items) == 4
    assert sum(item['amount'] for item in items.values()) == pytest.approx(sum(values))
    assert sum(item['weight'] for item in items.values()) == pytest.approx(1.0)
    assert actual['portfolio_statistics']['Initial_Value'] == pytest.approx(sum(values))
    assert sorted(item['amount'] for key, item in items.items() if key != 'A') == sorted(values[1:])


def test_strategy_rejects_zero_remaining_allocation_after_failed_stock():
    request = _request([
        {'symbol': 'ZZZZ', 'weight': 100.0},
        {'symbol': 'CASH', 'weight': 0.0, 'asset_type': 'cash'},
    ], strategy='sma_strategy')
    with pytest.raises(ValueError, match='성공한 종목의 투자금액이 없습니다'):
        _run_strategy(request, {'ZZZZ': RuntimeError('unavailable')})


@pytest.mark.parametrize('first_error', [None, YfinanceRateLimitError('quota'), RuntimeError('fetch failed')])
def test_daily_update_uses_repository_and_keeps_processing_after_fetch_error(monkeypatch, first_error):
    from scripts import daily_price_update as daily

    connection = Mock()
    connection.execute.return_value.fetchall.return_value = [('AAPL',), ('MSFT',)]
    engine = Mock()
    engine.connect.return_value = connection
    monkeypatch.setattr(daily.DatabaseConnectionManager, 'get_engine', lambda: engine)
    repository = Mock()
    monkeypatch.setattr(daily, 'YFinanceRepository', lambda: repository)
    frame = pd.DataFrame({'Close': [100.]})
    fetch = Mock(side_effect=[first_error or frame, frame])
    monkeypatch.setattr(daily.data_fetcher, 'fetch_stock_data', fetch)
    monkeypatch.setattr(daily.time, 'sleep', lambda _: None)

    daily.update_all_stock_data()

    assert fetch.call_count == 2
    assert repository.save_ticker_data.call_count == (1 if first_error else 2)
    repository.save_ticker_data.assert_any_call('MSFT', frame)
    connection.close.assert_called_once()
