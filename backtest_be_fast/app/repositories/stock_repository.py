"""
주식 데이터 Repository

**역할**:
- yfinance_db 모듈의 직접적인 사용 금지 및 추상화 계층 제공
- 주가 데이터, 뉴스, 티커 메타데이터 접근 통합 관리
- 데이터 소스 독립적인 인터페이스 제공

**주요 기능**:
1. load_stock_data(): 주가 데이터 조회 (DB 우선)
   - 누락 기간이 있으면 yfinance로 자동 보완
   - 새 데이터를 DB에 저장
2. save_stock_data(): DataFrame을 DB에 저장
3. get_ticker_info(): 티커 메타데이터 조회 (currency, first_trade_date 포함)
4. get_tickers_info_batch(): 여러 티커의 메타데이터 배치 조회
5. load_ticker_news(): 티커의 뉴스 데이터 조회
6. save_ticker_news(): 티커의 뉴스 데이터 저장

**의존성**:
- app.services.yfinance_db: 실제 데이터 접근 구현
- pandas: 데이터 처리

**연관 컴포넌트**:
- Backend: app/services/portfolio_service.py (Repository 사용)
- Backend: app/services/backtest_engine.py (Repository 사용)
- Backend: app/services/data_service.py (Repository 사용)
- Backend: app/repositories/data_repository.py (Repository 사용)
- Backend: app/utils/currency_converter.py (Repository 사용)
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
        """
        주가 데이터 조회 (DB 우선)

        Args:
            ticker: 종목 심볼
            start_date: 시작 날짜
            end_date: 종료 날짜
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 대기 시간 (초)

        Returns:
            주가 데이터 DataFrame
        """
        pass

    @abstractmethod
    def save_stock_data(self, ticker: str, df: pd.DataFrame) -> int:
        """
        주가 데이터를 DB에 저장

        Args:
            ticker: 종목 심볼
            df: 저장할 데이터 DataFrame

        Returns:
            저장된 행 수
        """
        pass

    @abstractmethod
    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """
        티커의 메타데이터 조회

        Args:
            ticker: 종목 심볼

        Returns:
            티커 정보 딕셔너리 (currency, first_trade_date 포함)
        """
        pass

    @abstractmethod
    def get_tickers_info_batch(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        여러 티커의 메타데이터 배치 조회 (N+1 쿼리 최적화)

        Args:
            tickers: 종목 심볼 리스트

        Returns:
            티커별 정보 딕셔너리
        """
        pass

    @abstractmethod
    def load_ticker_news(self, ticker: str, max_age_hours: int = 3) -> Optional[list]:
        """
        티커의 뉴스 데이터 조회

        Args:
            ticker: 종목 심볼
            max_age_hours: 최대 age (시간)

        Returns:
            뉴스 리스트 또는 None
        """
        pass

    @abstractmethod
    def save_ticker_news(self, ticker: str, news_list: list) -> int:
        """
        티커의 뉴스 데이터 저장

        Args:
            ticker: 종목 심볼
            news_list: 저장할 뉴스 리스트

        Returns:
            저장된 행 수
        """
        pass


class StockRepository(StockRepositoryInterface):
    """yfinance_db를 기반으로 하는 주식 데이터 Repository 구현"""

    def __init__(self):
        """주식 Repository 초기화"""
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
        """
        주가 데이터 조회 (DB 우선 전략 사용)

        yfinance_db.load_ticker_data를 래핑합니다.

        Args:
            ticker: 종목 심볼
            start_date: 시작 날짜
            end_date: 종료 날짜
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 대기 시간 (초)

        Returns:
            주가 데이터 DataFrame
        """
        return yfinance_db.load_ticker_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

    def save_stock_data(self, ticker: str, df: pd.DataFrame) -> int:
        """
        주가 데이터를 DB에 저장

        yfinance_db.save_ticker_data를 래핑합니다.

        Args:
            ticker: 종목 심볼
            df: 저장할 데이터 DataFrame

        Returns:
            저장된 행 수
        """
        return yfinance_db.save_ticker_data(ticker=ticker, df=df)

    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """
        티커의 메타데이터 조회

        yfinance_db.get_ticker_info_from_db를 래핑합니다.

        Args:
            ticker: 종목 심볼

        Returns:
            티커 정보 딕셔너리 (symbol, currency, company_name, exchange, first_trade_date)
        """
        return yfinance_db.get_ticker_info_from_db(ticker=ticker)

    def get_tickers_info_batch(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        여러 티커의 메타데이터 배치 조회

        yfinance_db.get_ticker_info_batch_from_db를 래핑합니다.
        N+1 쿼리 문제를 최적화합니다.

        Args:
            tickers: 종목 심볼 리스트

        Returns:
            티커별 정보 딕셔너리 (key: ticker, value: info dict)
        """
        return yfinance_db.get_ticker_info_batch_from_db(tickers=tickers)

    def load_ticker_news(self, ticker: str, max_age_hours: int = 3) -> Optional[list]:
        """
        티커의 뉴스 데이터 조회

        yfinance_db.load_news_from_db를 래핑합니다.

        Args:
            ticker: 종목 심볼
            max_age_hours: 최대 age (시간)

        Returns:
            뉴스 리스트 또는 None
        """
        return yfinance_db.load_news_from_db(ticker=ticker, max_age_hours=max_age_hours)

    def save_ticker_news(self, ticker: str, news_list: list) -> int:
        """
        티커의 뉴스 데이터 저장

        yfinance_db.save_news_to_db를 래핑합니다.

        Args:
            ticker: 종목 심볼
            news_list: 저장할 뉴스 리스트

        Returns:
            저장된 행 수
        """
        return yfinance_db.save_news_to_db(ticker=ticker, news_list=news_list)


# 싱글톤 인스턴스
_stock_repository_instance: Optional[StockRepository] = None


def get_stock_repository() -> StockRepository:
    """StockRepository 싱글톤 인스턴스 획득"""
    global _stock_repository_instance
    if _stock_repository_instance is None:
        _stock_repository_instance = StockRepository()
    return _stock_repository_instance
