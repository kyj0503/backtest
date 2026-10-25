"""Currency failures must not become successful USD calculations."""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.schemas.requests import BacktestRequest
from app.services.backtest_engine import BacktestEngine
from app.services.validation_service import ValidationService
from app.services.portfolio.portfolio_data_loader import PortfolioDataLoader
from app.services.portfolio.portfolio_price_alignment import pre_calculate_prices
from app.utils.currency_converter import CurrencyConverter

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('metadata', [{}, {'AAA': {}}, {'AAA': {'currency': None}}, {'AAA': {'currency': 'XXX'}}])
def test_missing_currency_metadata_is_rejected(metadata):
    repository = Mock()
    repository.get_tickers_info_batch.return_value = metadata
    with pytest.raises(ValueError, match='AAA'):
        asyncio.run(PortfolioDataLoader(repository).load_ticker_currencies(['AAA']))


@pytest.mark.parametrize('rate', [0.0, -1.0, float('nan'), float('inf')])
def test_invalid_fx_never_falls_back_to_parity(rate):
    index = pd.DatetimeIndex(['2024-01-01', '2024-01-02'])
    info = {'AAA': DcaStrategyInfo(symbol='AAA', allocation=1, asset_type='stock',
                                  investment_type='lump_sum', monthly_amount=1000)}
    with pytest.raises(ValueError, match='환율'):
        pre_calculate_prices(index, {'AAA': 1000}, {'AAA': pd.DataFrame({'Close': 100000}, index=index)},
                             info, {'AAA': 'KRW'}, {'KRW': {d.date(): rate for d in index}})


def test_future_fx_is_not_used_to_fill_earlier_stock_price():
    index = pd.DatetimeIndex(['2024-01-01', '2024-01-02'])
    repository = Mock()
    repository.load_stock_data.return_value = pd.DataFrame({'Close': [1300]}, index=index[1:])
    converter = CurrencyConverter()
    converter.stock_repository = repository
    with pytest.raises(ValueError, match='환율'):
        asyncio.run(converter.load_and_prepare_exchange_rates('KRW', '2024-01-01', '2024-01-02', index))


def test_cache_first_strategy_does_not_need_yahoo_info_and_measures_duration():
    index = pd.bdate_range('2023-01-02', '2023-04-03')
    frame = pd.DataFrame({'Open': 100.0, 'High': 101.0, 'Low': 99.0, 'Close': 100.0, 'Volume': 1000}, index=index)
    repository = Mock()
    repository.get_stock_data = AsyncMock(return_value=frame)
    fetcher = Mock()
    fetcher.validate_ticker.side_effect = AssertionError('Cached prices must not call Yahoo metadata')
    engine = BacktestEngine(data_repository=repository,
                            validation_service_instance=ValidationService(data_fetcher_instance=fetcher))
    request = BacktestRequest(ticker='AAA', start_date='2023-01-02', end_date='2023-04-03',
                              initial_cash=1000, strategy='sma_strategy', commission=0)
    with patch.object(engine, '_convert_to_usd', AsyncMock(return_value=frame)):
        result = asyncio.run(engine.run_backtest(request))
    fetcher.validate_ticker.assert_not_called()
    repository.get_stock_data.assert_awaited_once()
    assert 0 < result.execution_time_seconds < 10
    assert result.execution_time_seconds != 0.5


@pytest.mark.parametrize('missing_metadata', [False, True])
def test_real_http_route_uses_actual_funding_and_rejects_missing_currency(missing_metadata):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.v1.endpoints import backtest as endpoint

    index = pd.bdate_range('2024-01-03', '2024-03-05')
    frame = pd.DataFrame({'Close': 100.0}, index=index)
    repository = Mock()
    repository.load_stock_data.return_value = frame
    repository.get_tickers_info_batch.return_value = {} if missing_metadata else {
        'AAA': {'currency': 'USD', 'first_trade_date': '2000-01-01'}}
    loader = PortfolioDataLoader(repository)
    with patch.object(endpoint, 'get_stock_repository', return_value=repository), \
         patch.object(endpoint.portfolio_manager_service, 'data_loader', loader), TestClient(app) as client:
        response = client.post('/api/v1/backtest', json={
            'portfolio': [{'symbol': 'AAA', 'amount': 1000, 'investment_type': 'dca', 'dca_frequency': 'monthly_1'}],
            'start_date': '2024-01-03', 'end_date': '2024-03-06', 'strategy': 'buy_hold_strategy',
            'commission': 0, 'rebalance_frequency': 'none',
            'include_stock_data': False, 'include_exchange_rates': False, 'include_benchmarks': False,
            'include_news': False, 'include_volatility_events': False,
        })
    assert response.status_code == (422 if missing_metadata else 200), response.text
    if not missing_metadata:
        stats = response.json()['data']['portfolio_statistics']
        assert stats['Initial_Value'] == 2000
        assert stats['Final_Value'] == 2000
        assert stats['Total_Return'] == 0
