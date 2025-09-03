from fastapi import APIRouter, Depends, HTTPException
from app.services.backtest import BacktestService
from app.models.schemas import BacktestRequest, BacktestResponse, BacktestError
from app.core.exceptions import BacktestError as BacktestServiceError

router = APIRouter()

@router.post("/", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    backtest_service: BacktestService = Depends()
) -> BacktestResponse:
    """
    백테스트를 실행합니다.
    
    Parameters
    ----------
    request : BacktestRequest
        백테스트 요청 파라미터
    backtest_service : BacktestService
        백테스트 서비스 인스턴스
        
    Returns
    -------
    BacktestResponse
        백테스트 결과
        
    Raises
    ------
    HTTPException
        백테스트 실행 중 오류 발생 시
    """
    try:
        result = await backtest_service.run_backtest(request)
        return BacktestResponse(**result)
    except BacktestServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.message,
                "code": e.code
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "code": "INTERNAL_SERVER_ERROR"
            }
        ) 