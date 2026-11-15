"""PortfolioCalculator._calculate_realistic_equity_curve forward-fill 회귀 테스트

**버그 (P1-10)**: `_calculate_realistic_equity_curve`의 date_range 순회 루프에서,
어떤 종목이 특정 날짜에 equity 데이터가 없을 때(예: 혼합 KR/US 포트폴리오에서
한국 공휴일에 미국은 거래일인 경우 등) "중간에 데이터가 없으면 마지막 값 사용
(forward fill)"이라는 주석과 달리 실제로는 `result['final_value']`
(백테스트 "종료 시점"의 최종 자산가치)를 그 중간 날짜에 주입하고 있었다.

이로 인해 equity_curve에 스파이크가 생기고, 그로부터 파생되는 daily_returns가
왜곡되어 PortfolioManagerService._calculate_daily_return_stats()가 계산하는
Annual_Volatility, Profit_Factor, Positive_Days/Negative_Days 등 하류 지표가
모두 오염된다 (portfolio_manager_service.py: equity_curve, daily_returns,
weight_history = await portfolio_calculator._calculate_realistic_equity_curve(...)
-> dr_stats = self._calculate_daily_return_stats(daily_returns) 호출 경로로 확인됨).

**수정**: date_range(정렬된 날짜 목록)를 순회하며 종목별로 "마지막으로 관측된"
equity 값을 추적해 진짜 forward fill을 수행한다. 아직 한 번도 관측되지 않은
종목(= date_range 시작일보다 늦게 데이터가 시작하는 종목 포함)은 최초 관측 전까지
초기 투자금(amount)을 사용한다.
"""
import pytest

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_calculator_service import portfolio_calculator

pytestmark = pytest.mark.unit


def _make_request(portfolio: list) -> PortfolioBacktestRequest:
    """_calculate_realistic_equity_curve는 all_dates가 비어있을 때만(모든 종목에
    equity curve가 없을 때) request를 fallback 경로에서 사용한다. 아래 테스트들은
    항상 최소 한 종목의 equity curve를 채워 넣으므로 request 내용 자체는 계산
    결과에 영향을 주지 않지만, 실제 운영 코드(portfolio_manager_service.py)와
    동일한 모양의 유효한 요청 객체를 사용해 둔다.
    """
    return PortfolioBacktestRequest(
        portfolio=portfolio,
        start_date="2024-01-01",
        end_date="2024-01-04",
        strategy="sma_strategy",
    )


def _stock_result(amount: float, final_value: float, equity_curve: dict) -> dict:
    """portfolio_manager_service.run_strategy_portfolio_backtest()가 만드는
    portfolio_results[symbol] 항목과 동일한 모양(shape)의 딕셔너리를 만든다.
    strategy_stats는 BacktestResult.__dict__ 를 흉내낸 것으로, equity_curve는
    {'YYYY-MM-DD': float(equity)} 형태다 (app/services/backtest_engine.py:329-332,
    app/schemas/responses.py:89 참조).
    """
    return {
        'amount': amount,
        'final_value': final_value,
        'weight': None,
        'strategy_stats': {'equity_curve': equity_curve},
    }


@pytest.mark.asyncio
async def test_forward_fill_uses_last_observed_value_not_final_value():
    """RED(core): 중간 날짜에 데이터가 없는 종목은 '마지막으로 관측된 값'을
    forward fill 해야 하며, 백테스트 "최종" 값(final_value)을 주입해서는 안 된다.

    A는 3일 모두 데이터가 있고, B는 가운데 날짜(day2=2024-01-02)가 빠져 있으며
    final_value(500)는 이웃 관측값(day1=100)과 크게 다르다.
    버그가 있으면 day2의 포트폴리오 가치는 1005 + 500 = 1505 가 되지만,
    올바른 forward fill이라면 1005 + 100(=B의 day1 관측값) = 1105 여야 한다.
    """
    portfolio_results = {
        'A': _stock_result(
            amount=1000, final_value=1010,
            equity_curve={'2024-01-01': 1000, '2024-01-02': 1005, '2024-01-03': 1010},
        ),
        'B': _stock_result(
            amount=100, final_value=500,
            equity_curve={'2024-01-01': 100, '2024-01-03': 500},  # day2 없음
        ),
    }
    request = _make_request([
        {"symbol": "A", "amount": 1000},
        {"symbol": "B", "amount": 100},
    ])

    equity_curve, _daily_returns, _weight_history = (
        await portfolio_calculator._calculate_realistic_equity_curve(
            request, portfolio_results, total_amount=1100
        )
    )

    assert equity_curve['2024-01-02'] == pytest.approx(1105.0), (
        f"day2 포트폴리오 가치는 B의 마지막 관측값(100)을 forward fill 해야 하는데 "
        f"실제로는 {equity_curve['2024-01-02']}였음 "
        f"(final_value 500이 중간 날짜에 잘못 주입되었는지 의심됨)"
    )


