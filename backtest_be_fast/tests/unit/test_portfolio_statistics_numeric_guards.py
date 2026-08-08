"""포트폴리오 통계의 수치 안정성 테스트 (P1-16 / P1-17)

`annual_volatility > 0` 가드는 부동소수점 노이즈에 취약하다. 동일한 값
여러 개의 `Series.std()`가 정확한 0이 아니라 ~1e-18을 반환할 수 있어,
가드를 통과한 뒤 나눗셈에서 Sharpe가 천문학적 값(1e17 규모)이 된다.
데이터 포인트가 하나뿐이면 `std()`가 NaN이라 변동성이 NaN으로 응답에
그대로 유출된다.

두 구현(PortfolioMetrics / PortfolioCalculator)이 같은 계산을 중복하므로
양쪽 모두에 대해 검증한다.
"""
import pandas as pd
import pytest

from app.services.portfolio.portfolio_metrics import PortfolioMetrics
from app.services.portfolio_calculator_service import PortfolioCalculator

pytestmark = pytest.mark.unit

IMPLEMENTATIONS = [
    pytest.param(PortfolioMetrics(), id='PortfolioMetrics'),
    pytest.param(PortfolioCalculator(), id='PortfolioCalculator'),
]


def _stats(impl, values, total_amount=1000.0):
    """구현체의 calculate_portfolio_statistics를 호출한다.

    입력은 정규화된 포트폴리오 가치(시작=1.0) 컬럼과 일간 수익률 컬럼을 가진
    DataFrame이다 — 시뮬레이션 엔진이 만들어 넘기는 형태와 동일하다.
    """
    index = pd.bdate_range('2024-01-01', periods=len(values))
    normalized = pd.Series(values, index=index) / values[0]
    frame = pd.DataFrame({
        'Portfolio_Value': normalized,
        'Daily_Return': normalized.pct_change().fillna(0.0) * 100,
    })
    return impl.calculate_portfolio_statistics(frame, total_amount)


def _noisy_flat_frame(n=30):
    """값이 사실상 변하지 않지만 부동소수점 노이즈가 낀 프레임.

    시뮬레이션 엔진은 매일 `보유수량 × 가격 / 총투자금`으로 정규화 가치를
    누적 계산하므로, 가격이 고정이어도 결과가 1.0에 정확히 떨어지지 않고
    1.0 ± 1e-16 수준으로 흔들린다. 이 노이즈가 std()를 정확한 0이 아닌
    아주 작은 양수로 만들어 `> 0` 가드를 통과시킨다.
    """
    index = pd.bdate_range('2024-01-01', periods=n)
    eps = 2.220446049250313e-16  # 1.0 근방의 float 간격
    values = [1.0 + (eps if i % 2 else 0.0) for i in range(n)]
    normalized = pd.Series(values, index=index)
    return pd.DataFrame({
        'Portfolio_Value': normalized,
        'Daily_Return': normalized.pct_change().fillna(0.0) * 100,
    })


class TestSharpeIsNotBlownUpByFloatingPointNoise:
    @pytest.mark.parametrize('impl', IMPLEMENTATIONS)
    def test_noise_level_variation_does_not_explode_sharpe(self, impl):
        """부동소수점 노이즈 수준의 변동은 변동성 0으로 취급되어야 한다.

        수정 전: std()가 ~1e-16을 반환해 `annual_volatility > 0` 가드를
        통과하고, 나눗셈에서 Sharpe가 1e17 규모로 폭발했다.
        """
        stats = impl.calculate_portfolio_statistics(_noisy_flat_frame(), 1000.0)

        sharpe = stats['Sharpe_Ratio']
        assert abs(sharpe) < 100.0, f"노이즈 수준 변동에서 Sharpe가 폭발: {sharpe}"

    @pytest.mark.parametrize('impl', IMPLEMENTATIONS)
    def test_exactly_flat_portfolio_reports_zero(self, impl):
        """값이 정확히 동일하면 변동성·Sharpe 모두 0이어야 한다 (회귀 가드)."""
        stats = _stats(impl, [1000.0] * 30)

        assert stats['Annual_Volatility'] == pytest.approx(0.0, abs=1e-9)
        assert stats['Sharpe_Ratio'] == pytest.approx(0.0, abs=1e-9)


class TestNoNaNLeaksIntoStatistics:
    @pytest.mark.parametrize('impl', IMPLEMENTATIONS)
    def test_single_data_point_does_not_leak_nan(self, impl):
        """데이터가 한 점뿐이면 std()가 NaN이지만 응답에 NaN이 나가면 안 된다."""
        stats = _stats(impl, [1000.0])

        for key, value in stats.items():
            if isinstance(value, float):
                assert not pd.isna(value), f"{key}가 NaN으로 유출됨"

    @pytest.mark.parametrize('impl', IMPLEMENTATIONS)
    def test_normal_series_still_reports_real_numbers(self, impl):
        """정상 데이터에서는 기존대로 의미 있는 값이 나와야 한다 (회귀 가드)."""
        stats = _stats(impl, [1000, 1010, 1005, 1030, 1020, 1050])

        assert stats['Annual_Volatility'] > 0
        assert stats['Sharpe_Ratio'] != 0
        assert not pd.isna(stats['Sharpe_Ratio'])
