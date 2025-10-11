"""
백테스트 API 엔드포인트 통합 테스트

**테스트 범위**:
- POST /api/v1/backtest 엔드포인트
- 요청/응답 직렬화
- 전체 백테스트 플로우 (API → Service → Engine)
- 에러 처리 및 상태 코드

**테스트 원칙**:
- FastAPI TestClient 사용
- 실제 서비스 계층 호출 (목킹 최소화)
- 외부 API (yfinance) 호출은 fixtures 사용
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestBacktestEndpoint:
    """백테스트 엔드포인트 통합 테스트"""
    
    # Given: 유효한 단일 자산 백테스트 요청
    # When: POST /api/v1/backtest 호출
    # Then: 200 OK 및 백테스트 결과 반환
    @pytest.mark.integration
    def test_single_asset_backtest_success(self):
        """단일 자산 백테스트 API 성공 검증"""
        # Given
        payload = {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 10000.0,
                    "investment_type": "lump_sum",
                    "asset_type": "stock"
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy",
            "commission": 0.002,
            "rebalance_frequency": "monthly"
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        
        # 응답 구조 검증
        assert "portfolio_stats" in data
        assert "individual_stats" in data
        assert "benchmark_data" in data
        assert "exchange_rate_data" in data
        assert "news_data" in data
        
        # 백테스트 결과 검증
        portfolio_stats = data["portfolio_stats"]
        assert "total_return" in portfolio_stats
        assert "max_drawdown" in portfolio_stats
        assert "sharpe_ratio" in portfolio_stats
        assert "num_trades" in portfolio_stats
    
    # Given: SMA 전략 백테스트 요청
    # When: POST /api/v1/backtest 호출
    # Then: 200 OK 및 전략 결과 반환
    @pytest.mark.integration
    def test_sma_strategy_backtest_success(self):
        """SMA 전략 백테스트 API 성공 검증"""
        # Given
        payload = {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 10000.0
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "sma_strategy",
            "strategy_params": {
                "short_window": 10,
                "long_window": 30
            },
            "commission": 0.002
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_stats"]["num_trades"] >= 0
    
    # Given: 다중 자산 포트폴리오 백테스트 요청
    # When: POST /api/v1/backtest 호출
    # Then: 200 OK 및 개별 자산 통계 반환
    @pytest.mark.integration
    def test_multiple_assets_backtest_success(self):
        """다중 자산 포트폴리오 백테스트 API 성공 검증"""
        # Given
        payload = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000.0},
                {"symbol": "GOOGL", "amount": 3000.0},
                {"symbol": "MSFT", "amount": 2000.0}
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy"
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        
        # 개별 자산 통계 검증
        individual_stats = data["individual_stats"]
        assert len(individual_stats) == 3
        
        symbols = {stat["symbol"] for stat in individual_stats}
        assert symbols == {"AAPL", "GOOGL", "MSFT"}
    
    # Given: 잘못된 날짜 형식
    # When: POST /api/v1/backtest 호출
    # Then: 422 Unprocessable Entity
    def test_invalid_date_format_returns_422(self):
        """잘못된 날짜 형식 시 422 에러 반환 검증"""
        # Given
        payload = {
            "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
            "start_date": "2023/01/01",  # 잘못된 포맷
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy"
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 422
    
    # Given: 빈 포트폴리오
    # When: POST /api/v1/backtest 호출
    # Then: 422 Unprocessable Entity
    def test_empty_portfolio_returns_422(self):
        """빈 포트폴리오 시 422 에러 반환 검증"""
        # Given
        payload = {
            "portfolio": [],  # 빈 리스트
            "start_date": "2023-01-01",
            "end_date": "2023-06-30"
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 422
    
    # Given: 종료일이 시작일보다 이전
    # When: POST /api/v1/backtest 호출
    # Then: 422 Unprocessable Entity
    def test_end_date_before_start_date_returns_422(self):
        """종료일이 시작일보다 이전일 때 422 에러 반환 검증"""
        # Given
        payload = {
            "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
            "start_date": "2023-12-31",
            "end_date": "2023-01-01",  # 시작일보다 이전
            "strategy": "buy_hold_strategy"
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 422
    
    # Given: 유효하지 않은 전략명
    # When: POST /api/v1/backtest 호출
    # Then: 422 Unprocessable Entity
    def test_invalid_strategy_returns_422(self):
        """유효하지 않은 전략명 시 422 에러 반환 검증"""
        # Given
        payload = {
            "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "invalid_strategy"  # 존재하지 않는 전략
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 422
    
    # Given: RSI 전략 및 파라미터
    # When: POST /api/v1/backtest 호출
    # Then: 200 OK 및 파라미터 적용된 결과 반환
    @pytest.mark.integration
    def test_rsi_strategy_with_params(self):
        """RSI 전략 파라미터 적용 검증"""
        # Given
        payload = {
            "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "rsi_strategy",
            "strategy_params": {
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_stats" in data
    
    # Given: 벤치마크 데이터 포함 요청
    # When: POST /api/v1/backtest 호출
    # Then: 벤치마크 데이터 반환
    @pytest.mark.integration
    def test_benchmark_data_included(self):
        """벤치마크 데이터 포함 검증"""
        # Given
        payload = {
            "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy"
        }
        
        # When
        response = client.post("/api/v1/backtest", json=payload)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        
        benchmark_data = data["benchmark_data"]
        assert "sp500" in benchmark_data
        assert "nasdaq" in benchmark_data
        assert len(benchmark_data["sp500"]) > 0
        assert len(benchmark_data["nasdaq"]) > 0


class TestHealthCheck:
    """헬스 체크 엔드포인트 테스트"""
    
    # Given: 헬스 체크 엔드포인트
    # When: GET /health 호출
    # Then: 200 OK
    def test_health_check_endpoint(self):
        """헬스 체크 엔드포인트 검증"""
        # When
        response = client.get("/health")
        
        # Then
        assert response.status_code == 200
