"""PortfolioMetrics.calculate_portfolio_statistics / PortfolioCalculator.calculate_portfolio_statistics
직접 단위 테스트 (P1-12).

**배경**: portfolio_metrics.py는 어떤 테스트도 직접 임포트하지 않는 상태였다.
같은 파일 안의 calculate_daily_metrics_and_history는 시뮬레이션 엔진을 통해
간접적으로는 실행되지만(test_dca_schedule_alignment.py 등), 이 파일의
calculate_portfolio_statistics(샤프 비율/최대 낙폭/연환산 등 통계 전체를
계산하는 메서드)는 어떤 경로로도 실행된 적이 없었다.

**두 구현을 함께 검증하는 이유**: portfolio_calculator_service.py의
PortfolioCalculator.calculate_portfolio_statistics는 portfolio_manager_service.py가
실제로 호출하는 "라이브" 구현이고, portfolio_metrics.py의 PortfolioMetrics는
동일한 로직을 그대로 복제한 별도 구현이다(현재 프로덕션 호출 경로에서는
쓰이지 않는 것으로 보인다 -- portfolio_manager_service.py는
`self.metrics = PortfolioMetrics()`를 만들어 두고도 실제로 호출하지 않는다).
두 구현이 문자 그대로 동일한 공식을 사용하므로, 같은 테스트 케이스를
파라미터화해 두 구현 모두에 대해 동일한 손으로 계산한 값을 검증한다 --
이렇게 하면 향후 한쪽만 고쳐지고 다른 쪽이 방치되는 경우(중복 코드의
전형적인 위험)도 함께 잡아낸다.

각 테스트의 기대값은 이 파일의 공식을 그대로 옮긴 것이 아니라, 입력을 손으로
골라 계산기/직접 산술로 미리 구한 값이다 (자세한 계산 과정은 각 테스트의
주석 참고).
"""
import math

import pandas as pd
import pytest

from app.services.portfolio.portfolio_metrics import PortfolioMetrics
from app.services.portfolio_calculator_service import PortfolioCalculator

pytestmark = pytest.mark.unit

IMPLEMENTATIONS = [
    pytest.param(PortfolioMetrics.calculate_portfolio_statistics, id='PortfolioMetrics'),
    pytest.param(PortfolioCalculator.calculate_portfolio_statistics, id='PortfolioCalculator'),
]


def _df(dates, values, returns=None):
    """Portfolio_Value/Daily_Return 컬럼을 가진 DataFrame을 만든다.

    returns를 명시하지 않으면 values의 일간 변화율(pct_change, 첫날은 0)로
    자동 계산한다 -- 대부분의 테스트에서 두 컬럼이 서로 내적으로 일관되게
    만들기 위함이다. 명시적으로 다른 조합을 테스트하고 싶을 때만 returns를
    직접 넘긴다.
    """
    idx = pd.to_datetime(dates)
    if returns is None:
        returns = pd.Series(values, index=idx).pct_change().fillna(0.0).tolist()
    return pd.DataFrame({'Portfolio_Value': values, 'Daily_Return': returns}, index=idx)


@pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
class TestDrawdownShapes:
    """드로우다운은 Portfolio_Value의 '지금까지의 최고점 대비 하락률'이다."""

    def test_monotonically_rising_curve_has_zero_drawdown(self, calc_statistics):
        """단조 증가 곡선은 매일이 곧 신고점이므로 낙폭이 존재할 수 없다."""
        df = _df(
            ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            [1.0, 1.02, 1.05, 1.10, 1.20],
        )
        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Max_Drawdown'] == pytest.approx(0.0)
        assert stats['Avg_Drawdown'] == 0  # 낙폭<0인 날이 하나도 없으면 코드가 0을 기본값으로 반환

    def test_monotonically_falling_curve_drawdown_hand_derived(self, calc_statistics):
        """단조 하락 곡선은 running_max가 첫날(1.0)에 고정되므로,
        drawdown[i] = value[i] - 1 (퍼센트 단위)가 그대로 성립한다.
        손으로 계산: [0, -10, -20, -30]% -> Max=-30, Avg(음수만)=(-10-20-30)/3=-20.
        """
        df = _df(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'], [1.0, 0.9, 0.8, 0.7])
        stats = calc_statistics(df, total_amount=500.0)

        assert stats['Max_Drawdown'] == pytest.approx(-30.0)
        assert stats['Avg_Drawdown'] == pytest.approx(-20.0)


@pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
class TestSharpeRatioAndVolatility:
    def test_zero_volatility_series_gives_zero_annual_volatility_and_zero_sharpe(self, calc_statistics):
        """일간 수익률이 전부 동일(0.5%)하면 표준편차는 정확히 0이다 -- 곡선이
        꾸준히 우상향하고 있어도(진짜 수익이 나고 있어도) 변동성이 0이면
        Sharpe_Ratio는 (분모가 0이 되는 나눗셈 대신) 0으로 안전하게
        디폴트되어야 한다.

        원소 개수는 의도적으로 9개로 제한한다 -- pandas Series.std()는 원소가
        모두 동일해도 배열 길이가 10 이상이면(pairwise summation 전략 전환
        추정) 부동소수점 잔차로 정확히 0.0이 아닌 극미량(~1e-18)을 반환하는
        것을 컨테이너에서 직접 확인했다(길이 2~9는 항상 정확히 0.0). 그
        "거의 0"이지만 정확히 0은 아닌 변동성이 Sharpe_Ratio를 얼마나 비정상적인
        값으로 폭발시키는지는 별도 테스트
        (test_near_zero_but_nonzero_volatility_from_float_noise_makes_sharpe_explode)
        에서 다룬다.
        """
        n = 9
        values = [1.005 ** i for i in range(n)]
        returns = [0.005] * n  # 매일 동일 -> std == 0.0 (길이<10이므로 부동소수점 잔차 없음)
        df = _df([f'2024-01-{i + 1:02d}' for i in range(n)], values, returns=returns)

        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Annual_Volatility'] == 0.0
        assert stats['Sharpe_Ratio'] == 0
        # 대조: 이 곡선은 실제로 계속 상승했으므로 Annual_Return 자체는 0이 아니다
        # (변동성=0이라는 것과 수익률=0이라는 것은 별개임을 확인).
        assert stats['Annual_Return'] > 0

    def test_float_noise_volatility_is_treated_as_zero(self, calc_statistics):
        """위 테스트와 정확히 동일한 시나리오를 10개 원소로
        늘리기만 해도(수익률은 여전히 모두 "동일한" 0.5%다) pandas
        Series.std()가 부동소수점 잔차로 정확히 0이 아닌 9.14e-19 안팎의
        극미값을 반환한다 (컨테이너에서 직접 측정: pd.Series([0.005]*10).std()
        == 9.14279549108516e-19, 반면 길이 9 이하는 전부 정확히 0.0).

        `annual_volatility > 0` 가드는 "엄격하게 0보다 큰가"만 검사하므로 이
        극미값도 통과시켜 버리고, 그 극미값이 분모로 쓰이면서 Sharpe_Ratio가
        3.57e17 규모(!)의 무의미한 값으로 폭발한다 -- 코드가 원래 막으려던
        "말도 안 되는 극단값"을 오히려 만들어내는 셈이다. 변동성이 사실상
        0(스테이블코인형 자산, 머니마켓 펀드 등)에 가까운 진짜 데이터에서도
        동일한 부동소수점 잔차가 발생할 수 있으므로, 이는 순전히 인위적인
        테스트 데이터에서만 나타나는 현상이 아니다.

        수정(P1-16): 연환산 변동성이 VOLATILITY_EPSILON 이하이면 0으로 보고
        Sharpe도 0으로 둔다. 이 테스트는 그 계약을 고정한다."""
        n = 10
        values = [1.005 ** i for i in range(n)]
        returns = [0.005] * n
        df = _df([f'2024-01-{i + 1:02d}' for i in range(n)], values, returns=returns)

        stats = calc_statistics(df, total_amount=1000.0)

        # 부동소수점 잔차 수준의 변동성은 0으로 취급된다.
        assert stats['Annual_Volatility'] == pytest.approx(0.0, abs=1e-9)
        # 따라서 Sharpe가 폭발하지 않는다 (수정 전 실측: 3.57e17).
        assert stats['Sharpe_Ratio'] == pytest.approx(0.0, abs=1e-9)

    def test_flat_zero_return_series_has_zero_sharpe_and_profit_factor_one(self, calc_statistics):
        """가격이 전혀 움직이지 않는(진짜 flat) 경우: 변동성 0, 수익률 0,
        gross_profit/gross_loss 모두 0 -> Profit_Factor는 1.0(이익도 손실도
        없을 때의 디폴트)이어야 한다."""
        df = _df([f'2024-01-{i + 1:02d}' for i in range(5)], [1.0] * 5, returns=[0.0] * 5)

        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Total_Return'] == pytest.approx(0.0)
        assert stats['Annual_Volatility'] == pytest.approx(0.0)
        assert stats['Sharpe_Ratio'] == 0
        assert stats['Profit_Factor'] == 1.0
        assert stats['Positive_Days'] == 0
        assert stats['Negative_Days'] == 0
        assert stats['Win_Rate'] == 0


@pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
class TestSingleDataPoint:
    def test_single_row_duration_zero_reports_zero_without_leaking_nan(self, calc_statistics):
        """단일 데이터 포인트(시작일==종료일인 백테스트)에서:
        - duration == 0 이므로 코드의 명시적 가드에 의해 Annual_Return은 0.
        - pandas Series.std()는 원소가 1개면 정의상 NaN을 반환한다(ddof=1 기본값).
          수정(P1-17) 전에는 그 NaN이 Annual_Volatility 필드로 그대로
          유출됐다. 이제는 0.0으로 정규화되어 응답에 NaN이 실리지 않는다.
        """
        df = _df(['2024-06-15'], [1.0], returns=[0.0])

        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Duration'] == '0 days'
        assert stats['Annual_Return'] == 0
        assert stats['Sharpe_Ratio'] == 0
        assert not math.isnan(stats['Annual_Volatility']), "NaN이 응답에 유출되면 안 된다"
        assert stats['Annual_Volatility'] == pytest.approx(0.0)


@pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
class TestAnnualizationWindow:
    def test_leap_year_full_span_duration_counts_the_extra_day(self, calc_statistics):
        """2024년은 윤년이다. 1/1~12/31 구간의 실제 캘린더 일수는 365일
        (2월이 29일까지 있기 때문에, 평년의 364일보다 하루 많다 -- pandas
        Timestamp 뺄셈으로 사전에 확인한 값). Annual_Return 공식
        ((final_value)**(365.25/duration) - 1)*100 에서 duration=365를
        직접 사용하는지 확인한다 (365.25/364로 잘못 계산되면 결과가 달라진다).
        """
        df = _df(['2024-01-01', '2024-12-31'], [1.0, 1.5])

        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Duration'] == '365 days'
        # ((1.5)**(365.25/365) - 1) * 100, 별도로 계산기로 검증한 값.
        assert stats['Annual_Return'] == pytest.approx(50.04166315911227, rel=1e-9)

    def test_sub_year_window_extrapolates_annual_return(self, calc_statistics):
        """1년 미만 구간(30일, 5% 수익)을 연환산하면 큰 폭으로 확대(extrapolate)
        된다. ((1.05)**(365.25/30) - 1) * 100, 계산기로 검증한 값."""
        df = _df(['2024-01-01', '2024-01-31'], [1.0, 1.05])

        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Duration'] == '30 days'
        assert stats['Annual_Return'] == pytest.approx(81.12554955402196, rel=1e-9)


@pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
class TestWinRateConsecutiveStreaksAndProfitFactor:
    def test_win_rate_and_consecutive_streaks_hand_derived(self, calc_statistics):
        """수익률 부호 수열: +,+,-,+,-,-,+ (7일).
        - 연속 상승 최대: 2 (처음 두 날)
        - 연속 하락 최대: 2 (5,6번째 날)
        - 상승일 4/7, 하락일 3/7 -> 승률 = 4/7*100 = 57.142857...%
        """
        returns = [0.01, 0.02, -0.01, 0.03, -0.02, -0.01, 0.01]
        values = [1.0]
        for r in returns:
            values.append(values[-1] * (1 + r))
        values = values[1:]
        dates = [f'2024-02-{i + 1:02d}' for i in range(7)]
        df = _df(dates, values, returns=returns)

        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Positive_Days'] == 4
        assert stats['Negative_Days'] == 3
        assert stats['Win_Rate'] == pytest.approx(4 / 7 * 100)
        assert stats['Max_Consecutive_Gains'] == 2
        assert stats['Max_Consecutive_Losses'] == 2

    def test_all_gains_profit_factor_defaults_to_two(self, calc_statistics):
        """손실일이 하나도 없으면 gross_loss==0이 되어 일반적인 비율 계산이
        불가능하다. 코드는 이 경우 (이익이 있는 한) Profit_Factor를 2.0으로
        디폴트한다."""
        returns = [0.01, 0.02, 0.03]
        values = [1.0]
        for r in returns:
            values.append(values[-1] * (1 + r))
        values = values[1:]
        df = _df(['2024-01-01', '2024-01-02', '2024-01-03'], values, returns=returns)

        stats = calc_statistics(df, total_amount=1000.0)

        assert stats['Profit_Factor'] == 2.0
        assert stats['Negative_Days'] == 0


@pytest.mark.parametrize('calc_statistics', IMPLEMENTATIONS)
class TestEmptyInput:
    def test_empty_dataframe_raises_indexerror(self, calc_statistics):
        """빈 DataFrame(행 0개)에 대한 방어 코드가 없다 -- index[0] 접근에서
        바로 IndexError가 발생한다. 우아한 처리(빈 통계 딕셔너리 반환 등)가
        아니라 예외로 실패한다는 계약을 문서화해 둔다."""
        df = pd.DataFrame({'Portfolio_Value': [], 'Daily_Return': []})

        with pytest.raises(IndexError):
            calc_statistics(df, total_amount=1000.0)
