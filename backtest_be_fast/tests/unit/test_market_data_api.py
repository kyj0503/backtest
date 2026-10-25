"""Feed reads cannot trigger simulations or consume simulation capacity."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.endpoints import backtest, market_data
from app.services.backtest_runner import BacktestJobRunner

pytestmark = pytest.mark.unit
QUERY = [('symbols', 'AAPL'), ('symbols', 'MSFT'),
         ('start_date', '2023-01-01'), ('end_date', '2023-06-30')]


@pytest.fixture
def runner(tmp_path, monkeypatch):
    job = BacktestJobRunner(
        slot_dir=str(tmp_path / 'feeds'), max_concurrent=1, per_client=1,
        queue_timeout=0.02, exec_timeout=1, cancel_grace=0.2,
    )
    monkeypatch.setattr(market_data, 'get_market_data_runner', lambda: job)
    yield job
    job.shutdown()


def test_market_data_is_independent_of_simulation(monkeypatch, runner):
    collector = MagicMock(return_value={
        'sp500_benchmark': [{'close': 100}, {'close': 110}],
        'latest_news': {'AAPL': []}, 'supplemental_status': {'news': 'empty'},
    })
    simulation = AsyncMock(side_effect=AssertionError('must not run'))
    monkeypatch.setattr(market_data.unified_data_service, 'collect_all_unified_data', collector)
    monkeypatch.setattr(backtest.portfolio_manager_service, 'run_portfolio_backtest', simulation)
    with TestClient(app) as client:
        response = client.get('/api/v1/market-data', params=QUERY)
    assert response.status_code == 200, response.text
    assert response.json()['data']['sp500_total_return_pct'] == pytest.approx(10)
    assert collector.call_args.kwargs['symbols'] == ['AAPL', 'MSFT']
    assert collector.call_args.kwargs['timeout_seconds'] > 0
    simulation.assert_not_called()


@pytest.mark.parametrize('params', [
    [('symbols', '../secret'), ('start_date', '2023-01-01'), ('end_date', '2023-06-30')],
    [('start_date', '2023-06-30'), ('end_date', '2023-01-01')],
    [('start_date', '2023-01-01'), ('end_date', '2099-01-01')],
    [('start_date', '2000-01-01'), ('end_date', '2023-01-01')],
    [('start_date', '2023-01-01'), ('end_date', '2023-06-30')] + [('symbols', 'AAPL')] * 21,
])
def test_invalid_read_is_rejected_before_io(params, monkeypatch):
    collector = MagicMock(side_effect=AssertionError('must not fetch'))
    monkeypatch.setattr(market_data.unified_data_service, 'collect_all_unified_data', collector)
    with TestClient(app) as client:
        response = client.get('/api/v1/market-data', params=params)
    assert response.status_code == 422
    collector.assert_not_called()


def test_all_flags_disabled_skips_all_reference_io(monkeypatch):
    repo = MagicMock()
    repo.get_tickers_info_batch.return_value = {}
    monkeypatch.setattr(backtest, 'get_stock_repository', lambda: repo)
    monkeypatch.setattr(backtest.portfolio_manager_service, 'run_portfolio_backtest',
                        AsyncMock(return_value={'status': 'success', 'data': {'portfolio_statistics': {'Total_Return': 12}}}))
    collector = MagicMock(side_effect=AssertionError('no reference I/O in simulation'))
    monkeypatch.setattr(backtest.unified_data_service, 'collect_all_unified_data', collector)
    payload = {
        'portfolio': [{'symbol': 'AAPL', 'amount': 1000}],
        'start_date': '2023-01-01', 'end_date': '2023-06-30',
        **{f'include_{section}': False for section in
           ('news', 'benchmarks', 'exchange_rates', 'stock_data', 'volatility_events')},
    }
    with TestClient(app) as client:
        response = client.post('/api/v1/backtest', json=payload)
    assert response.status_code == 200, response.text
    assert response.json()['data']['portfolio_statistics']['Total_Return'] == 12
    assert set(response.json()['data']['supplemental_status'].values()) == {'skipped'}
    collector.assert_not_called()


def test_busy_feed_queue_does_not_claim_a_simulation_slot(monkeypatch, runner):
    slot = runner.global_pool.try_acquire()
    assert slot is not None
    collector = MagicMock(side_effect=AssertionError('queued request must not start'))
    monkeypatch.setattr(market_data.unified_data_service, 'collect_all_unified_data', collector)
    try:
        with TestClient(app) as client:
            response = client.get('/api/v1/market-data', params=QUERY)
        assert response.status_code == 503
        assert response.headers.get('retry-after')
        collector.assert_not_called()
    finally:
        slot.release()
