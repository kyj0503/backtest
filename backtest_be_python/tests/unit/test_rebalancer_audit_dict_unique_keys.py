"""[P3-29] execute_rebalancing_trades의 weights_before/weights_after가
표시 심볼(dca_info[unique_key].symbol)로 키가 잡혀 있어, 같은 이름의 항목이
여러 개면 서로 충돌하는 문제 검증.

**버그 요약**: 이전 배치(P2-07)에서 중복 현금 항목("CASH"를 이름으로 하는
현금을 여러 개 추가하는 경우)에 고유 키(unique_key, 예: 'CASH__cash_1',
'CASH__cash_2')를 부여해 amounts/dca_info 딕셔너리 충돌을 해결했다. 그런데
`execute_rebalancing_trades`의 `weights_before`/`weights_after`는 여전히
`dca_info[unique_key].symbol`(표시용 심볼, 둘 다 "CASH")로 키를 잡으므로,
두 현금 항목이 이 리포팅 딕셔너리 안에서 다시 충돌한다 -- 나중에 처리되는
항목이 먼저 항목을 덮어써 하나가 사라진다. 총액(total_portfolio_value)이나
`individual_returns`는 unique_key 기반이라 영향받지 않는다 -- 이 리포트
딕셔너리만의 문제다.

**FIX**: `weights_before`/`weights_after`를 `unique_key`로 키를 잡는다.

**기존 테스트와의 호환**: test_rebalancer_delisted.py::test_no_delisted_stocks_behavior_unchanged
는 dca_info={'A': symbol='AAA', 'C': symbol='CCC'}처럼 unique_key와 symbol이
(우연히, 그 테스트만의 축약 표기로) 다른 픽스처를 쓰면서 `weights_after['AAA']`로
접근한다. 실제 프로덕션에서는 주식의 unique_key가 항상 symbol과 동일하므로
(portfolio_manager_service.py: asset_type != 'cash'면 unique_key = symbol)
이 케이스는 실제로 발생하지 않지만, 그 핀된 테스트 파일은 이번 배치에서 수정할
수 없는 파일이다. 아래 구현은 "같은 심볼이 두 번 이상 나타나 충돌이 실제로
일어날 때만" unique_key로 폴백하고, 충돌이 없는 통상적인 경우(주식 전부,
그리고 현금이 이름당 하나씩만 있는 경우)는 예전처럼 symbol을 키로 사용해
그 핀된 테스트를 포함한 기존 계약을 그대로 보존한다.
"""
import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer

pytestmark = pytest.mark.unit


def _cash_info(symbol: str, allocation: float) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=allocation, asset_type='cash',
        investment_type='lump_sum', monthly_amount=0.0,
    )


def _stock_info(symbol: str, allocation: float) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=allocation, asset_type='stock',
        investment_type='lump_sum', monthly_amount=0.0,
    )


