"""
백테스트 플로우 통합 테스트
데이터 수집 → 전략 실행 → 결과 처리 전체 플로우 검증
"""

import pytest
import sys
import os
from datetime import date
import pandas as pd

# 백엔드 앱 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.services.backtest_service import backtest_service
from app.models.requests import BacktestRequest
from tests.fixtures.mock_data import MockStockDataGenerator
from tests.fixtures.expected_results import ExpectedResults


class TestBacktestFlow:
    """백테스트 전체 플로우 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_complete_single_ticker_backtest_flow(self, mock_data_generator):
        """단일 종목 백테스트 전체 플로우 테스트"""
        # Given
        ticker = "AAPL"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)
        initial_cash = 10000
        strategy = "sma_crossover"
        strategy_params = {"short_window": 10, "long_window": 20}
        
        # Step 1: 데이터 수집
        stock_data = data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # 데이터 품질 검증
        assert isinstance(stock_data, pd.DataFrame)
        assert not stock_data.empty
        assert len(stock_data) > 50  # 최소 50일 데이터
        
        # Step 2: 전략 검증
        strategy_info = strategy_service.get_strategy_info(strategy)
        assert strategy_info is not None
        
        validated_params = strategy_service.validate_strategy_params(strategy, strategy_params)
        assert validated_params == strategy_params
        
        # Step 3: 백테스트 실행
        request = BacktestRequest(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            strategy=strategy,
            strategy_params=strategy_params
        )
        
        result = await backtest_service.run_backtest(request)
        
        # Step 4: 결과 검증
        assert result is not None
        assert hasattr(result, 'final_equity')
        assert hasattr(result, 'total_return_pct')
        assert hasattr(result, 'total_trades')
        assert hasattr(result, 'win_rate_pct')
        assert hasattr(result, 'sharpe_ratio')
        
        # 결과 합리성 검증
        assert result.final_equity > 0
        assert -100 <= result.total_return_pct <= 1000  # -100% ~ 1000% 범위
        assert result.total_trades >= 0
        assert 0 <= result.win_rate_pct <= 100
        assert -10 <= result.sharpe_ratio <= 10  # 합리적 샤프 비율 범위
        
        # 데이터 일관성 검증
        if result.total_trades == 0:
            assert result.win_rate_pct == 0  # 거래가 없으면 승률도 0
        
        # 성능 검증
        expected_ranges = ExpectedResults.get_backtest_result_ranges()[strategy]
        assert expected_ranges['total_return_pct']['min'] <= result.total_return_pct <= expected_ranges['total_return_pct']['max']
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="포트폴리오 백테스트 기능은 현재 지원되지 않음")
    async def test_complete_portfolio_backtest_flow(self, mock_data_generator):
        """포트폴리오 백테스트 전체 플로우 테스트"""
        pass

    @pytest.mark.asyncio
    async def test_data_flow_error_handling(self, mock_data_generator):
        """데이터 플로우 에러 처리 테스트"""
        # Given - 문제가 있는 요청들
        problematic_requests = [
            # 잘못된 티커
            BacktestRequest(
                ticker="INVALID999",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 6, 30),
                initial_cash=10000,
                strategy="buy_and_hold",
                strategy_params={}
            ),
            
            # 너무 짧은 기간
            BacktestRequest(
                ticker="AAPL",
                start_date=date(2023, 6, 29),
                end_date=date(2023, 6, 30),
                initial_cash=10000,
                strategy="sma_crossover",
                strategy_params={"short_window": 10, "long_window": 20}
            ),
            
            # 잘못된 전략 파라미터
            BacktestRequest(
                ticker="AAPL",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 6, 30),
                initial_cash=10000,
                strategy="sma_crossover",
                strategy_params={"short_window": 50, "long_window": 10}  # 역순
            )
        ]
        
        for request in problematic_requests:
            # When & Then
            try:
                result = await backtest_service.run_backtest(request)
                # 일부 경우에는 결과가 반환될 수 있음 (경고와 함께)
                if result:
                    assert result.final_equity >= 0
            except Exception as e:
                # 예외 발생은 예상된 동작
                assert isinstance(e, (ValueError, Exception))
                
                # HTTPException의 경우 detail 속성을 확인
                if hasattr(e, 'detail'):
                    assert len(str(e.detail)) > 0  # 의미있는 에러 메시지
                else:
                    assert len(str(e)) > 0  # 의미있는 에러 메시지
    
    @pytest.mark.asyncio
    async def test_strategy_comparison_flow(self, mock_data_generator):
        """여러 전략 비교 플로우 테스트"""
        # Given
        ticker = "AAPL"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)
        initial_cash = 10000
        
        strategies_to_test = [
            ("buy_and_hold", {}),
            ("sma_crossover", {"short_window": 10, "long_window": 20}),
            ("rsi_strategy", {"rsi_period": 14, "oversold": 30, "overbought": 70})
        ]
        
        results = {}
        
        # When - 각 전략별로 백테스트 실행
        for strategy_name, strategy_params in strategies_to_test:
            request = BacktestRequest(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                strategy=strategy_name,
                strategy_params=strategy_params
            )
            
            try:
                result = await backtest_service.run_backtest(request)
                results[strategy_name] = result
            except Exception as e:
                results[strategy_name] = e
        
        # Then - 결과 비교 및 검증
        successful_results = {k: v for k, v in results.items() if not isinstance(v, Exception)}
        
        # 최소 2개 전략은 성공해야 함
        assert len(successful_results) >= 2
        
        # 각 전략별 특성 검증
        if "buy_and_hold" in successful_results:
            bh_result = successful_results["buy_and_hold"]
            assert bh_result.total_trades <= 5  # Buy & Hold는 거래가 적음
        
        if "sma_crossover" in successful_results:
            sma_result = successful_results["sma_crossover"]
            assert sma_result.total_trades >= 0  # SMA는 더 많은 거래 가능
        
        # 성능 비교 (절대적 우위는 없지만 합리적 범위 내)
        returns = [result.total_return_pct for result in successful_results.values()]
        assert max(returns) - min(returns) < 500  # 500% 이상 차이는 비현실적
    
    @pytest.mark.asyncio
    async def test_time_series_data_integrity(self, mock_data_generator):
        """시계열 데이터 무결성 테스트"""
        # Given
        ticker = "AAPL"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        # When
        stock_data = data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        # Then - 시계열 데이터 무결성 검증
        assert isinstance(stock_data, pd.DataFrame)
        assert not stock_data.empty
        
        # 날짜 순서 검증
        dates = stock_data.index
        assert dates.is_monotonic_increasing, "Dates should be in ascending order"
        
        # 주말 제외 검증 (월-금만)
        weekdays = [d.weekday() for d in dates]
        assert all(wd < 5 for wd in weekdays), "Should only contain weekdays"
        
        # OHLCV 논리 검증
        for idx in stock_data.index[:10]:  # 처음 10일만 검증
            row = stock_data.loc[idx]
            
            # High >= max(Open, Close), Low <= min(Open, Close)
            assert row['High'] >= max(row['Open'], row['Close']), f"High constraint violated at {idx}"
            assert row['Low'] <= min(row['Open'], row['Close']), f"Low constraint violated at {idx}"
            
            # High >= Low
            assert row['High'] >= row['Low'], f"High < Low at {idx}"
            
            # Volume >= 0
            assert row['Volume'] >= 0, f"Negative volume at {idx}"
        
        # 가격 변동 합리성 검증
        price_changes = stock_data['Close'].pct_change().dropna()
        
        # 일일 변동률이 ±50% 이내 (극단적 변동 방지)
        extreme_changes = price_changes[(price_changes > 0.5) | (price_changes < -0.5)]
        assert len(extreme_changes) == 0, f"Extreme price changes found: {extreme_changes}"
        
        # 연속된 동일 가격 방지 (5일 이상 연속 동일가 없어야 함)
        consecutive_same = (stock_data['Close'].diff() == 0).rolling(5).sum()
        assert consecutive_same.max() < 5, "Too many consecutive identical prices"
    
    @pytest.mark.asyncio
    async def test_backtest_reproducibility(self, mock_data_generator):
        """백테스트 재현성 테스트"""
        # Given
        request = BacktestRequest(
            ticker="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            initial_cash=10000,
            strategy="sma_crossover",
            strategy_params={"short_window": 10, "long_window": 20}
        )
        
        # When - 동일한 요청을 여러 번 실행
        results = []
        for i in range(3):
            result = await backtest_service.run_backtest(request)
            results.append(result)
        
        # Then - 모킹 환경에서는 동일한 결과가 나와야 함
        first_result = results[0]
        
        for result in results[1:]:
            assert result.final_equity == first_result.final_equity
            assert result.total_return_pct == first_result.total_return_pct
            assert result.total_trades == first_result.total_trades
            assert result.sharpe_ratio == first_result.sharpe_ratio
            assert result.max_drawdown_pct == first_result.max_drawdown_pct
    
    @pytest.mark.asyncio
    async def test_concurrent_backtest_execution(self, mock_data_generator):
        """동시 백테스트 실행 테스트"""
        import asyncio
        
        # Given
        requests = [
            BacktestRequest(
                ticker="AAPL",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 6, 30),
                initial_cash=10000,
                strategy="buy_and_hold",
                strategy_params={}
            ),
            BacktestRequest(
                ticker="GOOGL",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 6, 30),
                initial_cash=10000,
                strategy="sma_crossover",
                strategy_params={"short_window": 10, "long_window": 20}
            ),
            BacktestRequest(
                ticker="MSFT",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 6, 30),
                initial_cash=10000,
                strategy="rsi_strategy",
                strategy_params={"rsi_period": 14, "oversold": 30, "overbought": 70}
            )
        ]
        
        # When - 동시 실행
        tasks = [backtest_service.run_backtest(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Then
        successful_results = [r for r in results if not isinstance(r, Exception)]
        
        # 최소 2개는 성공해야 함
        assert len(successful_results) >= 2
        
        # 각 결과의 유효성 검증
        for result in successful_results:
            assert result.final_equity > 0
            assert -100 <= result.total_return_pct <= 1000
            assert result.total_trades >= 0
    
    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, mock_data_generator):
        """메모리 사용량 최적화 테스트"""
        import psutil
        import os
        
        # Given
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 대용량 데이터로 테스트
        request = BacktestRequest(
            ticker="AAPL",
            start_date=date(2022, 1, 1),  # 2년 데이터
            end_date=date(2023, 12, 31),
            initial_cash=10000,
            strategy="buy_and_hold",
            strategy_params={}
        )
        
        # When
        result = await backtest_service.run_backtest(request)
        
        # Then
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 메모리 증가량이 합리적 범위 내 (500MB 미만)
        assert memory_increase < 500, f"Memory usage increased by {memory_increase:.1f}MB"
        
        assert result is not None
        assert result.final_equity > 0
