"""
backtest_service 단위 테스트
백테스트 실행, 결과 처리, 성능 검증 테스트
"""

import pytest
import sys
import os
from datetime import date
from unittest.mock import Mock, patch
import pandas as pd

# 백엔드 앱 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.backtest_service import backtest_service
from app.models.requests import BacktestRequest, OptimizationRequest, PlotRequest
from fastapi import HTTPException
from app.core.custom_exceptions import DataNotFoundError, BacktestValidationError, ValidationError
from tests.fixtures.mock_data import MockStockDataGenerator
from tests.fixtures.expected_results import ExpectedResults


class TestBacktestService:
    """backtest_service 모듈 단위 테스트"""
    
    @pytest.mark.asyncio
    async def test_run_backtest_buy_and_hold_success(self, sample_backtest_request, mock_data_generator):
        """Buy & Hold 전략 백테스트 성공 테스트"""
        # Given
        request = sample_backtest_request
        request.strategy = "buy_and_hold"
        request.strategy_params = {}
        
        # When
        result = await backtest_service.run_backtest(request)
        
        # Then
        assert result is not None
        assert hasattr(result, 'final_equity')
        assert hasattr(result, 'total_return_pct')
        assert hasattr(result, 'sharpe_ratio')
        assert hasattr(result, 'max_drawdown_pct')
        assert hasattr(result, 'total_trades')
        
        # 결과 범위 검증
        expected_ranges = ExpectedResults.get_backtest_result_ranges()['buy_and_hold']
        
        assert expected_ranges['total_return_pct']['min'] <= result.total_return_pct <= expected_ranges['total_return_pct']['max']
        assert expected_ranges['sharpe_ratio']['min'] <= result.sharpe_ratio <= expected_ranges['sharpe_ratio']['max']
        assert expected_ranges['max_drawdown_pct']['min'] <= result.max_drawdown_pct <= expected_ranges['max_drawdown_pct']['max']
        assert expected_ranges['total_trades']['min'] <= result.total_trades <= expected_ranges['total_trades']['max']
        
        # Buy & Hold 특성 검증
        assert result.total_trades <= 10  # Buy & Hold는 거래가 적어야 함
        assert result.final_equity > 0  # 최종 자산은 양수
    
    @pytest.mark.asyncio
    async def test_run_backtest_sma_crossover_success(self, sample_backtest_request, mock_data_generator):
        """SMA Crossover 전략 백테스트 성공 테스트"""
        # Given
        request = sample_backtest_request
        request.strategy = "sma_crossover"
        request.strategy_params = {
            "short_window": 10,
            "long_window": 20
        }
        
        # When
        result = await backtest_service.run_backtest(request)
        
        # Then
        assert result is not None
        
        # 결과 범위 검증
        expected_ranges = ExpectedResults.get_backtest_result_ranges()['sma_crossover']
        
        assert expected_ranges['total_return_pct']['min'] <= result.total_return_pct <= expected_ranges['total_return_pct']['max']
        assert expected_ranges['sharpe_ratio']['min'] <= result.sharpe_ratio <= expected_ranges['sharpe_ratio']['max']
        assert expected_ranges['total_trades']['min'] <= result.total_trades <= expected_ranges['total_trades']['max']
        
        # SMA Crossover 특성 검증
        assert result.total_trades >= 0  # 거래 횟수는 0 이상
        assert isinstance(result.win_rate_pct, (int, float))  # 승률은 숫자
        assert 0 <= result.win_rate_pct <= 100  # 승률은 0-100%
    
    @pytest.mark.asyncio
    async def test_run_backtest_rsi_strategy_success(self, sample_backtest_request, mock_data_generator):
        """RSI 전략 백테스트 성공 테스트"""
        # Given
        request = sample_backtest_request
        request.strategy = "rsi_strategy"
        request.strategy_params = {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70
        }
        
        # When
        result = await backtest_service.run_backtest(request)
        
        # Then
        assert result is not None
        
        # 결과 범위 검증
        expected_ranges = ExpectedResults.get_backtest_result_ranges()['rsi_strategy']
        
        assert expected_ranges['total_return_pct']['min'] <= result.total_return_pct <= expected_ranges['total_return_pct']['max']
        assert expected_ranges['total_trades']['min'] <= result.total_trades <= expected_ranges['total_trades']['max']
        
        # RSI 전략 특성 검증 (일반적으로 더 많은 거래)
        assert isinstance(result.profit_factor, (int, float))
        assert result.profit_factor >= 0  # 수익 팩터는 0 이상
    
    @pytest.mark.asyncio
    async def test_run_backtest_invalid_strategy(self, sample_backtest_request):
        """잘못된 전략으로 백테스트 실행 테스트"""
        # Given
        request = sample_backtest_request
        request.strategy = "invalid_strategy"
        request.strategy_params = {}
        
        # When & Then
        with pytest.raises((BacktestValidationError, ValueError, HTTPException)) as exc_info:
            await backtest_service.run_backtest(request)
        
        assert "strategy" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_run_backtest_insufficient_data(self, mock_data_generator):
        """데이터 부족 시 백테스트 실행 테스트"""
        # Given
        request = BacktestRequest(
            ticker="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2),  # 극도로 짧은 기간
            initial_cash=10000,
            strategy="sma_crossover",
            strategy_params={"short_window": 10, "long_window": 20}
        )
        
        # When & Then
        # 데이터가 부족하면 오류 또는 경고와 함께 결과 반환
        try:
            result = await backtest_service.run_backtest(request)
            # 결과가 반환되면 합리적인 값인지 확인
            if result:
                assert result.final_equity >= 0
        except (DataNotFoundError, BacktestValidationError):
            # 데이터 부족 오류는 예상된 동작
            pass
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="포트폴리오 백테스트 기능은 현재 지원되지 않음")
    async def test_run_portfolio_backtest_success(self, sample_portfolio_request, mock_data_generator):
        """포트폴리오 백테스트 성공 테스트"""
        # Given
        request = sample_portfolio_request
        
        # When
        result = await backtest_service.run_portfolio_backtest(request)
        
        # Then
        assert result is not None
        assert hasattr(result, 'individual_results')
        assert hasattr(result, 'portfolio_result')
        
        # 개별 결과 검증
        assert len(result.individual_results) == len(request.portfolio)
        for individual_result in result.individual_results:
            assert hasattr(individual_result, 'ticker')
            assert hasattr(individual_result, 'final_equity')
            assert individual_result.final_equity > 0
        
        # 포트폴리오 결과 검증
        assert hasattr(result.portfolio_result, 'total_equity')
        assert hasattr(result.portfolio_result, 'total_return_pct')
        assert result.portfolio_result.total_equity > 0
        
        # 포트폴리오 합계 검증
        individual_total = sum(ir.final_equity for ir in result.individual_results)
        assert abs(individual_total - result.portfolio_result.total_equity) < 1.0  # 소수점 오차 허용
    
    # @pytest.mark.asyncio
    # async def test_run_portfolio_backtest_unequal_weights(self, mock_data_generator):
    #     """불균등 포트폴리오 백테스트 테스트"""
    #     # Given
    #     request = BacktestRequest(
    #         ticker="AAPL",  # 단일 종목으로 변경
    #         start_date=date(2023, 1, 1),
    #         end_date=date(2023, 6, 30),
    #         strategy="buy_and_hold",
    #         strategy_params={}
    #     )
    #     
    #     # When
    #     result = await backtest_service.run_backtest(request)
    #     
    #     # Then
    #     assert result is not None
        
        # 투자 금액 비중 검증
        total_amount = sum(request.amounts)
        for i, individual_result in enumerate(result.individual_results):
            expected_weight = request.amounts[i] / total_amount
            # 비중이 올바르게 반영되었는지 확인 (정확한 계산은 복잡하므로 대략적 검증)
            assert individual_result.final_equity > 0
    
    @pytest.mark.asyncio
    async def test_optimize_strategy_success(self, mock_data_generator):
        """전략 최적화 성공 테스트"""
        # Given
        request = OptimizationRequest(
            ticker="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            initial_cash=10000,
            strategy="sma_crossover",
            param_ranges={
                "short_window": [5, 15],
                "long_window": [20, 30]
            },
            method="grid",
            max_tries=10  # 빠른 테스트를 위해 제한
        )
        
        # When
        result = await backtest_service.optimize_strategy(request)
        
        # Then
        assert result is not None
        assert hasattr(result, 'best_params')
        assert hasattr(result, 'best_score')
        assert hasattr(result, 'execution_time_seconds')
        
        # 최적 파라미터 검증
        assert 'short_window' in result.best_params
        assert 'long_window' in result.best_params
        assert result.best_params['short_window'] < result.best_params['long_window']
        
        # 최적 점수 검증
        assert isinstance(result.best_score, (int, float))
        
        # 실행 시간 검증
        assert result.execution_time_seconds > 0
        assert result.execution_time_seconds < 120  # 2분 이내
    
    @pytest.mark.asyncio
    async def test_backtest_with_different_initial_cash(self, mock_data_generator):
        """다양한 초기 자본으로 백테스트 테스트"""
        # Given
        cash_amounts = [1000, 10000, 100000]
        base_request = BacktestRequest(
            ticker="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            initial_cash=10000,  # 기본값, 아래에서 변경
            strategy="buy_and_hold",
            strategy_params={}
        )
        
        results = []
        
        for cash in cash_amounts:
            # When
            request = base_request.copy()
            request.initial_cash = cash
            result = await backtest_service.run_backtest(request)
            results.append((cash, result))
        
        # Then
        assert len(results) == len(cash_amounts)
        
        for cash, result in results:
            assert result is not None
            assert result.final_equity > 0
            
            # 초기 자본과 최종 자본의 관계 검증
            # (수익률이 동일하다면 최종 자본도 비례해야 함)
            # 하지만 실제로는 수수료, 슬리피지 등으로 정확히 비례하지 않을 수 있음
            assert result.final_equity >= cash * 0.5  # 최소 50% 이상은 남아야 함
    
    @pytest.mark.asyncio
    async def test_backtest_performance_benchmark(self, sample_backtest_request, mock_data_generator):
        """백테스트 성능 벤치마크 테스트"""
        import time
        
        # Given
        request = sample_backtest_request
        benchmarks = ExpectedResults.get_performance_benchmarks()
        max_time = benchmarks['backtest_execution']['buy_and_hold_1year']
        
        # When
        start_time = time.time()
        result = await backtest_service.run_backtest(request)
        execution_time = time.time() - start_time
        
        # Then
        assert execution_time <= max_time, \
            f"Backtest took {execution_time:.2f}s, exceeds limit of {max_time}s"
        
        assert result is not None
        assert result.final_equity > 0
    
    @pytest.mark.asyncio
    async def test_backtest_result_consistency(self, sample_backtest_request, mock_data_generator):
        """백테스트 결과 일관성 테스트 (동일 입력 → 동일 출력)"""
        # Given
        request = sample_backtest_request
        
        # When - 동일한 요청을 여러 번 실행
        result1 = await backtest_service.run_backtest(request)
        result2 = await backtest_service.run_backtest(request)
        
        # Then - 모킹 환경에서는 동일한 결과가 나와야 함
        assert result1.final_equity == result2.final_equity
        assert result1.total_return_pct == result2.total_return_pct
        assert result1.total_trades == result2.total_trades
        assert result1.sharpe_ratio == result2.sharpe_ratio
    
    @pytest.mark.asyncio
    async def test_backtest_commission_impact(self, mock_data_generator):
        """수수료가 백테스트 결과에 미치는 영향 테스트"""
        # Given
        base_request = BacktestRequest(
            ticker="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            initial_cash=10000,
            strategy="sma_crossover",
            strategy_params={"short_window": 10, "long_window": 20}
        )
        
        # When - 수수료 없음 vs 수수료 있음
        request_no_commission = base_request.copy()
        request_no_commission.commission = 0.0
        
        request_with_commission = base_request.copy()
        request_with_commission.commission = 0.001  # 0.1%
        
        result_no_commission = await backtest_service.run_backtest(request_no_commission)
        result_with_commission = await backtest_service.run_backtest(request_with_commission)
        
        # Then - 수수료가 있으면 수익률이 낮아져야 함
        if result_no_commission.total_trades > 0 and result_with_commission.total_trades > 0:
            assert result_with_commission.final_equity <= result_no_commission.final_equity
            assert result_with_commission.total_return_pct <= result_no_commission.total_return_pct
    
    @pytest.mark.asyncio
    async def test_backtest_different_time_periods(self, mock_data_generator):
        """다양한 기간별 백테스트 테스트"""
        # Given
        periods = [
            (date(2023, 1, 1), date(2023, 3, 31)),   # 3개월
            (date(2023, 1, 1), date(2023, 6, 30)),   # 6개월
            (date(2023, 1, 1), date(2023, 12, 31)),  # 1년
        ]
        
        results = []
        
        for start_date, end_date in periods:
            # When
            request = BacktestRequest(
                ticker="AAPL",
                start_date=start_date,
                end_date=end_date,
                initial_cash=10000,
                strategy="buy_and_hold",
                strategy_params={}
            )
            
            result = await backtest_service.run_backtest(request)
            results.append((start_date, end_date, result))
        
        # Then
        assert len(results) == len(periods)
        
        for start_date, end_date, result in results:
            assert result is not None
            assert result.final_equity > 0
            
            # 기간이 길수록 더 많은 데이터 포인트가 있어야 함
            period_days = (end_date - start_date).days
            assert period_days > 0
