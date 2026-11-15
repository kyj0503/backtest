"""데이터 Repository

Repository 패턴으로 주가 데이터 접근을 추상화합니다.
3단계 캐싱 전략: 메모리 → DB → yfinance API
"""
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
import pandas as pd
import logging
from abc import ABC, abstractmethod
from cachetools import TTLCache

from app.utils.data_fetcher import data_fetcher
from app.repositories.stock_repository import get_stock_repository
from app.constants.data_loading import CacheConfig

# `if key in cache: return cache[key]` 패턴은 두 호출 사이에 TTL이 만료되면
# (예: 그 사이의 self.logger.debug() 호출 등으로 실제 시간이 흐르면) `in`은 True를
# 반환했지만 `[]`는 KeyError를 던지는 TOCTOU 레이스를 만든다. `.get(key, sentinel)`은
# 존재확인과 조회를 하나의 원자적 호출로 묶어 이 레이스를 없앤다.
_CACHE_MISS = object()


class DataRepositoryInterface(ABC):
    """데이터 Repository 인터페이스"""

    @abstractmethod
    async def get_stock_data(self, ticker: str, start_date: Union[date, str],
                           end_date: Union[date, str]) -> pd.DataFrame:
        pass

    @abstractmethod
    async def cache_stock_data(self, ticker: str, data: pd.DataFrame) -> bool:
        pass

    @abstractmethod
    async def invalidate_cache(self, ticker: str) -> bool:
        pass

    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        pass


class YfinanceDataRepository(DataRepositoryInterface):
    """yfinance 기반 데이터 Repository"""

    def __init__(self):
        self.data_fetcher = data_fetcher
        self.logger = logging.getLogger(__name__)
        # maxsize=500에 대응하는 CacheConfig 상수는 없어 리터럴로 둔다(캐시 항목
        # 개수 제한이며 CacheConfig는 TTL류 상수만 정의한다). ttl=3600은
        # CacheConfig.MEMORY_TTL_RECENT와 정확히 일치하므로 그 상수를 사용한다.
        self._memory_cache: TTLCache = TTLCache(maxsize=500, ttl=CacheConfig.MEMORY_TTL_RECENT)
        self.stock_repository = get_stock_repository()

    async def get_stock_data(self, ticker: str, start_date: Union[date, str],
                           end_date: Union[date, str]) -> pd.DataFrame:
        """주식 데이터 조회 (메모리 → DB → yfinance)"""
        try:
            cache_key = f"{ticker}_{start_date}_{end_date}"

            # .get()으로 존재확인과 조회를 하나의 원자적 호출로 묶는다 (TOCTOU 방지).
            # 이전의 `if cache_key in self._memory_cache: return self._memory_cache[cache_key]`는
            # 두 호출 사이에 TTL이 만료되면 KeyError가 새어나갈 수 있었다.
            cached_value = self._memory_cache.get(cache_key, _CACHE_MISS)
            if cached_value is not _CACHE_MISS:
                self.logger.debug(f"메모리 캐시에서 데이터 반환: {cache_key}")
                return cached_value

            try:
                cached_data = await asyncio.to_thread(
                    self.stock_repository.load_stock_data, ticker, start_date, end_date
                )
                if cached_data is not None and not cached_data.empty:
                    self.logger.debug(f"MySQL 캐시에서 데이터 반환: {ticker}")
                    self._memory_cache[cache_key] = cached_data
                    return cached_data
            except Exception as e:
                self.logger.warning(f"MySQL 캐시 조회 실패: {str(e)}")

            self.logger.info(f"실시간 데이터 페칭: {ticker}")
            fresh_data = await asyncio.to_thread(
                self.data_fetcher.fetch_stock_data, ticker, start_date, end_date
            )

            await self.cache_stock_data(ticker, fresh_data)

            self._memory_cache[cache_key] = fresh_data

            return fresh_data

        except Exception as e:
            self.logger.error(f"주식 데이터 조회 실패: {ticker}, {str(e)}")
            raise
    
    async def cache_stock_data(self, ticker: str, data: pd.DataFrame) -> bool:
        """주식 데이터 캐시 저장"""
        try:
            # MySQL 캐시에 저장 (stock_repository 사용)
            success = await asyncio.to_thread(
                self.stock_repository.save_stock_data, ticker, data
            )
            if success > 0:
                self.logger.info(f"데이터 캐시 저장 완료: {ticker}, {success}행")
                return True

            return False
            
        except Exception as e:
            self.logger.error(f"데이터 캐시 저장 실패: {ticker}, {str(e)}")
            return False
    
    async def invalidate_cache(self, ticker: str) -> bool:
        """특정 티커의 캐시 무효화"""
        try:
            # 메모리 캐시에서 제거
            keys_to_remove = [key for key in list(self._memory_cache.keys())
                            if key.startswith(f"{ticker}_")]

            for key in keys_to_remove:
                self._memory_cache.pop(key, None)

            self.logger.info(f"캐시 무효화 완료: {ticker}")
            return True

        except Exception as e:
            self.logger.error(f"캐시 무효화 실패: {ticker}, {str(e)}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        try:
            memory_stats = {
                'total_entries': len(self._memory_cache),
                'max_size': self._memory_cache.maxsize,
                'ttl_seconds': self._memory_cache.ttl,
            }

            mysql_stats = {
                'total_tickers': 0,
                'total_records': 0,
                'disk_usage_mb': 0
            }

            return {
                'memory_cache': memory_stats,
                'mysql_cache': mysql_stats,
            }

        except Exception as e:
            self.logger.error(f"캐시 통계 조회 실패: {str(e)}")
            return {}


# 전역 인스턴스
DataRepository = YfinanceDataRepository()
data_repository = DataRepository
