"""
PortfolioManagerService Helper Methods Unit Tests

Tests the static helper methods in PortfolioManagerService.
These are pure functions that perform calculations without I/O.
"""
import pytest
import numpy as np
from datetime import datetime, date
from typing import Dict, Any

from app.services.portfolio_manager_service import PortfolioManagerService


@pytest.mark.unit
class TestCalculateWeightedStats:
    """Test PortfolioManagerService._calculate_weighted_stats() static method"""

    def test_calculate_weighted_stats_with_valid_portfolio(self):
        """Test weighted statistics calculation with valid portfolio results"""
        portfolio_results = {
            'AAPL': {
                'symbol': 'AAPL',
                'weight': 0.4,
                'strategy_stats': {
                    'total_trades': 10,
                    'win_rate_pct': 60.0,
                    'max_drawdown_pct': -10.5,
                    'sharpe_ratio': 1.5
                }
            },
            'TSLA': {
                'symbol': 'TSLA',
                'weight': 0.6,
                'strategy_stats': {
                    'total_trades': 15,
                    'win_rate_pct': 55.0,
                    'max_drawdown_pct': -15.0,
                    'sharpe_ratio': 1.2
                }
            }
        }

        stats = PortfolioManagerService._calculate_weighted_stats(portfolio_results)

        # Total trades: 10 + 15 = 25
        assert stats['total_trades'] == 25

        # Weighted win rate: 0.4 * 60.0 + 0.6 * 55.0 = 24 + 33 = 57.0
        assert stats['weighted_win_rate'] == pytest.approx(57.0)

        # Weighted max drawdown: 0.4 * 10.5 + 0.6 * 15.0 = 4.2 + 9.0 = 13.2
        assert stats['weighted_max_drawdown'] == pytest.approx(13.2)

        # Weighted sharpe: 0.4 * 1.5 + 0.6 * 1.2 = 0.6 + 0.72 = 1.32
        assert stats['weighted_sharpe_ratio'] == pytest.approx(1.32)

    def test_calculate_weighted_stats_with_three_assets(self):
        """Test weighted stats with three assets"""
        portfolio_results = {
            'AAPL': {
                'weight': 0.3,
                'strategy_stats': {
                    'total_trades': 8,
                    'win_rate_pct': 65.0,
                    'max_drawdown_pct': -8.0,
                    'sharpe_ratio': 1.8
                }
            },
            'GOOGL': {
                'weight': 0.3,
                'strategy_stats': {
                    'total_trades': 12,
                    'win_rate_pct': 50.0,
                    'max_drawdown_pct': -12.0,
                    'sharpe_ratio': 1.3
                }
            },
            'MSFT': {
                'weight': 0.4,
                'strategy_stats': {
                    'total_trades': 10,
                    'win_rate_pct': 70.0,
                    'max_drawdown_pct': -5.0,
                    'sharpe_ratio': 2.0
                }
            }
        }

        stats = PortfolioManagerService._calculate_weighted_stats(portfolio_results)

        assert stats['total_trades'] == 30
        # 0.3 * 65 + 0.3 * 50 + 0.4 * 70 = 19.5 + 15 + 28 = 62.5
        assert stats['weighted_win_rate'] == pytest.approx(62.5)

    def test_calculate_weighted_stats_with_missing_fields(self):
        """Test that missing fields default to 0"""
        portfolio_results = {
            'AAPL': {
                'weight': 1.0,
                'strategy_stats': {}
            }
        }

        stats = PortfolioManagerService._calculate_weighted_stats(portfolio_results)

        assert stats['total_trades'] == 0
        assert stats['weighted_win_rate'] == 0.0
        assert stats['weighted_max_drawdown'] == 0.0
        assert stats['weighted_sharpe_ratio'] == 0.0

    def test_calculate_weighted_stats_with_equal_weights(self):
        """Test weighted stats with equal weights (simple average)"""
        portfolio_results = {
            'AAPL': {
                'weight': 0.5,
                'strategy_stats': {
                    'total_trades': 10,
                    'win_rate_pct': 60.0,
                    'max_drawdown_pct': -10.0,
                    'sharpe_ratio': 1.5
                }
            },
            'TSLA': {
                'weight': 0.5,
                'strategy_stats': {
                    'total_trades': 10,
                    'win_rate_pct': 40.0,
                    'max_drawdown_pct': -20.0,
                    'sharpe_ratio': 0.5
                }
            }
        }

        stats = PortfolioManagerService._calculate_weighted_stats(portfolio_results)

        # With equal weights, should be simple average
        assert stats['weighted_win_rate'] == pytest.approx(50.0)
        assert stats['weighted_max_drawdown'] == pytest.approx(15.0)
        assert stats['weighted_sharpe_ratio'] == pytest.approx(1.0)


