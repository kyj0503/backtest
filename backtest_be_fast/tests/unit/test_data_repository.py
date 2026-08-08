"""
DataRepository Unit Tests

Tests the YfinanceDataRepository with 3-tier caching: memory (TTLCache) → DB → yfinance.
All external I/O (yfinance API, DB) are mocked.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from unittest.mock import Mock, AsyncMock, patch
from cachetools import TTLCache

from app.repositories.data_repository import YfinanceDataRepository


@pytest.mark.unit
class TestYfinanceDataRepositoryGetStockData:
    """Test YfinanceDataRepository.get_stock_data() with caching strategy"""

    @pytest.fixture
    def mock_data_fetcher(self):
        """Mock data fetcher for yfinance calls"""
        fetcher = Mock()
        return fetcher

    @pytest.fixture
    def mock_stock_repository(self):
        """Mock stock repository for DB access"""
        repo = Mock()
        return repo

    @pytest.fixture
    def sample_price_data(self):
        """Sample price DataFrame"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        prices = np.linspace(100, 130, 30)
        return pd.DataFrame({
            'Open': prices,
            'High': prices * 1.02,
            'Low': prices * 0.98,
            'Close': prices,
            'Volume': [1000000] * 30
        }, index=dates)

    @pytest.fixture
    def repository(self, mock_data_fetcher, mock_stock_repository):
        """YfinanceDataRepository instance with mocks"""
        repo = YfinanceDataRepository()
        repo.data_fetcher = mock_data_fetcher
        repo.stock_repository = mock_stock_repository
        return repo

    @pytest.mark.asyncio
    async def test_memory_cache_hit_returns_cached_data(
        self, repository, sample_price_data
    ):
        """Test that memory cache (TTLCache) returns data when valid"""
        # Pre-populate memory cache
        cache_key = "AAPL_2023-01-01_2023-01-30"
        repository._memory_cache[cache_key] = sample_price_data

        result = await repository.get_stock_data(
            ticker='AAPL',
            start_date='2023-01-01',
            end_date='2023-01-30'
        )

        # Should return cached data without hitting DB or API
        pd.testing.assert_frame_equal(result, sample_price_data)
        repository.stock_repository.load_stock_data.assert_not_called()
        repository.data_fetcher.fetch_stock_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_memory_miss_db_hit_returns_from_db(
        self, repository, mock_stock_repository, sample_price_data
    ):
        """Test that DB cache is queried on memory miss"""
        # Ensure memory cache is empty
        repository._memory_cache.clear()

        # Mock DB to return data
        mock_stock_repository.load_stock_data = Mock(return_value=sample_price_data)

        result = await repository.get_stock_data(
            ticker='TSLA',
            start_date='2023-02-01',
            end_date='2023-02-28'
        )

        # Should return DB data
        pd.testing.assert_frame_equal(result, sample_price_data)

        # Should populate memory cache
        cache_key = "TSLA_2023-02-01_2023-02-28"
        assert cache_key in repository._memory_cache

    @pytest.mark.asyncio
    async def test_memory_and_db_miss_fetches_from_yfinance(
        self, repository, mock_stock_repository, mock_data_fetcher, sample_price_data
    ):
        """Test that yfinance is called when both memory and DB miss"""
        # Clear memory cache
        repository._memory_cache.clear()

        # Mock DB to return empty
        mock_stock_repository.load_stock_data = Mock(return_value=None)

        # Mock yfinance to return fresh data
        mock_data_fetcher.fetch_stock_data = Mock(return_value=sample_price_data)
        mock_stock_repository.save_stock_data = Mock(return_value=10)

        result = await repository.get_stock_data(
            ticker='NVDA',
            start_date='2023-03-01',
            end_date='2023-03-31'
        )

        # Should fetch from yfinance
        mock_data_fetcher.fetch_stock_data.assert_called_once()

        # Should return fetched data
        pd.testing.assert_frame_equal(result, sample_price_data)

        # Should save to DB cache
        mock_stock_repository.save_stock_data.assert_called_once()

        # Should populate memory cache
        cache_key = "NVDA_2023-03-01_2023-03-31"
        assert cache_key in repository._memory_cache

    @pytest.mark.asyncio
    async def test_db_query_failure_falls_through_to_yfinance(
        self, repository, mock_stock_repository, mock_data_fetcher, sample_price_data
    ):
        """Test that DB failure doesn't break flow and falls through to yfinance"""
        repository._memory_cache.clear()

        # Mock DB to raise exception
        mock_stock_repository.load_stock_data = Mock(side_effect=Exception("DB connection error"))

        # Mock yfinance to return data
        mock_data_fetcher.fetch_stock_data = Mock(return_value=sample_price_data)
        mock_stock_repository.save_stock_data = Mock(return_value=5)

        result = await repository.get_stock_data(
            ticker='MSFT',
            start_date='2023-04-01',
            end_date='2023-04-30'
        )

        # Should still return data from yfinance
        pd.testing.assert_frame_equal(result, sample_price_data)


