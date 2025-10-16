"""
데이터 로딩 서비스

**역할**:
- 주가 데이터 조회를 위한 단일 진입점 제공
- DB 우선 조회 후 yfinance로 fallback하는 전략 구현
- 데이터 소스 추상화로 테스트 용이성 향상

**주요 기능**:
1. get_ticker_data(): 주식 데이터 조회
   - DB에서 먼저 조회 시도
   - 데이터가 없으면 yfinance API 호출
   - 조회한 데이터를 DB에 캐싱
2. 에러 핸들링: 데이터 조회 실패 시 예외 발생

**데이터 소스 우선순위**:
1. MySQL 데이터베이스 (캐시, 빠름)
2. yfinance API (외부, 느림)

**의존성**:
- app/repositories/data_repository.py: DB 접근
- app/services/yfinance_db.py: yfinance 데이터 로딩
- app/utils/data_fetcher.py: 데이터 페칭 유틸리티

**연관 컴포넌트**:
- Backend: app/services/backtest_service.py (데이터 사용)
- Backend: app/services/portfolio_service.py (포트폴리오 데이터 로드)
- Database: database/schema.sql (daily_prices 테이블)

**사용 예**:
```python
data_service = DataService()
df = await data_service.get_ticker_data("AAPL", "2023-01-01", "2023-12-31")
```
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