@pytest.mark.unit
class TestCalculateDailyReturnStats:
    """Test PortfolioManagerService._calculate_daily_return_stats() static method"""

    def test_calculate_daily_return_stats_with_mixed_returns(self):
        """Test daily return statistics with mixed positive/negative returns"""
        daily_returns = {
            '2023-01-01': 0.02,   # +2%
            '2023-01-02': -0.01,  # -1%
            '2023-01-03': 0.03,   # +3%
            '2023-01-04': 0.01,   # +1%
            '2023-01-05': -0.02,  # -2%
        }

        stats = PortfolioManagerService._calculate_daily_return_stats(daily_returns)

        # Annual volatility: std([0.02, -0.01, 0.03, 0.01, -0.02]) * sqrt(252)
        returns_list = [0.02, -0.01, 0.03, 0.01, -0.02]
        expected_volatility = np.std(returns_list) * np.sqrt(252)
        assert stats['annual_volatility'] == pytest.approx(expected_volatility, rel=0.01)

        # Profit factor: (0.02 + 0.03 + 0.01) / (0.01 + 0.02) = 0.06 / 0.03 = 2.0
        assert stats['profit_factor'] == pytest.approx(2.0)

        # Positive days: 3, Negative days: 2
        assert stats['positive_days'] == 3
        assert stats['negative_days'] == 2

    def test_calculate_daily_return_stats_all_positive(self):
        """Test with all positive returns"""
        daily_returns = {
            '2023-01-01': 0.01,
            '2023-01-02': 0.02,
            '2023-01-03': 0.015,
        }

        stats = PortfolioManagerService._calculate_daily_return_stats(daily_returns)

        # No losses, so profit factor should be 0.0 (division by zero handling)
        assert stats['profit_factor'] == 0.0
        assert stats['positive_days'] == 3
        assert stats['negative_days'] == 0

    def test_calculate_daily_return_stats_all_negative(self):
        """Test with all negative returns"""
        daily_returns = {
            '2023-01-01': -0.01,
            '2023-01-02': -0.02,
            '2023-01-03': -0.015,
        }

        stats = PortfolioManagerService._calculate_daily_return_stats(daily_returns)

        # No gains, so profit factor should be 0.0
        assert stats['profit_factor'] == 0.0
        assert stats['positive_days'] == 0
        assert stats['negative_days'] == 3

    def test_calculate_daily_return_stats_single_return(self):
        """Test with single return (edge case for volatility)"""
        daily_returns = {
            '2023-01-01': 0.05
        }

        stats = PortfolioManagerService._calculate_daily_return_stats(daily_returns)

        # With single value, volatility should be 0
        assert stats['annual_volatility'] == 0.0
        assert stats['positive_days'] == 1
        assert stats['negative_days'] == 0

    def test_calculate_daily_return_stats_with_zeros(self):
        """Test with zero returns"""
        daily_returns = {
            '2023-01-01': 0.0,
            '2023-01-02': 0.01,
            '2023-01-03': 0.0,
            '2023-01-04': -0.01,
        }

        stats = PortfolioManagerService._calculate_daily_return_stats(daily_returns)

        # Zeros should not count as positive or negative
        assert stats['positive_days'] == 1
        assert stats['negative_days'] == 1


