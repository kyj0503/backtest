"""통계 (Go internal/engine/stats.go).

위험 지표는 모든 달력일 평가값으로 계산한다(F09). 휴장일은 직전 가격을 유지한다.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from . import civil

DAYS_PER_YEAR = 365.0

# 값이 없음(키 생략)을 나타내는 표식. None은 JSON null이다.
ABSENT = object()


def clean_return(r: float) -> float:
    """부동소수점 잡음(|r| ≤ 1e-11)을 0으로 만든다(F10)."""
    if abs(r) <= 1e-11:
        return 0.0
    return r


def mean(v: List[float]) -> float:
    if not v:
        return 0.0
    s = 0.0
    for x in v:
        s += x
    return s / len(v)


def stddev(v: List[float]) -> float:
    """표본 표준편차(n-1)."""
    if len(v) < 2:
        return 0.0
    m = mean(v)
    s = 0.0
    for x in v:
        s += (x - m) * (x - m)
    return math.sqrt(s / (len(v) - 1))


def sharpe(v: List[float]) -> float:
    """무위험 수익률 0의 연환산 샤프 비율. 변동성이 사실상 0이면 0."""
    sd = stddev(v)
    if sd * math.sqrt(DAYS_PER_YEAR) * 100 <= 1e-9:
        return 0.0
    return mean(v) / sd * math.sqrt(DAYS_PER_YEAR)


def daily_returns(equity: List[float]) -> List[float]:
    out = [0.0] * len(equity)
    for i in range(1, len(equity)):
        if equity[i - 1] > 0:
            out[i] = clean_return(equity[i] / equity[i - 1] - 1)
    return out


def profit_factor(pnl: List[float]) -> Optional[float]:
    """청산 거래의 수수료 차감 USD 이익 합 / 손실 합의 절댓값. 손실이 없으면 None."""
    gains = losses = 0.0
    for p in pnl:
        if p > 0:
            gains += p
        elif p < 0:
            losses -= p
    if losses <= 0:
        return None
    r = gains / losses
    if math.isinf(r) or math.isnan(r):
        return None
    return r


def go_pow(x: float, y: float) -> float:
    try:
        return math.pow(x, y)
    except OverflowError:
        return math.inf
    except ValueError:
        return math.nan


def statistics(start: int, end: int, equity: List[float], returns: List[float], contributed: float,
               start_ratio: float, trades: int) -> Dict[str, Any]:
    """일별 평가액과 납입 흐름을 제거한 일간 수익률로 portfolio_statistics를 만든다.

    키 순서는 Go Statistics 직렬화 순서다. Trade_Win_Rate·sp500_total_return_pct·alpha_vs_sp500_pct는
    호출자가 필요할 때 채운다(ABSENT면 생략).
    """
    r = [clean_return(x) for x in returns]
    duration = end - start
    growth = start_ratio
    for x in r:
        growth *= 1 + x
    index, peak = start_ratio, 1.0
    drawdowns: List[float] = []
    max_dd = 0.0
    gain = loss = max_gain = max_loss = pos = neg = 0
    for x in r:
        index *= 1 + x
        peak = max(peak, index)
        d = 0.0
        if peak > 0:
            d = (index / peak - 1) * 100
        if d < -1e-9:
            drawdowns.append(d)
            max_dd = min(max_dd, d)
        if x > 0:
            gain += 1
            pos += 1
        else:
            gain = 0
        if x < 0:
            loss += 1
            neg += 1
        else:
            loss = 0
        max_gain, max_loss = max(max_gain, gain), max(max_loss, loss)
    vol = stddev(r) * math.sqrt(DAYS_PER_YEAR) * 100
    if vol <= 1e-9:
        vol = 0.0
    annual = 0.0
    if duration > 0:
        annual = (go_pow(max(growth, 0.0), 365.25 / duration) - 1) * 100
    peak_value = 0.0
    for v in equity:
        peak_value = max(peak_value, v)
    final = equity[-1]
    win_rate = pos / len(r) * 100 if r else 0.0
    return {
        "Start": civil.fmt(start),
        "End": civil.fmt(end),
        "Duration": f"{duration} days",
        "Initial_Value": contributed,
        "Final_Value": final,
        "Peak_Value": peak_value,
        "Total_Return": (final / contributed - 1) * 100,
        "Annual_Return": annual,
        "Time_Weighted_Return": clean_return(growth - 1) * 100,
        "Annual_Volatility": vol,
        "Return_Observation_Days_Per_Year": int(DAYS_PER_YEAR),
        "Annualization_Basis": "calendar_daily",
        "Sharpe_Ratio": sharpe(r),
        "Max_Drawdown": max_dd,
        "Avg_Drawdown": mean(drawdowns),
        "Max_Consecutive_Gains": max_gain,
        "Max_Consecutive_Losses": max_loss,
        "Total_Trading_Days": end - start + 1,
        "Total_Trades": trades,
        "Positive_Days": pos,
        "Negative_Days": neg,
        "Win_Rate": win_rate,
        "Trade_Win_Rate": ABSENT,
        "Profit_Factor": None,
        "sp500_total_return_pct": ABSENT,
        "alpha_vs_sp500_pct": ABSENT,
    }


def finalize(stats: Dict[str, Any]) -> Dict[str, Any]:
    """ABSENT 키를 뺀 사본."""
    return {k: v for k, v in stats.items() if v is not ABSENT}
