"""
중앙화된 데이터 로딩 서비스

모든 데이터 로딩 로직을 통합하여 단일 책임 원칙을 준수합니다.
- DB 우선, fallback to yfinance 패턴 통합
- 캐시 관리 중앙화
- 테스트 용이성 향상
"""
from typing import Union
from datetime import date
import pandas as pd
import logging

from app.repositories.data_repository import data_repository
from app.services.yfinance_db import load_ticker_data
from app.utils.data_fetcher import data_fetcher
from app.core.exceptions import DataNotFoundError

logger = logging.getLogger(__name__)


class DataService:
    """중앙화된 데이터 로딩 서비스"""
    
    def __init__(self):
        self.data_repository = data_repository
        self.data_fetcher = data_fetcher
    
    async def get_ticker_data(
        self,
        ticker: str,
        start_date: Union[date, str],
        end_date: Union[date, str],
        use_db_first: bool = True
    ) -> pd.DataFrame:
        """
        주식 데이터 조회 (DB 우선, fallback to yfinance)
        
        Args:
            ticker: 티커 심볼
            start_date: 시작 날짜
            end_date: 종료 날짜
            use_db_first: DB를 우선 사용할지 여부
        
        Returns:
            DataFrame: 주식 데이터
        
        Raises:
            DataNotFoundError: 데이터를 찾을 수 없을 때
        """
        try:
            if use_db_first:
                # 1. DB 캐시에서 조회 시도
                df = load_ticker_data(ticker, start_date, end_date)
                if df is not None and not df.empty:
                    logger.debug(f"DB 캐시에서 데이터 반환: {ticker}")
                    return df
            
            # 2. yfinance에서 실시간 조회
            logger.info(f"yfinance에서 데이터 조회: {ticker}")
            df = self.data_fetcher.get_stock_data(ticker, start_date, end_date)
            
            if df is None or df.empty:
                raise DataNotFoundError(ticker, str(start_date), str(end_date))
            
            return df
            
        except DataNotFoundError:
            raise
        except Exception as e:
            logger.error(f"데이터 조회 실패: {ticker}, {e}")
            raise DataNotFoundError(ticker, str(start_date), str(end_date))
    
    def get_ticker_data_sync(
        self,
        ticker: str,
        start_date: Union[date, str],
        end_date: Union[date, str],
        use_db_first: bool = True
    ) -> pd.DataFrame:
        """
        주식 데이터 조회 (동기 버전)
        
        기존 코드와의 호환성을 위한 동기 버전입니다.
        """
        try:
            if use_db_first:
                # 1. DB 캐시에서 조회 시도
                df = load_ticker_data(ticker, start_date, end_date)
                if df is not None and not df.empty:
                    logger.debug(f"DB 캐시에서 데이터 반환: {ticker}")
                    return df
            
            # 2. yfinance에서 실시간 조회
            logger.info(f"yfinance에서 데이터 조회: {ticker}")
            df = self.data_fetcher.get_stock_data(ticker, start_date, end_date)
            
            if df is None or df.empty:
                raise DataNotFoundError(ticker, str(start_date), str(end_date))
            
            return df
            
        except DataNotFoundError:
            raise
        except Exception as e:
            logger.error(f"데이터 조회 실패: {ticker}, {e}")
            raise DataNotFoundError(ticker, str(start_date), str(end_date))


# 전역 인스턴스
data_service = DataService()
