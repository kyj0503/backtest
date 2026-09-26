"""포트폴리오 성과 지표 계산의 수치 안정성 헬퍼

`portfolio_calculator_service.PortfolioCalculator`와
`portfolio.portfolio_metrics.PortfolioMetrics`가 같은 통계 계산을 중복
구현하고 있어(중복 자체는 별도 정리 대상), 최소한 수치 가드는 한곳에서
공유한다.
"""
import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

# 이보다 작은 연환산 변동성은 0으로 취급한다.
#
# 일간 수익률이 수학적으로 모두 같아도(예: 현금 100% 포트폴리오, 고정 성장률)
# 부동소수점 누적 오차 때문에 `Series.std()`가 정확한 0이 아니라 ~1e-17을
# 반환한다. 이 값으로 나누면 Sharpe가 1e14 규모로 폭발한다 — 실측 4.57e14.
# 연환산 변동성은 백분율 단위이므로 1e-9%(= 사실상 무변동)를 경계로 둔다.
VOLATILITY_EPSILON = 1e-9

# 이보다 얕은 낙폭(%)은 부동소수점 누적 오차로 보고 0으로 취급한다.
DRAWDOWN_EPSILON = 1e-9


def annualized_volatility(daily_returns: pd.Series) -> float:
    """일간 수익률(%)에서 연환산 변동성(%)을 계산한다.

    데이터가 한 점뿐이면 `std()`가 NaN이므로 0.0을 반환한다 — NaN이 그대로
    응답에 실려 나가면 클라이언트에서 JSON 직렬화·표시가 깨진다.
    """
    if daily_returns is None or len(daily_returns) == 0:
        return 0.0

    std = daily_returns.std()
    if std is None or np.isnan(std):
        return 0.0

    volatility = float(std * np.sqrt(TRADING_DAYS_PER_YEAR) * 100)
    return 0.0 if volatility <= VOLATILITY_EPSILON else volatility


def drawdown_from_returns(daily_returns: pd.Series) -> pd.Series:
    """일간 수익률(소수)로 만든 시간가중 지수에서 낙폭(%) 시계열을 계산한다.

    `Portfolio_Value`(평가금)로 낙폭을 재면 DCA 납입금이 평가금을 밀어 올려
    하락을 가린다 — 2년간 -40% 꾸준히 하락한 종목에 월 적립하면 평가금은
    거의 매달 신고점이라 MDD가 -2.85%로 보고됐다(실제 손익 -24%).
    `Daily_Return`은 이미 당일 납입금을 뺀 값이므로 그 누적곱이 납입과 무관한
    "1원당 가치" 지수가 된다. 납입이 없으면 이 지수는 평가금과 비례하므로
    일시금·전략 경로의 결과는 달라지지 않는다.
    """
    if daily_returns is None or len(daily_returns) == 0:
        return pd.Series(dtype=float)

    index = (1.0 + daily_returns.fillna(0.0)).cumprod()
    running_max = index.cummax()
    drawdown = (index - running_max) / running_max * 100
    # 누적곱은 완전히 회복한 날에도 1.0이 아니라 0.9999…가 되어 -1e-14% 같은
    # 가짜 낙폭일을 만든다. 그대로 두면 Avg_Drawdown의 분모(낙폭일 수)가 부풀어
    # 평균이 반토막 난다(-10% → -5%). VOLATILITY_EPSILON과 같은 경계로 0 처리한다.
    return drawdown.where(drawdown < -DRAWDOWN_EPSILON, 0.0)


def safe_sharpe_ratio(annual_return: float, annual_volatility: float) -> float:
    """변동성이 사실상 0이면 Sharpe를 0으로 둔다 (0 나눗셈·폭발 방지)."""
    if annual_volatility is None or np.isnan(annual_volatility):
        return 0.0
    if annual_volatility <= VOLATILITY_EPSILON:
        return 0.0
    return float(annual_return / annual_volatility)
