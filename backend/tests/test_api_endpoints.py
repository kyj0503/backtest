"""
API 엔드포인트 테스트
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app


class TestBacktestAPI:
    """백테스트 API 엔드포인트 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.client = TestClient(app)
    
    def test_chart_data_endpoint_success(self, sample_backtest_request):
        """차트 데이터 API 성공 테스트"""
        with patch('app.services.backtest_service.generate_chart_data') as mock_service:
            # Mock 차트 데이터 응답
            mock_response = {
                "ohlc_data": [
                    {"date": "2023-01-01", "open": 150.0, "high": 155.0, "low": 149.0, "close": 152.0, "volume": 1000000}
                ],
                "equity_data": [
                    {"date": "2023-01-01", "equity": 10000, "return_pct": 0.0}
                ],
                "trade_markers": [],
                "indicators": {},
                "summary_stats": {
                    "total_return": 5.0,
                    "sharpe_ratio": 1.2
                }
            }
            mock_service.return_value = mock_response
            
            response = self.client.post("/api/v1/backtest/chart-data", json=sample_backtest_request)
            
            assert response.status_code == 200
            data = response.json()
            assert "ohlc_data" in data
            assert "equity_data" in data
            assert "summary_stats" in data
    
    def test_chart_data_endpoint_invalid_ticker(self, sample_backtest_request):
        """잘못된 티커로 차트 데이터 API 테스트"""
        invalid_request = sample_backtest_request.copy()
        invalid_request["ticker"] = "INVALID"
        
        with patch('app.utils.data_fetcher.DataFetcher.get_stock_data') as mock_data_fetcher:
            from app.core.custom_exceptions import InvalidSymbolError
            mock_data_fetcher.side_effect = InvalidSymbolError("INVALID")
            
            response = self.client.post("/api/v1/backtest/chart-data", json=invalid_request)
            
            assert response.status_code == 422
            assert "유효하지 않은 종목 심볼" in response.json()["detail"]
    
    def test_chart_data_endpoint_no_data(self, sample_backtest_request):
        """데이터 없음 차트 데이터 API 테스트"""
        with patch('app.utils.data_fetcher.DataFetcher.get_stock_data') as mock_data_fetcher:
            from app.core.custom_exceptions import DataNotFoundError
            mock_data_fetcher.side_effect = DataNotFoundError("AAPL", "2023-01-01", "2023-12-31")
            
            response = self.client.post("/api/v1/backtest/chart-data", json=sample_backtest_request)
            
            assert response.status_code == 404
            assert "데이터를 찾을 수 없습니다" in response.json()["detail"]
    
    def test_chart_data_endpoint_rate_limit(self, sample_backtest_request):
        """API 제한 차트 데이터 API 테스트"""
        with patch('app.utils.data_fetcher.DataFetcher.get_stock_data') as mock_data_fetcher:
            from app.core.custom_exceptions import YFinanceRateLimitError
            mock_data_fetcher.side_effect = YFinanceRateLimitError()
            
            response = self.client.post("/api/v1/backtest/chart-data", json=sample_backtest_request)
            
            assert response.status_code == 429
            assert "요청 제한" in response.json()["detail"]
    
    def test_portfolio_backtest_success(self, sample_portfolio_request):
        """포트폴리오 백테스트 성공 테스트"""
        with patch('app.services.portfolio_service.run_portfolio_backtest') as mock_service:
            mock_response = {
                "status": "success",
                "results": {
                    "total_return": 15.5,
                    "annual_return": 12.3,
                    "volatility": 18.7,
                    "sharpe_ratio": 0.85
                }
            }
            mock_service.return_value = mock_response
            
            response = self.client.post("/api/v1/backtest/portfolio", json=sample_portfolio_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "results" in data
    
    def test_portfolio_backtest_empty_portfolio(self):
        """빈 포트폴리오 백테스트 테스트"""
        empty_request = {
            "portfolio": [],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "cash": 10000
        }
        
        response = self.client.post("/api/v1/backtest/portfolio", json=empty_request)
        
        assert response.status_code == 400
        assert "포트폴리오가 비어있습니다" in response.json()["detail"]
    
    def test_portfolio_backtest_too_many_stocks(self):
        """너무 많은 종목 포트폴리오 테스트"""
        large_portfolio = {
            "portfolio": [{"ticker": f"STOCK{i}", "amount": 1000} for i in range(15)],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "cash": 10000
        }
        
        response = self.client.post("/api/v1/backtest/portfolio", json=large_portfolio)
        
        assert response.status_code == 400
        assert "최대 10개 종목" in response.json()["detail"]
    
    def test_chart_data_validation_error(self):
        """차트 데이터 요청 검증 오류 테스트"""
        invalid_request = {
            "ticker": "",  # 빈 티커
            "start_date": "2023-01-01",
            "end_date": "2022-12-31",  # 시작일보다 이른 종료일
            "strategy": "invalid_strategy"
        }
        
        response = self.client.post("/api/v1/backtest/chart-data", json=invalid_request)
        
        # FastAPI validation error
        assert response.status_code in [400, 422]
