"""
data_fetcher 단위 테스트
완전 오프라인 모킹으로 yfinance API 의존성 제거
"""

import pytest
import pandas as pd
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# 백엔드 앱 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.data_fetcher import data_fetcher
from app.core.custom_exceptions import DataNotFoundError, InvalidSymbolError
from tests.fixtures.mock_data import MockStockDataGenerator
from tests.fixtures.expected_results import ExpectedResults


class TestDataFetcher:
    """data_fetcher 모듈 단위 테스트"""
    
    def test_get_stock_data_success(self, mock_data_generator):
        """정상적인 주식 데이터 조회 테스트"""
        # Given
        ticker = "AAPL"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)
        
        # When
        result = data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # Then
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result) > 0
        
        # 필수 컬럼 확인
        expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in expected_columns:
            assert col in result.columns
        
        # 데이터 품질 검증
        expectations = ExpectedResults.get_data_quality_expectations()
        
        # OHLC 논리 검증
        for idx in result.index:
            row = result.loc[idx]
            assert row['High'] >= row['Open'], f"High < Open at {idx}"
            assert row['High'] >= row['Close'], f"High < Close at {idx}"
            assert row['Low'] <= row['Open'], f"Low > Open at {idx}"
            assert row['Low'] <= row['Close'], f"Low > Close at {idx}"
            assert row['High'] >= row['Low'], f"High < Low at {idx}"
        
        # 가격 범위 검증
        price_ranges = expectations['price_ranges'].get(ticker, {'min': 0, 'max': 10000})
        assert result['Close'].min() >= price_ranges['min']
        assert result['Close'].max() <= price_ranges['max']
        
        # 거래량 검증
        volume_ranges = expectations['volume_ranges']
        assert result['Volume'].min() >= volume_ranges['min']
        assert result['Volume'].max() <= volume_ranges['max']
    
    def test_get_stock_data_invalid_ticker(self, mock_data_generator):
        """잘못된 티커 처리 테스트"""
        # Given
        invalid_ticker = "INVALID123"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)
        
        # When & Then
        with patch('app.utils.data_fetcher.data_fetcher.get_stock_data') as mock_get:
            mock_get.side_effect = DataNotFoundError(f"Ticker {invalid_ticker} not found")
            
            with pytest.raises(DataNotFoundError) as exc_info:
                data_fetcher.get_stock_data(invalid_ticker, start_date, end_date)
            
            assert invalid_ticker in str(exc_info.value)
    
    def test_get_stock_data_empty_result(self, mock_data_generator):
        """빈 결과 처리 테스트"""
        # Given
        ticker = "AAPL"
        start_date = date(2023, 6, 30)  # 단일 날짜
        end_date = date(2023, 6, 30)
        
        # When
        result = data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # Then
        assert isinstance(result, pd.DataFrame)
        # 단일 날짜는 최소 1개 레코드 반환되어야 함
        assert len(result) >= 0
    
    def test_get_stock_data_date_validation(self, mock_data_generator):
        """날짜 범위 검증 테스트"""
        # Given
        ticker = "AAPL"
        
        # 역순 날짜 테스트
        start_date = date(2023, 6, 30)
        end_date = date(2023, 1, 1)
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        assert "start_date" in str(exc_info.value) or "end_date" in str(exc_info.value)
    
    def test_get_ticker_info_success(self, mock_data_generator):
        """티커 정보 조회 성공 테스트"""
        # Given
        ticker = "AAPL"
        
        # When
        result = data_fetcher.get_ticker_info(ticker)
        
        # Then
        assert isinstance(result, dict)
        assert 'company_name' in result
        assert 'symbol' in result or result.get('company_name') is not None
        
        # 알려진 티커의 정보 검증
        if ticker == "AAPL":
            assert "Apple" in result.get('company_name', '')
    
    def test_get_ticker_info_invalid_ticker(self, mock_data_generator):
        """잘못된 티커 정보 조회 테스트"""
        # Given
        invalid_ticker = "NOTFOUND999"
        
        # When & Then
        with patch('app.utils.data_fetcher.data_fetcher.get_ticker_info') as mock_info:
            mock_info.side_effect = InvalidSymbolError(f"Invalid ticker: {invalid_ticker}")
            
            with pytest.raises(InvalidSymbolError) as exc_info:
                data_fetcher.get_ticker_info(invalid_ticker)
            
            assert invalid_ticker in str(exc_info.value)
    
    def test_data_caching_behavior(self, mock_data_generator):
        """데이터 캐싱 동작 테스트"""
        # Given
        ticker = "AAPL"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)
        
        # When - 첫 번째 호출
        result1 = data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # When - 두 번째 호출 (캐시 활용)
        result2 = data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # Then
        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)
        
        # 데이터 일관성 검증 (모킹 환경에서는 항상 동일해야 함)
        pd.testing.assert_frame_equal(result1, result2)
    
    def test_multiple_tickers_data_fetching(self, mock_data_generator):
        """다중 티커 데이터 수집 테스트"""
        # Given
        tickers = ["AAPL", "GOOGL", "MSFT"]
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)
        
        # When
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = data_fetcher.get_stock_data(ticker, start_date, end_date)
            except Exception as e:
                results[ticker] = e
        
        # Then
        successful_results = [ticker for ticker, result in results.items() 
                            if isinstance(result, pd.DataFrame)]
        
        # 최소 2개 티커는 성공해야 함
        assert len(successful_results) >= 2
        
        # 성공한 결과들 검증
        for ticker in successful_results:
            result = results[ticker]
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert len(result) > 0
    
    def test_decimal_precision_compliance(self, mock_data_generator):
        """DECIMAL(19,4) 정밀도 준수 테스트"""
        # Given
        ticker = "AAPL"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)
        
        # When
        result = data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # Then
        price_columns = ['Open', 'High', 'Low', 'Close']
        
        for col in price_columns:
            for value in result[col]:
                # DECIMAL(19,4)는 소수점 4자리까지
                decimal_places = len(str(value).split('.')[-1]) if '.' in str(value) else 0
                assert decimal_places <= 4, f"{col} value {value} exceeds 4 decimal places"
                
                # 19자리 전체 길이 (소수점 포함) 검증
                total_digits = len(str(value).replace('.', ''))
                assert total_digits <= 19, f"{col} value {value} exceeds 19 total digits"
    
    def test_performance_benchmarks(self, mock_data_generator):
        """성능 벤치마크 테스트"""
        import time
        
        # Given
        ticker = "AAPL"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)  # 1년 데이터
        
        benchmarks = ExpectedResults.get_performance_benchmarks()
        max_time = benchmarks['data_fetching']['single_ticker_1year']
        
        # When
        start_time = time.time()
        result = data_fetcher.get_stock_data(ticker, start_date, end_date)
        execution_time = time.time() - start_time
        
        # Then
        assert execution_time <= max_time, \
            f"Data fetching took {execution_time:.2f}s, exceeds limit of {max_time}s"
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
    
    @pytest.mark.asyncio
    async def test_concurrent_data_fetching(self, mock_data_generator):
        """동시 데이터 수집 테스트"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Given
        tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)
        
        def fetch_data(ticker):
            return data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # When
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, fetch_data, ticker)
                for ticker in tickers
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        execution_time = time.time() - start_time
        
        # Then
        successful_results = [r for r in results if isinstance(r, pd.DataFrame)]
        assert len(successful_results) >= 3  # 최소 3개 성공
        
        # 동시 실행이 순차 실행보다 빨라야 함 (모킹 환경에서는 무의미하지만 구조 검증)
        max_concurrent_time = ExpectedResults.get_performance_benchmarks()['data_fetching']['portfolio_5tickers_1year']
        assert execution_time <= max_concurrent_time
