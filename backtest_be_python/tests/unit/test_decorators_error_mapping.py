"""handle_portfolio_errors의 ValidationError 상태 코드/메시지 일관성 회귀 테스트 (P3-20b)

버그: ValidationError는 app/core/exceptions.py에서 이미 HTTP 400으로 정의되어
있는데, handle_portfolio_errors는 이를 detail=str(e)로 감싸 422로 재포장했다.
Starlette의 HTTPException.__str__()은 "{status_code}: {detail}" 형식을
반환하므로 (직접 확인: str(HTTPException(400, "msg")) == "400: msg"),
재포장된 422 응답 본문에는 "422 응답인데 본문은 400이라고 말하는" 모순된
"400: " 접두사가 그대로 노출되었다.

상태 코드 결정: 422를 유지한다 (400으로 바꾸지 않는다). 이미 존재하는 엔드포인트
레벨 계약 테스트 tests/unit/test_portfolio_backtest_error_contract.py::
TestPortfolioBacktestErrorContract::test_validation_error_returns_422 가
POST /api/v1/backtest 전체 스택(@handle_portfolio_errors 포함)에서
ValidationError -> 422를 이미 고정해 놓았다. 그 테스트는 이번 작업 범위 밖이라
수정할 수 없으므로, 상태 코드는 422로 유지하고 detail만 e.detail(원본 메시지)로
교체해 "400: " 접두사 모순을 제거한다.

docstring 매핑도 실제 동작과 어긋나 있었다: InvalidSymbolError는
app/core/exceptions.py에서 실제로는 422(HTTP_422_UNPROCESSABLE_ENTITY)로
정의되어 있는데 데코레이터 파일 상단 docstring은 "InvalidSymbolError → 400"
이라고 잘못 적어 놓았다.
"""
import pytest
from fastapi import HTTPException

from app.api.v1.decorators import handle_portfolio_errors
from app.core.exceptions import DataNotFoundError, InvalidSymbolError, ValidationError


pytestmark = pytest.mark.unit


@handle_portfolio_errors
async def _raise_validation_error():
    raise ValidationError("포트폴리오 구성이 올바르지 않습니다")


@handle_portfolio_errors
async def _raise_data_not_found():
    raise DataNotFoundError("AAPL", "2023-01-01", "2023-02-01")


@handle_portfolio_errors
async def _raise_invalid_symbol():
    raise InvalidSymbolError("???")


class TestValidationErrorDetailHasNoContradictoryStatusPrefix:
    """ValidationError의 detail 메시지에 다른 상태 코드를 암시하는 접두사가
    섞여 나가면 안 된다."""

    @pytest.mark.asyncio
    async def test_detail_does_not_start_with_400_prefix(self):
        with pytest.raises(HTTPException) as exc_info:
            await _raise_validation_error()

        detail = str(exc_info.value.detail)
        assert not detail.startswith("400: "), f"모순된 상태 접두사 누출: {detail!r}"

    @pytest.mark.asyncio
    async def test_detail_equals_original_clean_message(self):
        with pytest.raises(HTTPException) as exc_info:
            await _raise_validation_error()

        assert exc_info.value.detail == "포트폴리오 구성이 올바르지 않습니다"


class TestValidationErrorStatusCodeMatchesDocumentedMapping:
    @pytest.mark.asyncio
    async def test_status_code_is_422(self):
        """기존 엔드포인트 레벨 계약 테스트가 이미 이 매핑을 고정하고 있다
        (test_portfolio_backtest_error_contract.py::test_validation_error_returns_422)."""
        with pytest.raises(HTTPException) as exc_info:
            await _raise_validation_error()

        assert exc_info.value.status_code == 422


class TestOtherCustomExceptionsStillPassThroughUnchanged:
    """회귀 가드: ValidationError 처리 수정이 다른 예외의 통과 경로를 깨지
    않는지 확인한다."""

    @pytest.mark.asyncio
    async def test_data_not_found_error_still_returns_404(self):
        with pytest.raises(HTTPException) as exc_info:
            await _raise_data_not_found()

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_symbol_error_still_returns_its_own_422(self):
        with pytest.raises(HTTPException) as exc_info:
            await _raise_invalid_symbol()

        assert exc_info.value.status_code == 422
