"""
PortfolioManagerService Helper Methods Unit Tests

Tests the static helper methods in PortfolioManagerService.
These are pure functions that perform calculations without I/O.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any

from app.services.portfolio_manager_service import PortfolioManagerService
from app.utils.metrics_math import annualized_volatility, daily_profit_factor, up_day_ratio


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

        # Trade win rate (거래 수 가중): (10 * 60 + 15 * 55) / 25 = 1425 / 25 = 57.0
        assert stats['trade_win_rate'] == pytest.approx(57.0)

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
        # 거래 수 가중(투자금 비중이 아님): (8 * 65 + 12 * 50 + 10 * 70) / 30 = 1820 / 30
        assert stats['trade_win_rate'] == pytest.approx(1820 / 30)

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
        # 거래가 없으면 승률은 정의되지 않는다 (0%가 아니다)
        assert stats['trade_win_rate'] is None
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

        # With equal trade counts, should be simple average
        assert stats['trade_win_rate'] == pytest.approx(50.0)
        assert stats['weighted_max_drawdown'] == pytest.approx(15.0)
        assert stats['weighted_sharpe_ratio'] == pytest.approx(1.0)


@pytest.mark.unit
class TestDailyReturnDefinitions:
    """전략 경로의 일 기준 통계는 이제 metrics_math 헬퍼(PortfolioCalculator 경유)로
    buy&hold와 같은 정의를 쓴다 (A-09). 과거 _calculate_daily_return_stats를 검증하던
    입력을 그대로 새 헬퍼에 넣어 본다."""

    def test_mixed_returns(self):
        returns = pd.Series([0.02, -0.01, 0.03, 0.01, -0.02])

        # (0.02 + 0.03 + 0.01) / (0.01 + 0.02) = 2.0
        assert daily_profit_factor(returns) == pytest.approx(2.0)
        assert up_day_ratio(returns) == pytest.approx(60.0)
        # 표본 표준편차(ddof=1) — buy&hold 경로와 같은 추정량
        expected_volatility = returns.std() * np.sqrt(252) * 100
        assert annualized_volatility(returns) == pytest.approx(expected_volatility)

    def test_all_positive_profit_factor_is_undefined(self):
        """수정 전: 전략 경로 0.0, buy&hold 경로 2.0으로 서로 달랐다."""
        assert daily_profit_factor(pd.Series([0.01, 0.02, 0.015])) is None

    def test_all_negative_profit_factor_is_zero(self):
        assert daily_profit_factor(pd.Series([-0.01, -0.02, -0.015])) == 0.0

    def test_single_return_volatility_is_zero(self):
        assert annualized_volatility(pd.Series([0.05])) == 0.0

    def test_zeros_are_neither_up_nor_down_days(self):
        returns = pd.Series([0.0, 0.01, 0.0, -0.01])

        assert up_day_ratio(returns) == pytest.approx(25.0)
        assert daily_profit_factor(returns) == pytest.approx(1.0)


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
        # buy&hold 포지션은 청산된 거래가 없어 거래 승률을 정의할 수 없다.
        # 과거에는 수익이면 100, 아니면 0을 지어냈다
        assert aapl_result['win_rate'] is None

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
        assert tsla_result['win_rate'] is None  # 손실이어도 0%가 아니라 계산 불가

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
        assert cash_result['win_rate'] is None

    def test_format_strategy_mode_without_trades_has_none_win_rate(self):
        """거래가 없는 종목(신호 없음)과 현금은 거래 승률이 없다 — 0%가 아니라 None.
        포트폴리오 Trade_Win_Rate(거래 없으면 None)와 같은 규칙이다."""
        individual_returns = {
            'NVDA': {
                'symbol': 'NVDA', 'weight': 0.5, 'amount': 5000.0, 'return': 0.0,
                'final_value': 5000.0, 'trades': 0, 'win_rate': 0.0,
            },
            'CASH': {
                'symbol': 'CASH', 'weight': 0.5, 'amount': 5000.0, 'return': 0.0,
                'final_value': 5000.0, 'trades': 0, 'win_rate': 0.0,
            },
        }

        results = PortfolioManagerService._format_individual_results_list(
            individual_returns, mode='strategy'
        )

        assert [r['win_rate'] for r in results] == [None, None]

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
