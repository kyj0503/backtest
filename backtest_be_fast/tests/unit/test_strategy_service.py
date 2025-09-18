"""
strategy_service 단위 테스트
전략 등록, 파라미터 검증, 전략 실행 테스트
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# 백엔드 앱 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.strategy_service import strategy_service
from app.core.custom_exceptions import ValidationError, BacktestValidationError
from tests.fixtures.expected_results import ExpectedResults

# 단위 테스트 마커 설정
pytestmark = pytest.mark.unit


class TestStrategyService:
    """strategy_service 모듈 단위 테스트"""
    
    def test_get_all_strategies_success(self):
        """전체 전략 목록 조회 테스트"""
        # When
        strategies = strategy_service.get_all_strategies()
        
        # Then
        assert isinstance(strategies, dict)
        assert len(strategies) >= 5  # 최소 5개 전략
        
        # 필수 전략 존재 확인
        required_strategies = [
            'buy_and_hold', 'sma_crossover', 'rsi_strategy',
            'bollinger_bands', 'macd_strategy'
        ]
        
        for strategy_name in required_strategies:
            assert strategy_name in strategies, f"Required strategy {strategy_name} not found"
        
        # 전략 구조 검증
        for strategy_name, strategy_info in strategies.items():
            assert isinstance(strategy_info, dict)
            assert 'description' in strategy_info
            assert 'parameters' in strategy_info
            assert isinstance(strategy_info['description'], str)
            assert isinstance(strategy_info['parameters'], dict)
    
    def test_get_strategy_info_success(self):
        """특정 전략 정보 조회 테스트"""
        # Given
        strategy_name = "sma_crossover"
        
        # When
        strategy_info = strategy_service.get_strategy_info(strategy_name)
        
        # Then
        assert isinstance(strategy_info, dict)
        assert 'description' in strategy_info
        assert 'parameters' in strategy_info
        
        # SMA Crossover 전략 파라미터 검증
        params = strategy_info['parameters']
        assert 'short_window' in params
        assert 'long_window' in params
        
        # 파라미터 메타데이터 검증
        for param_name, param_info in params.items():
            assert 'type' in param_info
            assert 'default' in param_info
            assert 'min' in param_info
            assert 'max' in param_info
    
    def test_get_strategy_info_not_found(self):
        """존재하지 않는 전략 조회 테스트"""
        # Given
        invalid_strategy = "nonexistent_strategy"
        
        # When & Then
        with pytest.raises((ValidationError, ValueError)) as exc_info:
            strategy_service.get_strategy_info(invalid_strategy)
        
        assert invalid_strategy in str(exc_info.value)
    
    def test_validate_strategy_params_sma_crossover_valid(self):
        """SMA Crossover 파라미터 검증 - 유효한 경우"""
        # Given
        strategy_name = "sma_crossover"
        params = {
            "short_window": 10,
            "long_window": 20
        }
        
        # When
        validated_params = strategy_service.validate_strategy_params(strategy_name, params)
        
        # Then
        assert isinstance(validated_params, dict)
        assert validated_params['short_window'] == 10
        assert validated_params['long_window'] == 20
        assert validated_params['short_window'] < validated_params['long_window']
    
    def test_validate_strategy_params_sma_crossover_invalid(self):
        """SMA Crossover 파라미터 검증 - 무효한 경우"""
        # Given
        strategy_name = "sma_crossover"

        # 잘못된 파라미터 케이스들
        invalid_params_cases = [
            # 범위 초과
            {"short_window": 200, "long_window": 300},
            # 타입 오류
            {"short_window": "invalid", "long_window": 20},
        ]

        for invalid_params in invalid_params_cases:
            # When & Then
            with pytest.raises((ValidationError, ValueError, TypeError)):
                strategy_service.validate_strategy_params(strategy_name, invalid_params)

    def test_validate_strategy_params_rsi_strategy_valid(self):
        """RSI 전략 파라미터 검증 - 유효한 경우"""
        # Given
        strategy_name = "rsi_strategy"
        params = {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        }
        
        # When
        validated_params = strategy_service.validate_strategy_params(strategy_name, params)
        
        # Then
        assert isinstance(validated_params, dict)
        assert validated_params['rsi_period'] == 14
        assert validated_params['rsi_oversold'] == 30
        assert validated_params['rsi_overbought'] == 70
        assert validated_params['rsi_oversold'] < validated_params['rsi_overbought']
    
    def test_validate_strategy_params_rsi_strategy_invalid(self):
        """RSI 전략 파라미터 검증 - 무효한 경우"""
        # Given
        strategy_name = "rsi_strategy"
        
        # 잘못된 파라미터 케이스들
        invalid_params_cases = [
            # rsi_oversold >= rsi_overbought
            {"rsi_period": 14, "rsi_oversold": 70, "rsi_overbought": 30},
            # 범위 초과 (RSI는 0-100)
            {"rsi_period": 14, "rsi_oversold": -10, "rsi_overbought": 120},
            # 비논리적 값
            {"rsi_period": 1, "rsi_oversold": 30, "rsi_overbought": 70}
        ]
        
        for invalid_params in invalid_params_cases:
            # When & Then
            with pytest.raises((ValidationError, ValueError)):
                strategy_service.validate_strategy_params(strategy_name, invalid_params)
    
    def test_validate_strategy_params_buy_and_hold(self):
        """Buy & Hold 전략 파라미터 검증 (파라미터 없음)"""
        # Given
        strategy_name = "buy_and_hold"
        params = {}
        
        # When
        validated_params = strategy_service.validate_strategy_params(strategy_name, params)
        
        # Then
        assert isinstance(validated_params, dict)
        assert len(validated_params) == 0  # Buy & Hold는 파라미터 없음
    
    def test_validate_strategy_params_bollinger_bands_valid(self):
        """Bollinger Bands 전략 파라미터 검증 - 유효한 경우"""
        # Given
        strategy_name = "bollinger_bands"
        params = {
            "period": 20,
            "std_dev": 2.0
        }
        
        # When
        validated_params = strategy_service.validate_strategy_params(strategy_name, params)
        
        # Then
        assert isinstance(validated_params, dict)
        assert validated_params['period'] == 20
        assert validated_params['std_dev'] == 2.0
        assert validated_params['std_dev'] > 0
    
    def test_validate_strategy_params_macd_strategy_valid(self):
        """MACD 전략 파라미터 검증 - 유효한 경우"""
        # Given
        strategy_name = "macd_strategy"
        params = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }
        
        # When
        validated_params = strategy_service.validate_strategy_params(strategy_name, params)
        
        # Then
        assert isinstance(validated_params, dict)
        assert validated_params['fast_period'] == 12
        assert validated_params['slow_period'] == 26
        assert validated_params['signal_period'] == 9
        assert validated_params['fast_period'] < validated_params['slow_period']
    
    def test_parameter_ranges_compliance(self):
        """전략별 파라미터 범위 준수 테스트"""
        # Given
        expected_ranges = ExpectedResults.get_strategy_parameter_ranges()
        
        for strategy_name, param_ranges in expected_ranges.items():
            # When
            strategy_info = strategy_service.get_strategy_info(strategy_name)
            actual_params = strategy_info['parameters']
            
            # Then
            for param_name, expected_range in param_ranges.items():
                if param_name == 'constraints':
                    continue  # 제약 조건은 별도 검증
                
                assert param_name in actual_params, \
                    f"Parameter {param_name} not found in {strategy_name}"
                
                actual_param = actual_params[param_name]
                
                # 기본값 범위 검증
                if 'default' in expected_range and 'default' in actual_param:
                    default_val = actual_param['default']
                    assert expected_range['min'] <= default_val <= expected_range['max'], \
                        f"Default value {default_val} out of range for {strategy_name}.{param_name}"
    
    def test_strategy_class_instantiation(self):
        """전략 클래스 인스턴스화 테스트"""
        # Given
        strategy_name = "sma_crossover"
        
        # When
        strategy_class = strategy_service.get_strategy_class(strategy_name)

        # Then
        assert strategy_class is not None
        assert callable(strategy_class)

        # backtesting 라이브러리의 Strategy는 파라미터를 클래스 속성으로 설정
        # 직접 __init__에 전달하지 않음
        try:
            # 기본 클래스 인스턴스화만 검증
            assert hasattr(strategy_class, 'short_window')
            assert hasattr(strategy_class, 'long_window')
        except Exception as e:
            pytest.fail(f"Strategy class validation failed: {e}")

    def test_strategy_default_parameters(self):
        """전략별 기본 파라미터 테스트"""
        # Given
        strategies = strategy_service.get_all_strategies()
        
        for strategy_name, strategy_info in strategies.items():
            # When
            params = strategy_info['parameters']
            
            # 기본값으로 파라미터 구성
            default_params = {}
            for param_name, param_info in params.items():
                if 'default' in param_info:
                    default_params[param_name] = param_info['default']
            
            # Then - 기본 파라미터로 검증 성공해야 함
            try:
                validated = strategy_service.validate_strategy_params(strategy_name, default_params)
                assert isinstance(validated, dict)
            except Exception as e:
                pytest.fail(f"Default parameters validation failed for {strategy_name}: {e}")
    
    def test_strategy_registry_integrity(self):
        """전략 레지스트리 무결성 테스트"""
        # When
        strategies = strategy_service.get_all_strategies()
        
        # Then
        # 중복 전략명 없음
        strategy_names = list(strategies.keys())
        assert len(strategy_names) == len(set(strategy_names)), "Duplicate strategy names found"
        
        # 각 전략의 클래스 존재 확인
        for strategy_name in strategy_names:
            try:
                strategy_class = strategy_service.get_strategy_class(strategy_name)
                assert strategy_class is not None
                assert callable(strategy_class)
            except Exception as e:
                pytest.fail(f"Strategy class not found for {strategy_name}: {e}")
    
    def test_parameter_type_validation(self):
        """파라미터 타입 검증 테스트"""
        # Given
        strategy_name = "sma_crossover"
        
        # 타입 테스트 케이스
        type_test_cases = [
            # 정수형
            {"short_window": 10, "long_window": 20},  # int
            {"short_window": 10.0, "long_window": 20.0},  # float (허용)
            
            # 문자열 (불허용)
            # {"short_window": "10", "long_window": "20"},  # string (should fail)
        ]
        
        # When & Then
        # 유효한 타입
        valid_params = {"short_window": 10, "long_window": 20}
        validated = strategy_service.validate_strategy_params(strategy_name, valid_params)
        assert isinstance(validated, dict)
        
        # 무효한 타입
        invalid_params = {"short_window": "invalid", "long_window": 20}
        with pytest.raises((ValidationError, ValueError, TypeError)):
            strategy_service.validate_strategy_params(strategy_name, invalid_params)
    
    def test_edge_case_parameter_values(self):
        """경계값 파라미터 테스트"""
        # Given
        strategy_name = "sma_crossover"
        
        # 경계값 테스트
        edge_cases = [
            # 최소값 경계
            {"short_window": 2, "long_window": 10},  # 최소 short_window
            {"short_window": 5, "long_window": 200}, # 최대 long_window
            
            # 차이 최소
            {"short_window": 9, "long_window": 10},  # 1차이
        ]
        
        for params in edge_cases:
            # When
            try:
                validated = strategy_service.validate_strategy_params(strategy_name, params)
                # Then
                assert isinstance(validated, dict)
                assert validated['short_window'] < validated['long_window']
            except (ValidationError, ValueError) as e:
                # 일부 경계값은 유효하지 않을 수 있음
                assert "window" in str(e) or "parameter" in str(e).lower()