@pytest.mark.unit
class TestFormatIndividualResultsList:
    """Test PortfolioManagerService._format_individual_results_list() static method"""

    def test_format_strategy_mode_returns_correct_structure(self):
        """Test format for strategy mode with all fields"""
        individual_returns = {
            'AAPL': {
                'symbol': 'AAPL',
                'weight': 0.5,
                'amount': 5000.0,
                'return': 20.0,
                'final_value': 6000.0,
                'trades': 8,
                'win_rate': 62.5
            },
            'TSLA': {
                'symbol': 'TSLA',
                'weight': 0.5,
                'amount': 5000.0,
                'return': 15.0,
                'final_value': 5750.0,
                'trades': 12,
                'win_rate': 58.3
            }
        }

        portfolio_results = {
            'AAPL': {
                'strategy_stats': {
                    'sharpe_ratio': 1.5
                }
            },
            'TSLA': {
                'strategy_stats': {
                    'sharpe_ratio': 1.2
                }
            }
        }

        results = PortfolioManagerService._format_individual_results_list(
            individual_returns, portfolio_results, mode='strategy'
        )

        assert len(results) == 2

        # Check AAPL result
        aapl_result = next(r for r in results if r['ticker'] == 'AAPL')
        assert aapl_result['final_equity'] == 6000.0
        assert aapl_result['total_return_pct'] == 20.0
        assert aapl_result['sharpe_ratio'] == 1.5
        assert aapl_result['weight'] == 0.5
        assert aapl_result['amount'] == 5000.0
        assert aapl_result['trades'] == 8
        assert aapl_result['win_rate'] == 62.5

    def test_format_buy_hold_mode_returns_correct_structure(self):
        """Test format for buy_hold mode"""
        individual_returns = {
            'AAPL': {
                'symbol': 'AAPL',
                'weight': 0.4,
                'amount': 4000.0,
                'return': 25.0
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'weight': 0.6,
                'amount': 6000.0,
                'return': 18.0
            }
        }

        results = PortfolioManagerService._format_individual_results_list(
            individual_returns, mode='buy_hold'
        )

        assert len(results) == 2

        # Check AAPL result
        aapl_result = next(r for r in results if r['ticker'] == 'AAPL')
        # final_equity = amount + (amount * return / 100) = 4000 + 1000 = 5000
        assert aapl_result['final_equity'] == 5000.0
        assert aapl_result['total_return_pct'] == 25.0
        assert aapl_result['sharpe_ratio'] == 0.0  # Not calculated in buy_hold
        assert aapl_result['trades'] == 1
        assert aapl_result['win_rate'] == 100.0  # Positive return

    def test_format_buy_hold_mode_with_negative_return(self):
        """Test buy_hold mode with negative return"""
        individual_returns = {
            'TSLA': {
                'symbol': 'TSLA',
                'weight': 1.0,
                'amount': 10000.0,
                'return': -10.0
            }
        }

        results = PortfolioManagerService._format_individual_results_list(
            individual_returns, mode='buy_hold'
        )

        tsla_result = results[0]
        # final_equity = 10000 + (10000 * -10 / 100) = 10000 - 1000 = 9000
        assert tsla_result['final_equity'] == 9000.0
        assert tsla_result['win_rate'] == 0.0  # Negative return

    def test_format_buy_hold_mode_with_cash(self):
        """Test buy_hold mode with cash asset"""
        individual_returns = {
            'CASH': {
                'symbol': '',  # Empty symbol for cash
                'weight': 0.2,
                'amount': 2000.0,
                'return': 0.0
            },
            'AAPL': {
                'symbol': 'AAPL',
                'weight': 0.8,
                'amount': 8000.0,
                'return': 15.0
            }
        }

        results = PortfolioManagerService._format_individual_results_list(
            individual_returns, mode='buy_hold'
        )

        # Check CASH result
        cash_result = next(r for r in results if r['ticker'] == 'CASH')
        assert cash_result['final_equity'] == 2000.0
        assert cash_result['total_return_pct'] == 0.0
        # Note: buy_hold mode sets trades=1 if symbol exists, even for cash (line 155)
        # This matches the actual implementation behavior
        assert cash_result['win_rate'] == 0.0  # 0 return means win_rate is 0

    def test_format_strategy_mode_without_portfolio_results(self):
        """Test strategy mode without portfolio_results (sharpe defaults to 0)"""
        individual_returns = {
            'NVDA': {
                'symbol': 'NVDA',
                'weight': 1.0,
                'amount': 10000.0,
                'return': 30.0,
                'final_value': 13000.0,
                'trades': 5,
                'win_rate': 80.0
            }
        }

        results = PortfolioManagerService._format_individual_results_list(
            individual_returns, portfolio_results=None, mode='strategy'
        )

        nvda_result = results[0]
        assert nvda_result['sharpe_ratio'] == 0.0  # Default when no portfolio_results

    def test_format_empty_individual_returns(self):
        """Test with empty individual_returns"""
        results = PortfolioManagerService._format_individual_results_list(
            {}, mode='strategy'
        )

        assert results == []

    def test_format_multiple_assets_preserves_all(self):
        """Test that all assets are preserved in output"""
        individual_returns = {
            f'STOCK{i}': {
                'symbol': f'STOCK{i}',
                'weight': 0.1,
                'amount': 1000.0,
                'return': 10.0 * i,
                'final_value': 1000.0 + (100.0 * i),
                'trades': i,
                'win_rate': 50.0 + i
            }
            for i in range(1, 11)  # 10 stocks
        }

        results = PortfolioManagerService._format_individual_results_list(
            individual_returns, mode='strategy'
        )

        assert len(results) == 10
        tickers = [r['ticker'] for r in results]
        assert all(f'STOCK{i}' in tickers for i in range(1, 11))
