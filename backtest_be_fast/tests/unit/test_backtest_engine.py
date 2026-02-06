"""
BacktestEngine Unit Tests

Tests the core backtesting engine that wraps backtesting.py library.
All external dependencies (yfinance, DB, file I/O) are mocked.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backtesting import Strategy

from app.services.backtest_engine import BacktestEngine
from app.schemas.requests import BacktestRequest, StrategyType
from app.schemas.responses import BacktestResult
from fastapi import HTTPException


@pytest.mark.unit
class TestBacktestEngineRunBacktest:
    """Test BacktestEngine.run_backtest() method"""

    @pytest.fixture
    def mock_data_repository(self):
        """Mock data repository"""
        repo = Mock()
        repo.get_stock_data = AsyncMock()
        return repo

    @pytest.fixture
    def mock_strategy_service(self):
        """Mock strategy service"""
        service = Mock()

        # Create a simple mock strategy class
        class MockStrategy(Strategy):
            def init(self):
                pass
            def next(self):
                pass

        service.get_strategy_class = Mock(return_value=MockStrategy)
        return service

    @pytest.fixture
    def mock_validation_service(self):
        """Mock validation service"""
        service = Mock()
        service.validate_backtest_request = Mock()
        return service

    @pytest.fixture
    def sample_price_data(self):
        """Sample price DataFrame"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        prices = np.linspace(100, 150, 50)
        return pd.DataFrame({
            'Open': prices,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': [1000000] * 50
        }, index=dates)

    @pytest.fixture
    def backtest_request(self):
        """Sample backtest request"""
        return BacktestRequest(
            ticker='AAPL',
            start_date='2023-01-01',
            end_date='2023-02-19',
            initial_cash=10000.0,
            strategy=StrategyType.BUY_HOLD_STRATEGY,
            commission=0.002
        )

    @pytest.fixture
    def mock_backtest_stats(self):
        """Mock successful backtest stats from backtesting.py"""
        stats = pd.Series({
            '# Trades': 5,
            'Return [%]': 25.5,
            'Return (Ann.) [%]': 35.2,
            'Buy & Hold Return [%]': 50.0,
            'Equity Final [$]': 12550.0,
            'Volatility [%]': 15.3,
            'Sharpe Ratio': 1.45,
            'Sortino Ratio': 2.1,
            'Calmar Ratio': 1.8,
            'Max. Drawdown [%]': -8.5,
            'Avg. Drawdown [%]': -3.2,
            'Win Rate [%]': 60.0,
            'Profit Factor': 2.3,
            'Avg. Trade [%]': 5.1,
            'Best Trade [%]': 12.5,
            'Worst Trade [%]': -4.2,
            'SQN': 1.8
        })
        return stats

    @pytest.mark.asyncio
    async def test_run_backtest_success_returns_valid_result(
        self,
        mock_data_repository,
        mock_strategy_service,
        mock_validation_service,
        sample_price_data,
        backtest_request,
        mock_backtest_stats
    ):
        """Test successful backtest execution returns BacktestResult"""
        # Setup engine with mocks
        engine = BacktestEngine(
            data_repository=mock_data_repository,
            strategy_service_instance=mock_strategy_service,
            validation_service_instance=mock_validation_service
        )

        # Mock data loading
        mock_data_repository.get_stock_data.return_value = sample_price_data

        # Mock currency conversion (return unchanged for USD)
        with patch('app.services.backtest_engine.currency_converter') as mock_converter:
            mock_converter.convert_dataframe_to_usd = AsyncMock(return_value=sample_price_data)

            # Mock backtest execution
            with patch.object(engine, '_execute_backtest', return_value=mock_backtest_stats):
                result = await engine.run_backtest(backtest_request)

        # Assertions
        assert isinstance(result, BacktestResult)
        assert result.ticker == 'AAPL'
        assert result.strategy == StrategyType.BUY_HOLD_STRATEGY
        assert result.total_return_pct == 25.5
        assert result.final_equity == 12550.0
        assert result.total_trades == 5
        assert result.sharpe_ratio == 1.45

    @pytest.mark.asyncio
    async def test_run_backtest_invalid_result_reraises_as_http_exception(
        self,
        mock_data_repository,
        mock_strategy_service,
        mock_validation_service,
        sample_price_data,
        backtest_request
    ):
        """Test that invalid backtest result triggers fallback logic (changed after recent fix)

        Note: After recent fix, accessing missing keys in stats now raises HTTPException
        rather than falling back silently.
        """
        engine = BacktestEngine(
            data_repository=mock_data_repository,
            strategy_service_instance=mock_strategy_service,
            validation_service_instance=mock_validation_service
        )

        mock_data_repository.get_stock_data.return_value = sample_price_data

        # Mock invalid result (missing '# Trades' key)
        invalid_stats = pd.Series({'Return [%]': 0.0})

        with patch('app.services.backtest_engine.currency_converter') as mock_converter:
            mock_converter.convert_dataframe_to_usd = AsyncMock(return_value=sample_price_data)

            with patch.object(engine, '_execute_backtest', return_value=invalid_stats):
                # After recent fix, this should raise HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    await engine.run_backtest(backtest_request)

                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_run_backtest_unknown_exception_reraises(
        self,
        mock_data_repository,
        mock_strategy_service,
        mock_validation_service,
        backtest_request
    ):
        """Test that unknown exceptions are re-raised (recent fix)"""
        engine = BacktestEngine(
            data_repository=mock_data_repository,
            strategy_service_instance=mock_strategy_service,
            validation_service_instance=mock_validation_service
        )

        # Mock unexpected error during data loading
        mock_data_repository.get_stock_data.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await engine.run_backtest(backtest_request)

        assert exc_info.value.status_code == 500
        assert "백테스트 실행 실패" in exc_info.value.detail


