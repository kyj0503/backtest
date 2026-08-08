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


def safe_sharpe_ratio(annual_return: float, annual_volatility: float) -> float:
    """변동성이 사실상 0이면 Sharpe를 0으로 둔다 (0 나눗셈·폭발 방지)."""
    if annual_volatility is None or np.isnan(annual_volatility):
        return 0.0
    if annual_volatility <= VOLATILITY_EPSILON:
        return 0.0
    return float(annual_return / annual_volatility)
