"""PortfolioCalculator._fallback_equity_curve(_sync) 단위 테스트 (P1-12).

`_calculate_realistic_equity_curve`의 all_dates가 비어 있을 때(포트폴리오의
모든 종목이 equity curve 데이터를 갖지 못했을 때) 사용되는 선형 성장 가정
fallback 경로. test_portfolio_calculator_equity_curve.py는 forward-fill
버그(P1-10)를 다루는 _calculate_realistic_equity_curve의 "정상" 경로를
검증하지만, 그 안에서 갈라지는 이 fallback 경로는 지금까지 직접 테스트된
적이 없었다.
"""
import pytest

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_calculator_service import portfolio_calculator

pytestmark = pytest.mark.unit


def _request(start_date: str, end_date: str) -> PortfolioBacktestRequest:
    return PortfolioBacktestRequest(
        portfolio=[{"symbol": "A", "amount": 1000.0}],
        start_date=start_date, end_date=end_date, strategy="sma_strategy",
    )


class TestFallbackEquityCurveLinearGrowth:
    @pytest.mark.asyncio
    async def test_linear_growth_matches_hand_calculated_daily_values(self):
        """종목 A만 있고 equity curve가 전혀 없다(strategy_stats에 equity_curve
        키가 없거나 falsy). final_value=1100, total_amount=1000(10% 성장)을
        5일간 선형 보간한다.

        손으로 계산 (growth_rate=0.10, progress=i/4):
          day0: 1000.0 (직접 대입)
          day1: 1000*(1+0.10*0.25) = 1025.0,  수익률 (1025-1000)/1000*100 = 2.5
          day2: 1000*(1+0.10*0.50) = 1050.0,  수익률 (1050-1025)/1025*100 = 2.4390243902439024
          day3: 1000*(1+0.10*0.75) = 1075.0,  수익률 (1075-1050)/1050*100 = 2.380952380952381
          day4: 1000*(1+0.10*1.00) = 1100.0,  수익률 (1100-1075)/1075*100 = 2.3255813953488373
        (day4의 값이 final_value=1100과 정확히 일치하는지도 함께 확인한다.)
        """
        request = _request('2024-01-01', '2024-01-05')
        portfolio_results = {
            'A': {'amount': 1000.0, 'final_value': 1100.0, 'strategy_stats': {}},
        }

        equity_curve, daily_returns, _weight_history = await portfolio_calculator._calculate_realistic_equity_curve(
            request, portfolio_results, total_amount=1000.0,
        )

        assert equity_curve['2024-01-01'] == pytest.approx(1000.0)
        assert equity_curve['2024-01-02'] == pytest.approx(1025.0)
        assert equity_curve['2024-01-03'] == pytest.approx(1050.0)
        assert equity_curve['2024-01-04'] == pytest.approx(1075.0)
        assert equity_curve['2024-01-05'] == pytest.approx(1100.0)

        assert daily_returns['2024-01-01'] == pytest.approx(0.0)
        assert daily_returns['2024-01-02'] == pytest.approx(2.5)
        assert daily_returns['2024-01-03'] == pytest.approx(2.4390243902439024)
        assert daily_returns['2024-01-04'] == pytest.approx(2.380952380952381)
        assert daily_returns['2024-01-05'] == pytest.approx(2.3255813953488373)

    @pytest.mark.asyncio
    async def test_fixed_initial_weights_are_held_constant_across_the_fallback_period(self):
        """fallback 경로는 실제 비중 변화를 추적할 방법이 없으므로, 초기
        비중(각 종목의 amount/total_amount)을 전체 기간 동안 그대로 유지한다
        (코드 주석에 명시된 의도된 설계 -- 실제 시세 반영이 아님에 주의)."""
        request = _request('2024-01-01', '2024-01-03')
        portfolio_results = {
            'A': {'amount': 600.0, 'final_value': 700.0, 'strategy_stats': {}},
            'B': {'amount': 400.0, 'final_value': 380.0, 'strategy_stats': {}},
        }

        _equity_curve, _daily_returns, weight_history = await portfolio_calculator._calculate_realistic_equity_curve(
            request, portfolio_results, total_amount=1000.0,
        )

        assert len(weight_history) == 3
        for day_weights in weight_history:
            assert day_weights['A'] == pytest.approx(0.6)
            assert day_weights['B'] == pytest.approx(0.4)

    @pytest.mark.asyncio
    async def test_no_growth_still_produces_flat_curve_without_division_by_zero(self):
        """final_value == total_amount (0% 성장)이어도 예외 없이 평탄한
        곡선을 만들어야 한다 (growth_rate=0이 이후 곱셈에서 0-나눗셈을
        유발하지 않는지 확인)."""
        request = _request('2024-01-01', '2024-01-02')
        portfolio_results = {
            'A': {'amount': 1000.0, 'final_value': 1000.0, 'strategy_stats': {}},
        }

        equity_curve, daily_returns, _weight_history = await portfolio_calculator._calculate_realistic_equity_curve(
            request, portfolio_results, total_amount=1000.0,
        )

        assert equity_curve['2024-01-01'] == pytest.approx(1000.0)
        assert equity_curve['2024-01-02'] == pytest.approx(1000.0)
        assert daily_returns['2024-01-02'] == pytest.approx(0.0)