@pytest.mark.asyncio
async def test_forward_fill_gap_produces_no_spike_reversal_artifact():
    """gap 구간에 스파이크(가짜 급등) 후 반전(가짜 급락) 아티팩트가 생기면 안 된다.

    B는 day1=100(관측), day2=없음(gap), day3=105(관측), day4=500(관측, == final_value).
    버그가 있으면 day2는 final_value(500)를 조기 주입해 가짜로 +36.36%p 급등한 뒤,
    day3에 실제 관측값(105)으로 돌아가며 -26.33%p 급락하는 스파이크/반전 아티팩트가
    생긴다. 올바른 forward fill이라면 day2는 변화가 없고(0%), day3는 실제 소폭
    변화(+0.45%)만 나타나며, 진짜 큰 변화(+35.75%)는 실제로 데이터가 나타나는
    day4에만 반영되어야 한다.
    """
    portfolio_results = {
        'A': _stock_result(
            amount=1000, final_value=1000,
            equity_curve={
                '2024-01-01': 1000, '2024-01-02': 1000,
                '2024-01-03': 1000, '2024-01-04': 1000,
            },
        ),
        'B': _stock_result(
            amount=100, final_value=500,
            equity_curve={'2024-01-01': 100, '2024-01-03': 105, '2024-01-04': 500},  # day2 없음
        ),
    }
    request = _make_request([
        {"symbol": "A", "amount": 1000},
        {"symbol": "B", "amount": 100},
    ])

    _equity_curve, daily_returns, _weight_history = (
        await portfolio_calculator._calculate_realistic_equity_curve(
            request, portfolio_results, total_amount=1100
        )
    )

    day2_return = daily_returns['2024-01-02']
    day3_return = daily_returns['2024-01-03']

    # 아티팩트의 형태: day2가 크게 양수(급등)이면서 동시에 day3가 크게 음수(급락).
    assert not (day2_return > 20 and day3_return < -10), (
        f"day2={day2_return:.4f}%, day3={day3_return:.4f}% -- "
        f"forward fill이 아니라 final_value 조기 주입으로 인한 "
        f"스파이크/반전 아티팩트로 보임"
    )

    # 정확한 기대값: gap 구간(day2)은 변화 없음(forward fill), 실제 변화는
    # 그 값이 실제로 관측되는 날(day3)에만 반영되어야 한다.
    expected_day2 = (1100 - 1100) / 1100 * 100  # A 불변 + B forward-fill(100) => 무변화
    expected_day3 = (1105 - 1100) / 1100 * 100  # B가 105로 소폭 회복(day3 실측)
    assert day2_return == pytest.approx(expected_day2, abs=1e-9)
    assert day3_return == pytest.approx(expected_day3, abs=1e-9)


@pytest.mark.asyncio
async def test_no_gaps_equity_curve_matches_direct_sum():
    """회귀 방지 가드: 모든 종목이 모든 날짜에 데이터를 갖는 경우(gap 없음)에는
    forward fill 로직이 전혀 개입하지 않으므로 동작이 수정 전과 동일해야 한다.
    """
    portfolio_results = {
        'A': _stock_result(
            amount=1000, final_value=1010,
            equity_curve={'2024-01-01': 1000, '2024-01-02': 1005, '2024-01-03': 1010},
        ),
        'B': _stock_result(
            amount=100, final_value=104,
            equity_curve={'2024-01-01': 100, '2024-01-02': 102, '2024-01-03': 104},
        ),
    }
    request = _make_request([
        {"symbol": "A", "amount": 1000},
        {"symbol": "B", "amount": 100},
    ])

    equity_curve, _daily_returns, _weight_history = (
        await portfolio_calculator._calculate_realistic_equity_curve(
            request, portfolio_results, total_amount=1100
        )
    )

    assert equity_curve['2024-01-01'] == pytest.approx(1100.0)
    assert equity_curve['2024-01-02'] == pytest.approx(1107.0)
    assert equity_curve['2024-01-03'] == pytest.approx(1114.0)


@pytest.mark.asyncio
async def test_symbol_starting_after_first_date_keeps_initial_amount_until_first_observation():
    """date_range의 첫 날짜보다 늦게 데이터가 시작하는 종목(C)은, 실제 관측이
    시작되기 전까지 초기 투자금(amount)을 유지해야 한다 (final_value를 조기
    주입하면 안 된다).

    C는 day3(2024-01-03)에만 데이터가 있다 (day1, day2에는 없음).
    기존 버그 코드는 `i == 0`(day1)에서만 amount를 사용하고, day2(i == 1)부터는
    바로 else 분기로 빠져 final_value(300)를 잘못 주입한다.
    """
    portfolio_results = {
        'A': _stock_result(
            amount=1000, final_value=1010,
            equity_curve={'2024-01-01': 1000, '2024-01-02': 1005, '2024-01-03': 1010},
        ),
        'C': _stock_result(
            amount=50, final_value=300,
            equity_curve={'2024-01-03': 300},  # day1, day2 없음 (늦게 시작하는 종목)
        ),
    }
    request = _make_request([
        {"symbol": "A", "amount": 1000},
        {"symbol": "C", "amount": 50},
    ])

    equity_curve, _daily_returns, _weight_history = (
        await portfolio_calculator._calculate_realistic_equity_curve(
            request, portfolio_results, total_amount=1050
        )
    )

    assert equity_curve['2024-01-01'] == pytest.approx(1050.0)  # 1000 + 50(초기 투자금)
    assert equity_curve['2024-01-02'] == pytest.approx(1055.0), (
        f"C가 아직 한 번도 관측되지 않은 day2에는 초기 투자금(50)을 유지해야 "
        f"하는데 실제로는 {equity_curve['2024-01-02']}였음 "
        f"(final_value 300이 첫 관측 전에 조기 주입되었는지 의심됨)"
    )
    assert equity_curve['2024-01-03'] == pytest.approx(1310.0)  # 1010 + 300(실제 관측값)
