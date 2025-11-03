"""
포트폴리오 스키마 검증 테스트

**테스트 범위**:
- PortfolioStock 모델의 데이터 검증 로직
- PortfolioBacktestRequest 모델의 검증 로직
- DCA 기간과 백테스트 기간 간의 관계 검증
- 날짜 포맷 및 범위 검증

**테스트 원칙**:
- 잘못된 입력에 대한 ValidationError 발생 확인
- 올바른 입력의 변환 및 저장 확인
- 경계값 테스트 (최소/최대값)
"""
import pytest
from pydantic import ValidationError
from app.schemas.schemas import PortfolioStock, PortfolioBacktestRequest


class TestPortfolioStock:
    """포트폴리오 종목 모델 테스트"""
    
    def test_valid_lump_sum_stock(self):
        """유효한 일시불 종목 생성 검증"""
        # Given
        data = {
            "symbol": "AAPL",
            "amount": 5000.0,
            "investment_type": "lump_sum",
            "asset_type": "stock"
        }
        
        # When
        stock = PortfolioStock(**data)
        
        # Then
        assert stock.symbol == "AAPL"
        assert stock.amount == 5000.0
        assert stock.investment_type == "lump_sum"
        assert stock.asset_type == "stock"
    
    def test_valid_dca_stock(self):
        """유효한 분할 매수 종목 생성 검증"""
        # Given
        data = {
            "symbol": "GOOGL",
            "amount": 12000.0,
            "investment_type": "dca",
            "dca_periods": 12,
            "asset_type": "stock"
        }
        
        # When
        stock = PortfolioStock(**data)
        
        # Then
        assert stock.symbol == "GOOGL"
        assert stock.amount == 12000.0
        assert stock.investment_type == "dca"
        assert stock.dca_periods == 12
    
    def test_invalid_investment_type_raises_error(self):
        """잘못된 투자 방식 시 예외 발생 검증"""
        # Given
        data = {
            "symbol": "AAPL",
            "amount": 5000.0,
            "investment_type": "invalid_type"  # 잘못된 투자 방식
        }
        
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            PortfolioStock(**data)
        
        assert "투자 방식은 lump_sum 또는 dca만 가능합니다" in str(exc_info.value)
    
    def test_negative_amount_raises_error(self):
        """음수 투자 금액 시 예외 발생 검증"""
        # Given
        data = {
            "symbol": "AAPL",
            "amount": -1000.0  # 음수
        }
        
        # When & Then
        with pytest.raises(ValidationError):
            PortfolioStock(**data)


