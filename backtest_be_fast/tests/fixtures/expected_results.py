"""
테스트 예상 결과 데이터
백테스트 결과 검증을 위한 기준값들
"""

from datetime import date
from typing import Dict, Any, List
from decimal import Decimal


class ExpectedResults:
    """
    테스트 예상 결과 관리 클래스
    다양한 시나리오별 예상 결과값 제공
    """
    
    @staticmethod
    def get_backtest_result_ranges() -> Dict[str, Dict[str, Any]]:
        """
        백테스트 결과 허용 범위
        오프라인 모킹 데이터 특성상 정확한 값보다는 합리적 범위 검증
        """
        return {
            'buy_and_hold': {
                'total_return_pct': {'min': -50.0, 'max': 100.0},
                'sharpe_ratio': {'min': -3.0, 'max': 5.0},
                'max_drawdown_pct': {'min': -80.0, 'max': 0.0},  # 드로우다운은 음수값
                'total_trades': {'min': 0, 'max': 10},  # Buy & Hold는 거래 적음
                'win_rate_pct': {'min': 0.0, 'max': 100.0},
                'profit_factor': {'min': 0.0, 'max': 10.0}
            },
            'sma_crossover': {
                'total_return_pct': {'min': -80.0, 'max': 200.0},
                'sharpe_ratio': {'min': -5.0, 'max': 8.0},
                'max_drawdown_pct': {'min': -90.0, 'max': 0.0},  # 드로우다운은 음수값
                'total_trades': {'min': 0, 'max': 100},
                'win_rate_pct': {'min': 0.0, 'max': 100.0},
                'profit_factor': {'min': 0.0, 'max': 20.0}
            },
            'rsi_strategy': {
                'total_return_pct': {'min': -70.0, 'max': 150.0},
                'sharpe_ratio': {'min': -4.0, 'max': 6.0},
                'max_drawdown_pct': {'min': -85.0, 'max': 0.0},  # 드로우다운은 음수값
                'total_trades': {'min': 0, 'max': 200},
                'win_rate_pct': {'min': 20.0, 'max': 80.0},
                'profit_factor': {'min': 0.1, 'max': 15.0}
            },
            'bollinger_bands': {
                'total_return_pct': {'min': -60.0, 'max': 120.0},
                'sharpe_ratio': {'min': -3.5, 'max': 4.5},
                'max_drawdown_pct': {'min': -75.0, 'max': 0.0},  # 드로우다운은 음수값
                'total_trades': {'min': 0, 'max': 150},
                'win_rate_pct': {'min': 25.0, 'max': 75.0},
                'profit_factor': {'min': 0.2, 'max': 12.0}
            },
            'macd_strategy': {
                'total_return_pct': {'min': -75.0, 'max': 180.0},
                'sharpe_ratio': {'min': -4.5, 'max': 7.0},
                'max_drawdown_pct': {'min': -88.0, 'max': 0.0},  # 드로우다운은 음수값
                'total_trades': {'min': 0, 'max': 120},
                'win_rate_pct': {'min': 15.0, 'max': 85.0},
                'profit_factor': {'min': 0.1, 'max': 18.0}
            }
        }
    
    @staticmethod
    def get_data_quality_expectations() -> Dict[str, Any]:
        """
        데이터 품질 검증 기준
        """
        return {
            'ohlcv_columns': ['Open', 'High', 'Low', 'Close', 'Volume'],
            'price_ranges': {
                'AAPL': {'min': 50.0, 'max': 500.0},
                'GOOGL': {'min': 1000.0, 'max': 5000.0},
                'MSFT': {'min': 100.0, 'max': 800.0},
                'TSLA': {'min': 200.0, 'max': 2000.0}
            },
            'volume_ranges': {
                'min': 1000,  # 최소 거래량
                'max': 500000000  # 최대 거래량
            },
            'date_consistency': {
                'no_weekends': True,
                'no_gaps_over_7_days': True,
                'chronological_order': True
            },
            'ohlc_logic': {
                'high_gte_open': True,
                'high_gte_close': True,
                'low_lte_open': True,
                'low_lte_close': True,
                'high_gte_low': True
            },
            'decimal_precision': 4  # DECIMAL(19,4)
        }
    
    @staticmethod
    def get_performance_benchmarks() -> Dict[str, Dict[str, float]]:
        """
        성능 벤치마크 (실행 시간 목표)
        """
        return {
            'data_fetching': {
                'single_ticker_1year': 2.0,  # 2초 이내
                'single_ticker_5years': 5.0,  # 5초 이내
                'portfolio_5tickers_1year': 8.0  # 8초 이내
            },
            'backtest_execution': {
                'buy_and_hold_1year': 3.0,  # 3초 이내
                'sma_crossover_1year': 5.0,  # 5초 이내
                'complex_strategy_1year': 10.0  # 10초 이내
            },
            'api_response': {
                'chart_data_endpoint': 15.0,  # 15초 이내
                'portfolio_endpoint': 25.0,  # 25초 이내
                'optimization_endpoint': 60.0  # 60초 이내
            }
        }
    
    @staticmethod
    def get_error_scenarios() -> Dict[str, Dict[str, Any]]:
        """
        오류 시나리오별 예상 응답
        """
        return {
            'invalid_ticker': {
                'expected_status_code': [404, 422],
                'expected_error_types': ['DataNotFoundError', 'InvalidSymbolError'],
                'test_inputs': ['INVALID', 'NOTFOUND', '123INVALID']
            },
            'invalid_date_range': {
                'expected_status_code': [400, 422],
                'expected_error_types': ['ValidationError'],
                'test_inputs': [
                    {'start_date': '2023-12-31', 'end_date': '2023-01-01'},  # 역순
                    {'start_date': '1900-01-01', 'end_date': '1900-01-02'},  # 너무 과거
                    {'start_date': '2030-01-01', 'end_date': '2030-01-02'}   # 미래
                ]
            },
            'invalid_strategy': {
                'expected_status_code': [400, 422],
                'expected_error_types': ['ValidationError', 'StrategyNotFoundError'],
                'test_inputs': ['invalid_strategy', 'nonexistent', '']
            },
            'invalid_parameters': {
                'expected_status_code': [400, 422],
                'expected_error_types': ['ValidationError', 'ParameterValidationError'],
                'test_inputs': [
                    {'short_window': -1, 'long_window': 20},  # 음수
                    {'short_window': 50, 'long_window': 10},  # 역순
                    {'short_window': 'invalid', 'long_window': 20}  # 타입 오류
                ]
            },
            'insufficient_data': {
                'expected_status_code': [422, 500],
                'expected_error_types': ['InsufficientDataError'],
                'test_conditions': [
                    'date_range_too_short',
                    'weekend_only_range',
                    'holiday_only_range'
                ]
            }
        }
    
    @staticmethod
    def get_chart_data_structure() -> Dict[str, Any]:
        """
        차트 데이터 구조 검증 기준
        """
        return {
            'required_fields': [
                'ticker', 'strategy', 'start_date', 'end_date',
                'ohlc_data', 'equity_data', 'trade_markers',
                'indicators', 'summary_stats'
            ],
            'ohlc_data_fields': ['date', 'open', 'high', 'low', 'close', 'volume'],
            'equity_data_fields': ['date', 'equity', 'return_pct', 'drawdown_pct'],
            'trade_marker_fields': ['date', 'type', 'side', 'price', 'size'],
            'summary_stats_fields': [
                'total_return_pct', 'sharpe_ratio', 'max_drawdown_pct',
                'total_trades', 'win_rate_pct', 'profit_factor'
            ],
            'data_types': {
                'date': str,
                'numeric_fields': ['price', 'return_pct', 'sharpe_ratio'],
                'integer_fields': ['total_trades', 'size', 'volume'],
                'percentage_fields': ['return_pct', 'drawdown_pct', 'win_rate_pct']
            }
        }
    
    @staticmethod
    def get_strategy_parameter_ranges() -> Dict[str, Dict[str, Any]]:
        """
        전략별 파라미터 유효 범위
        """
        return {
            'sma_crossover': {
                'short_window': {'min': 2, 'max': 50, 'default': 10},
                'long_window': {'min': 10, 'max': 200, 'default': 20},
                'constraints': ['short_window < long_window']
            },
            'rsi_strategy': {
                'rsi_period': {'min': 2, 'max': 50, 'default': 14},
                'rsi_oversold': {'min': 10, 'max': 40, 'default': 30},
                'rsi_overbought': {'min': 60, 'max': 90, 'default': 70},
                'constraints': ['rsi_oversold < rsi_overbought']
            },
            'bollinger_bands': {
                'period': {'min': 5, 'max': 100, 'default': 20},
                'std_dev': {'min': 0.5, 'max': 4.0, 'default': 2.0}
            },
            'macd_strategy': {
                'fast_period': {'min': 5, 'max': 50, 'default': 12},
                'slow_period': {'min': 10, 'max': 100, 'default': 26},
                'signal_period': {'min': 2, 'max': 20, 'default': 9},
                'constraints': ['fast_period < slow_period']
            }
        }
    
    @staticmethod
    def get_portfolio_validation_rules() -> Dict[str, Any]:
        """
        포트폴리오 검증 규칙
        """
        return {
            'max_tickers': 50,
            'min_amount_per_ticker': 100.0,
            'max_amount_per_ticker': 10000000.0,
            'min_total_amount': 1000.0,
            'max_total_amount': 100000000.0,
            'weight_constraints': {
                'min_weight': 0.01,  # 1%
                'max_weight': 0.50,  # 50%
                'sum_tolerance': 0.001  # 0.1% 허용 오차
            },
            'diversification_rules': {
                'max_single_sector_weight': 0.40,  # 40%
                'min_number_of_sectors': 2
            }
        }
