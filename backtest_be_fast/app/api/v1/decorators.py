"""
API 엔드포인트용 데코레이터 모듈

**역할**:
- API 엔드포인트의 에러 처리 로직을 데코레이터로 중앙화
- 중복 코드 제거 및 일관된 에러 응답 형식 제공
- 로깅 및 모니터링 지원

**주요 데코레이터**:
1. @handle_portfolio_errors: 포트폴리오 백테스트 에러 처리
   - DataNotFoundError → 404
   - InvalidSymbolError → 400
   - ValidationError → 422
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
    YFinanceRateLimitError,
    ValidationError
)

logger = logging.getLogger(__name__)


def handle_backtest_errors(func):
    """
    백테스트 API 공통 에러 핸들러 데코레이터
    
    모든 백테스트 관련 API에서 발생할 수 있는 예외를 일관되게 처리합니다.
    - 커스텀 예외: 그대로 전파 (이미 적절한 HTTP 상태코드 포함)
    - ValidationError: 422 Unprocessable Entity로 변환
    - 기타 예외: 500 Internal Server Error로 변환하고 에러 ID 생성
    
    사용 예시:
    ```python
    @router.post("/chart-data")
    @handle_backtest_errors
    async def get_chart_data(request: BacktestRequest):
        return await backtest_service.run_backtest(request)
    ```
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        
        except ValidationError as e:
            # ValidationError는 422 Unprocessable Entity로 변환
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except (DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError) as e:
            # 이미 적절한 HTTP 상태코드를 가진 커스텀 예외들은 그대로 전파
            raise e
        
        except ValueError as e:
            # ValueError는 일반적으로 검증 오류
            error_id = log_error_for_debugging(e, func.__name__, {})
            logger.error(f"[{error_id}] Validation error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=get_user_friendly_message("ValidationError", str(e))
            )
        
        except Exception as e:
            # 예상치 못한 모든 에러는 500 에러로 변환하고 에러 ID 생성
            error_id = log_error_for_debugging(e, func.__name__, {})
            logger.error(f"[{error_id}] Unexpected error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"예상치 못한 오류가 발생했습니다. (오류 ID: {error_id})"
            )
    
    return wrapper


def handle_portfolio_errors(func):
    """
    포트폴리오 API 공통 에러 핸들러 데코레이터
    
    포트폴리오 백테스트 관련 API에서 발생할 수 있는 예외를 일관되게 처리합니다.
    handle_backtest_errors와 유사하지만 포트폴리오 특화 에러 처리 추가 가능.
    
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
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except (DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError) as e:
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
