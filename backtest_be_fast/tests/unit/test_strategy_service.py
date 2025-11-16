"""
전략 서비스 단위 테스트

**테스트 범위**:
- 전략 클래스 반환 로직
- 전략 파라미터 검증
- 전략 정보 조회

**테스트 원칙**:
- FIRST 원칙 준수 (Fast, Independent, Repeatable, Self-Validating, Timely)
- Given-When-Then 구조 사용
- 핵심 비즈니스 로직에 집중
"""
import pytest
from app.services.strategy_service import StrategyService
from app.strategies.buy_hold_strategy import BuyAndHoldStrategy
from app.strategies.sma_strategy import SMACrossStrategy
from app.strategies.rsi_strategy import RSIStrategy
from app.strategies.bollinger_strategy import BollingerBandsStrategy
from app.strategies.macd_strategy import MACDStrategy
from app.strategies.ema_strategy import EMAStrategy


class TestStrategyService:
    """전략 서비스 테스트"""
    
    def setup_method(self):
        """각 테스트 전 실행: 서비스 인스턴스 생성"""
        self.service = StrategyService()
    
    # Given: 매수 후 보유 전략 요청
    # When: 전략 클래스 반환
    # Then: BuyAndHoldStrategy 클래스 반환
    def test_buy_hold_strategy_class(self):
        """매수 후 보유 전략 클래스 반환 검증"""
        # Given
        strategy_name = "buy_hold_strategy"
        
        # When
        strategy_class = self.service.get_strategy_class(strategy_name)
        
        # Then
        assert strategy_class == BuyAndHoldStrategy
    
    # Given: SMA 전략 요청
    # When: 전략 클래스 반환
    # Then: SMACrossStrategy 클래스 반환
    def test_sma_strategy_class(self):
        """SMA 전략 클래스 반환 검증"""
        # Given
        strategy_name = "sma_strategy"
        
        # When
        strategy_class = self.service.get_strategy_class(strategy_name)
        
        # Then
        assert strategy_class == SMACrossStrategy
    
    # Given: RSI 전략 요청
    # When: 전략 클래스 반환
    # Then: RSIStrategy 클래스 반환
    def test_rsi_strategy_class(self):
        """RSI 전략 클래스 반환 검증"""
        # Given
        strategy_name = "rsi_strategy"
        
        # When
        strategy_class = self.service.get_strategy_class(strategy_name)
        
        # Then
        assert strategy_class == RSIStrategy
    
    # Given: 존재하지 않는 전략명
    # When: 전략 클래스 반환 시도
    # Then: ValueError 예외 발생
    def test_invalid_strategy_name_raises_error(self):
        """유효하지 않은 전략명 시 예외 발생 검증"""
        # Given
        strategy_name = "invalid_strategy"
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.service.get_strategy_class(strategy_name)
        
        assert "지원하지 않는 전략" in str(exc_info.value)
    
    # Given: SMA 전략 파라미터
    # When: 파라미터 검증
    # Then: 유효한 파라미터 반환
    def test_validate_sma_strategy_params(self):
        """SMA 전략 파라미터 검증"""
        # Given
        strategy_name = "sma_strategy"
        params = {"short_window": 10, "long_window": 30}
        
        # When
        validated = self.service.validate_strategy_params(strategy_name, params)
        
        # Then
        assert validated["short_window"] == 10
        assert validated["long_window"] == 30
    
    # Given: 잘못된 SMA 파라미터 (short >= long)
    # When: 파라미터 검증
    # Then: ValueError 예외 발생
    def test_invalid_sma_params_raises_error(self):
        """잘못된 SMA 파라미터 검증"""
        # Given
        strategy_name = "sma_strategy"
        params = {"short_window": 30, "long_window": 10}  # 잘못된 순서
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.service.validate_strategy_params(strategy_name, params)
        
        assert "short_window" in str(exc_info.value) and "long_window" in str(exc_info.value)
    
    # Given: 빈 파라미터로 전략 요청
    # When: 파라미터 검증
    # Then: 기본값 적용
    def test_strategy_params_with_defaults(self):
        """빈 파라미터 시 기본값 적용 검증"""
        # Given
        strategy_name = "sma_strategy"
        params = {}
        
        # When
        validated = self.service.validate_strategy_params(strategy_name, params)
        
        # Then
        assert "short_window" in validated
        assert "long_window" in validated
    
    # Given: 전략 서비스
    # When: 모든 전략 목록 조회
    # Then: 6개 전략 반환
    def test_get_all_strategies(self):
        """모든 전략 목록 조회 검증"""
        # When
        strategies = self.service.get_all_strategies()
        
        # Then
        assert len(strategies) == 6
        assert "sma_strategy" in strategies
        assert "rsi_strategy" in strategies
        assert "bollinger_strategy" in strategies
        assert "macd_strategy" in strategies
        assert "buy_hold_strategy" in strategies
        assert "ema_strategy" in strategies
    
    # Given: 특정 전략명
    # When: 전략 정보 조회
    # Then: 전략 세부 정보 반환
    def test_get_strategy_info(self):
        """전략 정보 조회 검증"""
        # Given
        strategy_name = "sma_strategy"
        
        # When
        info = self.service.get_strategy_info(strategy_name)
        
        # Then
        assert "name" in info
        assert "description" in info
        assert "parameters" in info
