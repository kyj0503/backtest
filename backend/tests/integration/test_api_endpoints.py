"""
API 엔드포인트 통합 테스트
FastAPI TestClient를 사용한 실제 HTTP 요청 테스트
"""

import pytest
import json
from datetime import date
from fastapi.testclient import TestClient
import sys
import os

# 백엔드 앱 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app
from tests.fixtures.expected_results import ExpectedResults


class TestAPIEndpoints:
    """API 엔드포인트 통합 테스트"""
    
    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)
    
    def test_chart_data_endpoint_success(self, client):
        """차트 데이터 엔드포인트 성공 테스트"""
        # Given
        payload = {
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
        
        # When
        response = client.post("/api/v1/backtest/chart-data", json=payload)
        
        # Then
        assert response.status_code == 200
        
        data = response.json()
        
        # 응답 구조 검증
        chart_structure = ExpectedResults.get_chart_data_structure()
        required_fields = chart_structure['required_fields']
        
        for field in required_fields:
            assert field in data, f"Required field {field} missing from response"
        
        # 기본 정보 검증
        assert data['ticker'] == payload['ticker']
        assert data['strategy'] == payload['strategy']
        assert data['start_date'] == payload['start_date']
        assert data['end_date'] == payload['end_date']
        
        # OHLC 데이터 검증
        ohlc_data = data['ohlc_data']
        assert isinstance(ohlc_data, list)
        assert len(ohlc_data) > 0
        
        ohlc_fields = chart_structure['ohlc_data_fields']
        for ohlc_record in ohlc_data[:3]:  # 첫 3개 레코드 검증
            for field in ohlc_fields:
                assert field in ohlc_record, f"OHLC field {field} missing"
        
        # Equity 데이터 검증
        equity_data = data['equity_data']
        assert isinstance(equity_data, list)
        assert len(equity_data) > 0
        
        equity_fields = chart_structure['equity_data_fields']
        for equity_record in equity_data[:3]:
            for field in equity_fields:
                assert field in equity_record, f"Equity field {field} missing"
        
        # 거래 마커 검증
        trade_markers = data['trade_markers']
        assert isinstance(trade_markers, list)
        # 거래 마커는 0개일 수도 있음 (Buy & Hold 등)
        
        if len(trade_markers) > 0:
            trade_fields = chart_structure['trade_marker_fields']
            for trade_record in trade_markers[:3]:
                for field in trade_fields:
                    assert field in trade_record, f"Trade field {field} missing"
        
        # 요약 통계 검증
        summary_stats = data['summary_stats']
        assert isinstance(summary_stats, dict)
        
        stats_fields = chart_structure['summary_stats_fields']
        for field in stats_fields:
            assert field in summary_stats, f"Summary stat {field} missing"
            
            # 숫자 필드 타입 검증
            if field in ['total_return_pct', 'sharpe_ratio', 'max_drawdown_pct', 'profit_factor']:
                assert isinstance(summary_stats[field], (int, float)), f"{field} should be numeric"
            
            if field == 'total_trades':
                assert isinstance(summary_stats[field], int), f"{field} should be integer"
                assert summary_stats[field] >= 0, f"{field} should be non-negative"
    
    def test_chart_data_endpoint_invalid_ticker(self, client):
        """차트 데이터 엔드포인트 - 잘못된 티커"""
        # Given
        payload = {
            "ticker": "INVALID123",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "buy_and_hold"
        }
        
        # When
        response = client.post("/api/v1/backtest/chart-data", json=payload)
        
        # Then
        error_scenarios = ExpectedResults.get_error_scenarios()['invalid_ticker']
        expected_codes = error_scenarios['expected_status_code']
        
        assert response.status_code in expected_codes
        
        # 에러 응답 구조 검증
        if response.status_code >= 400:
            error_data = response.json()
            assert 'detail' in error_data or 'message' in error_data
    
    def test_chart_data_endpoint_invalid_date_range(self, client):
        """차트 데이터 엔드포인트 - 잘못된 날짜 범위"""
        # Given
        payload = {
            "ticker": "AAPL",
            "start_date": "2023-12-31",  # 종료일보다 늦음
            "end_date": "2023-01-01",
            "initial_cash": 10000,
            "strategy": "buy_and_hold"
        }
        
        # When
        response = client.post("/api/v1/backtest/chart-data", json=payload)
        
        # Then
        error_scenarios = ExpectedResults.get_error_scenarios()['invalid_date_range']
        expected_codes = error_scenarios['expected_status_code']
        
        assert response.status_code in expected_codes
    
    def test_chart_data_endpoint_invalid_strategy(self, client):
        """차트 데이터 엔드포인트 - 잘못된 전략"""
        # Given
        payload = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "nonexistent_strategy"
        }
        
        # When
        response = client.post("/api/v1/backtest/chart-data", json=payload)
        
        # Then
        error_scenarios = ExpectedResults.get_error_scenarios()['invalid_strategy']
        expected_codes = error_scenarios['expected_status_code']
        
        assert response.status_code in expected_codes
    
    def test_chart_data_endpoint_invalid_parameters(self, client):
        """차트 데이터 엔드포인트 - 잘못된 파라미터"""
        # Given
        payload = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "sma_crossover",
            "strategy_params": {
                "short_window": 50,  # long_window보다 큼
                "long_window": 10
            }
        }
        
        # When
        response = client.post("/api/v1/backtest/chart-data", json=payload)
        
        # Then
        error_scenarios = ExpectedResults.get_error_scenarios()['invalid_parameters']
        expected_codes = error_scenarios['expected_status_code']
        
        assert response.status_code in expected_codes
    
    def test_portfolio_endpoint_success(self, client):
        """포트폴리오 백테스트 엔드포인트 성공 테스트"""
        # Given
        payload = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000, "investment_type": "lump_sum"},
                {"symbol": "GOOGL", "amount": 5000, "investment_type": "lump_sum"}
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_and_hold",
            "strategy_params": {}
        }
        
        # When
        response = client.post("/api/v1/backtest/portfolio", json=payload)
        
        # Then
        if response.status_code != 200:
            print(f"Portfolio endpoint error: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        
        # 래핑된 응답 구조 확인
        assert 'data' in data
        actual_data = data['data']
        
        # 응답 구조 검증
        assert 'individual_returns' in actual_data
        assert 'portfolio_composition' in actual_data
        
        # 개별 결과 검증
        individual_returns = actual_data['individual_returns']
        assert isinstance(individual_returns, dict)
        
        # 각 개별 결과 검증 (딕셔너리 형태)
        for symbol_key, result in individual_returns.items():
            assert 'amount' in result
            assert 'investment_type' in result
            assert 'start_price' in result
            assert 'end_price' in result
            assert isinstance(result['amount'], (int, float))
        
        # 포트폴리오 구성 정보 검증
        portfolio_composition = actual_data['portfolio_composition']
        assert isinstance(portfolio_composition, list)
        assert len(portfolio_composition) == len(payload['portfolio'])
        
        # 총 투자 금액 계산 (포트폴리오 구성에서)
        total_amount = sum(comp['amount'] for comp in portfolio_composition)
        assert total_amount > 0
    
    def test_portfolio_endpoint_unequal_weights(self, client):
        """포트폴리오 엔드포인트 - 불균등 비중"""
        # Given
        payload = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 2000, "investment_type": "lump_sum"},
                {"symbol": "GOOGL", "amount": 5000, "investment_type": "lump_sum"},
                {"symbol": "MSFT", "amount": 8000, "investment_type": "lump_sum"}
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_and_hold"
        }
        
        # When
        response = client.post("/api/v1/backtest/portfolio", json=payload)
        
        # Then
        if response.status_code != 200:
            print(f"Portfolio unequal weights error: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        
        # 래핑된 응답 구조 확인
        assert 'data' in data
        actual_data = data['data']
        
        # 실제 API 응답 구조에 맞게 검증
        assert 'individual_returns' in actual_data
        assert 'portfolio_composition' in actual_data
        
        # 투자 금액 비율 확인 (포트폴리오 구성에서)
        portfolio_composition = actual_data['portfolio_composition']
        total_amount = sum(comp['amount'] for comp in portfolio_composition)
        
        # 각 종목의 비중 계산 및 검증
        for i, composition in enumerate(portfolio_composition):
            expected_weight = payload['portfolio'][i]['amount'] / total_amount
            actual_weight = composition['amount'] / total_amount
            assert abs(actual_weight - expected_weight) < 0.01, f"Weight {i}: expected {expected_weight}, got {actual_weight}"
    
    def test_api_response_times(self, client):
        """API 응답 시간 벤치마크 테스트"""
        import time
        
        benchmarks = ExpectedResults.get_performance_benchmarks()
        
        # 차트 데이터 엔드포인트 성능 테스트
        payload = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "buy_and_hold"
        }
        
        start_time = time.time()
        response = client.post("/api/v1/backtest/chart-data", json=payload)
        execution_time = time.time() - start_time
        
        # 성능 검증
        max_time = benchmarks['api_response']['chart_data_endpoint']
        assert execution_time <= max_time, \
            f"Chart data API took {execution_time:.2f}s, exceeds limit of {max_time}s"
        
        assert response.status_code == 200
    
    def test_api_error_handling_consistency(self, client):
        """API 에러 처리 일관성 테스트"""
        # 다양한 잘못된 요청들
        invalid_requests = [
            # 필수 필드 누락
            {
                "start_date": "2023-01-01",
                "end_date": "2023-06-30",
                "initial_cash": 10000,
                "strategy": "buy_and_hold"
                # ticker 누락
            },
            
            # 잘못된 데이터 타입
            {
                "ticker": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-06-30",
                "initial_cash": "invalid",  # 문자열
                "strategy": "buy_and_hold"
            },
            
            # 음수 값
            {
                "ticker": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-06-30",
                "initial_cash": -1000,  # 음수
                "strategy": "buy_and_hold"
            }
        ]
        
        for invalid_payload in invalid_requests:
            # When
            response = client.post("/api/v1/backtest/chart-data", json=invalid_payload)
            
            # Then
            assert response.status_code >= 400, "Should return client error for invalid request"
            
            # 에러 응답 구조 일관성 검증
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    # FastAPI는 보통 'detail' 필드를 사용
                    assert 'detail' in error_data or 'message' in error_data or 'error' in error_data
                except json.JSONDecodeError:
                    # JSON이 아닌 응답도 허용 (HTML 에러 페이지 등)
                    pass
    
    def test_api_cors_headers(self, client):
        """API CORS 헤더 테스트"""
        # When
        response = client.options("/api/v1/backtest/chart-data")
        
        # Then
        # OPTIONS 요청은 허용되어야 함
        assert response.status_code in [200, 204, 405]  # 405는 OPTIONS가 비활성화된 경우
        
        # 실제 요청에서 CORS 헤더 확인
        payload = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_cash": 10000,
            "strategy": "buy_and_hold"
        }
        
        response = client.post("/api/v1/backtest/chart-data", json=payload)
        
        # 개발 환경에서는 CORS가 허용되어야 함
        if 'access-control-allow-origin' in response.headers:
            assert response.headers['access-control-allow-origin'] in ['*', 'http://localhost:5174']
    
    def test_api_request_validation(self, client):
        """API 요청 검증 테스트"""
        # Given - 각 필드별 경계값 테스트
        boundary_tests = [
            # 최소/최대 현금
            {"ticker": "AAPL", "initial_cash": 1, "strategy": "buy_and_hold"},  # 최소
            {"ticker": "AAPL", "initial_cash": 1000000000, "strategy": "buy_and_hold"},  # 매우 큰 값
            
            # 날짜 범위
            {"ticker": "AAPL", "start_date": "2020-01-01", "end_date": "2020-01-02", "strategy": "buy_and_hold"},  # 1일
        ]
        
        for test_payload in boundary_tests:
            # 기본값 설정
            payload = {
                "ticker": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-06-30",
                "initial_cash": 10000,
                "strategy": "buy_and_hold",
                "strategy_params": {}
            }
            payload.update(test_payload)
            
            # When
            response = client.post("/api/v1/backtest/chart-data", json=payload)
            
            # Then
            # 경계값이어도 유효한 요청이면 성공하거나 합리적인 에러 반환
            assert response.status_code in [200, 400, 422, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'ticker' in data
                assert data['ticker'] == payload['ticker']
