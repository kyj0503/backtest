"""
요청 모델 검증 테스트 (직렬화/역직렬화)

**테스트 범위**:
- Pydantic 모델의 데이터 검증 로직
- 날짜 포맷 파싱
- 필수 필드 및 기본값 검증
- 유효성 검사 규칙

**테스트 원칙**:
- 잘못된 입력에 대한 ValidationError 발생 확인
- 올바른 입력의 변환 및 저장 확인
- 경계값 테스트 (최소/최대값)
"""
import pytest
from datetime import date
from pydantic import ValidationError
from app.schemas.requests import (
    StrategyType,
    BacktestRequest
)


class TestStrategyType:
    """전략 타입 Enum 테스트"""
    
    # Given: 유효한 전략 타입 문자열
    # When: Enum 값 조회
    # Then: 올바른 Enum 값 반환
    def test_valid_strategy_types(self):
        """유효한 전략 타입 검증"""
        assert StrategyType.SMA_STRATEGY.value == "sma_strategy"
        assert StrategyType.RSI_STRATEGY.value == "rsi_strategy"
        assert StrategyType.BOLLINGER_STRATEGY.value == "bollinger_strategy"
        assert StrategyType.MACD_STRATEGY.value == "macd_strategy"
        assert StrategyType.BUY_HOLD_STRATEGY.value == "buy_hold_strategy"
        assert StrategyType.EMA_STRATEGY.value == "ema_strategy"
    
    # Given: 모든 전략 타입 Enum
    # When: 값 개수 확인
    # Then: 6개 전략 타입 존재
    def test_strategy_type_count(self):
        """전략 타입 개수 검증 (6개)"""
        assert len(StrategyType) == 6


class TestBacktestRequest:
    """백테스트 요청 모델 테스트"""
    
    # Given: 유효한 백테스트 요청 데이터
    # When: BacktestRequest 인스턴스 생성
    # Then: 모델 생성 성공 및 필드값 정확함
    def test_valid_backtest_request(self):
        """유효한 백테스트 요청 생성 검증"""
        # Given
        data = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 10000.0,
            "strategy": "sma_strategy",
            "strategy_params": {"short_window": 10, "long_window": 20},
            "commission": 0.002
        }
        
        # When
        request = BacktestRequest(**data)
        
        # Then
        assert request.ticker == "AAPL"
        assert request.start_date == date(2023, 1, 1)
        assert request.end_date == date(2023, 12, 31)
        assert request.initial_cash == 10000.0
        assert request.strategy == StrategyType.SMA_STRATEGY
        assert request.commission == 0.002
    
    # Given: 잘못된 날짜 포맷
    # When: BacktestRequest 인스턴스 생성 시도
    # Then: ValidationError 발생
    def test_invalid_date_format_raises_error(self):
        """잘못된 날짜 포맷 시 예외 발생 검증"""
        # Given
        data = {
            "ticker": "AAPL",
            "start_date": "2023/01/01",  # 잘못된 포맷
            "end_date": "2023-12-31",
            "strategy": "sma_strategy"
        }
        
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(**data)
        
        assert "날짜 형식은 YYYY-MM-DD여야 합니다" in str(exc_info.value)
    
    # Given: 종료일이 시작일보다 이전
    # When: BacktestRequest 인스턴스 생성 시도
    # Then: ValidationError 발생
    def test_end_date_before_start_date_raises_error(self):
        """종료일이 시작일보다 이전일 때 예외 발생 검증"""
        # Given
        data = {
            "ticker": "AAPL",
            "start_date": "2023-12-31",
            "end_date": "2023-01-01",  # 시작일보다 이전
            "strategy": "sma_strategy"
        }
        
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            BacktestRequest(**data)
        
        assert "종료 날짜는 시작 날짜보다 이후여야 합니다" in str(exc_info.value)
    
    # Given: 음수 초기 투자금액
    # When: BacktestRequest 인스턴스 생성 시도
    # Then: ValidationError 발생
    def test_negative_initial_cash_raises_error(self):
        """음수 초기 투자금액 시 예외 발생 검증"""
        # Given
        data = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": -1000.0,  # 음수
            "strategy": "sma_strategy"
        }
        
        # When & Then
        with pytest.raises(ValidationError):
            BacktestRequest(**data)
    
    # Given: 유효 범위 초과 수수료
    # When: BacktestRequest 인스턴스 생성 시도
    # Then: ValidationError 발생
    def test_commission_out_of_range_raises_error(self):
        """수수료 유효 범위 초과 시 예외 발생 검증"""
        # Given
        data = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "strategy": "sma_strategy",
            "commission": 0.15  # 0.1 초과
        }
        
        # When & Then
        with pytest.raises(ValidationError):
            BacktestRequest(**data)
    
    # Given: 기본값만으로 요청
    # When: BacktestRequest 인스턴스 생성
    # Then: 기본값 적용됨
    def test_default_values_applied(self):
        """기본값 적용 검증"""
        # Given
        data = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "strategy": "buy_hold_strategy"
        }
        
        # When
        request = BacktestRequest(**data)
        
        # Then
        assert request.initial_cash == 10000.0  # 기본값
        assert request.commission == 0.002  # 기본값
        assert request.spread == 0.0  # 기본값
        assert request.strategy_params is None  # 기본값
