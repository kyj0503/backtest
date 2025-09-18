"""
데이터 캐시 관리 Repository
yfinance 데이터 캐시 및 관리 로직 분리
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
import pandas as pd
import logging
from abc import ABC, abstractmethod

from app.utils.data_fetcher import data_fetcher
from app.services import yfinance_db


class DataRepositoryInterface(ABC):
    """데이터 Repository 인터페이스"""
    
    @abstractmethod
    async def get_stock_data(self, ticker: str, start_date: Union[date, str], 
                           end_date: Union[date, str]) -> pd.DataFrame:
        """주식 데이터 조회 (캐시 우선)"""
        pass
    
    @abstractmethod
    async def cache_stock_data(self, ticker: str, data: pd.DataFrame) -> bool:
        """주식 데이터 캐시 저장"""
        pass
    
    @abstractmethod
    async def invalidate_cache(self, ticker: str) -> bool:
        """특정 티커의 캐시 무효화"""
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        pass


class YFinanceDataRepository(DataRepositoryInterface):
    """yfinance 기반 데이터 Repository"""
    
    def __init__(self):
        self.data_fetcher = data_fetcher
        self.logger = logging.getLogger(__name__)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1시간 TTL
    
    async def get_stock_data(self, ticker: str, start_date: Union[date, str], 
                           end_date: Union[date, str]) -> pd.DataFrame:
        """주식 데이터 조회 (캐시 우선)"""
        try:
            # 캐시 키 생성
            cache_key = f"{ticker}_{start_date}_{end_date}"
            
            # 1. 메모리 캐시 확인
            if self._is_cache_valid(cache_key):
                self.logger.debug(f"메모리 캐시에서 데이터 반환: {cache_key}")
                return self._memory_cache[cache_key]['data']
            
            # 2. MySQL 캐시 확인
            try:
                cached_data = yfinance_db.load_ticker_data(ticker, start_date, end_date)
                if cached_data is not None and not cached_data.empty:
                    self.logger.debug(f"MySQL 캐시에서 데이터 반환: {ticker}")
                    # 메모리 캐시에도 저장
                    self._memory_cache[cache_key] = {
                        'data': cached_data,
                        'timestamp': datetime.now()
                    }
                    return cached_data
            except Exception as e:
                self.logger.warning(f"MySQL 캐시 조회 실패: {str(e)}")
            
            # 3. 실시간 데이터 페칭
            self.logger.info(f"실시간 데이터 페칭: {ticker}")
            fresh_data = self.data_fetcher.get_stock_data(ticker, start_date, end_date)
            
            # 4. 캐시에 저장
            await self.cache_stock_data(ticker, fresh_data)
            
            # 5. 메모리 캐시에 저장
            self._memory_cache[cache_key] = {
                'data': fresh_data,
                'timestamp': datetime.now()
            }
            
            return fresh_data
            
        except Exception as e:
            self.logger.error(f"주식 데이터 조회 실패: {ticker}, {str(e)}")
            raise
    
    async def cache_stock_data(self, ticker: str, data: pd.DataFrame) -> bool:
        """주식 데이터 캐시 저장"""
        try:
            # MySQL 캐시에 저장 (yfinance_db 함수 사용)
            success = yfinance_db.save_ticker_data(ticker, data)
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
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self._memory_cache:
            return False
        
        cached_time = self._memory_cache[cache_key]['timestamp']
        elapsed = (datetime.now() - cached_time).total_seconds()
        
        return elapsed < self._cache_ttl
    
    def _calculate_hit_rate(self) -> float:
        """캐시 히트율 계산 (간단한 구현)"""
        # TODO: 실제 히트율 계산 로직 구현
        return 0.0


class MockDataRepository(DataRepositoryInterface):
    """테스트용 Mock 데이터 Repository"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._mock_data: Dict[str, pd.DataFrame] = {}
    
    async def get_stock_data(self, ticker: str, start_date: Union[date, str], 
                           end_date: Union[date, str]) -> pd.DataFrame:
        """Mock 주식 데이터 반환"""
        # 간단한 Mock 데이터 생성
        import numpy as np
        from datetime import timedelta
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dates = pd.date_range(start, end, freq='D')
        
        # 주말 제외
        dates = dates[dates.weekday < 5]
        
        # Mock OHLCV 데이터 생성
        base_price = 100.0
        data = {
            'Open': [base_price + np.random.normal(0, 2) for _ in dates],
            'High': [base_price + np.random.normal(3, 2) for _ in dates],
            'Low': [base_price + np.random.normal(-3, 2) for _ in dates],
            'Close': [base_price + np.random.normal(0, 2) for _ in dates],
            'Volume': [np.random.randint(1000000, 10000000) for _ in dates]
        }
        
        df = pd.DataFrame(data, index=dates)
        
        # High >= Low 보장
        df['High'] = np.maximum(df['High'], df['Low'])
        
        return df
    
    async def cache_stock_data(self, ticker: str, data: pd.DataFrame) -> bool:
        """Mock 캐시 저장"""
        self._mock_data[ticker] = data
        return True
    
    async def invalidate_cache(self, ticker: str) -> bool:
        """Mock 캐시 무효화"""
        if ticker in self._mock_data:
            del self._mock_data[ticker]
        return True
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Mock 캐시 통계"""
        return {
            'total_entries': len(self._mock_data),
            'memory_usage_mb': 0.1,
            'cache_hit_rate': 1.0
        }


# Repository 팩토리
class DataRepositoryFactory:
    """데이터 Repository 팩토리"""
    
    @staticmethod
    def create(repository_type: str = "yfinance") -> DataRepositoryInterface:
        """Repository 인스턴스 생성"""
        if repository_type == "yfinance":
            return YFinanceDataRepository()
        elif repository_type == "mock":
            return MockDataRepository()
        else:
            raise ValueError(f"지원하지 않는 Repository 타입: {repository_type}")


# 전역 인스턴스
DataRepository = DataRepositoryFactory.create("yfinance")
data_repository = DataRepository
