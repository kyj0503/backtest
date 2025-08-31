"""
백엔드 유닛 테스트를 위한 설정과 픽스처

완전 오프라인 모킹 시스템:
✅ yfinance API 호출 없음
✅ 데이터베이스 연결 없음  
✅ 네트워크 의존성 제거
✅ 일관된 테스트 결과 보장
"""
import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from app.main import app
from app.core.custom_exceptions import DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError

# 완전 오프라인 모킹 데이터 import
from tests.fixtures.mock_data import (
    MockYFinanceTicker,
    mock_yf_download, 
    get_mock_stock_data,
    get_mock_stock_info,
    MOCK_DATASETS
)


@pytest.fixture(scope="session", autouse=True)
def mock_database():
    """테스트 환경에서 데이터베이스 연결을 모킹"""
    with patch('app.services.yfinance_db._get_engine') as mock_engine, \
         patch('app.services.yfinance_db.save_ticker_data') as mock_save, \
         patch('app.services.yfinance_db.load_ticker_data') as mock_load:
        
        # 데이터베이스 연결 없이 None 반환
        mock_engine.return_value = None
        mock_save.return_value = 0  # 저장된 행 수
        mock_load.return_value = None  # 캐시된 데이터 없음
        
        yield {
            'engine': mock_engine,
            'save': mock_save,
            'load': mock_load
        }


@pytest.fixture
def mock_api_services():
    """API 테스트용 서비스 모킹 - 오프라인 데이터 사용"""
    with patch('app.services.backtest_service.BacktestService.generate_chart_data') as mock_chart, \
         patch('app.services.portfolio_service.PortfolioBacktestService.run_portfolio_backtest') as mock_portfolio:
        
        # 모킹된 차트 데이터 (실제 구조 반영)
        mock_chart_response = {
            "ohlc_data": [
                {"date": "2023-01-01", "open": 150.0, "high": 155.0, "low": 149.0, "close": 152.0, "volume": 1000000}
            ],
            "equity_data": [
                {"date": "2023-01-01", "equity": 10000, "return_pct": 0.0}
            ],
            "trade_markers": [],
            "indicators": {},
            "summary_stats": {
                "total_return_pct": 15.5,
                "win_rate_pct": 66.7,
                "sharpe_ratio": 1.2
            }
        }
        mock_chart.return_value = mock_chart_response
        
        # 모킹된 포트폴리오 백테스트 결과
        mock_portfolio_response = {
            "status": "success",
            "data": {
                "portfolio_statistics": {
                    "total_return": 15.5,
                    "annual_return": 12.3,
                    "volatility": 18.7,
                    "sharpe_ratio": 0.85
                }
            }
        }
        mock_portfolio.return_value = mock_portfolio_response
        
        yield {
            'chart': mock_chart,
            'portfolio': mock_portfolio
        }


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
            {"symbol": "AAPL", "amount": 5000},
            {"symbol": "GOOGL", "amount": 3000},
            {"symbol": "MSFT", "amount": 2000}
        ],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "strategy": "buy_and_hold",
        "rebalance_frequency": "monthly"
    }


class MockingHelper:
    """
    완전 오프라인 모킹 헬퍼
    
    ⚠️ 주의: 이 클래스는 yfinance API를 전혀 사용하지 않습니다!
    ✅ 수학적 알고리즘으로 생성된 모의 데이터만 사용합니다.
    """
    
    @staticmethod
    def create_mock_dataframe(ticker: str = "AAPL", scenario: str = "normal"):
        """오프라인 모의 DataFrame 생성"""
        return get_mock_stock_data(ticker, scenario)
    
    @staticmethod
    def create_empty_dataframe():
        """빈 DataFrame 생성"""
        return get_mock_stock_data("INVALID", "empty")
    
    @staticmethod
    def create_mock_stock_info(ticker: str = "AAPL"):
        """오프라인 모의 주식 정보 생성"""
        return get_mock_stock_info(ticker)


@pytest.fixture
def mocking_helper():
    """모킹 헬퍼 픽스처"""
    return MockingHelper
