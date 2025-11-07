"""
Pytest Configuration and Global Fixtures

이 파일은 모든 테스트에서 공통으로 사용하는 fixtures를 정의합니다.
단위 테스트는 DB 없이 실행 가능하도록 설계되었습니다.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator, Optional
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from datetime import datetime

# Optional imports for integration tests
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.orm import sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    from httpx import AsyncClient
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# 앱 임포트는 테스트 실행 시에만
try:
    from app.main import app
    from app.core.config import Settings
except ImportError:
    app = None
    Settings = None


# ============================================================================
# 환경 설정
# ============================================================================

@pytest.fixture(scope="session")
def test_settings():
    """테스트용 설정"""
    if Settings is None:
        pytest.skip("Settings not available")

    return Settings(
        DATABASE_URL="mysql+aiomysql://test:test@localhost:3306/test_backtest",
        SECRET_KEY="test-secret-key-for-testing-only",
        DEBUG=True,
    )


# ============================================================================
# 데이터베이스 Fixtures (Integration Tests Only)
# ============================================================================

@pytest.fixture(scope="session")
async def db_engine(test_settings):
    """데이터베이스 엔진 (세션 스코프) - Integration tests only"""
    if not HAS_SQLALCHEMY:
        pytest.skip("SQLAlchemy not installed")

    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 (각 테스트마다 새로운 세션) - Integration tests only"""
    if not HAS_SQLALCHEMY:
        pytest.skip("SQLAlchemy not installed")

    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()  # 테스트 후 롤백


# ============================================================================
# HTTP Client Fixtures (Integration Tests Only)
# ============================================================================

@pytest.fixture
async def client() -> AsyncGenerator:
    """테스트용 HTTP 클라이언트 - Integration tests only"""
    if not HAS_HTTPX:
        pytest.skip("httpx not installed")

    if app is None:
        pytest.skip("FastAPI app not available")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Mock Fixtures (Unit Tests)
# ============================================================================

@pytest.fixture
def mock_data_repository():
    """Mock 데이터 리포지토리"""
    repo = Mock()
    repo.get_price_data = AsyncMock(return_value=[
        {
            "date": datetime(2023, 1, 1),
            "open": Decimal("150.00"),
            "high": Decimal("155.00"),
            "low": Decimal("149.00"),
            "close": Decimal("152.00"),
            "volume": 1000000
        },
        {
            "date": datetime(2023, 1, 2),
            "open": Decimal("152.00"),
            "high": Decimal("158.00"),
            "low": Decimal("151.00"),
            "close": Decimal("157.00"),
            "volume": 1200000
        },
    ])
    repo.save_price_data = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_yfinance_service():
    """Mock Yahoo Finance 서비스"""
    service = Mock()
    service.download = AsyncMock(return_value={
        "dates": ["2023-01-01", "2023-01-02"],
        "close": [150.0, 155.0],
        "volume": [1000000, 1200000]
    })
    return service


# ============================================================================
# 테스트 데이터 Fixtures
# ============================================================================

@pytest.fixture
def sample_backtest_request():
    """샘플 백테스트 요청 데이터"""
    return {
        "symbol": "AAPL",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 10000.0,
        "strategy": "buy_and_hold",
        "parameters": {}
    }


@pytest.fixture
def sample_portfolio_data():
    """샘플 포트폴리오 데이터"""
    return {
        "initial_cash": Decimal("10000.00"),
        "positions": [],
        "trades": []
    }


@pytest.fixture
def sample_price_data():
    """샘플 가격 데이터"""
    return [
        {
            "date": "2023-01-01",
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 152.0,
            "volume": 1000000
        },
        {
            "date": "2023-01-02",
            "open": 152.0,
            "high": 158.0,
            "low": 151.0,
            "close": 157.0,
            "volume": 1200000
        },
        {
            "date": "2023-01-03",
            "open": 157.0,
            "high": 160.0,
            "low": 156.0,
            "close": 159.0,
            "volume": 1100000
        }
    ]


# ============================================================================
# 유틸리티 Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """시간을 고정하는 fixture"""
    try:
        from freezegun import freeze_time as ft
        return ft
    except ImportError:
        pytest.skip("freezegun not installed")


@pytest.fixture
def faker():
    """Faker 인스턴스"""
    try:
        from faker import Faker
        return Faker()
    except ImportError:
        pytest.skip("faker not installed")


# ============================================================================
# 테스트 마커 Auto-use Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_mocks(request):
    """각 테스트 후 모든 mock 리셋"""
    yield
    # 테스트 후 정리 작업


@pytest.fixture(autouse=True)
def log_test_name(request):
    """테스트 이름 로깅 (verbose 모드에서만)"""
    if request.config.getoption("verbose") > 0:
        print(f"\n▶ Running: {request.node.name}")
    yield
    if request.config.getoption("verbose") > 0:
        print(f"✓ Completed: {request.node.name}")
