"""
PortfolioRebalancer 상장폐지 종목 처리 시 리밸런싱 가치 보존(P1-06) 검증

버그 요약 (P1-06):
    execute_rebalancing_trades 의 total_portfolio_value 는 상장폐지 종목의
    가치(시뮬레이션 엔진이 주입하는 마지막 유효 가격 기준)를 포함한다.
    calculate_adjusted_weights 는 상장폐지 종목의 비중을 0으로 두고 거래
    가능 종목들의 비중 합계가 1.0이 되도록 재조정한다. 그런데
    target_value = total_portfolio_value * target_weight 계산에서
    total_portfolio_value 를 그대로 사용하면, 상장폐지 종목의 가치가
    "거래 가능 종목에게 재분배되는 몫"과 "상장폐지 종목이 그대로 보유
    유지하는 몫" 양쪽에 이중으로 반영되어 리밸런싱마다 유령(phantom)
    가치가 생성된다.

불변식(invariant): 수수료를 제외하면 리밸런싱 전후 총 자산 가치(주식 평가액
+ 현금)는 항상 보존되어야 한다.
    post_total == pre_total - commission_cost
"""
import pytest
import pandas as pd

from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.domain.portfolio_domain import DcaStrategyInfo

pytestmark = pytest.mark.unit


def _stock_info(symbol: str, allocation: float) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol,
        allocation=allocation,
        asset_type='stock',
        investment_type='lump_sum',
        monthly_amount=0.0,
    )


def _cash_info(symbol: str, allocation: float) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol,
        allocation=allocation,
        asset_type='cash',
        investment_type='lump_sum',
        monthly_amount=0.0,
    )


def _post_rebalance_total(result, current_prices):
    """리밸런싱 결과에서 총 자산 가치(주식 평가액 + 현금)를 계산한다."""
    stock_value = sum(
        qty * current_prices[key]
        for key, qty in result['updated_shares'].items()
        if key in current_prices
    )
    return stock_value + result['updated_available_cash']


