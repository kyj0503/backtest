"""
포트폴리오 스키마 검증 테스트

**테스트 범위**:
- PortfolioStock 모델의 데이터 검증 로직
- PortfolioBacktestRequest 모델의 검증 로직
- DCA 기간과 백테스트 기간 간의 관계 검증
- 날짜 포맷 및 범위 검증
"""
import pytest
from pydantic import ValidationError
from app.schemas.schemas import PortfolioStock, PortfolioBacktestRequest
from app.schemas.requests import StrategyType

pytestmark = pytest.mark.unit


class TestPortfolioStock:
    """포트폴리오 종목 모델 테스트"""
    
    def test_valid_lump_sum_stock(self):
        """유효한 일시불 종목 생성 검증"""
        data = {
            "symbol": "AAPL",
            "amount": 5000.0,
            "investment_type": "lump_sum",
            "asset_type": "stock"
        }
        stock = PortfolioStock(**data)
        assert stock.symbol == "AAPL"
        assert stock.amount == 5000.0
        assert stock.investment_type == "lump_sum"
        assert stock.asset_type == "stock"
    
    def test_valid_dca_stock(self):
        """유효한 분할 매수 종목 생성 검증"""
        data = {
            "symbol": "GOOGL",
            "amount": 12000.0,
            "investment_type": "dca",
            "dca_frequency": "monthly_1",
            "asset_type": "stock"
        }
        stock = PortfolioStock(**data)
        assert stock.symbol == "GOOGL"
        assert stock.amount == 12000.0
        assert stock.investment_type == "dca"
        assert stock.dca_frequency == 'monthly_1'
    
    def test_invalid_investment_type_raises_error(self):
        data = {
            "symbol": "AAPL",
            "amount": 5000.0,
            "investment_type": "invalid_type"
        }
        with pytest.raises(ValidationError) as exc_info:
            PortfolioStock(**data)
        assert "투자 방식은 lump_sum 또는 dca만 가능합니다" in str(exc_info.value)
    
    def test_negative_amount_raises_error(self):
        data = {
            "symbol": "AAPL",
            "amount": -1000.0
        }
        with pytest.raises(ValidationError):
            PortfolioStock(**data)


class TestPortfolioBacktestRequest:
    """포트폴리오 백테스트 요청 모델 테스트"""
    
    def test_valid_portfolio_backtest_request(self):
        data = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000.0},
                {"symbol": "GOOGL", "amount": 3000.0}
            ],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "commission": 0.002,
            "strategy": "buy_hold_strategy"
        }
        request = PortfolioBacktestRequest(**data)
        assert len(request.portfolio) == 2
    
    def test_end_date_before_start_date_raises_error(self):
        data = {
            "portfolio": [{"symbol": "AAPL", "amount": 5000.0}],
            "start_date": "2024-01-01",
            "end_date": "2023-01-01",
            "strategy": "buy_hold_strategy"
        }
        with pytest.raises(ValidationError) as exc_info:
            PortfolioBacktestRequest(**data)
        assert "종료 날짜는 시작 날짜보다 이후여야 합니다" in str(exc_info.value)
    
    def test_dca_periods_exceeds_backtest_period_raises_error(self):
        """DCA 기간이 백테스트 기간보다 긴 경우 예외 발생 검증"""
        # Given: 10개월 백테스트 기간, 12개월 DCA interval (monthly_12 = 1년)
        data = {
            "portfolio": [{
                "symbol": "AAPL",
                "amount": 12000.0,
                "investment_type": "dca",
                "dca_frequency": "monthly_12" # 1년마다
            }],
            "start_date": "2023-01-01",
            "end_date": "2023-10-31",  # 약 10개월
            "strategy": "buy_hold_strategy"
        }
        with pytest.raises(ValidationError) as exc_info:
            PortfolioBacktestRequest(**data)
        assert "DCA" in str(exc_info.value)
    
    def test_dca_periods_within_backtest_period_succeeds(self):
        # Given: 24개월 백테스트 기간, 1개월 DCA
        data = {
            "portfolio": [{
                "symbol": "AAPL",
                "amount": 12000.0,
                "investment_type": "dca",
                "dca_frequency": "monthly_1" 
            }],
            "start_date": "2023-01-01",
            "end_date": "2025-01-01",
            "strategy": "buy_hold_strategy"
        }
        request = PortfolioBacktestRequest(**data)
        assert request.portfolio[0].dca_frequency == 'monthly_1'

    def test_multiple_stocks_with_invalid_dca_period_raises_error(self):
        # Given: 10개월 백테스트 기간
        data = {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 6000.0,
                    "investment_type": "dca",
                    "dca_frequency": "monthly_1" # 유효 (매월)
                },
                {
                    "symbol": "GOOGL",
                    "amount": 12000.0,
                    "investment_type": "dca",
                    "dca_frequency": "monthly_12" # 무효 (12개월마다 > 10개월 기간)
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-10-31",
            "strategy": "buy_hold_strategy"
        }
        with pytest.raises(ValidationError) as exc_info:
            PortfolioBacktestRequest(**data)
        assert "GOOGL" in str(exc_info.value)

    def test_edge_case_dca_equals_backtest_period(self):
        """DCA 기간이 백테스트 기간과 거의 같은 경우"""
        # 1년 기간, 1년 DCA
        data = {
            "portfolio": [{
                "symbol": "AAPL",
                "amount": 12000.0,
                "investment_type": "dca",
                "dca_frequency": "monthly_12"
            }],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01", # 정확히 1년
            "strategy": "buy_hold_strategy"
        }
        request = PortfolioBacktestRequest(**data)
        assert request.portfolio[0].dca_frequency == 'monthly_12'

    def test_empty_portfolio_raises_error(self):
        data = {
            "portfolio": [],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "strategy": "buy_hold_strategy"
        }
        with pytest.raises(ValidationError):
            PortfolioBacktestRequest(**data)

    def test_invalid_date_format_raises_error(self):
        data = {
            "portfolio": [{"symbol": "AAPL", "amount": 5000.0}],
            "start_date": "2023/01/01",
            "end_date": "2024-01-01",
            "strategy": "buy_hold_strategy"
        }
        with pytest.raises(ValidationError):
            PortfolioBacktestRequest(**data)

    def test_default_strategy_is_valid_strategy_type(self):
        """strategy 미입력 시 기본값이 StrategyType의 유효한 값이어야 함 (P2-03)"""
        data = {
            "portfolio": [{"symbol": "AAPL", "amount": 5000.0}],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        }
        request = PortfolioBacktestRequest(**data)
        assert request.strategy in {s.value for s in StrategyType}

    def test_invalid_strategy_raises_error(self):
        """StrategyType에 없는 임의의 strategy 값은 ValidationError 발생 (P2-03)"""
        data = {
            "portfolio": [{"symbol": "AAPL", "amount": 5000.0}],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "strategy": "nonsense_strategy",
        }
        with pytest.raises(ValidationError):
            PortfolioBacktestRequest(**data)

    def test_sma_strategy_still_accepted(self):
        """sma_strategy와 같은 유효한 StrategyType 값은 계속 허용됨 (P2-03)"""
        data = {
            "portfolio": [{"symbol": "AAPL", "amount": 5000.0}],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "strategy": "sma_strategy",
        }
        request = PortfolioBacktestRequest(**data)
        assert request.strategy == "sma_strategy"
