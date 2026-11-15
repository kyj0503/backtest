"""StrategyType enum과 실행 경로의 정합성 테스트

`buy_hold_strategy`는 backtesting.py 전략 클래스가 아니라 자체 시뮬레이터
(`run_buy_and_hold_portfolio_backtest`)로 처리되므로 STRATEGIES 레지스트리에
의도적으로 없다. 그래서 enum 값과 레지스트리가 1:1이 아니고, 이 비대칭이
조용히 깨지면(예: 새 enum 값을 추가하고 레지스트리 등록을 잊거나, buy&hold를
엔진 경로로 잘못 라우팅하면) 런타임에야 ValueError로 드러난다.

여기서 그 계약을 명시적으로 고정한다.
"""
import pytest

from app.schemas.requests import StrategyType
from app.services.strategy_service import STRATEGIES, StrategyService

pytestmark = pytest.mark.unit

# 전략 클래스가 아니라 전용 시뮬레이터로 처리되는 값
SIMULATOR_ONLY_STRATEGIES = {'buy_hold_strategy'}


class TestStrategyEnumMatchesExecutionPath:
    def test_every_enum_value_is_either_registered_or_simulator_only(self):
        """enum의 모든 값은 레지스트리에 있거나 시뮬레이터 전용이어야 한다.

        새 전략을 enum에만 추가하고 STRATEGIES 등록을 빠뜨리면 여기서 잡힌다.
        """
        for member in StrategyType:
            value = member.value
            registered = value in STRATEGIES
            simulator_only = value in SIMULATOR_ONLY_STRATEGIES
            assert registered ^ simulator_only, (
                f"{value}는 STRATEGIES 등록({registered})과 시뮬레이터 전용"
                f"({simulator_only}) 중 정확히 하나여야 한다"
            )

    def test_registry_has_no_entry_outside_the_enum(self):
        """레지스트리에 enum에 없는 전략이 남아 있으면 안 된다 (삭제 누락 방지)."""
        enum_values = {member.value for member in StrategyType}
        assert set(STRATEGIES) <= enum_values

    def test_simulator_only_strategy_is_not_resolvable_as_a_class(self):
        """buy_hold를 엔진 경로로 보내면 조용히 잘못 도는 대신 명확히 실패해야 한다."""
        service = StrategyService()
        for value in SIMULATOR_ONLY_STRATEGIES:
            with pytest.raises(ValueError, match=value):
                service.get_strategy_class(value)

    def test_registered_strategies_resolve_to_a_class(self):
        service = StrategyService()
        for value in STRATEGIES:
            assert service.get_strategy_class(value) is not None
