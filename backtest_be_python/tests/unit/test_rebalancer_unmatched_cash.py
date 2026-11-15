"""[P3-28] "어떤 dca_info 항목과도 매칭되지 않는 현금"이 리밸런싱에서
사라지는 문제에 대한 도달 가능성(reachability) 분석과 회귀 가드.

**감사 항목 요약**: execute_rebalancing_trades에 전달되는 available_cash가
cash_holdings(= dca_info의 asset_type=='cash' 항목들의 합)로 설명되지 않는
"미매칭" 현금을 포함하고 있다면, 그 몫은 updated_cash_holdings /
updated_available_cash에 반영되지 않고 사라질 수 있다 (아래
TestHypotheticalUnmatchedCashIfInvariantWereViolated가 그 크기를 직접 측정한다).

**결론 (이 파일이 인코딩하는 것)**: 실제 프로덕션 호출 경로
    portfolio_manager_service.calculate_dca_portfolio_returns
    -> portfolio_simulation_engine.execute_simulation (+ initialize_portfolio_state)
    -> portfolio_rebalancer.execute_rebalancing_trades
를 따라가면, 이 "미매칭 현금" 상태는 구조적으로 발생할 수 없다. 근거는 다음
네 가지이며, 아래 TestUnmatchedCashInvariant가 그 근거를 코드로 고정한다.

1. portfolio_manager_service.calculate_dca_portfolio_returns (약 180-183행):
       cash_amount = sum(
           amount for unique_key, amount in amounts.items()
           if unique_key in dca_info and dca_info[unique_key].asset_type == 'cash'
       )
   execute_simulation에 전달되는 최초 available_cash(=cash_amount)는 항상
   "amounts를 dca_info의 asset_type=='cash'로 필터링한 합"으로 계산된다.

2. portfolio_simulation_engine.initialize_portfolio_state (75행):
       cash_holdings = {k: v for k, v in amounts.items() if dca_info[k].asset_type == 'cash'}
   cash_holdings는 정확히 같은 amounts 딕셔너리를 정확히 같은 조건으로
   필터링해서 만들어진다 -- 즉 cash_holdings의 모든 key는 정의상(tautologically)
   dca_info에 asset_type=='cash'로 존재하는 항목이다. "dca_info에 매칭되지
   않는 cash_holdings 항목"은 애초에 만들어질 수 없다. 그리고 1번과 완전히
   동일한 필터를 동일한 amounts에 적용하므로 시뮬레이션 시작 시점에
   available_cash == sum(cash_holdings.values())가 항상 성립한다.

3. rebalance_helper.calculate_target_weights (약 336-339행)는 amounts의 모든
   key에 대해 (금액이 0이더라도) target_weight 항목을 만든다. 따라서
   cash_holdings의 모든 key는 반드시 target_weights/adjusted_target_weights에도
   나타난다 -- execute_rebalancing_trades의 재분배 루프
   (for unique_key, target_weight in adjusted_target_weights.items())가
   cash_holdings의 어떤 key도 건너뛰지 않는다는 뜻이다.

4. execute_rebalancing_trades 자신의 갱신 로직
   (updated_available_cash = sum(updated_cash_holdings.values()), 약 269/273행)도
   available_cash를 별도로 갱신하지 않고 항상 cash_holdings 합계로 재계산하므로,
   리밸런싱 이후에도 두 값은 계속 동기 상태로 유지된다 (execute_simulation의
   유일한 재대입 지점: state.available_cash = rebalance_result['updated_available_cash']).

1~4를 종합하면, available_cash가 cash_holdings(=dca_info의 cash 항목)보다
"더 큰" 상태, 즉 "매칭되지 않는 현금"은 이 함수의 유일한 실제 호출 경로에서
결코 만들어질 수 없다 -- 매 시뮬레이션 스텝에서 두 값이 동일한 소스(amounts)와
동일한 필터(dca_info의 asset_type=='cash')로부터 재계산되기 때문이다.

따라서 이 항목은 "존재할 수 없는 상태에 대한 방어 코드를 추가하지 말라"는
지침에 따라 portfolio_rebalancer.py의 프로덕션 코드를 변경하지 않는다.
아래 TestHypotheticalUnmatchedCashIfInvariantWereViolated 클래스는 이 상태를
함수 유닛 테스트 수준에서 (실제 호출자를 우회해) 인위적으로 만들었을 때 현재
무슨 일이 일어나는지를 수치로 문서화한다 -- 프로덕션에서 도달 가능하다는
뜻이 아니라, 향후 이 함수가 다른 방식으로 호출될 경우를 위한 기록이다.
"""
import pytest
import pandas as pd

from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine
from app.services.rebalance_helper import RebalanceHelper
from app.domain.portfolio_domain import DcaStrategyInfo

pytestmark = pytest.mark.unit


def _stock_info(symbol: str, allocation: float) -> DcaStrategyInfo:
    return DcaStrategyInfo(symbol=symbol, allocation=allocation, asset_type='stock',
                            investment_type='lump_sum', monthly_amount=0.0)


def _cash_info(symbol: str, allocation: float) -> DcaStrategyInfo:
    return DcaStrategyInfo(symbol=symbol, allocation=allocation, asset_type='cash',
                            investment_type='lump_sum', monthly_amount=0.0)


