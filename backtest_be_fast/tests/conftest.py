"""
pytest 설정 및 글로벌 픽스처
완전 오프라인 모킹 시스템으로 외부 의존성 제거
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import pandas as pd
import numpy as np

# 백엔드 앱을 Python 경로에 추가
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

from tests.fixtures.mock_data import MockStockDataGenerator


@pytest.fixture(scope="session", autouse=True)
def setup_offline_environment():
    """
    완전 오프라인 환경 설정
    모든 외부 의존성(yfinance, MySQL)을 모킹
    """
    # Mock 데이터 생성기 초기화 (고정 시드로 재현성 보장)
    mock_generator = MockStockDataGenerator(seed=42)
    
    def mock_ticker_factory(ticker_symbol):
        """티커별 Mock 객체 생성"""
        mock_ticker_instance = Mock()
        
        # 유효한 티커 목록
        valid_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX', 'ORCL', 'CRM']
        
        if ticker_symbol.upper() in valid_tickers:
            # 유효한 티커의 경우 - 동일한 시드로 재현성 보장
            mock_ticker_instance.info = mock_generator.generate_ticker_info(ticker_symbol)
            mock_ticker_instance.history.return_value = mock_generator.generate_ohlcv_data(ticker_symbol, seed=42)
        else:
            # 무효한 티커의 경우 빈 데이터 반환
            mock_ticker_instance.info = {}
            mock_ticker_instance.history.return_value = pd.DataFrame()
        
        return mock_ticker_instance
    
    def mock_download_func(ticker, start, end, group_by='ticker'):
        """yfinance.download 함수 모킹"""
        valid_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX', 'ORCL', 'CRM']
        
        if ticker.upper() in valid_tickers:
            return mock_generator.generate_ohlcv_data(ticker, seed=42)
        else:
            return pd.DataFrame()  # 무효한 티커는 빈 데이터
    
    def mock_load_ticker_data(ticker, start_date, end_date):
        """load_ticker_data 모킹"""
        valid_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX', 'ORCL', 'CRM']
        
        if ticker.upper() in valid_tickers:
            return mock_generator.generate_ohlcv_data(ticker, start_date, end_date, seed=42)
        else:
            return pd.DataFrame()
    
    def mock_save_ticker_data(ticker, data):
        """save_ticker_data 모킹 (아무것도 하지 않음)"""
        pass
    
    def mock_sqlalchemy_engine():
        """SQLAlchemy 엔진 및 연결 객체 완전 모킹"""
        mock_engine = Mock()
        mock_connection = Mock()
        
        # 연결 성공 시뮬레이션
        mock_engine.connect.return_value = mock_connection
        mock_connection.execute.return_value = Mock(fetchone=Mock(return_value=None))
        mock_connection.close.return_value = None
        
        return mock_engine
    
    def mock_get_engine():
        """_get_engine 함수 모킹"""
        return mock_sqlalchemy_engine()
    
    # yfinance, 데이터베이스, SQLAlchemy 엔진 모킹
    with patch('yfinance.Ticker', side_effect=mock_ticker_factory) as mock_ticker, \
         patch('yfinance.download', side_effect=mock_download_func) as mock_download, \
         patch('app.services.yfinance_db.load_ticker_data', side_effect=mock_load_ticker_data) as mock_load, \
         patch('app.services.yfinance_db.save_ticker_data', side_effect=mock_save_ticker_data) as mock_save, \
         patch('app.services.yfinance_db._get_engine', side_effect=mock_get_engine) as mock_engine_func, \
         patch('app.services.portfolio_service.load_ticker_data', side_effect=mock_load_ticker_data) as mock_portfolio_load, \
         patch('app.api.v1.endpoints.backtest.load_ticker_data', side_effect=mock_load_ticker_data) as mock_api_load:
        
        yield {
            'mock_ticker': mock_ticker,
            'mock_download': mock_download,
            'mock_load': mock_load,
            'mock_save': mock_save,
            'mock_engine': mock_engine_func,
            'mock_portfolio_load': mock_portfolio_load,
            'mock_api_load': mock_api_load,
            'mock_generator': mock_generator
        }


@pytest.fixture
def mock_data_generator():
    """Mock 데이터 생성기 픽스처 (고정 시드)"""
    return MockStockDataGenerator(seed=42)


@pytest.fixture
def sample_stock_data(mock_data_generator):
    """샘플 주식 데이터 픽스처"""
    return mock_data_generator.generate_ohlcv_data('AAPL')


@pytest.fixture
def sample_backtest_request():
    """샘플 백테스트 요청 픽스처"""
    from app.models.requests import BacktestRequest
    
    return BacktestRequest(
        ticker="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 6, 30),
        initial_cash=10000,
        strategy="sma_crossover",
        strategy_params={
            "short_window": 10,
            "long_window": 20
        }
    )


@pytest.fixture
def sample_portfolio_request():
    """샘플 포트폴리오 요청 픽스처"""
    # 포트폴리오 백테스트는 현재 지원되지 않으므로 일반 백테스트 요청으로 대체
    from app.models.requests import BacktestRequest
    
    return BacktestRequest(
        symbol="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 6, 30),
        initial_cash=10000.0,
        strategy="buy_and_hold",
        strategy_params={}
    )


@pytest.fixture
def fastapi_client():
    """FastAPI 테스트 클라이언트 픽스처"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    return TestClient(app)


@pytest.fixture
def client():
    """Legacy name for TestClient used by integration tests"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


# pytest 설정
def pytest_configure(config):
    """pytest 초기 설정"""
    # 경고 메시지 필터링
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)


def pytest_collection_modifyitems(config, items):
    """테스트 아이템 수정"""
    # 비동기 테스트 마킹
    for item in items:
        if "async" in item.name:
            item.add_marker(pytest.mark.asyncio)