@pytest.mark.unit
class TestBacktestEngineBuildStrategy:
    """Test BacktestEngine._build_strategy() method"""

    @pytest.fixture
    def mock_strategy_service(self):
        """Mock strategy service with base strategy"""
        service = Mock()

        class BaseStrategy(Strategy):
            sma_short = 10
            sma_long = 20

            def init(self):
                pass

            def next(self):
                pass

        service.get_strategy_class = Mock(return_value=BaseStrategy)
        service.validate_strategy_params = Mock(side_effect=lambda name, params: params)
        return service

    @pytest.fixture
    def engine(self, mock_strategy_service):
        """BacktestEngine instance with mocked strategy service"""
        return BacktestEngine(strategy_service_instance=mock_strategy_service)

    def test_build_strategy_no_params_returns_base_class(self, engine, mock_strategy_service):
        """Test that _build_strategy returns base class when no params provided"""
        base_strategy = mock_strategy_service.get_strategy_class.return_value

        result = engine._build_strategy('sma_strategy', None)

        assert result == base_strategy
        assert result.sma_short == 10
        assert result.sma_long == 20

    def test_build_strategy_with_params_applies_overrides(self, engine, mock_strategy_service):
        """Test that _build_strategy applies parameter overrides correctly"""
        params = {'sma_short': 15, 'sma_long': 30}

        result = engine._build_strategy('sma_strategy', params)

        # Should return a new class with overridden values
        assert result != mock_strategy_service.get_strategy_class.return_value
        assert result.sma_short == 15
        assert result.sma_long == 30

    def test_build_strategy_ignores_non_attribute_params(self, engine, mock_strategy_service):
        """Test that _build_strategy ignores params that don't exist on base class"""
        params = {'sma_short': 15, 'invalid_param': 999}

        result = engine._build_strategy('sma_strategy', params)

        # Should only override valid attributes
        assert result.sma_short == 15
        assert not hasattr(result, 'invalid_param')