class TestDuplicateNamedCashEntriesProduceDistinctAuditEntries:
    """핵심 TDD 시나리오: 이름이 같은 현금 항목 두 개가 weights_before/after에서
    서로 다른 두 개의 항목으로 남아야 한다 (충돌로 하나가 사라지면 안 됨)."""

    def _two_cash_case(self):
        rebalancer = PortfolioRebalancer()

        dca_info = {
            'A': _stock_info('AAA', 0.4),
            'CASH__cash_1': _cash_info('CASH', 0.2),
            'CASH__cash_2': _cash_info('CASH', 0.4),
        }
        shares = {'A': 4.0}
        current_prices = {'A': 100.0}  # A 평가액 = 400
        cash_holdings = {'CASH__cash_1': 200.0, 'CASH__cash_2': 400.0}  # 서로 다른 금액
        available_cash = 600.0
        total_stock_value = 400.0
        adjusted_target_weights = {'A': 0.4, 'CASH__cash_1': 0.2, 'CASH__cash_2': 0.4}

        result = rebalancer.execute_rebalancing_trades(
            current_date=pd.Timestamp('2024-01-02'),
            adjusted_target_weights=adjusted_target_weights,
            shares=shares,
            current_prices=current_prices,
            available_cash=available_cash,
            cash_holdings=cash_holdings,
            commission=0.0,
            total_stock_value=total_stock_value,
            dca_info=dca_info,
            delisted_stocks=set(),
        )
        return result

    def test_weights_before_has_two_distinct_entries_for_duplicate_cash_names(self):
        result = self._two_cash_case()
        weights_before = result['weights_before']

        # 수정 전 버그: 둘 다 'CASH' 키로 기록되어 하나가 다른 하나를 덮어쓰므로
        # len(weights_before) == 2 (A, CASH)에 그쳤다.
        assert len(weights_before) == 3, (
            f"현금 항목 두 개가 충돌 없이 각자의 항목으로 남아야 함: {weights_before}"
        )

    def test_weights_after_has_two_distinct_entries_for_duplicate_cash_names(self):
        result = self._two_cash_case()
        weights_after = result['weights_after']

        assert len(weights_after) == 3, (
            f"현금 항목 두 개가 충돌 없이 각자의 항목으로 남아야 함: {weights_after}"
        )

    def test_each_cash_entry_keeps_its_own_correct_weight_value(self):
        """단순히 개수만 맞는 게 아니라, 각 항목이 자기 자신의 값을 유지해야
        한다 (충돌 시 나중 값으로 두 항목 모두가 잘못 보고되는 것도 방지)."""
        result = self._two_cash_case()
        weights_before = result['weights_before']

        cash_1_weight = weights_before.get('CASH__cash_1')
        cash_2_weight = weights_before.get('CASH__cash_2')

        assert cash_1_weight is not None, f"CASH__cash_1 항목이 없음: {weights_before}"
        assert cash_2_weight is not None, f"CASH__cash_2 항목이 없음: {weights_before}"
        assert cash_1_weight == pytest.approx(200.0 / 1000.0)
        assert cash_2_weight == pytest.approx(400.0 / 1000.0)
        assert cash_1_weight != cash_2_weight

    def test_stock_entry_still_present_alongside_the_two_cash_entries(self):
        result = self._two_cash_case()
        # 'AAA'는 이 리밸런싱 참가자 중 유일한 심볼이므로(충돌 없음), 기존과
        # 동일하게 심볼로 접근 가능해야 한다 -- 충돌이 있는 CASH만 unique_key로
        # 폴백한다.
        assert result['weights_before'].get('AAA') == pytest.approx(400.0 / 1000.0)


class TestNonCollidingCasesUnaffected:
    """회귀 가드: 심볼 충돌이 없는 통상적인 경우(주식 전부, 현금 이름당 하나씩)는
    영향받지 않아야 한다 -- 이는 test_rebalancer_delisted.py의 기존 계약과도
    맞아야 한다."""

    def test_single_named_assets_still_readable_by_display_symbol(self):
        rebalancer = PortfolioRebalancer()
        dca_info = {
            'A': _stock_info('AAA', 0.5),
            'C': _stock_info('CCC', 0.5),
        }
        shares = {'A': 15.0, 'C': 2.0}
        current_prices = {'A': 10.0, 'C': 20.0}
        target_weights = {'A': 0.5, 'C': 0.5}
        total_stock_value = sum(shares[k] * current_prices[k] for k in shares)

        result = rebalancer.execute_rebalancing_trades(
            current_date=pd.Timestamp('2024-01-02'),
            adjusted_target_weights=target_weights,
            shares=shares,
            current_prices=current_prices,
            available_cash=0.0,
            cash_holdings={},
            commission=0.0,
            total_stock_value=total_stock_value,
            dca_info=dca_info,
            delisted_stocks=set(),
        )

        # 충돌이 없으므로 예전처럼 심볼로 접근 가능해야 한다 (핀 고정된
        # test_rebalancer_delisted.py::test_no_delisted_stocks_behavior_unchanged
        # 와 동일한 접근 방식).
        assert result['weights_after']['AAA'] == pytest.approx(0.5, rel=1e-6)
        assert result['weights_after']['CCC'] == pytest.approx(0.5, rel=1e-6)

    def test_single_cash_entry_still_readable_by_display_symbol(self):
        rebalancer = PortfolioRebalancer()
        dca_info = {
            'A': _stock_info('AAA', 0.6),
            'CASH': _cash_info('CASH', 0.4),
        }
        shares = {'A': 6.0}
        current_prices = {'A': 100.0}
        cash_holdings = {'CASH': 400.0}
        target_weights = {'A': 0.6, 'CASH': 0.4}

        result = rebalancer.execute_rebalancing_trades(
            current_date=pd.Timestamp('2024-01-02'),
            adjusted_target_weights=target_weights,
            shares=shares,
            current_prices=current_prices,
            available_cash=400.0,
            cash_holdings=cash_holdings,
            commission=0.0,
            total_stock_value=600.0,
            dca_info=dca_info,
            delisted_stocks=set(),
        )

        assert result['weights_before']['CASH'] == pytest.approx(0.4)
        assert result['weights_after']['CASH'] == pytest.approx(0.4)
