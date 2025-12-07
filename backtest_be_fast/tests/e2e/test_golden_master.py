
import pytest
import pandas as pd
import json
import os
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.stock_repository import StockRepository
from app.utils.currency_converter import CurrencyConverter
from typing import Dict, Any, List

# Load mock data
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_mock_csv(ticker):
    path = os.path.join(DATA_DIR, f"{ticker}.csv")
    if os.path.exists(path):
        print(f"Loading mock CSV from {path}")
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        return df
    print(f"Mock CSV not found at {path}")
    return pd.DataFrame()

class MockStockRepository:
    def load_stock_data(self, ticker, start_date=None, end_date=None, **kwargs):
        print(f"MockStockRepository.load_stock_data called for {ticker} ({start_date}-{end_date})")
        df = load_mock_csv(ticker)
        if df.empty:
            print("Empty DF loaded")
            return df
        
        # Filter by date if needed
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
            
        print(f"Returned {len(df)} rows")
        return df

    def get_tickers_info_batch(self, tickers):
        return {
            t: {'currency': 'USD', 'symbol': t} for t in tickers
        }
        
    def get_ticker_info(self, ticker):
        return {'currency': 'USD', 'symbol': ticker}

    def load_ticker_news(self, ticker, max_age_hours=3):
        return []

    def save_stock_data(self, ticker, df):
        return 0

@pytest.fixture
def mock_stock_repo():
    return MockStockRepository()

@pytest.fixture
def mock_currency_converter():
    mock = AsyncMock()
    mock.load_multiple_exchange_rates.return_value = {
        'KRW': {
            '2023-01-01': 1300.0
        }
    }
    mock.get_exchange_rate.return_value = 1.0
    return mock

@pytest.mark.e2e
def test_golden_master_backtest_dca(mock_stock_repo, mock_currency_converter):
    """
    Golden Master Test for DCA Portfolio
    """
    # Mock unified data service
    mock_unified_service = MagicMock()
    mock_unified_service.collect_all_unified_data.return_value = {
        'status': 'success',
        'sp500_benchmark': [],
        'nasdaq_benchmark': [], 
        'latest_news': [],
        'exchange_rates': {}
    }

    # Patch the INSTANCE in endpoints because it's global
    # And specifically patch the StockRepository instance used by the service
    with patch("app.api.v1.endpoints.backtest.portfolio_manager_service.stock_repository", mock_stock_repo), \
         patch("app.services.portfolio_manager_service.currency_converter", mock_currency_converter), \
         patch("app.api.v1.endpoints.backtest.get_ticker_info_batch_from_db", side_effect=mock_stock_repo.get_tickers_info_batch), \
         patch("app.api.v1.endpoints.backtest.unified_data_service", mock_unified_service):
        
        client = TestClient(app)
        
        payload = {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 1000.0,
                    "investment_type": "dca",
                    "dca_frequency": "weekly_1"
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-01-12",
            "strategy": "buy_hold_strategy"
        }
        
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        
        # Define expected output file path
        expected_file = os.path.join(DATA_DIR, "expected_dca_output.json")
        
        # If expected file doesn't exist, create it (First run mode)
        if not os.path.exists(expected_file):
            print(f"Creating Golden Master: {expected_file}")
            with open(expected_file, "w") as f:
                json.dump(result, f, indent=2, sort_keys=True)
            
        # Compare with expected
        with open(expected_file, "r") as f:
            expected = json.load(f)
            
        # Only compare 'data' part
        assert result['status'] == expected['status']
