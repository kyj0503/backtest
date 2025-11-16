"""데이터 로딩 서비스

주가 데이터 조회를 위한 단일 진입점을 제공합니다.
DB 우선 조회 후 yfinance API로 fallback합니다.
"""
from typing import Union
from datetime import date
import pandas as pd
import logging
import asyncio

from app.repositories.data_repository import data_repository
from app.repositories.stock_repository import get_stock_repository
from app.utils.data_fetcher import data_fetcher
from app.core.exceptions import DataNotFoundError

logger = logging.getLogger(__name__)


class DataService:
    """데이터 로딩 서비스"""

    def __init__(self):
        self.data_repository = data_repository
        self.data_fetcher = data_fetcher
        self.stock_repository = get_stock_repository()

    def _get_ticker_data_internal(
        self,
        ticker: str,
        start_date: Union[date, str],
        end_date: Union[date, str],
        use_db_first: bool = True
    ) -> pd.DataFrame:
        """주식 데이터 조회 (DB 우선, yfinance fallback)"""
        try:
            if use_db_first:
                df = self.stock_repository.load_stock_data(ticker, start_date, end_date)
                if df is not None and not df.empty:
                    logger.debug(f"DB 캐시에서 데이터 반환: {ticker}")
                    return df

            logger.info(f"yfinance에서 데이터 조회: {ticker}")
            df = self.data_fetcher.fetch_stock_data(ticker, start_date, end_date)

            if df is None or df.empty:
                raise DataNotFoundError(ticker, str(start_date), str(end_date))

            return df

        except DataNotFoundError:
            raise
        except Exception as e:
            logger.error(f"데이터 조회 실패: {ticker}, {e}")
            raise DataNotFoundError(ticker, str(start_date), str(end_date))

    async def get_ticker_data(
        self,
        ticker: str,
        start_date: Union[date, str],
        end_date: Union[date, str],
        use_db_first: bool = True
    ) -> pd.DataFrame:
        """주식 데이터 조회 (비동기)"""
        return await asyncio.to_thread(
            self._get_ticker_data_internal,
            ticker, start_date, end_date, use_db_first
        )

    def get_ticker_data_sync(
        self,
        ticker: str,
        start_date: Union[date, str],
        end_date: Union[date, str],
        use_db_first: bool = True
    ) -> pd.DataFrame:
        """주식 데이터 조회 (동기)"""
        return self._get_ticker_data_internal(ticker, start_date, end_date, use_db_first)


# 전역 인스턴스
data_service = DataService()