@pytest.mark.unit
class TestBacktestEngineConvertResultToResponse:
    """Test BacktestEngine._convert_result_to_response() method"""

    @pytest.fixture
    def engine(self):
        """BacktestEngine instance"""
        return BacktestEngine()

    @pytest.fixture
    def backtest_request(self):
        """Sample backtest request"""
        return BacktestRequest(
            ticker='TSLA',
            start_date='2023-01-01',
            end_date='2023-12-31',
            initial_cash=50000.0,
            strategy=StrategyType.SMA_STRATEGY,
            commission=0.001
        )

    @pytest.fixture
    def complete_stats(self):
        """Complete stats from backtesting.py with all fields"""
        return pd.Series({
            '# Trades': 12,
            'Return [%]': 45.8,
            'Return (Ann.) [%]': 48.2,
            'Buy & Hold Return [%]': 62.5,
            'Equity Final [$]': 72900.0,
            'Volatility [%]': 22.1,
            'Sharpe Ratio': 1.85,
            'Sortino Ratio': 2.45,
            'Calmar Ratio': 2.1,
            'Max. Drawdown [%]': -12.3,
            'Avg. Drawdown [%]': -4.5,
            'Win Rate [%]': 66.7,
            'Profit Factor': 2.8,
            'Avg. Trade [%]': 3.8,
            'Best Trade [%]': 15.2,
            'Worst Trade [%]': -6.1,
            'SQN': 2.2
        })

    def test_convert_result_properly_maps_all_stats_fields(
        self, engine, backtest_request, complete_stats
    ):
        """Test that _convert_result_to_response properly maps all backtesting.py stats"""
        result = engine._convert_result_to_response(complete_stats, backtest_request)

        # Basic info
        assert result.ticker == 'TSLA'
        assert result.strategy == StrategyType.SMA_STRATEGY
        assert result.start_date == '2023-01-01'
        assert result.end_date == '2023-12-31'
        assert result.duration_days == 364

        # Financial metrics
        assert result.initial_cash == 50000.0
        assert result.final_equity == 72900.0
        assert result.total_return_pct == 45.8
        assert result.annualized_return_pct == 48.2
        assert result.buy_and_hold_return_pct == 62.5
        assert result.cagr_pct == 48.2

        # Risk metrics
        assert result.volatility_pct == 22.1
        assert result.sharpe_ratio == 1.85
        assert result.sortino_ratio == 2.45
        assert result.calmar_ratio == 2.1
        assert result.max_drawdown_pct == -12.3
        assert result.avg_drawdown_pct == -4.5

        # Trading metrics
        assert result.total_trades == 12
        assert result.win_rate_pct == 66.7
        assert result.profit_factor == 2.8
        assert result.avg_trade_pct == 3.8
        assert result.best_trade_pct == 15.2
        assert result.worst_trade_pct == -6.1
        assert result.sqn == 2.2

    def test_convert_result_handles_missing_optional_fields(
        self, engine, backtest_request
    ):
        """Test that conversion handles missing optional fields gracefully"""
        minimal_stats = pd.Series({
            '# Trades': 3,
            'Return [%]': 10.0,
            'Equity Final [$]': 55000.0
        })

        result = engine._convert_result_to_response(minimal_stats, backtest_request)

        # Should use defaults for missing fields
        assert result.total_trades == 3
        assert result.total_return_pct == 10.0
        assert result.annualized_return_pct == 0.0
        assert result.sharpe_ratio == 0.0


@pytest.mark.unit
class TestBacktestEngineCreateFallbackResult:
    """Test BacktestEngine._create_fallback_result() method"""

    @pytest.fixture
    def engine(self):
        """BacktestEngine instance with mocked validation service"""
        validation_service = Mock()
        validation_service.create_fallback_stats = Mock(return_value={
            'Equity Final [$]': 10000.0,
            'Return [%]': 0.0,
            '# Trades': 0,
            'Win Rate [%]': 0.0,
            'Volatility [%]': 0.0,
            'Sharpe Ratio': 0.0,
            'Max. Drawdown [%]': 0.0
        })
        return BacktestEngine(validation_service_instance=validation_service)

    @pytest.fixture
    def backtest_request(self):
        """Sample backtest request"""
        return BacktestRequest(
            ticker='NVDA',
            start_date='2023-06-01',
            end_date='2023-07-01',
            initial_cash=25000.0,
            strategy=StrategyType.RSI_STRATEGY,
            commission=0.002
        )

    @pytest.fixture
    def sample_data(self):
        """Sample price data"""
        dates = pd.date_range(start='2023-06-01', periods=30, freq='D')
        return pd.DataFrame({
            'Close': np.linspace(100, 110, 30)
        }, index=dates)

    def test_create_fallback_result_returns_valid_backtest_result(
        self, engine, backtest_request, sample_data
    ):
        """Test that fallback result is a valid BacktestResult with correct ticker/dates"""
        result = engine._create_fallback_result(sample_data, backtest_request)

        assert isinstance(result, BacktestResult)
        assert result.ticker == 'NVDA'
        assert result.strategy == StrategyType.RSI_STRATEGY
        assert result.start_date == '2023-06-01'
        assert result.end_date == '2023-07-01'
        assert result.duration_days == 30
        assert result.initial_cash == 25000.0
        # Fallback uses the mocked value from create_fallback_stats
        assert result.final_equity == 10000.0  # From mocked create_fallback_stats
        assert result.total_return_pct == 0.0
        assert result.total_trades == 0

    def test_create_fallback_result_handles_exception_gracefully(
        self, engine, backtest_request
    ):
        """Test that fallback creation handles exceptions and returns minimal result"""
        # Force exception in create_fallback_stats
        engine.validation_service.create_fallback_stats.side_effect = Exception("Fallback error")

        result = engine._create_fallback_result(pd.DataFrame(), backtest_request)

        # Should still return a valid result
        assert isinstance(result, BacktestResult)
        assert result.ticker == 'NVDA'
        assert result.total_trades == 0
        assert result.final_equity == 25000.0