@pytest.mark.unit
class TestYfinanceDataRepositoryInvalidateCache:
    """Test YfinanceDataRepository.invalidate_cache() method"""

    @pytest.fixture
    def repository(self):
        """YfinanceDataRepository instance"""
        return YfinanceDataRepository()

    @pytest.fixture
    def sample_data(self):
        """Sample DataFrame"""
        return pd.DataFrame({
            'Close': [100, 101, 102]
        })

    @pytest.mark.asyncio
    async def test_invalidate_cache_removes_correct_keys(self, repository, sample_data):
        """Test that invalidate_cache removes all keys for a ticker"""
        # Populate cache with multiple date ranges for same ticker
        repository._memory_cache["AAPL_2023-01-01_2023-01-31"] = sample_data
        repository._memory_cache["AAPL_2023-02-01_2023-02-28"] = sample_data
        repository._memory_cache["AAPL_2023-03-01_2023-03-31"] = sample_data
        repository._memory_cache["TSLA_2023-01-01_2023-01-31"] = sample_data

        # Invalidate AAPL
        result = await repository.invalidate_cache("AAPL")

        assert result is True

        # AAPL keys should be removed
        assert "AAPL_2023-01-01_2023-01-31" not in repository._memory_cache
        assert "AAPL_2023-02-01_2023-02-28" not in repository._memory_cache
        assert "AAPL_2023-03-01_2023-03-31" not in repository._memory_cache

        # TSLA key should remain
        assert "TSLA_2023-01-01_2023-01-31" in repository._memory_cache

    @pytest.mark.asyncio
    async def test_invalidate_cache_handles_nonexistent_ticker(self, repository):
        """Test that invalidating non-existent ticker succeeds"""
        result = await repository.invalidate_cache("NONEXISTENT")
        assert result is True


@pytest.mark.unit
class TestYfinanceDataRepositoryTTLCache:
    """Test TTLCache behavior in YfinanceDataRepository"""

    def test_ttlcache_initialization_has_correct_params(self):
        """Test that TTLCache is initialized with maxsize=500 and ttl=3600"""
        repo = YfinanceDataRepository()

        assert isinstance(repo._memory_cache, TTLCache)
        assert repo._memory_cache.maxsize == 500
        assert repo._memory_cache.ttl == 3600

    def test_ttlcache_evicts_expired_entries_automatically(self):
        """Test that TTLCache automatically removes expired entries"""
        # Create a cache with very short TTL for testing
        cache = TTLCache(maxsize=10, ttl=0.1)

        cache["key1"] = "value1"
        assert "key1" in cache

        # Wait for expiration (TTL 0.1 seconds)
        import time
        time.sleep(0.2)

        # Should be automatically evicted
        assert "key1" not in cache

    def test_ttlcache_maxsize_evicts_oldest_entries(self):
        """Test that maxsize limit evicts LRU entries"""
        cache = TTLCache(maxsize=3, ttl=3600)

        cache["key1"] = "value1"
        cache["key2"] = "value2"
        cache["key3"] = "value3"

        # Adding 4th item should evict key1 (oldest)
        cache["key4"] = "value4"

        assert "key1" not in cache
        assert "key2" in cache
        assert "key3" in cache
        assert "key4" in cache


@pytest.mark.unit
class TestYfinanceDataRepositoryCacheStockData:
    """Test YfinanceDataRepository.cache_stock_data() method"""

    @pytest.fixture
    def repository(self):
        """YfinanceDataRepository instance"""
        repo = YfinanceDataRepository()
        repo.stock_repository = Mock()
        return repo

    @pytest.fixture
    def sample_data(self):
        """Sample price DataFrame"""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'Close': np.linspace(100, 110, 10)
        }, index=dates)

    @pytest.mark.asyncio
    async def test_cache_stock_data_saves_to_db_successfully(
        self, repository, sample_data
    ):
        """Test that cache_stock_data saves to DB and returns True"""
        repository.stock_repository.save_stock_data = Mock(return_value=10)

        result = await repository.cache_stock_data('AAPL', sample_data)

        assert result is True
        repository.stock_repository.save_stock_data.assert_called_once_with('AAPL', sample_data)

    @pytest.mark.asyncio
    async def test_cache_stock_data_returns_false_on_zero_rows(
        self, repository, sample_data
    ):
        """Test that cache_stock_data returns False when no rows saved"""
        repository.stock_repository.save_stock_data = Mock(return_value=0)

        result = await repository.cache_stock_data('TSLA', sample_data)

        assert result is False

    @pytest.mark.asyncio
    async def test_cache_stock_data_handles_exception(
        self, repository, sample_data
    ):
        """Test that cache_stock_data handles exceptions gracefully"""
        repository.stock_repository.save_stock_data = Mock(side_effect=Exception("DB error"))

        result = await repository.cache_stock_data('NVDA', sample_data)

        assert result is False


@pytest.mark.unit
class TestYfinanceDataRepositoryGetCacheStats:
    """Test YfinanceDataRepository.get_cache_stats() method"""

    @pytest.fixture
    def repository(self):
        """YfinanceDataRepository instance"""
        return YfinanceDataRepository()

    @pytest.mark.asyncio
    async def test_get_cache_stats_returns_memory_stats(self, repository):
        """Test that cache stats include memory cache information"""
        # Add some entries
        repository._memory_cache["key1"] = pd.DataFrame()
        repository._memory_cache["key2"] = pd.DataFrame()

        stats = await repository.get_cache_stats()

        assert 'memory_cache' in stats
        assert stats['memory_cache']['total_entries'] == 2
        assert stats['memory_cache']['max_size'] == 500
        assert stats['memory_cache']['ttl_seconds'] == 3600

    @pytest.mark.asyncio
    async def test_get_cache_stats_includes_mysql_placeholder(self, repository):
        """Test that cache stats include MySQL cache placeholder"""
        stats = await repository.get_cache_stats()

        assert 'mysql_cache' in stats
        assert 'total_tickers' in stats['mysql_cache']
        assert 'total_records' in stats['mysql_cache']
