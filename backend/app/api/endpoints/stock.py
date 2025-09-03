from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.stock import StockService
from app.models.schemas import StockPriceResponse, StockPriceError
from app.core.exceptions import BacktestError

router = APIRouter()

@router.get(
    "/prices/{symbol}",
    response_model=StockPriceResponse,
    responses={
        400: {"model": StockPriceError, "description": "잘못된 요청"},
        404: {"model": StockPriceError, "description": "데이터를 찾을 수 없음"},
        500: {"model": StockPriceError, "description": "서버 내부 오류"}
    }
)
async def get_stock_prices(
    symbol: str,
    days: Optional[int] = Query(5, ge=1, le=30, description="조회할 일수 (1-30일)")
) -> StockPriceResponse:
    """
    주식 종목의 최근 N일간 주가 데이터를 조회합니다.
    
    Parameters
    ----------
    symbol : str
        주식 심볼 (예: "AAPL")
    days : int, optional
        조회할 일수 (기본값: 5, 최대: 30)
        
    Returns
    -------
    StockPriceResponse
        주가 데이터와 메타데이터를 포함한 응답
    """
    try:
        # 심볼 검증
        if not symbol.isalpha():
            raise BacktestError(
                "주식 심볼은 영문자만 사용할 수 있습니다.",
                "INVALID_SYMBOL"
            )
        
        # 데이터 조회
        result = StockService.get_recent_prices(symbol, days)
        return StockPriceResponse(**result)
        
    except BacktestError as e:
        if e.code == "INVALID_SYMBOL":
            raise HTTPException(status_code=400, detail=str(e))
        elif e.code == "NO_DATA":
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"서버 내부 오류: {str(e)}"
        ) 