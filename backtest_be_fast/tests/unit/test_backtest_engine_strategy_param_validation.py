"""전략 파라미터 검증 우회 회귀 테스트 (P2-05)

BacktestEngine._build_strategy()는 StrategyService.validate_strategy_params()가
ValueError를 던지면(= 파라미터가 STRATEGIES 스펙의 min/max/type/제약을 위반) 그
경고만 로깅하고 검증되지 않은 원본 값(params)을 그대로 전략 클래스에 주입했다.
그 결과 STRATEGIES에 정의된 모든 min/max 캡이 사실상 우회 가능했다.

구체적 피해 사례: rsi_strategy의 rsi_period(min=2)에 0을 보내면 검증은 실패하지만
그 값이 그대로 RsiStrategy.rsi_period에 주입되어 지표 계산(ewm(alpha=1/period))에서
0-division류 오류로 이어진다.

수정: 검증 실패 시 원본 값으로 폴백하지 않고 ValidationError(400)를 발생시켜 요청을
실패시킨다. 성공 경로(유효한 파라미터)는 기존과 동일하게 동작해야 한다.
"""
import pytest

from app.core.exceptions import ValidationError
from app.services.backtest_engine import BacktestEngine


pytestmark = pytest.mark.unit


@pytest.fixture
def engine():
    """실제 StrategyService를 사용하는 BacktestEngine (검증 로직 목킹 없음)"""
    return BacktestEngine()


class TestRejectedParamsRaiseInsteadOfFallback:
    """검증에 실패한 파라미터는 원본 값으로 폴백하지 않고 예외를 발생시켜야 한다"""

    def test_rsi_period_below_min_raises_validation_error(self, engine):
        """rsi_period의 스펙 min은 2. 0은 이를 위반하므로 요청이 실패해야 한다.

        수정 전에는 이 값이 그대로 RsiStrategy.rsi_period=0 에 주입되어
        (버그 리포트에 따르면) 지표 계산 중 0-division류 오류로 이어졌다.
        """
        with pytest.raises(ValidationError):
            engine._build_strategy('rsi_strategy', {'rsi_period': 0})

    def test_rsi_overbought_above_max_raises_validation_error(self, engine):
        """rsi_overbought의 스펙 max는 90. min 캡뿐 아니라 max 캡도 우회 불가해야 한다."""
        with pytest.raises(ValidationError):
            engine._build_strategy('rsi_strategy', {'rsi_overbought': 999})

    def test_validation_error_message_names_offending_parameter(self, engine):
        """예외 메시지는 어떤 파라미터가 거부되었는지 사용자에게 알려줘야 한다."""
        with pytest.raises(ValidationError) as exc_info:
            engine._build_strategy('rsi_strategy', {'rsi_period': 0})

        assert 'rsi_period' in exc_info.value.detail


class TestValidInRangeParamsStillApplied:
    """검증을 통과하는 파라미터는 기존과 동일하게 전략 클래스에 반영되어야 한다 (회귀 가드)"""

    def test_min_boundary_value_is_accepted_and_applied(self, engine):
        """rsi_period=2는 min 경계값이므로 유효하며 그대로 적용되어야 한다.

        (sibling test_strategy_param_override.py는 중간값 21을 사용하므로 여기서는
        경계값 케이스로 보완한다 — 중복 아님.)
        """
        result = engine._build_strategy('rsi_strategy', {'rsi_period': 2})

        assert result.rsi_period == 2