def _manager_cash_amount(amounts, dca_info):
    """portfolio_manager_service.calculate_dca_portfolio_returns의 cash_amount
    계산과 동일한 공식 (약 180-183행)."""
    return sum(
        amount for unique_key, amount in amounts.items()
        if unique_key in dca_info and dca_info[unique_key].asset_type == 'cash'
    )


class TestUnmatchedCashInvariant:
    """실제 호출 경로(매니저 + 엔진)를 구성하는 공식들이 항상 서로 일치하는
    입력만 만들어낸다는 것을 여러 포트폴리오 구성에서 확인한다."""

    @pytest.mark.parametrize('amounts,dca_info', [
        # 현금 없음
        (
            {'A': 1000.0},
            {'A': _stock_info('AAA', 1.0)},
        ),
        # 현금 한 종목
        (
            {'A': 600.0, 'CASH': 400.0},
            {'A': _stock_info('AAA', 0.6), 'CASH': _cash_info('CASH', 0.4)},
        ),
        # 현금 여러 종목 + 주식 여러 종목
        (
            {'A': 300.0, 'B': 300.0, 'CASH1': 200.0, 'CASH2': 200.0},
            {
                'A': _stock_info('AAA', 0.3), 'B': _stock_info('BBB', 0.3),
                'CASH1': _cash_info('CASH1', 0.2), 'CASH2': _cash_info('CASH2', 0.2),
            },
        ),
        # 현금 금액이 0인 경우도 포함
        (
            {'A': 1000.0, 'CASH': 0.0},
            {'A': _stock_info('AAA', 1.0), 'CASH': _cash_info('CASH', 0.0)},
        ),
    ])
    def test_available_cash_always_equals_sum_of_cash_holdings(self, amounts, dca_info):
        engine = PortfolioSimulationEngine()

        cash_amount = _manager_cash_amount(amounts, dca_info)
        stock_amounts = {k: v for k, v in amounts.items() if dca_info[k].asset_type != 'cash'}

        state = engine.initialize_portfolio_state(
            stock_amounts=stock_amounts, cash_amount=cash_amount,
            amounts=amounts, dca_info=dca_info,
        )

        assert state.available_cash == pytest.approx(sum(state.cash_holdings.values()))
        # cash_holdings의 모든 key는 정의상 dca_info의 asset_type=='cash' 항목이다.
        assert set(state.cash_holdings.keys()) == {
            k for k in amounts if dca_info[k].asset_type == 'cash'
        }

    def test_every_cash_holding_key_appears_in_target_weights(self):
        """cash_holdings의 모든 key가 target_weights(그리고 결국
        adjusted_target_weights)에도 나타나 재분배 루프에서 누락되지 않음을 확인."""
        amounts = {'A': 300.0, 'B': 300.0, 'CASH1': 200.0, 'CASH2': 200.0}
        dca_info = {
            'A': _stock_info('AAA', 0.3), 'B': _stock_info('BBB', 0.3),
            'CASH1': _cash_info('CASH1', 0.2), 'CASH2': _cash_info('CASH2', 0.2),
        }
        cash_keys = {k for k in amounts if dca_info[k].asset_type == 'cash'}

        target_weights = RebalanceHelper.calculate_target_weights(amounts, dca_info)

        assert cash_keys <= set(target_weights.keys())

    def test_all_tradeable_assets_delisted_cash_bucket_absorbs_available_cash_fully(self):
        """모든 주식이 상장폐지되어 allocatable_pool_value가 사실상 현금뿐이어도,
        그 현금은 (invariant 덕분에) 항상 실제 cash_holdings 항목에 귀속되어
        있으므로 리밸런싱 후에도 전액 보존되어야 한다."""
        rebalancer = PortfolioRebalancer()

        dca_info = {
            'A': _stock_info('AAA', 0.4),   # 상장폐지
            'B': _stock_info('BBB', 0.4),   # 상장폐지
            'CASH': _cash_info('CASH', 0.2),
        }
        amounts = {'A': 100.0, 'B': 100.0, 'CASH': 50.0}  # target_weights: A=0.4,B=0.4,CASH=0.2
        shares = {'A': 10.0, 'B': 5.0}
        current_prices = {'A': 10.0, 'B': 20.0}
        delisted_stocks = {'A', 'B'}
        cash_holdings = {'CASH': 50.0}
        available_cash = 50.0  # invariant: sum(cash_holdings.values())와 정확히 일치

        target_weights = RebalanceHelper.calculate_target_weights(amounts, dca_info)
        total_stock_value = sum(shares[k] * current_prices[k] for k in shares)  # 200

        adjusted_target_weights = rebalancer.calculate_adjusted_weights(
            target_weights=target_weights, delisted_stocks=delisted_stocks, dca_info=dca_info,
        )
        # 유일하게 거래 가능한 CASH가 재분배 대상의 100%를 흡수해야 한다
        assert adjusted_target_weights['CASH'] == pytest.approx(1.0)

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
            delisted_stocks=delisted_stocks,
        )

        pre_total = total_stock_value + available_cash  # 250
        post_total = (
            sum(result['updated_shares'][k] * current_prices[k] for k in result['updated_shares'])
            + result['updated_available_cash']
        )

        assert result['updated_shares']['A'] == pytest.approx(shares['A'])
        assert result['updated_shares']['B'] == pytest.approx(shares['B'])
        assert result['updated_available_cash'] == pytest.approx(available_cash)
        assert post_total == pytest.approx(pre_total, rel=1e-9)
