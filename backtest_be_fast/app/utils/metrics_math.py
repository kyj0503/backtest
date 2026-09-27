"""포트폴리오 성과 지표 계산의 공통 헬퍼

`portfolio_calculator_service.PortfolioCalculator`와
`portfolio.portfolio_metrics.PortfolioMetrics`가 같은 통계 계산을 중복
구현하고 있어(중복 자체는 별도 정리 대상), 지표의 정의와 수치 가드는
한곳에서 공유한다. 전략 경로도 PortfolioCalculator를 거치므로 같은 필드는
어느 경로에서든 같은 정의를 갖는다(A-09).
"""
from typing import Optional

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

# 시뮬레이션 결과 DataFrame.attrs에 싣는 "첫 평가일 평가금 / 투입 원금" 키
TWR_START_RATIO_ATTR = 'twr_start_ratio'


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


def time_weighted_annual_return(
    daily_returns: pd.Series,
    duration_days: int,
    start_ratio: float = 1.0,
) -> float:
    """일간 수익률(소수)의 누적곱(시간가중 지수)으로 연환산 수익률(%)을 계산한다.

    과거에는 `(최종 평가금 / 총 납입액) ** (365.25 / 기간) - 1`로 계산했다.
    DCA는 마지막 납입금이 거의 투자되지 않았는데도 전 기간 복리를 적용받은
    것처럼 분모에 잡혀, 상승장에서 연환산 수익률이 가격 상승률보다 크게
    눌렸다(A-19). `Daily_Return`은 당일 납입금을 뺀 값이므로 누적곱이 납입 시점과
    무관한 "1원당 가치" 지수가 된다 — 낙폭(`drawdown_from_returns`)과 같은 정의다.

    `start_ratio`는 `Daily_Return`에 잡히지 않는 첫 평가일의 손익(첫 평가금 /
    그날까지 투입한 원금)이다. 시뮬레이션은 전일 평가금이 없는 첫날의 수익률을
    0으로 기록하지만 첫날 매수 수수료만큼 평가금은 줄어 있으므로, 이 비율을 곱해야
    납입이 없는 일시금의 결과가 기존 공식과 같아진다.
    """
    if duration_days is None or duration_days <= 0:
        return 0.0
    if daily_returns is None or len(daily_returns) == 0:
        return 0.0

    growth = float(start_ratio) * float((1.0 + daily_returns.fillna(0.0)).prod())
    if not np.isfinite(growth):
        return 0.0
    # 전액 손실(또는 그 이하)은 -100%다. 음수 밑에 분수 지수를 쓰면 NaN이 된다.
    growth = max(growth, 0.0)
    return float((growth ** (365.25 / duration_days) - 1) * 100)


def twr_start_ratio(frame: pd.DataFrame) -> float:
    """통계 입력 프레임에서 시간가중 지수의 시작 비율을 꺼낸다.

    시뮬레이션 엔진은 첫 평가일의 "평가금 / 투입 원금"을
    `attrs[TWR_START_RATIO_ATTR]`로 넘긴다. DCA는 첫날 평가금이 총 납입액의
    일부라 `Portfolio_Value[0]`(총 납입액 기준 정규화 값)을 쓸 수 없기 때문이다.
    속성이 없는 곡선(전략 경로처럼 중도 납입이 없는 곡선)은 원금 전체가 첫날
    투입된 것이므로 `Portfolio_Value[0]` 자체가 그 비율이다.
    """
    ratio = frame.attrs.get(TWR_START_RATIO_ATTR)
    if ratio is None:
        ratio = frame['Portfolio_Value'].iloc[0]
    return float(ratio)


def daily_profit_factor(daily_returns: pd.Series) -> Optional[float]:
    """일간 수익률의 이익 합 / 손실 합(절댓값). 손실일이 없으면 None.

    손실 합이 0이면 비율이 정의되지 않는다. 과거 구현은 이 경우 2.0/1.0/0.0 같은
    폴백 상수를 경로마다 다르게 넣었는데(A-09), 계산값처럼 보이는 지어낸 숫자다.
    응답에서는 JSON null로 나간다.
    """
    if daily_returns is None or len(daily_returns) == 0:
        return None
    gross_profit = float(daily_returns[daily_returns > 0].sum())
    gross_loss = float(abs(daily_returns[daily_returns < 0].sum()))
    if gross_loss <= 0:
        return None
    return gross_profit / gross_loss


def up_day_ratio(daily_returns: pd.Series) -> float:
    """일 기준 승률(%): 전체 거래일 중 수익률이 양수인 날의 비율."""
    if daily_returns is None or len(daily_returns) == 0:
        return 0.0
    return float((daily_returns > 0).sum() / len(daily_returns) * 100)
