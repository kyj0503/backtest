"""Each feed owns its data, failures and retries; calculation stays separate."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.endpoints import backtest, market_data
from app.core.cancellation import BacktestCancelled, CancelToken, bind_token

pytestmark = pytest.mark.unit
PERIOD = [('start_date', '2023-01-01'), ('end_date', '2023-06-30')]
QUERIES = {
    'prices': PERIOD + [('symbols', 'aapl'), ('symbols', 'MSFT'), ('symbols', 'AAPL')],
    'exchange-rates': PERIOD,
    'benchmarks': PERIOD,
    'news': [('symbols', 'AAPL'), ('symbols', 'MSFT'), ('limit', '7')],
}


@pytest.fixture
def runner(tmp_path, monkeypatch):
    factory = market_data.get_market_data_runner
    factory.cache_clear()
    monkeypatch.setattr(market_data.settings, 'backtest_slot_dir', str(tmp_path / 'jobs'))
    monkeypatch.setattr(market_data.settings, 'market_data_queue_timeout_seconds', 0.05)
    job = factory()
    yield job
    job.shutdown()
    factory.cache_clear()


def reference_data():
    data = market_data.unified_data_service.empty_unified_data(['AAPL', 'MSFT'], 'ok')
    data['sp500_benchmark'] = [{'close': 100}, {'close': 110}]
    return data


@pytest.mark.parametrize('section', QUERIES)
def test_reads_only_requested_resource(section, monkeypatch, runner):
    collector = MagicMock(return_value=reference_data())
    simulation = AsyncMock(side_effect=AssertionError('must not calculate'))
    monkeypatch.setattr(market_data.unified_data_service, 'collect_all_unified_data', collector)
    monkeypatch.setattr(backtest.portfolio_manager_service, 'run_portfolio_backtest', simulation)
    with TestClient(app) as client:
        response = client.get('/api/v1/' + section, params=QUERIES[section])
    assert response.status_code == 200, response.text
    data = response.json()['data']
    expected = set(market_data.READ_FIELDS[section]) | {'supplemental_status'}
    if section == 'benchmarks':
        expected.add('sp500_total_return_pct')
        assert data['sp500_total_return_pct'] == pytest.approx(10)
    assert set(data) == expected
    assert set(data['supplemental_status']) == set(market_data.READ_STATUSES[section])
    options = collector.call_args.kwargs
    assert options['include_ticker_info'] == (section == 'prices')
    assert options['include_stock_data'] == (section == 'prices')
    assert options['include_volatility_events'] == (section == 'prices')
    assert options['include_exchange_rates'] == (section == 'exchange-rates')
    assert options['include_benchmarks'] == (section == 'benchmarks')
    assert options['include_news'] == (section == 'news')
    assert options['symbols'] == (['AAPL', 'MSFT'] if section in ('prices', 'news') else [])
    if section == 'news':
        assert options['start_date'] is None and options['end_date'] is None
        assert options['news_display_count'] == 7
    simulation.assert_not_called()


@pytest.mark.parametrize(('section', 'params'), [
    ('prices', PERIOD),
    ('prices', PERIOD + [('symbols', '../secret')]),
    ('prices', PERIOD + [('symbols', 'AAPL')] * 21),
    ('prices', [('symbols', 'AAPL'), ('start_date', '2023-06-30'), ('end_date', '2023-01-01')]),
    ('exchange-rates', [('start_date', '2000-01-01'), ('end_date', '2023-01-01')]),
    ('benchmarks', [('start_date', '2023-01-01'), ('end_date', '2099-01-01')]),
    ('news', []),
    ('news', [('symbols', '../secret')]),
    ('news', [('symbols', 'AAPL')] * 21),
    ('news', [('symbols', 'AAPL'), ('limit', '0')]),
    ('news', [('symbols', 'AAPL'), ('limit', '21')]),
    ('news', [('symbols', 'AAPL'), ('start_date', '2023-01-01')]),
    ('exchange-rates', PERIOD + [('symbols', 'AAPL')]),
])
def test_invalid_read_is_rejected_before_io(section, params, monkeypatch):
    collector = MagicMock(side_effect=AssertionError('must not fetch'))
    monkeypatch.setattr(market_data.unified_data_service, 'collect_all_unified_data', collector)
    with TestClient(app) as client:
        response = client.get('/api/v1/' + section, params=params)
    assert response.status_code == 422, response.text
    collector.assert_not_called()


def test_four_resources_can_run_concurrently_from_same_ip(monkeypatch, runner):
    barrier = Barrier(4)

    def collect(**kwargs):
        barrier.wait(timeout=5)
        return reference_data()

    monkeypatch.setattr(market_data.unified_data_service, 'collect_all_unified_data', collect)
    assert runner.max_concurrent == 4 and runner.per_client == 4
    with TestClient(app, client=('198.51.100.20', 50000)) as client:
        with ThreadPoolExecutor(max_workers=4) as executor:
            responses = list(executor.map(
                lambda section: client.get('/api/v1/' + section, params=QUERIES[section]), QUERIES))
    assert [response.status_code for response in responses] == [200] * 4


@pytest.mark.parametrize('section', QUERIES)
def test_all_reads_share_the_global_capacity(section, monkeypatch, runner):
    slots = [runner.global_pool.try_acquire() for _ in range(runner.max_concurrent)]
    assert all(slots)
    collector = MagicMock(side_effect=AssertionError('busy read must not start'))
    monkeypatch.setattr(market_data.unified_data_service, 'collect_all_unified_data', collector)
    try:
        with TestClient(app) as client:
            response = client.get('/api/v1/' + section, params=QUERIES[section])
        assert response.status_code == 503
        assert response.headers.get('retry-after')
        collector.assert_not_called()
    finally:
        for slot in slots:
            slot.release()


def test_news_does_not_fetch_metadata_or_require_dates(monkeypatch):
    service = market_data.unified_data_service
    metadata = MagicMock(side_effect=AssertionError('news must not fetch metadata'))
    monkeypatch.setattr(service, 'collect_ticker_info', metadata)
    monkeypatch.setattr(service, 'collect_latest_news', lambda *args: {'AAPL': [{'title': 'news'}]})
    data = service.collect_all_unified_data(
        ['AAPL'], include_ticker_info=False, include_stock_data=False,
        include_volatility_events=False, include_exchange_rates=False, include_benchmarks=False,
    )
    assert data['latest_news']['AAPL'][0]['title'] == 'news'
    metadata.assert_not_called()


def test_news_stops_before_cache_write_and_next_symbol_after_cancel(monkeypatch):
    service = market_data.unified_data_service
    token = CancelToken()
    news = MagicMock()
    news.search_news.side_effect = lambda *args, **kwargs: (token.cancel('test') or [{'title': 'news'}])
    repo = MagicMock()
    repo.load_ticker_news.return_value = []
    monkeypatch.setattr(service, 'news_service', news)
    monkeypatch.setattr(service, 'stock_repo', repo)
    with bind_token(token), pytest.raises(BacktestCancelled):
        service.collect_latest_news(['AAPL', 'MSFT'])
    assert news.search_news.call_count == 1
    repo.save_ticker_news.assert_not_called()


def test_all_flags_disabled_skips_reference_io(monkeypatch):
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
