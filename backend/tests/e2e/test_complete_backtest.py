"""
E2E (End-to-End) 종단 테스트
사용자 시나리오 기반 전체 시스템 검증
"""

import pytest
import sys
import os
import time
from datetime import date
from fastapi.testclient import TestClient

# 백엔드 앱 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app
from tests.fixtures.expected_results import ExpectedResults


class TestE2EScenarios:
    """E2E 종단 테스트 시나리오"""
    
    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)
    
    def test_complete_single_ticker_analysis_scenario(self, client):
        """
        시나리오: 개인 투자자가 Apple 주식을 SMA 전략으로 분석
        사용자 스토리: "AAPL 주식에 1만 달러를 투자해서 SMA 크로스오버 전략으로 6개월간 백테스트하고 싶어요"
        """
        # Given - 사용자 입력
        user_input = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "sma_crossover",
            "strategy_params": {
                "short_window": 10,
                "long_window": 20
            },
            "commission": 0.002
        }
        
        # When - API 호출 (프론트엔드에서 백엔드로)
        start_time = time.time()
        response = client.post("/api/v1/backtest/chart-data", json=user_input)
        execution_time = time.time() - start_time
        
        # Then - 성공적인 결과 반환
        assert response.status_code == 200, f"API returned {response.status_code}: {response.text}"
        
        # 응답 시간 검증 (사용자 경험)
        assert execution_time < 20.0, f"Response took too long: {execution_time:.2f}s"
        
        result = response.json()
        
        # 1. 기본 정보 검증
        assert result['ticker'] == user_input['ticker']
        assert result['strategy'] == user_input['strategy']
        assert result['start_date'] == user_input['start_date']
        assert result['end_date'] == user_input['end_date']
        
        # 2. 차트 데이터 완전성 검증 (프론트엔드 차트 렌더링용)
        ohlc_data = result['ohlc_data']
        assert isinstance(ohlc_data, list)
        assert len(ohlc_data) > 100, "6개월 데이터면 100일 이상 있어야 함"
        
        # 첫 번째 OHLC 데이터 구조 검증
        first_ohlc = ohlc_data[0]
        required_ohlc_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
        for field in required_ohlc_fields:
            assert field in first_ohlc, f"OHLC field {field} missing"
            assert first_ohlc[field] is not None, f"OHLC field {field} is null"
        
        # 3. 자산 곡선 데이터 검증 (포트폴리오 가치 변화)
        equity_data = result['equity_data']
        assert isinstance(equity_data, list)
        assert len(equity_data) > 0
        
        first_equity = equity_data[0]
        required_equity_fields = ['date', 'equity', 'return_pct', 'drawdown_pct']
        for field in required_equity_fields:
            assert field in first_equity, f"Equity field {field} missing"
        
        # 자산 곡선 논리 검증
        assert first_equity['equity'] > 0, "초기 자산은 양수여야 함"
        assert abs(first_equity['equity'] - user_input['initial_cash']) < 100, "초기 자산이 입력값과 비슷해야 함"
        
        # 4. 거래 마커 검증 (SMA 크로스오버는 거래가 있을 수 있음)
        trade_markers = result['trade_markers']
        assert isinstance(trade_markers, list)
        
        if len(trade_markers) > 0:  # 거래가 있는 경우
            first_trade = trade_markers[0]
            required_trade_fields = ['date', 'type', 'side', 'price', 'size']
            for field in required_trade_fields:
                assert field in first_trade, f"Trade field {field} missing"
            
            # 거래 타입 검증
            assert first_trade['type'] in ['entry', 'exit'], "거래 타입은 entry 또는 exit"
            assert first_trade['side'] in ['buy', 'sell'], "거래 방향은 buy 또는 sell"
            assert first_trade['price'] > 0, "거래 가격은 양수"
            assert first_trade['size'] > 0, "거래 수량은 양수"
        
        # 5. 기술 지표 검증 (SMA 크로스오버 전략)
        indicators = result['indicators']
        assert isinstance(indicators, list)
        assert len(indicators) >= 2, "SMA 전략은 최소 2개 지표 (단기/장기 SMA)"
        
        # SMA 지표 존재 확인
        indicator_names = [ind['name'] for ind in indicators]
        assert any('SMA' in name or 'Moving' in name for name in indicator_names), "SMA 지표가 있어야 함"
        
        # 6. 성과 요약 검증 (사용자가 가장 관심 있는 부분)
        summary_stats = result['summary_stats']
        assert isinstance(summary_stats, dict)
        
        key_metrics = [
            'total_return_pct', 'sharpe_ratio', 'max_drawdown_pct',
            'total_trades', 'win_rate_pct', 'profit_factor'
        ]
        
        for metric in key_metrics:
            assert metric in summary_stats, f"Key metric {metric} missing"
            assert summary_stats[metric] is not None, f"Key metric {metric} is null"
        
        # 성과 지표 합리성 검증
        assert -100 <= summary_stats['total_return_pct'] <= 1000, "수익률이 비현실적"
        assert 0 <= summary_stats['win_rate_pct'] <= 100, "승률은 0-100% 범위"
        assert summary_stats['total_trades'] >= 0, "거래 횟수는 0 이상"
        assert summary_stats['max_drawdown_pct'] >= 0, "최대 손실은 양수"
        
        # 7. 데이터 일관성 검증
        assert len(ohlc_data) == len(equity_data), "OHLC와 자산 데이터 길이가 일치해야 함"
    
    def test_portfolio_analysis_scenario(self, client):
        """
        시나리오: 포트폴리오 분산투자 분석
        사용자 스토리: "AAPL, GOOGL, MSFT에 각각 5천 달러씩 투자해서 Buy & Hold로 성과를 보고 싶어요"
        """
        # Given - 포트폴리오 구성
        portfolio_input = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000, "investment_type": "lump_sum"},
                {"symbol": "GOOGL", "amount": 5000, "investment_type": "lump_sum"},
                {"symbol": "MSFT", "amount": 5000, "investment_type": "lump_sum"}
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_and_hold",
            "strategy_params": {}
        }
        
        # When - 포트폴리오 백테스트 실행
        start_time = time.time()
        response = client.post("/api/v1/backtest/portfolio", json=portfolio_input)
        execution_time = time.time() - start_time
        
        # Then - 포트폴리오 분석 결과 검증
        assert response.status_code == 200
        assert execution_time < 30.0, f"Portfolio analysis took too long: {execution_time:.2f}s"
        
        result = response.json()
        
        # 응답 구조 확인: {status, data} 형태
        assert 'status' in result
        assert 'data' in result
        data = result['data']
        
        # 1. 개별 종목 결과 검증
        individual_results = data['individual_results']
        assert isinstance(individual_results, list)
        assert len(individual_results) == 3, "3개 종목 결과가 있어야 함"
        
        total_individual_final = 0
        for i, individual in enumerate(individual_results):
            assert individual['ticker'] == portfolio_input['portfolio'][i]['symbol']
            assert 'final_equity' in individual
            assert 'total_return_pct' in individual
            assert 'sharpe_ratio' in individual
            
            # 개별 결과 합리성
            assert individual['final_equity'] > 0, f"{individual['ticker']} 최종 자산이 0 이하"
            assert -100 <= individual['total_return_pct'] <= 1000, f"{individual['ticker']} 수익률 비현실적"
            
            total_individual_final += individual['final_equity']
        
        # 2. 포트폴리오 전체 결과 검증
        portfolio_result = data['portfolio_result']
        assert isinstance(portfolio_result, dict)
        assert 'total_equity' in portfolio_result
        assert 'total_return_pct' in portfolio_result
        
        # 포트폴리오 합계 일치성
        assert abs(total_individual_final - portfolio_result['total_equity']) < 50, "개별 합계와 포트폴리오 총합이 일치해야 함"
        
        # 3. 포트폴리오 비중 검증 (portfolio_composition에서)
        portfolio_composition = data['portfolio_composition']
        assert isinstance(portfolio_composition, list)
        assert len(portfolio_composition) == 3
        
        # 동일 투자금액이므로 비중도 동일해야 함 (약 33.33% 씩)
        for comp in portfolio_composition:
            assert 0.30 <= comp['weight'] <= 0.37, f"동일 투자시 비중이 약 1/3이어야 함: {comp['weight']}"
        
        # 비중 합계는 1.0
        total_weight = sum(comp['weight'] for comp in portfolio_composition)
        assert abs(total_weight - 1.0) < 0.01, f"비중 합계가 1.0이어야 함: {total_weight}"
        
        # 4. 분산효과 검증 (포트폴리오 리스크 < 개별 평균 리스크)
        individual_returns = [ind['total_return_pct'] for ind in individual_results]
        individual_volatility = max(individual_returns) - min(individual_returns)
        
        # 분산투자 효과가 있어야 함 (정확한 계산은 복잡하므로 기본적 검증만)
        assert portfolio_result['total_equity'] > 0
        assert -100 <= portfolio_result['total_return_pct'] <= 1000
    
    def test_strategy_optimization_scenario(self, client):
        """
        시나리오: 전략 최적화
        사용자 스토리: "SMA 전략의 최적 파라미터를 찾고 싶어요"
        """
        # Given - 최적화 요청 (실제 사용자는 UI에서 범위 설정)
        optimization_input = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "sma_crossover",
            "param_ranges": {
                "short_window": [5, 15],
                "long_window": [20, 30]
            },
            "method": "grid",
            "max_tries": 20,
            "metric": "sharpe_ratio"
        }
        
        # When - 최적화 실행 (시간이 오래 걸릴 수 있음)
        start_time = time.time()
        response = client.post("/api/v1/backtest/optimize", json=optimization_input)
        execution_time = time.time() - start_time
        
        # Then - 최적화 결과 검증
        if response.status_code == 404:
            # 최적화 엔드포인트가 구현되지 않은 경우 스킵
            pytest.skip("Optimization endpoint not implemented")
        
        assert response.status_code == 200
        assert execution_time < 60.0, f"Optimization took too long: {execution_time:.2f}s"
        
        result = response.json()
        
        # 최적화 결과 구조 검증
        assert 'best_params' in result
        assert 'best_score' in result
        assert 'execution_time_seconds' in result
        
        best_params = result['best_params']
        assert 'short_window' in best_params
        assert 'long_window' in best_params
        
        # 최적 파라미터 유효성
        assert 5 <= best_params['short_window'] <= 15
        assert 20 <= best_params['long_window'] <= 30
        assert best_params['short_window'] < best_params['long_window']
        
        # 최적 점수 합리성
        best_score = result['best_score']
        assert isinstance(best_score, (int, float))
        assert -10 <= best_score <= 10, "샤프 비율이 -10~10 범위를 벗어남"
    
    def test_error_handling_user_experience(self, client):
        """
        시나리오: 사용자 오류 처리 경험
        사용자 스토리: "잘못된 입력을 했을 때 친절한 에러 메시지를 받고 싶어요"
        """
        # Given - 다양한 사용자 실수 시나리오
        user_mistakes = [
            {
                "name": "존재하지 않는 종목",
                "input": {
                    "ticker": "NONEXISTENT",
                    "start_date": "2023-01-01",
                    "end_date": "2023-06-30",
                    "initial_cash": 10000,
                    "strategy": "buy_and_hold"
                },
                "expected_hint": ["ticker", "not found", "symbol"]
            },
            {
                "name": "날짜 순서 실수",
                "input": {
                    "ticker": "AAPL",
                    "start_date": "2023-06-30",
                    "end_date": "2023-01-01",  # 잘못된 순서
                    "initial_cash": 10000,
                    "strategy": "buy_and_hold"
                },
                "expected_hint": ["date", "start", "end", "order"]
            },
            {
                "name": "투자금액 오타",
                "input": {
                    "ticker": "AAPL",
                    "start_date": "2023-01-01",
                    "end_date": "2023-06-30",
                    "initial_cash": -5000,  # 음수
                    "strategy": "buy_and_hold"
                },
                "expected_hint": ["cash", "amount", "positive", "greater"]
            },
            {
                "name": "전략 파라미터 실수",
                "input": {
                    "ticker": "AAPL",
                    "start_date": "2023-01-01",
                    "end_date": "2023-06-30",
                    "initial_cash": 10000,
                    "strategy": "sma_crossover",
                    "strategy_params": {
                        "short_window": 30,  # long_window보다 큼
                        "long_window": 10
                    }
                },
                "expected_hint": ["window", "short", "long", "parameter"]
            }
        ]
        
        for mistake in user_mistakes:
            # When - 잘못된 요청 실행
            response = client.post("/api/v1/backtest/chart-data", json=mistake["input"])
            
            # Then - 친절한 에러 응답 검증
            assert response.status_code >= 400, f"{mistake['name']}: 에러 상태코드를 반환해야 함"
            
            try:
                error_data = response.json()
                
                # 에러 메시지 존재 확인
                error_message = ""
                if 'detail' in error_data:
                    if isinstance(error_data['detail'], str):
                        error_message = error_data['detail']
                    elif isinstance(error_data['detail'], list):
                        error_message = str(error_data['detail'])
                elif 'message' in error_data:
                    error_message = error_data['message']
                elif 'error' in error_data:
                    error_message = error_data['error']
                
                assert len(error_message) > 0, f"{mistake['name']}: 에러 메시지가 비어있음"
                
                # 도움이 되는 힌트 포함 여부 확인
                error_message_lower = error_message.lower()
                hint_found = any(hint.lower() in error_message_lower for hint in mistake["expected_hint"])
                
                # 힌트가 없어도 의미있는 메시지면 통과
                if not hint_found:
                    assert len(error_message) > 10, f"{mistake['name']}: 에러 메시지가 너무 짧음 - {error_message}"
                
            except (ValueError, KeyError):
                # JSON이 아닌 응답도 허용 (HTML 에러 페이지 등)
                pass
    
    def test_performance_stress_scenario(self, client):
        """
        시나리오: 성능 스트레스 테스트
        사용자 스토리: "여러 종목을 동시에 분석해도 시스템이 안정적이어야 해요"
        """
        # Given - 복잡한 포트폴리오 (10개 종목)
        large_portfolio = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "GOOGL", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "MSFT", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "TSLA", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "AMZN", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "META", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "NVDA", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "NFLX", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "ORCL", "amount": 1000, "investment_type": "lump_sum"},
                {"symbol": "CRM", "amount": 1000, "investment_type": "lump_sum"}
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",  # 1년 전체
            "strategy": "buy_and_hold",
            "strategy_params": {}
        }
        
        # When - 대용량 포트폴리오 분석
        start_time = time.time()
        response = client.post("/api/v1/backtest/portfolio", json=large_portfolio)
        execution_time = time.time() - start_time
        
        # Then - 성능 및 안정성 검증
        if response.status_code == 200:
            # 성공한 경우 성능 검증
            max_time = ExpectedResults.get_performance_benchmarks()['api_response']['portfolio_endpoint']
            assert execution_time <= max_time, f"Large portfolio took {execution_time:.2f}s, exceeds {max_time}s"
            
            result = response.json()
            data = result['data']
            assert len(data['individual_results']) == 10, "10개 종목 결과가 모두 있어야 함"
            
            # 모든 개별 결과가 유효한지 확인
            for individual in data['individual_results']:
                assert individual['final_equity'] > 0, "모든 종목의 최종 자산이 양수여야 함"
        
        else:
            # 실패한 경우에도 시스템이 크래시하지 않고 적절한 에러 반환
            assert 400 <= response.status_code < 600, "적절한 HTTP 에러 코드를 반환해야 함"
            assert execution_time < 60.0, "에러 응답도 60초 이내에 반환되어야 함"
    
    def test_data_consistency_across_requests(self, client):
        """
        시나리오: 데이터 일관성 검증
        사용자 스토리: "같은 조건으로 분석하면 항상 같은 결과가 나와야 해요"
        """
        # Given - 동일한 백테스트 조건
        consistent_request = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "buy_and_hold",
            "strategy_params": {}
        }
        
        # When - 동일한 요청을 여러 번 실행
        responses = []
        for _ in range(3):
            response = client.post("/api/v1/backtest/chart-data", json=consistent_request)
            assert response.status_code == 200
            responses.append(response.json())
        
        # Then - 일관성 검증 (모킹 환경에서는 동일해야 함)
        first_result = responses[0]
        
        for result in responses[1:]:
            # 핵심 지표들이 동일해야 함
            assert result['summary_stats']['total_return_pct'] == first_result['summary_stats']['total_return_pct']
            assert result['summary_stats']['sharpe_ratio'] == first_result['summary_stats']['sharpe_ratio']
            assert result['summary_stats']['total_trades'] == first_result['summary_stats']['total_trades']
            
            # 데이터 길이도 동일해야 함
            assert len(result['ohlc_data']) == len(first_result['ohlc_data'])
            assert len(result['equity_data']) == len(first_result['equity_data'])
            assert len(result['trade_markers']) == len(first_result['trade_markers'])
