from unittest.mock import Mock

import pandas as pd
import pytest

from app.core.exceptions import YfinanceRateLimitError


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
