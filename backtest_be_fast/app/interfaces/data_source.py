"""
데이터 소스 인터페이스

**역할**:
- 주식 데이터 소스에 대한 추상 인터페이스 정의
- 다양한 데이터 소스 구현 가능 (yfinance, API, DB 등)
- 의존성 주입을 통한 느슨한 결합

**인터페이스 메서드**:
1. get_stock_data(): 주식 데이터 조회
2. validate_ticker(): 종목 검증
3. get_ticker_info(): 종목 정보 조회

**구현체**:
- YFinanceDataSource: yfinance 기반 구현
- CachedDataSource: 캐싱 래퍼 (Decorator 패턴)

**사용 예**:
```python
from app.interfaces.data_source import DataSource
from app.interfaces.data_source import YFinanceDataSource

# 의존성 주입
data_source: DataSource = YFinanceDataSource()

# 또는 캐싱 포함
from app.interfaces.data_source import CachedDataSource
cached_source = CachedDataSource(data_source)
```

**의존성**:
- abc: 추상 기본 클래스
- pandas: 데이터 처리
- datetime: 날짜 처리

**연관 컴포넌트**:
- Backend: app/utils/data_fetcher.py (구현체 기반)
- Backend: app/services/ (사용처)
- Backend: app/di/container.py (DI 컨테이너)
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Dict, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """데이터 소스 추상 인터페이스"""

    @abstractmethod
    def get_stock_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True,
        cache_hours: int = 24
    ) -> pd.DataFrame:
        """
        주식 데이터를 조회합니다.

        Parameters
        ----------
        ticker : str
            주식 티커 심볼
        start_date : date
            시작 날짜
        end_date : date
            종료 날짜
        use_cache : bool, optional
            캐시 사용 여부 (기본값: True)
        cache_hours : int, optional
            캐시 유효 시간 (기본값: 24시간)

        Returns
        -------
        pd.DataFrame
            주식 데이터 (날짜, 시가, 고가, 저가, 종가, 거래량)

        Raises
        ------
        DataNotFoundError
            데이터를 찾을 수 없을 때
        InvalidSymbolError
            잘못된 티커 심볼일 때
        """
        pass

    @abstractmethod
    def validate_ticker(self, ticker: str) -> bool:
        """
        종목 심볼이 유효한지 검증합니다.

        Parameters
        ----------
        ticker : str
            주식 티커 심볼

        Returns
        -------
        bool
            유효한 종목이면 True, 아니면 False
        """
        pass

    @abstractmethod
    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """
        종목의 정보를 조회합니다.

        Parameters
        ----------
        ticker : str
            주식 티커 심볼

        Returns
        -------
        Dict[str, Any]
            종목 정보 (회사명, 산업, 시가총액 등)
        """
        pass


class YFinanceDataSource(DataSource):
    """yfinance 기반 데이터 소스 구현"""

    def __init__(self):
        """yfinance 데이터 소스 초기화"""
        # 기존 DataFetcher를 내부적으로 사용
        from app.utils.data_fetcher import DataFetcher
        self._fetcher = DataFetcher()

    def get_stock_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True,
        cache_hours: int = 24
    ) -> pd.DataFrame:
        """yfinance에서 주식 데이터를 조회합니다."""
        return self._fetcher.get_stock_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache,
            cache_hours=cache_hours
        )

    def validate_ticker(self, ticker: str) -> bool:
        """yfinance에서 종목 검증을 수행합니다."""
        return self._fetcher.validate_ticker(ticker)

    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """yfinance에서 종목 정보를 조회합니다."""
        return self._fetcher.get_ticker_info(ticker)


class CachedDataSource(DataSource):
    """캐싱을 추가하는 데코레이터 패턴 구현 (선택사항)"""

    def __init__(self, data_source: DataSource, cache_hours: int = 24):
        """
        캐싱 래퍼를 초기화합니다.

        Parameters
        ----------
        data_source : DataSource
            기본 데이터 소스
        cache_hours : int
            캐시 유효 시간
        """
        self._data_source = data_source
        self._cache = {}
        self._cache_hours = cache_hours

    def get_stock_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True,
        cache_hours: int = 24
    ) -> pd.DataFrame:
        """캐시를 확인한 후 데이터를 조회합니다."""
        # 현재는 단순 구현 - 향후 개선 가능
        return self._data_source.get_stock_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache,
            cache_hours=cache_hours
        )

    def validate_ticker(self, ticker: str) -> bool:
        """티커 검증을 캐시하지 않고 위임합니다."""
        return self._data_source.validate_ticker(ticker)

    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """종목 정보를 위임합니다."""
        return self._data_source.get_ticker_info(ticker)
