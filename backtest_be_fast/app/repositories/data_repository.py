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
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self.stock_repository = get_stock_repository()

    def _get_cache_ttl(self, end_date: Union[date, str]) -> int:
        """날짜에 따라 캐시 TTL 결정"""
        # 문자열을 date 객체로 변환
        if isinstance(end_date, str):
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        elif isinstance(end_date, datetime):
            end_date_obj = end_date.date()
        else:
            end_date_obj = end_date

        today = date.today()

        if end_date_obj < today:
            return CacheConfig.MEMORY_TTL_HISTORICAL

        return CacheConfig.MEMORY_TTL_RECENT

    async def get_stock_data(self, ticker: str, start_date: Union[date, str],
                           end_date: Union[date, str]) -> pd.DataFrame:
        """주식 데이터 조회 (메모리 → DB → yfinance)"""
        try:
            cache_key = f"{ticker}_{start_date}_{end_date}"

            if self._is_cache_valid(cache_key, end_date):
                self.logger.debug(f"메모리 캐시에서 데이터 반환: {cache_key}")
                return self._memory_cache[cache_key]['data']

            try:
                cached_data = await asyncio.to_thread(
                    self.stock_repository.load_stock_data, ticker, start_date, end_date
                )
                if cached_data is not None and not cached_data.empty:
                    self.logger.debug(f"MySQL 캐시에서 데이터 반환: {ticker}")
                    self._memory_cache[cache_key] = {
                        'data': cached_data,
                        'timestamp': datetime.now(),
                        'end_date': end_date
                    }
                    return cached_data
            except Exception as e:
                self.logger.warning(f"MySQL 캐시 조회 실패: {str(e)}")

            self.logger.info(f"실시간 데이터 페칭: {ticker}")
            fresh_data = await asyncio.to_thread(
                self.data_fetcher.fetch_stock_data, ticker, start_date, end_date
            )

            await self.cache_stock_data(ticker, fresh_data)

            self._memory_cache[cache_key] = {
                'data': fresh_data,
                'timestamp': datetime.now(),
                'end_date': end_date
            }
            
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
            keys_to_remove = [key for key in self._memory_cache.keys() 
                            if key.startswith(f"{ticker}_")]
            
            for key in keys_to_remove:
                del self._memory_cache[key]
            
            # MySQL 캐시에서 제거 (필요시)
            # TODO: MySQL 캐시 무효화 로직 구현
            
            self.logger.info(f"캐시 무효화 완료: {ticker}")
            return True
            
        except Exception as e:
            self.logger.error(f"캐시 무효화 실패: {ticker}, {str(e)}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        try:
            # 메모리 캐시 통계
            memory_stats = {
                'total_entries': len(self._memory_cache),
                'memory_usage_mb': len(str(self._memory_cache)) / (1024 * 1024),
                'oldest_entry': None,
                'newest_entry': None
            }
            
            if self._memory_cache:
                timestamps = [item['timestamp'] for item in self._memory_cache.values()]
                memory_stats['oldest_entry'] = min(timestamps)
                memory_stats['newest_entry'] = max(timestamps)
            
            # MySQL 캐시 통계 (필요시)
            mysql_stats = {
                'total_tickers': 0,
                'total_records': 0,
                'disk_usage_mb': 0
            }
            
            return {
                'memory_cache': memory_stats,
                'mysql_cache': mysql_stats,
                'cache_hit_rate': self._calculate_hit_rate()
            }
            
        except Exception as e:
            self.logger.error(f"캐시 통계 조회 실패: {str(e)}")
            return {}
    
    def _is_cache_valid(self, cache_key: str, end_date: Union[date, str]) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self._memory_cache:
            return False

        cached_time = self._memory_cache[cache_key]['timestamp']
        elapsed = (datetime.now() - cached_time).total_seconds()

        ttl = self._get_cache_ttl(end_date)

        return elapsed < ttl


# 전역 인스턴스
DataRepository = YfinanceDataRepository()
data_repository = DataRepository
