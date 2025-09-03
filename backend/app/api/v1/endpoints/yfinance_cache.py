from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from datetime import date
import logging

from app.utils.data_fetcher import data_fetcher
from app.services import yfinance_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/fetch-and-cache", status_code=status.HTTP_200_OK)
async def fetch_and_cache(
    ticker: str,
    start: Optional[date] = Query(None, description="시작일 YYYY-MM-DD"),
    end: Optional[date] = Query(None, description="종료일 YYYY-MM-DD"),
    interval: Optional[str] = Query("1d", description="간격(예: 1d,1wk,1mo)")
):
    """티커와 기간에 따라 yfinance에서 데이터를 받아 DB에 저장합니다.

    단순 전달 및 저장이며, 전처리 없이 원본을 저장합니다.
    """
    try:
        ticker = ticker.upper()
        # validate dates
        if start is None or end is None:
            raise HTTPException(status_code=400, detail="start와 end 파라미터를 지정하세요.")
        if start > end:
            raise HTTPException(status_code=400, detail="start는 end보다 이전이어야 합니다.")

        # fetch using existing DataFetcher
        df = data_fetcher.get_stock_data(ticker, start, end, use_cache=False)

        # store into DB
        saved = yfinance_db.save_ticker_data(ticker, df)

        return {"ticker": ticker, "rows_saved": saved, "start": str(start), "end": str(end)}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("fetch_and_cache 실패")
        raise HTTPException(status_code=500, detail=str(e))
