"""PortfolioRebalancer 수수료 비례 축소가 상장폐지 종목 보유 주식 수를
잘못 줄이는 문제(P3-27) 회귀 테스트.

**버그**: `execute_rebalancing_trades`는 `total_commission_cost`를 계산한 뒤,
    scale_factor = (total_portfolio_value - total_commission_cost) / total_portfolio_value
를 `new_shares` 전체(거래 가능 종목 + 상장폐지 종목 모두)에 곱했다. 그러나
상장폐지 종목은 거래가 불가능해 `commission_cost`에 전혀 기여하지 않으므로
(상장폐지 분기는 target_value/commission 계산 전에 `continue`한다), 수수료는
거래 가능 자산(주식 매매 + 현금)에서만 차감되어야 한다. 상장폐지 종목까지
포함한 `total_portfolio_value`를 축소 기준으로 쓰면, 매 리밸런싱마다 상장폐지
종목의 보유 주식 수가 (작지만 0이 아닌 만큼) 계속 줄어든다 -- 거래가 불가능한
자산인데도 말이다.

**수정**: 수수료 축소는 거래 가능 자산 가치(tradeable_value = 거래 가능
종목의 재조정 후 가치 합 + 현금)만을 기준으로 하고, 상장폐지 종목의 보유
주식 수에는 scale_factor를 적용하지 않는다.

**불변식**: `post_total(수수료 축소 후 총 자산가치) == pre_total - commission_cost`
는 계속 유지되어야 한다 (수수료가 거래 가능 자산에서 전부 차감되므로).
"""
import pytest
import pandas as pd

from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.domain.portfolio_domain import DcaStrategyInfo

pytestmark = pytest.mark.unit


def _stock_info(symbol: str, allocation: float) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=allocation, asset_type='stock',
        investment_type='lump_sum', monthly_amount=0.0,
    )


class TestCommissionScalingDoesNotShrinkDelistedShares:
    def _three_asset_case(self, commission: float):
        """A, C(거래 가능) + B(상장폐지) 3종목, 현금 없음. A/C 사이에 실제
        리밸런싱 거래가 발생하도록 초기 비중을 목표와 어긋나게 둔다."""
        rebalancer = PortfolioRebalancer()

        dca_info = {
            'A': _stock_info('AAA', 0.4),
            'C': _stock_info('CCC', 0.2),
            'B': _stock_info('BBB', 0.4),  # 상장폐지
        }
        shares = {'A': 1.0, 'C': 10.0, 'B': 5.0}
        current_prices = {'A': 100.0, 'C': 10.0, 'B': 20.0}
        delisted_stocks = {'B'}
        target_weights = {'A': 0.4, 'C': 0.2, 'B': 0.4}
        available_cash = 0.0

        total_stock_value = sum(shares[k] * current_prices[k] for k in shares)

        adjusted_target_weights = rebalancer.calculate_adjusted_weights(
            target_weights=target_weights, delisted_stocks=delisted_stocks, dca_info=dca_info,
        )

        result = rebalancer.execute_rebalancing_trades(
            current_date=pd.Timestamp('2024-01-02'),
            adjusted_target_weights=adjusted_target_weights,
            shares=shares,
            current_prices=current_prices,
            available_cash=available_cash,
            cash_holdings={},
            commission=commission,
            total_stock_value=total_stock_value,
            dca_info=dca_info,
            delisted_stocks=delisted_stocks,
        )

        pre_total = total_stock_value + available_cash
        return shares, current_prices, pre_total, result

    def test_delisted_share_count_exactly_unchanged_with_commission(self):
        """[핵심] 수수료가 있어도 상장폐지 종목(B)의 보유 주식 수는 정확히
        그대로여야 한다 -- 단 1주도 줄어들면 안 된다."""
        shares, _prices, _pre_total, result = self._three_asset_case(commission=0.10)

        assert result['updated_shares']['B'] == shares['B'], (
            f"상장폐지 종목 B의 보유 주식 수가 리밸런싱으로 변경됨: "
            f"{shares['B']} -> {result['updated_shares']['B']} "
            f"(거래 불가능한 자산인데 수수료 비례 축소가 잘못 적용됨)"
        )

    def test_total_value_invariant_holds_with_commission_and_delisted(self):
        """수수료가 있어도 (사전 가치 - 수수료) == 사후 가치 불변식이 유지되어야 한다."""
        shares, current_prices, pre_total, result = self._three_asset_case(commission=0.10)

        post_total = (
            sum(result['updated_shares'][k] * current_prices[k] for k in result['updated_shares'])
            + result['updated_available_cash']
        )

        assert result['commission_cost'] > 0
        assert post_total == pytest.approx(pre_total - result['commission_cost'], rel=1e-9)

    def test_measured_drift_of_pre_fix_formula(self):
        """[증거/문서화] 수정 전 공식이 상장폐지 종목에 얼마나 잘못된 축소를
        적용했는지를 수치로 기록해 둔다.

        old_scale = (total_portfolio_value - commission_cost) / total_portfolio_value
        (상장폐지 종목까지 포함한 전체 가치를 기준으로 축소하던 예전 공식)
        vs 올바른 공식: 상장폐지 종목은 축소하지 않음(scale=1.0).

        이 케이스(commission=0.10, B=5주 @ $20)에서 예전 공식은 B를
        5.0 -> 4.888888...주로 (약 2.22%, 0.1111주) 잘못 줄였을 것이다.
        """
        shares, _prices, pre_total, result = self._three_asset_case(commission=0.10)

        commission_cost = result['commission_cost']
        old_scale_factor = (pre_total - commission_cost) / pre_total
        old_wrong_b_shares = shares['B'] * old_scale_factor
        drift = shares['B'] - old_wrong_b_shares

        # 수정 전 공식이라면 B가 5.0주에서 아래 값으로 "잘못" 줄어들었을 것이다
        # (44/9 = 4.888888...889, drift = 1/9 = 0.111111...111주, 약 -2.22%).
        assert old_wrong_b_shares == pytest.approx(44.0 / 9.0, rel=1e-9)
        assert drift == pytest.approx(1.0 / 9.0, rel=1e-9)

        # 수정된 코드는 이 잘못된 값이 아니라 원래 값을 정확히 그대로 유지해야 한다.
        assert result['updated_shares']['B'] == pytest.approx(shares['B'])
        assert result['updated_shares']['B'] != pytest.approx(old_wrong_b_shares)

    def test_zero_commission_unaffected_regression_guard(self):
        """회귀 가드: 수수료가 0이면 (기존에 이미 초록색이던 케이스) 여전히
        상장폐지 종목이 정확히 유지되어야 한다."""
        shares, current_prices, pre_total, result = self._three_asset_case(commission=0.0)

        assert result['updated_shares']['B'] == pytest.approx(shares['B'])
        post_total = (
            sum(result['updated_shares'][k] * current_prices[k] for k in result['updated_shares'])
            + result['updated_available_cash']
        )
        assert post_total == pytest.approx(pre_total, rel=1e-9)
