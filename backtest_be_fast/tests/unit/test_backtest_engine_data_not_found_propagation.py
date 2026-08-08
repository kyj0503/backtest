"""DataNotFoundError가 BacktestEngine.run_backtest()에서 500으로 재래핑되지 않고
404로 그대로 전파되는지 확인하는 회귀 테스트 (P2-11 관련).

배경: yfinance_repository.load_ticker_data()가 "데이터 없음"을 더 이상 bare
ValueError가 아닌 DataNotFoundError로 발생시키도록 수정했다 (P2-11). 이 테스트는
BacktestEngine.run_backtest()의 예외 처리기(~line 101-123)가 이 변경을 별도 수정
없이 올바르게 처리하는지 확인한다.

run_backtest()의 except 블록은 다음 순서로 검사한다:
    1) isinstance(e, HTTPException) → 그대로 재발생
    2) isinstance(e, ValidationError) → 그대로 재발생
    3) isinstance(e, InvalidSymbolError) → 그대로 재발생
    4) 그 외 → HTTPException(500)으로 래핑

DataNotFoundError는 HTTPException의 서브클래스이므로 1번 분기에서 이미 원래
상태코드(404)를 보존한 채 재발생한다. 따라서 이 파일이 확인하는 것은 "핸들러
수정이 필요 없다"는 결론에 대한 증거이며, 실제 수정은 yfinance_repository.py
에서만 이루어졌다.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException

from app.core.exceptions import DataNotFoundError
from app.services.backtest_engine import BacktestEngine
from app.schemas.requests import BacktestRequest, StrategyType


pytestmark = pytest.mark.unit


@pytest.fixture
def mock_data_repository():
    repo = Mock()
    repo.get_stock_data = AsyncMock()
    return repo


@pytest.fixture
def mock_validation_service():
    service = Mock()
    service.validate_backtest_request = Mock()
    return service


@pytest.fixture
def backtest_request():
    return BacktestRequest(
        ticker='NODATA',
        start_date='2023-01-01',
        end_date='2023-02-19',
        initial_cash=10000.0,
        strategy=StrategyType.BUY_HOLD_STRATEGY,
        commission=0.002
    )


class TestDataNotFoundErrorPropagatesAs404:
    @pytest.mark.asyncio
    async def test_data_not_found_error_is_not_rewrapped_as_500(
        self, mock_data_repository, mock_validation_service, backtest_request
    ):
        engine = BacktestEngine(
            data_repository=mock_data_repository,
            validation_service_instance=mock_validation_service
        )
        mock_data_repository.get_stock_data.side_effect = DataNotFoundError(
            'NODATA', '2023-01-01', '2023-02-19'
        )

        with pytest.raises(HTTPException) as exc_info:
            await engine.run_backtest(backtest_request)

        assert exc_info.value.status_code == 404
        assert 'NODATA' in exc_info.value.detail