class TestPortfolioBacktestRequest:
    """포트폴리오 백테스트 요청 모델 테스트"""
    
    def test_valid_portfolio_backtest_request(self):
        """유효한 포트폴리오 백테스트 요청 생성 검증"""
        # Given
        data = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000.0},
                {"symbol": "GOOGL", "amount": 3000.0}
            ],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "commission": 0.002,
            "strategy": "buy_and_hold"
        }
        
        # When
        request = PortfolioBacktestRequest(**data)
        
        # Then
        assert len(request.portfolio) == 2
        assert request.start_date == "2023-01-01"
        assert request.end_date == "2024-01-01"
        assert request.commission == 0.002
    
    def test_end_date_before_start_date_raises_error(self):
        """종료일이 시작일보다 이전일 때 예외 발생 검증"""
        # Given
        data = {
            "portfolio": [{"symbol": "AAPL", "amount": 5000.0}],
            "start_date": "2024-01-01",
            "end_date": "2023-01-01",  # 시작일보다 이전
            "strategy": "buy_and_hold"
        }
        
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            PortfolioBacktestRequest(**data)
        
        assert "종료 날짜는 시작 날짜보다 이후여야 합니다" in str(exc_info.value)
    
    def test_dca_periods_exceeds_backtest_period_raises_error(self):
        """DCA 기간이 백테스트 기간보다 긴 경우 예외 발생 검증"""
        # Given: 10개월 백테스트 기간, 12개월 DCA 기간
        data = {
            "portfolio": [{
                "symbol": "AAPL",
                "amount": 12000.0,
                "investment_type": "dca",
                "dca_periods": 12  # 12개월
            }],
            "start_date": "2023-01-01",
            "end_date": "2023-10-31",  # 약 10개월
            "strategy": "buy_and_hold"
        }
        
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            PortfolioBacktestRequest(**data)
        
        error_message = str(exc_info.value)
        # 에러 메시지가 포함되어 있는지만 확인 (유니코드 인코딩 문제 회피)
        assert "DCA" in error_message
        assert "AAPL" in error_message
    
    def test_dca_periods_within_backtest_period_succeeds(self):
        """DCA 기간이 백테스트 기간보다 짧은 경우 성공"""
        # Given: 24개월 백테스트 기간, 12개월 DCA 기간
        data = {
            "portfolio": [{
                "symbol": "AAPL",
                "amount": 12000.0,
                "investment_type": "dca",
                "dca_periods": 12  # 12개월
            }],
            "start_date": "2023-01-01",
            "end_date": "2025-01-01",  # 24개월
            "strategy": "buy_and_hold"
        }
        
        # When
        request = PortfolioBacktestRequest(**data)
        
        # Then
        assert request.portfolio[0].dca_periods == 12
        assert request.portfolio[0].investment_type == "dca"
    
    def test_multiple_stocks_with_invalid_dca_period_raises_error(self):
        """여러 종목 중 하나라도 DCA 기간이 초과하면 예외 발생"""
        # Given: 10개월 백테스트 기간
        data = {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 6000.0,
                    "investment_type": "dca",
                    "dca_periods": 6  # 유효한 기간
                },
                {
                    "symbol": "GOOGL",
                    "amount": 12000.0,
                    "investment_type": "dca",
                    "dca_periods": 15  # 초과하는 기간
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-10-31",  # 약 10개월
            "strategy": "buy_and_hold"
        }
        
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            PortfolioBacktestRequest(**data)
        
        error_message = str(exc_info.value)
        # GOOGL이 에러를 발생시켰는지 확인
        assert "GOOGL" in error_message
        assert "DCA" in error_message
    
    def test_lump_sum_investment_not_affected_by_dca_validation(self):
        """일시불 투자는 DCA 검증의 영향을 받지 않음"""
        # Given: 짧은 백테스트 기간이지만 일시불 투자
        data = {
            "portfolio": [{
                "symbol": "AAPL",
                "amount": 10000.0,
                "investment_type": "lump_sum"  # 일시불
            }],
            "start_date": "2023-01-01",
            "end_date": "2023-03-01",  # 2개월만
            "strategy": "buy_and_hold"
        }
        
        # When
        request = PortfolioBacktestRequest(**data)
        
        # Then
        assert request.portfolio[0].investment_type == "lump_sum"
    
    def test_edge_case_dca_equals_backtest_period(self):
        """DCA 기간이 백테스트 기간과 거의 같은 경우 (경계값)"""
        # Given: 12개월 백테스트 기간, 12개월 DCA 기간
        data = {
            "portfolio": [{
                "symbol": "AAPL",
                "amount": 12000.0,
                "investment_type": "dca",
                "dca_periods": 12
            }],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",  # 정확히 12개월
            "strategy": "buy_and_hold"
        }
        
        # When
        request = PortfolioBacktestRequest(**data)
        
        # Then
        assert request.portfolio[0].dca_periods == 12
    
    def test_empty_portfolio_raises_error(self):
        """빈 포트폴리오 시 예외 발생 검증"""
        # Given
        data = {
            "portfolio": [],  # 빈 리스트
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "strategy": "buy_and_hold"
        }
        
        # When & Then
        with pytest.raises(ValidationError):
            PortfolioBacktestRequest(**data)
    
    def test_invalid_date_format_raises_error(self):
        """잘못된 날짜 포맷 시 예외 발생 검증"""
        # Given
        data = {
            "portfolio": [{"symbol": "AAPL", "amount": 5000.0}],
            "start_date": "2023/01/01",  # 잘못된 포맷
            "end_date": "2024-01-01",
            "strategy": "buy_and_hold"
        }
        
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            PortfolioBacktestRequest(**data)
        
        assert "날짜는 YYYY-MM-DD 형식이어야 합니다" in str(exc_info.value)

