"""주식 데이터 Repository

yfinance_db 모듈을 래핑하여 주가 데이터, 뉴스, 티커 메타데이터 접근을 통합 관리합니다.
DB 우선 조회 후 yfinance API로 자동 보완합니다.
"""

from typing import Optional, Union, List, Dict, Any
from datetime import date
import pandas as pd
import logging
from abc import ABC, abstractmethod

from app.services import yfinance_db

logger = logging.getLogger(__name__)


class StockRepositoryInterface(ABC):
    """주식 데이터 Repository 인터페이스"""

    @abstractmethod
    def load_stock_data(
        self,
        ticker: str,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> pd.DataFrame:
        """주가 데이터 조회 (DB 우선, yfinance fallback)"""
        pass

    @abstractmethod
    def save_stock_data(self, ticker: str, df: pd.DataFrame) -> int:
        """주가 데이터를 DB에 저장"""
        pass

    @abstractmethod
    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """티커 메타데이터 조회 (currency, first_trade_date 포함)"""
        pass

    @abstractmethod
    def get_tickers_info_batch(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """여러 티커의 메타데이터 배치 조회 (N+1 쿼리 최적화)"""
        pass

    @abstractmethod
    def load_ticker_news(self, ticker: str, max_age_hours: int = 3) -> Optional[list]:
        """티커의 뉴스 데이터 조회"""
        pass

    @abstractmethod
    def save_ticker_news(self, ticker: str, news_list: list) -> int:
        """티커의 뉴스 데이터 저장"""
        pass


class StockRepository(StockRepositoryInterface):
    """yfinance_db를 기반으로 하는 주식 데이터 Repository 구현"""

    def __init__(self):
        self.logger = logger
        self.logger.info("StockRepository 초기화됨")

    def load_stock_data(
        self,
        ticker: str,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> pd.DataFrame:
        """주가 데이터 조회 (DB 우선, yfinance fallback)"""
        return yfinance_db.load_ticker_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

    def save_stock_data(self, ticker: str, df: pd.DataFrame) -> int:
        """주가 데이터를 DB에 저장"""
        return yfinance_db.save_ticker_data(ticker=ticker, df=df)

    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """티커 메타데이터 조회 (currency, first_trade_date 포함)"""
        return yfinance_db.get_ticker_info_from_db(ticker=ticker)

    def get_tickers_info_batch(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """여러 티커의 메타데이터 배치 조회 (N+1 쿼리 최적화)"""
        return yfinance_db.get_ticker_info_batch_from_db(tickers=tickers)

    def load_ticker_news(self, ticker: str, max_age_hours: int = 3) -> Optional[list]:
        """티커의 뉴스 데이터 조회"""
        return yfinance_db.load_news_from_db(ticker=ticker, max_age_hours=max_age_hours)

    def save_ticker_news(self, ticker: str, news_list: list) -> int:
        """티커의 뉴스 데이터 저장"""
        return yfinance_db.save_news_to_db(ticker=ticker, news_list=news_list)


# 싱글톤 인스턴스
_stock_repository_instance: Optional[StockRepository] = None


def get_stock_repository() -> StockRepository:
    """StockRepository 싱글톤 인스턴스 획득"""
    global _stock_repository_instance
    if _stock_repository_instance is None:
        _stock_repository_instance = StockRepository()
    return _stock_repository_instance
