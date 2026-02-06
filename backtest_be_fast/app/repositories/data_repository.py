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
        self._memory_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)
        self.stock_repository = get_stock_repository()

    async def get_stock_data(self, ticker: str, start_date: Union[date, str],
                           end_date: Union[date, str]) -> pd.DataFrame:
        """주식 데이터 조회 (메모리 → DB → yfinance)"""
        try:
            cache_key = f"{ticker}_{start_date}_{end_date}"

            # TTLCache가 자동으로 만료된 항목을 제거하므로 존재 확인만 하면 됨
            if cache_key in self._memory_cache:
                self.logger.debug(f"메모리 캐시에서 데이터 반환: {cache_key}")
                return self._memory_cache[cache_key]

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
