"""
데이터 페처 유닛 테스트
"""
import pytest
from unittest.mock import patch, Mock
import pandas as pd
import numpy as np
from datetime import date

from app.utils.data_fetcher import DataFetcher
from app.core.custom_exceptions import DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError


class TestDataFetcher:
    """DataFetcher 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.data_fetcher = DataFetcher()
    
    @patch('app.utils.data_fetcher.yf.download')
    def test_get_stock_data_success(self, mock_download, mock_yfinance_success):
        """정상적인 주식 데이터 수집 테스트"""
        # Mock 설정
        mock_download.return_value = mock_yfinance_success
        
        # 테스트 실행
        result = self.data_fetcher.get_stock_data(
            ticker="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        # 검증
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'Close' in result.columns
        assert 'Volume' in result.columns
        mock_download.assert_called_once()
    
    @patch('app.utils.data_fetcher.yf.download')
    def test_get_stock_data_empty_response(self, mock_download, mock_yfinance_empty):
        """빈 데이터 응답 테스트"""
        mock_download.return_value = mock_yfinance_empty
        
        with pytest.raises(DataNotFoundError):
            self.data_fetcher.get_stock_data(
                ticker="INVALID",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31)
            )
    
    @patch('app.utils.data_fetcher.yf.download')
    def test_get_stock_data_connection_error(self, mock_download):
        """연결 오류 테스트"""
        # ConnectionError 시뮬레이션
        mock_download.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(YFinanceRateLimitError):
            self.data_fetcher.get_stock_data(
                ticker="AAPL",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31)
            )
    
    @patch('app.utils.data_fetcher.yf.download')
    def test_get_stock_data_invalid_ticker(self, mock_download):
        """잘못된 티커 테스트"""
        # 빈 DataFrame 반환 (잘못된 티커)
        mock_download.return_value = pd.DataFrame()
        
        with pytest.raises(DataNotFoundError):
            self.data_fetcher.get_stock_data(
                ticker="INVALID_TICKER",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31)
            )
    
    @patch('app.utils.data_fetcher.yf.download')
    def test_get_stock_data_insufficient_data(self, mock_download):
        """불충분한 데이터 테스트"""
        # 매우 적은 데이터포인트
        insufficient_data = pd.DataFrame({
            'Close': [100.0],
            'Volume': [1000000]
        }, index=[pd.Timestamp('2023-01-01')])
        
        mock_download.return_value = insufficient_data
        
        with pytest.raises(DataNotFoundError):
            self.data_fetcher.get_stock_data(
                ticker="AAPL",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31)
            )
    
    def test_validate_date_range(self):
        """날짜 범위 검증 테스트"""
        # 유효한 날짜 범위
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        # 예외가 발생하지 않아야 함
        self.data_fetcher.get_stock_data("AAPL", start_date, end_date)
        
        # 잘못된 날짜 범위 (시작일이 종료일보다 늦음)
        with pytest.raises(ValueError):
            self.data_fetcher.get_stock_data("AAPL", end_date, start_date)
