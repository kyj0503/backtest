"""
CurrencyConverter Unit Tests

Tests the currency conversion utilities for multi-currency support.
All external I/O (yfinance, DB) are mocked.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.utils.currency_converter import CurrencyConverter


@pytest.mark.unit
class TestGetConversionMultiplier:
    """Test CurrencyConverter.get_conversion_multiplier() static method"""

    def test_eur_returns_exchange_rate_directly(self):
        """Test EUR (and other USD-quoted currencies) return rate directly"""
        multiplier = CurrencyConverter.get_conversion_multiplier('EUR', 1.10)
        assert multiplier == 1.10

    def test_gbp_returns_exchange_rate_directly(self):
        """Test GBP returns exchange rate directly"""
        multiplier = CurrencyConverter.get_conversion_multiplier('GBP', 1.25)
        assert multiplier == 1.25

    def test_aud_returns_exchange_rate_directly(self):
        """Test AUD returns exchange rate directly"""
        multiplier = CurrencyConverter.get_conversion_multiplier('AUD', 0.65)
        assert multiplier == 0.65

    def test_cad_returns_exchange_rate_directly(self):
        """Test CAD returns exchange rate directly"""
        multiplier = CurrencyConverter.get_conversion_multiplier('CAD', 0.75)
        assert multiplier == 0.75

    def test_chf_returns_exchange_rate_directly(self):
        """Test CHF returns exchange rate directly"""
        multiplier = CurrencyConverter.get_conversion_multiplier('CHF', 1.12)
        assert multiplier == 1.12

    def test_krw_returns_inverse_rate(self):
        """Test KRW returns 1/rate (direct quote conversion)"""
        multiplier = CurrencyConverter.get_conversion_multiplier('KRW', 1300.0)
        assert multiplier == pytest.approx(1.0 / 1300.0)

    def test_jpy_returns_inverse_rate(self):
        """Test JPY returns 1/rate"""
        multiplier = CurrencyConverter.get_conversion_multiplier('JPY', 150.0)
        assert multiplier == pytest.approx(1.0 / 150.0)

    def test_zero_exchange_rate_returns_one(self):
        """Test that zero exchange rate returns 1.0 to avoid division by zero"""
        multiplier = CurrencyConverter.get_conversion_multiplier('KRW', 0.0)
        assert multiplier == 1.0


@pytest.mark.unit
class TestConvertDataframeToUsd:
    """Test CurrencyConverter.convert_dataframe_to_usd() method"""

    @pytest.fixture
    def mock_stock_repository(self):
        """Mock stock repository"""
        repo = Mock()
        repo.get_ticker_info = Mock(return_value={'currency': 'KRW'})
        repo.load_stock_data = Mock()
        return repo

    @pytest.fixture
    def converter(self, mock_stock_repository):
        """CurrencyConverter instance with mocked repository"""
        converter = CurrencyConverter()
        converter.stock_repository = mock_stock_repository
        return converter

    @pytest.fixture
    def sample_krw_data(self):
        """Sample price data in KRW"""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'Open': [50000.0] * 10,
            'High': [51000.0] * 10,
            'Low': [49000.0] * 10,
            'Close': [50500.0] * 10,
            'Volume': [1000000] * 10
        }, index=dates)

    @pytest.fixture
    def sample_exchange_data(self):
        """Sample exchange rate data (1 USD = 1300 KRW)"""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'Close': [1300.0] * 10
        }, index=dates)

    @pytest.mark.asyncio
    async def test_usd_currency_returns_data_unchanged(self, converter, sample_krw_data):
        """Test that USD currency returns original data without conversion"""
        converter.stock_repository.get_ticker_info.return_value = {'currency': 'USD'}

        result = await converter.convert_dataframe_to_usd(
            ticker='AAPL',
            data=sample_krw_data.copy(),
            start_date='2023-01-01',
            end_date='2023-01-10'
        )

        # Data should be unchanged
        pd.testing.assert_frame_equal(result, sample_krw_data)

    @pytest.mark.asyncio
    async def test_krw_converts_correctly_using_vectorized_operation(
        self, converter, sample_krw_data, sample_exchange_data, mock_stock_repository
    ):
        """Test KRW conversion using vectorized pandas operation"""
        converter.stock_repository.get_ticker_info.return_value = {'currency': 'KRW'}

        # Mock exchange rate loading
        with patch.object(converter, 'load_and_prepare_exchange_rates', new=AsyncMock(return_value=sample_exchange_data)):
            result = await converter.convert_dataframe_to_usd(
                ticker='005930.KS',
                data=sample_krw_data.copy(),
                start_date='2023-01-01',
                end_date='2023-01-10'
            )

        # Prices should be divided by exchange rate
        # 50000 KRW / 1300 = ~38.46 USD
        expected_close = 50500.0 / 1300.0
        assert result['Close'].iloc[0] == pytest.approx(expected_close, rel=0.01)

    @pytest.mark.asyncio
    async def test_unsupported_currency_returns_data_unchanged(self, converter, sample_krw_data):
        """Test unsupported currency returns original data with warning"""
        converter.stock_repository.get_ticker_info.return_value = {'currency': 'XXX'}

        result = await converter.convert_dataframe_to_usd(
            ticker='TEST',
            data=sample_krw_data.copy(),
            start_date='2023-01-01',
            end_date='2023-01-10'
        )

        # Data should be unchanged
        pd.testing.assert_frame_equal(result, sample_krw_data)

    @pytest.mark.asyncio
    async def test_conversion_error_raises_instead_of_returning_unconverted_data(
        self, converter, sample_krw_data
    ):
        """[P2-02] 환율 로딩이 실패해도 원본(KRW) 데이터를 조용히 그대로
        반환해서는 안 된다. USD로 변환되지 않은 원화 크기의 가격이 성공한
        것처럼 호출자에게 전달되면 하류 계산(예: USD 현금과의 합산)이 조용히
        오염되므로, 예외를 발생시켜 실패를 명시적으로 알려야 한다.

        (구 계약: 원본 데이터를 그대로 반환하는 test_conversion_error_returns_
        original_data -- 이 테스트가 그 계약을 대체한다.)
        """
        converter.stock_repository.get_ticker_info.return_value = {'currency': 'KRW'}

        # Force error in exchange rate loading
        with patch.object(converter, 'load_and_prepare_exchange_rates', side_effect=Exception("Network error")):
            with pytest.raises(ValueError, match="KRW"):
                await converter.convert_dataframe_to_usd(
                    ticker='005930.KS',
                    data=sample_krw_data.copy(),
                    start_date='2023-01-01',
                    end_date='2023-01-10'
                )


@pytest.mark.unit
class TestLoadAndPrepareExchangeRates:
    """Test CurrencyConverter.load_and_prepare_exchange_rates() method"""

    @pytest.fixture
    def mock_stock_repository(self):
        """Mock stock repository"""
        repo = Mock()
        return repo

    @pytest.fixture
    def converter(self, mock_stock_repository):
        """CurrencyConverter instance"""
        converter = CurrencyConverter()
        converter.stock_repository = mock_stock_repository
        return converter

    @pytest.fixture
    def sample_exchange_data(self):
        """Sample exchange rate DataFrame"""
        dates = pd.date_range(start='2022-12-01', periods=90, freq='D')
        return pd.DataFrame({
            'Open': np.linspace(1280, 1320, 90),
            'High': np.linspace(1285, 1325, 90),
            'Low': np.linspace(1275, 1315, 90),
            'Close': np.linspace(1280, 1320, 90),
            'Volume': [100000] * 90
        }, index=dates)

    @pytest.mark.asyncio
    async def test_usd_raises_valueerror(self, converter):
        """Test that USD currency raises ValueError (no conversion needed)"""
        with pytest.raises(ValueError, match="USD는 환율 변환이 필요하지 않습니다"):
            await converter.load_and_prepare_exchange_rates(
                currency='USD',
                start_date='2023-01-01',
                end_date='2023-12-31'
            )

    @pytest.mark.asyncio
    async def test_unsupported_currency_raises_valueerror(self, converter):
        """Test that unsupported currency raises ValueError"""
        with pytest.raises(ValueError, match="지원하지 않는 통화"):
            await converter.load_and_prepare_exchange_rates(
                currency='XXX',
                start_date='2023-01-01',
                end_date='2023-12-31'
            )

    @pytest.mark.asyncio
    async def test_successful_load_returns_dataframe(
        self, converter, mock_stock_repository, sample_exchange_data
    ):
        """Test successful exchange rate loading returns DataFrame"""
        # Mock stock repository to return exchange data
        mock_stock_repository.load_stock_data = Mock(return_value=sample_exchange_data)

        result = await converter.load_and_prepare_exchange_rates(
            currency='KRW',
            start_date='2023-01-01',
            end_date='2023-02-28',
            buffer_days=60
        )

        assert isinstance(result, pd.DataFrame)
        assert 'Close' in result.columns
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_empty_exchange_data_raises_valueerror(
        self, converter, mock_stock_repository
    ):
        """Test that empty exchange data raises ValueError"""
        mock_stock_repository.load_stock_data = Mock(return_value=pd.DataFrame())

        with pytest.raises(ValueError, match="환율 데이터를 로드할 수 없습니다"):
            await converter.load_and_prepare_exchange_rates(
                currency='KRW',
                start_date='2023-01-01',
                end_date='2023-02-28'
            )

    @pytest.mark.asyncio
    async def test_none_exchange_data_raises_valueerror(
        self, converter, mock_stock_repository
    ):
        """Test that None exchange data raises ValueError"""
        mock_stock_repository.load_stock_data = Mock(return_value=None)

        with pytest.raises(ValueError, match="환율 데이터를 로드할 수 없습니다"):
            await converter.load_and_prepare_exchange_rates(
                currency='JPY',
                start_date='2023-01-01',
                end_date='2023-02-28'
            )


@pytest.mark.unit
class TestCurrencyConverterEdgeCases:
    """Test edge cases in currency conversion"""

    @pytest.fixture
    def converter(self):
        """CurrencyConverter instance with minimal mocking"""
        converter = CurrencyConverter()
        converter.stock_repository = Mock()
        return converter

    @pytest.mark.asyncio
    async def test_empty_exchange_data_in_conversion_raises(self, converter):
        """[P2-02] 환율 데이터가 비어 있어 로딩이 실패하면(load_and_prepare_
        exchange_rates가 ValueError를 던지는 경우) 원본 데이터로 조용히
        폴백하지 않고 예외를 발생시켜야 한다."""
        converter.stock_repository.get_ticker_info = Mock(return_value={'currency': 'KRW'})

        data = pd.DataFrame({
            'Open': [100],
            'High': [110],
            'Low': [90],
            'Close': [105],
            'Volume': [1000]
        }, index=pd.date_range('2023-01-01', periods=1))

        # Mock empty exchange data
        with patch.object(converter, 'load_and_prepare_exchange_rates', side_effect=ValueError("No data")):
            with pytest.raises(ValueError):
                await converter.convert_dataframe_to_usd(
                    ticker='TEST',
                    data=data.copy(),
                    start_date='2023-01-01',
                    end_date='2023-01-01'
                )

    def test_zero_exchange_rate_edge_case(self):
        """Test that zero exchange rate is handled safely"""
        # Should return 1.0 to avoid division by zero
        multiplier = CurrencyConverter.get_conversion_multiplier('KRW', 0.0)
        assert multiplier == 1.0

        # EUR/GBP with zero should still return zero
        multiplier_eur = CurrencyConverter.get_conversion_multiplier('EUR', 0.0)
        assert multiplier_eur == 0.0