class TestDelistedStockRebalancingInvariant:
    """상장폐지 종목이 섞인 포트폴리오에서 리밸런싱 후 총 자산 가치가
    보존되는지(수수료만큼만 줄어드는지) 검증한다."""

    def _two_stock_case(self, commission: float, available_cash: float = 0.0):
        """A(거래 가능, 목표비중 50%) + B(상장폐지, 목표비중 50%) 2종목 시나리오."""
        rebalancer = PortfolioRebalancer()

        dca_info = {
            'A': _stock_info('AAA', 0.5),
            'B': _stock_info('BBB', 0.5),
        }
        shares = {'A': 10.0, 'B': 5.0}
        current_prices = {'A': 10.0, 'B': 20.0}  # B는 상장폐지 직전 마지막 유효 가격
        delisted_stocks = {'B'}
        target_weights = {'A': 0.5, 'B': 0.5}

        total_stock_value = sum(
            shares[k] * current_prices[k] for k in shares if k in current_prices
        )

        adjusted_target_weights = rebalancer.calculate_adjusted_weights(
            target_weights=target_weights,
            delisted_stocks=delisted_stocks,
            dca_info=dca_info,
        )
        # 상장폐지 종목 B는 0%로, 거래 가능한 A는 100%로 재조정되어야 함
        assert adjusted_target_weights['B'] == 0.0
        assert adjusted_target_weights['A'] == pytest.approx(1.0)

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

    def test_total_value_preserved_with_delisted_stock_and_zero_commission(self):
        """[핵심] 상장폐지 종목이 있어도 리밸런싱 후 총 자산 가치가 늘어나선 안 된다.

        수정 전 버그: 거래 가능 종목(A)에 total_portfolio_value(상장폐지 종목 B의
        가치까지 포함된 값) 전체를 재분배하면서, B가 그대로 보유 유지하는 가치까지
        더해져 총 자산이 B의 가치(이 시나리오에서는 $100)만큼 부풀려진다.
        """
        _, current_prices, pre_total, result = self._two_stock_case(commission=0.0)

        post_total = _post_rebalance_total(result, current_prices)

        assert post_total == pytest.approx(pre_total, rel=1e-9), (
            f"리밸런싱 후 총 자산가치가 보존되지 않음: pre={pre_total}, post={post_total} "
            f"(차이={post_total - pre_total})"
        )

    def test_delisted_position_share_count_unchanged(self):
        """상장폐지 종목(B)의 보유 주식 수는 리밸런싱으로 바뀌면 안 된다 (수수료 0일 때)."""
        shares, _current_prices, _pre_total, result = self._two_stock_case(commission=0.0)

        assert result['updated_shares']['B'] == pytest.approx(shares['B'])

    def test_no_delisted_stocks_behavior_unchanged(self):
        """상장폐지 종목이 없으면 기존 동작(불변식 + 목표비중 도달)이 그대로 유지되어야 한다.

        회귀 방지 가드: 이번 수정이 상장폐지가 없는 일반 케이스에 영향을 주지 않는지 확인.
        """
        rebalancer = PortfolioRebalancer()

        dca_info = {
            'A': _stock_info('AAA', 0.5),
            'C': _stock_info('CCC', 0.5),
        }
        shares = {'A': 15.0, 'C': 2.0}
        current_prices = {'A': 10.0, 'C': 20.0}
        delisted_stocks = set()
        target_weights = {'A': 0.5, 'C': 0.5}
        available_cash = 0.0

        total_stock_value = sum(
            shares[k] * current_prices[k] for k in shares if k in current_prices
        )

        adjusted_target_weights = rebalancer.calculate_adjusted_weights(
            target_weights=target_weights,
            delisted_stocks=delisted_stocks,
            dca_info=dca_info,
        )
        assert adjusted_target_weights == target_weights

        result = rebalancer.execute_rebalancing_trades(
            current_date=pd.Timestamp('2024-01-02'),
            adjusted_target_weights=adjusted_target_weights,
            shares=shares,
            current_prices=current_prices,
            available_cash=available_cash,
            cash_holdings={},
            commission=0.0,
            total_stock_value=total_stock_value,
            dca_info=dca_info,
            delisted_stocks=delisted_stocks,
        )

        pre_total = total_stock_value + available_cash
        post_total = _post_rebalance_total(result, current_prices)
        assert post_total == pytest.approx(pre_total, rel=1e-9)

        # 거래 가능 종목들은 목표 비중(각 50%)에 정확히 도달해야 한다
        assert result['weights_after']['AAA'] == pytest.approx(0.5, rel=1e-6)
        assert result['weights_after']['CCC'] == pytest.approx(0.5, rel=1e-6)

    def test_commission_scales_down_proportionally_with_delisted_stock(self):
        """수수료가 있을 때도 (사전 가치 - 수수료) == 사후 가치 불변식이 유지되어야 한다."""
        rebalancer = PortfolioRebalancer()

        dca_info = {
            'A': _stock_info('AAA', 0.3),
            'B': _stock_info('BBB', 0.4),   # 상장폐지
            'CASH': _cash_info('CASH', 0.3),
        }
        shares = {'A': 2.0, 'B': 5.0}
        current_prices = {'A': 10.0, 'B': 20.0}
        delisted_stocks = {'B'}
        target_weights = {'A': 0.3, 'B': 0.4, 'CASH': 0.3}
        cash_holdings = {'CASH': 30.0}
        available_cash = 30.0
        commission = 0.02

        total_stock_value = sum(
            shares[k] * current_prices[k] for k in shares if k in current_prices
        )

        adjusted_target_weights = rebalancer.calculate_adjusted_weights(
            target_weights=target_weights,
            delisted_stocks=delisted_stocks,
            dca_info=dca_info,
        )

        result = rebalancer.execute_rebalancing_trades(
            current_date=pd.Timestamp('2024-01-02'),
            adjusted_target_weights=adjusted_target_weights,
            shares=shares,
            current_prices=current_prices,
            available_cash=available_cash,
            cash_holdings=cash_holdings,
            commission=commission,
            total_stock_value=total_stock_value,
            dca_info=dca_info,
            delisted_stocks=delisted_stocks,
        )

        pre_total = total_stock_value + available_cash
        post_total = _post_rebalance_total(result, current_prices)

        assert result['commission_cost'] > 0
        assert post_total == pytest.approx(pre_total - result['commission_cost'], rel=1e-9)

        # 상장폐지 종목도 수수료 비례 축소 계수가 다른 자산과 동일하게 적용되어야 함
        expected_scale = (pre_total - result['commission_cost']) / pre_total
        assert result['updated_shares']['B'] == pytest.approx(shares['B'] * expected_scale)

    def test_all_stocks_delisted_no_trades_no_inflation_no_crash(self):
        """모든 종목이 상장폐지된 경우 거래 없이 그대로 유지되고 예외가 없어야 한다."""
        rebalancer = PortfolioRebalancer()

        dca_info = {
            'A': _stock_info('AAA', 0.5),
            'B': _stock_info('BBB', 0.5),
        }
        shares = {'A': 10.0, 'B': 5.0}
        current_prices = {'A': 10.0, 'B': 20.0}
        delisted_stocks = {'A', 'B'}
        target_weights = {'A': 0.5, 'B': 0.5}
        available_cash = 0.0

        total_stock_value = sum(
            shares[k] * current_prices[k] for k in shares if k in current_prices
        )

        adjusted_target_weights = rebalancer.calculate_adjusted_weights(
            target_weights=target_weights,
            delisted_stocks=delisted_stocks,
            dca_info=dca_info,
        )

        result = rebalancer.execute_rebalancing_trades(
            current_date=pd.Timestamp('2024-01-02'),
            adjusted_target_weights=adjusted_target_weights,
            shares=shares,
            current_prices=current_prices,
            available_cash=available_cash,
            cash_holdings={},
            commission=0.0,
            total_stock_value=total_stock_value,
            dca_info=dca_info,
            delisted_stocks=delisted_stocks,
        )

        assert result['trades_executed'] == 0
        assert result['rebalance_trades'] == []
        assert result['updated_shares']['A'] == pytest.approx(shares['A'])
        assert result['updated_shares']['B'] == pytest.approx(shares['B'])

        pre_total = total_stock_value + available_cash
        post_total = _post_rebalance_total(result, current_prices)
        assert post_total == pytest.approx(pre_total, rel=1e-9)
