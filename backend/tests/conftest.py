"""
백엔드 유닛 테스트를 위한 설정과 픽스처
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from app.main import app
from app.core.custom_exceptions import DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """테스트 세션에서 사용할 이벤트 루프 설정"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_yfinance_success():
    """yfinance 성공 케이스 모킹"""
    import pandas as pd
    import numpy as np
    
    # 가짜 주식 데이터 생성
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    data = {
        'Open': np.random.uniform(90, 110, len(dates)),
        'High': np.random.uniform(100, 120, len(dates)),
        'Low': np.random.uniform(80, 100, len(dates)),
        'Close': np.random.uniform(95, 115, len(dates)),
        'Volume': np.random.uniform(1000000, 5000000, len(dates))
    }
    
    mock_df = pd.DataFrame(data, index=dates)
    return mock_df


@pytest.fixture
def mock_yfinance_empty():
    """yfinance 빈 데이터 모킹"""
    import pandas as pd
    return pd.DataFrame()


@pytest.fixture
def sample_backtest_request():
    """백테스트 요청 샘플 데이터"""
    return {
        "ticker": "AAPL",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "strategy": "buy_and_hold",
        "initial_cash": 10000,
        "commission": 0.002
    }


@pytest.fixture
def sample_portfolio_request():
    """포트폴리오 백테스트 요청 샘플 데이터"""
    return {
        "portfolio": [
            {"ticker": "AAPL", "amount": 5000},
            {"ticker": "GOOGL", "amount": 3000},
            {"ticker": "MSFT", "amount": 2000}
        ],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "cash": 10000,
        "commission": 0.002,
        "rebalance_frequency": "monthly"
    }


class MockException:
    """테스트용 예외 클래스들"""
    
    @staticmethod
    def data_not_found():
        return DataNotFoundError("INVALID", "2023-01-01", "2023-12-31")
    
    @staticmethod
    def invalid_symbol():
        return InvalidSymbolError("INVALID")
    
    @staticmethod
    def rate_limit():
        return YFinanceRateLimitError()
