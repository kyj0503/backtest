"""
API 엔드포인트용 데코레이터 모듈

**역할**:
- API 엔드포인트의 에러 처리 로직을 데코레이터로 중앙화
- 중복 코드 제거 및 일관된 에러 응답 형식 제공
- 로깅 및 모니터링 지원

**주요 데코레이터**:
1. @handle_portfolio_errors: 포트폴리오 백테스트 에러 처리
   - DataNotFoundError → 404
   - InvalidSymbolError → 422 (app/core/exceptions.py에 정의된 자신의 상태 코드)
   - ValidationError → 422 (app/core/exceptions.py 자체 정의는 400이지만, 이
     데코레이터가 detail=e.detail로 422로 재포장한다 — 아래 wrapper 참고.
     tests/unit/test_portfolio_backtest_error_contract.py::
     test_validation_error_returns_422가 이 계약을 고정한다)
   - YfinanceRateLimitError → 429
   - 기타 예외 → 500

**에러 응답 형식**:
```json
{
  "error": "에러 유형",
  "detail": "상세 메시지",
  "timestamp": "2023-01-01T00:00:00"
}
```

**사용 패턴**:
```python
@router.post("/backtest")
@handle_portfolio_errors
async def run_backtest(request: BacktestRequest):
    # 비즈니스 로직
    pass
```

**의존성**:
- app/core/exceptions.py: 커스텀 예외 클래스
- FastAPI: HTTPException

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (데코레이터 사용)
- Backend: app/core/exceptions.py (예외 정의)

**장점**:
- DRY 원칙: 중복 코드 제거
- 일관성: 모든 엔드포인트에서 동일한 에러 형식
- 유지보수성: 에러 처리 로직 수정 시 한 곳만 변경
"""
from functools import wraps
import logging
from fastapi import HTTPException, status

from app.core.exceptions import (
    DataNotFoundError,
    InvalidSymbolError,
    YfinanceRateLimitError,
    ValidationError
)

import uuid

logger = logging.getLogger(__name__)


def log_error_for_debugging(error: Exception, source: str, context: dict) -> str:
    error_id = str(uuid.uuid4())
    logger.error(f"Error ID: {error_id} | Source: {source} | Error: {error}")
    return error_id


def get_user_friendly_message(error_type: str, detail: str) -> str:
    return f"[{error_type}] {detail}"



def handle_portfolio_errors(func):
    """
    포트폴리오 API 공통 에러 핸들러 데코레이터
    
    포트폴리오 백테스트 관련 API에서 발생할 수 있는 예외를 일관되게 처리합니다.

    사용 예시:
    ```python
    @router.post("/portfolio")
    @handle_portfolio_errors
    async def run_portfolio_backtest(request: PortfolioBacktestRequest):
        return await portfolio_service.run_portfolio_backtest(request)
    ```
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except ValidationError as e:
            # ValidationError 자신의 상태 코드는 400(app/core/exceptions.py)이지만,
            # 이 엔드포인트의 기존 계약(tests/unit/test_portfolio_backtest_error_contract.py::
            # test_validation_error_returns_422)이 422를 고정하고 있으므로 상태
            # 코드는 유지한다. detail만 str(e)(Starlette HTTPException.__str__()이
            # 반환하는 "{status_code}: {detail}" 형식, 예: "400: <메시지>") 대신
            # e.detail(원본 메시지)로 바꿔 422 응답 본문에 모순된 "400: " 접두사가
            # 섞이지 않도록 한다.
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.detail
            )

        except (DataNotFoundError, InvalidSymbolError, YfinanceRateLimitError) as e:
            raise e
        
        except ValueError as e:
            error_id = log_error_for_debugging(e, func.__name__, {})
            logger.error(f"[{error_id}] Portfolio validation error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=get_user_friendly_message("ValidationError", str(e))
            )
        
        except Exception as e:
            error_id = log_error_for_debugging(e, func.__name__, {})
            logger.error(f"[{error_id}] Unexpected portfolio error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"포트폴리오 처리 중 오류가 발생했습니다. (오류 ID: {error_id})"
            )
    
    return wrapper
