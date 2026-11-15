"""기술적 전략(SMA, EMA, MACD, RSI, Bollinger)의 지표와 바 단위 체결 엔진 (Go internal/strategy).

backtesting.py를 대체한다. 체결 규칙:
  - 신호는 봉의 종가로 만들고 다음 봉 시가에 체결한다(F01). 마지막 봉 신호는 체결하지 않는다.
  - 매수 수량 = 평가액 × 0.95 / (종가 × (1 + 수수료율)), 소수 단위(S01). 현금이 모자라면 취소.
  - 수수료는 매수·매도 각각 체결 금액 × 수수료율(F02).
  - 볼린저는 첫 완성 창의 봉부터, 교차 전략은 그다음 봉부터 신호를 본다(T03).
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.cancellation import check_cancelled
from .errors import validation

NAMES = ["buy_hold_strategy", "sma_strategy", "ema_strategy", "rsi_strategy", "bollinger_strategy", "macd_strategy"]
BUY_HOLD = "buy_hold_strategy"

# 공개 파라미터 이름·기본값·범위 (key, default, min, max)
SPECS = {
    "sma_strategy": [("short_window", 10, 2, 50), ("long_window", 20, 10, 200)],
    "ema_strategy": [("fast_window", 12, 5, 50), ("slow_window", 26, 10, 200)],
    "macd_strategy": [("fast_period", 12, 5, 50), ("slow_period", 26, 10, 100), ("signal_period", 9, 2, 20)],
    "rsi_strategy": [("rsi_period", 14, 2, 50), ("rsi_oversold", 30, 10, 40), ("rsi_overbought", 70, 60, 90)],
    "bollinger_strategy": [("period", 20, 5, 100), ("std_dev", 2, 0.5, 4)],
    BUY_HOLD: [],
}

ORDERED_PAIRS = [
    ("short_window", "long_window"),
    ("fast_window", "slow_window"),
    ("fast_period", "slow_period"),
    ("rsi_oversold", "rsi_overbought"),
]


def known(name: object) -> bool:
    return isinstance(name, str) and name in SPECS


def _fmt(v: float) -> str:
    """Go strconv.FormatFloat(v, 'f', -1, 64)."""
    v = float(v)
    if v == int(v) and abs(v) < 1e21:
        return str(int(v))
    return repr(v)


def _number(raw: Any) -> float:
    """JSON 숫자 또는 숫자 문자열(Go strategy.number). 불리언·그 밖은 오류."""
    if isinstance(raw, bool):
        raise ValueError("not a number")
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        s = raw.strip()
        if "_" in s:  # Go strconv.ParseFloat은 10진수에서 밑줄을 받지 않는다
            raise ValueError("not a number")
        return float(s)
    raise ValueError("not a number")


def parameters(name: str, given: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """사용자 입력을 검증한 파라미터. 정의되지 않은 키는 무시하고 std_dev를 뺀 값은 정수로 자른다."""
    specs = SPECS.get(name)
    if specs is None:
        raise validation("지원하지 않는 전략입니다.")
    given = given or {}
    out: Dict[str, float] = {}
    for key, default, lo, hi in specs:
        v = float(default)
        if key in given and given[key] is not None:
            try:
                v = _number(given[key])
            except (ValueError, TypeError, OverflowError):
                raise validation(f"{key}: 숫자를 입력해 주세요.")
        if key != "std_dev" and math.isfinite(v):
            v = float(math.trunc(v))
        if math.isnan(v) or math.isinf(v) or v < lo or v > hi:
            raise validation(f"{key}: 허용 범위는 {_fmt(lo)}~{_fmt(hi)}입니다.")
        out[key] = v
    for a, b in ORDERED_PAIRS:
        if a in out and b in out and out[a] >= out[b]:
            raise validation(f"{a}은 {b}보다 작아야 합니다.")
    return out


# ---------------------------------------------------------------------------
# 지표
# ---------------------------------------------------------------------------

def _mean(v: List[float]) -> float:
    if not v:
        return 0.0
    s = 0.0
    for x in v:
        s += x
    return s / len(v)


def _stddev(v: List[float]) -> float:
    if len(v) < 2:
        return 0.0
    m = _mean(v)
    s = 0.0
    for x in v:
        s += (x - m) * (x - m)
    return math.sqrt(s / (len(v) - 1))


def ema(values: List[float], alpha: float, adjust: bool) -> List[float]:
    """adjust=False는 pandas ewm(adjust=False)의 재귀식, True는 pandas 기본(가중치 정규화)."""
    out = [0.0] * len(values)
    if not values:
        return out
    num, den = values[0], 1.0
    for i, x in enumerate(values):
        if i > 0:
            if adjust:
                num = x + (1 - alpha) * num
                den = 1 + (1 - alpha) * den
            else:
                num = alpha * x + (1 - alpha) * num
        out[i] = num / den
    return out


def rolling(values: List[float], n: int, std: bool) -> List[float]:
    out = [0.0] * len(values)
    for i in range(len(values)):
        if i + 1 < n:
            out[i] = math.nan
            continue
        w = values[i + 1 - n:i + 1]
        out[i] = _stddev(w) if std else _mean(w)
    return out


def rsi(close: List[float], n: int) -> List[float]:
    """첫 n개 변화의 산술 평균으로 시작한 Wilder 평활(F08). 완전 평탄 구간은 50."""
    out = [math.nan] * len(close)
    if len(close) <= n:
        return out
    delta = [0.0] * len(close)
    for i in range(1, len(close)):
        delta[i] = close[i] - close[i - 1]
    gain = loss = 0.0
    for d in delta[1:n + 1]:
        gain += max(d, 0.0)
        loss += max(-d, 0.0)
    gain /= n
    loss /= n
    for i in range(n, len(close)):
        if i > n:
            gain = (gain * (n - 1) + max(delta[i], 0.0)) / n
            loss = (loss * (n - 1) + max(-delta[i], 0.0)) / n
        if gain + loss == 0:
            out[i] = 50.0
        else:
            out[i] = 100 * gain / (gain + loss)
    return out


# ---------------------------------------------------------------------------
# 체결 엔진
# ---------------------------------------------------------------------------

@dataclass
class ClosedTrade:
    entry_bar: int
    exit_bar: int
    entry_date: int
    exit_date: int
    entry_price: float
    exit_price: float
    size: float
    entry_fee: float
    exit_fee: float
    pnl: float
    ret: float


@dataclass
class OpenPosition:
    entry_bar: int
    entry_date: int
    entry_price: float
    size: float
    fee: float


@dataclass
class Output:
    equity: List[float] = field(default_factory=list)
    trades: List[ClosedTrade] = field(default_factory=list)
    open: Optional[OpenPosition] = None
    cash: float = 0.0
    indicators: List[tuple] = field(default_factory=list)  # (이름, 값 목록)
    first_close: float = 0.0


def _finite(v: float) -> bool:
    return math.isfinite(v)


def run(name: str, given: Optional[Dict[str, Any]], bars: list, valuations: List[tuple],
        initial: float, commission: float) -> Output:
    """bars는 USD로 환산한 거래일 봉, valuations는 모든 달력일의 (날짜, 평가 가격)이다."""
    if len(bars) < 2 or len(valuations) < 2:
        raise validation("전략 실행에 필요한 시세가 부족합니다.")
    p = parameters(name, given)
    close = [b.close for b in bars]
    a: List[float] = []
    b_: List[float] = []
    warmup = 0
    f = _fmt
    if name == "sma_strategy":
        a = rolling(close, int(p["short_window"]), False)
        b_ = rolling(close, int(p["long_window"]), False)
        warmup = int(p["long_window"]) - 1
        indicators = [("_sma_help…(C," + f(p["short_window"]) + ")", a),
                      ("_sma_help…(C," + f(p["long_window"]) + ")", b_)]
    elif name == "ema_strategy":
        a = ema(close, 2 / (p["fast_window"] + 1), False)
        b_ = ema(close, 2 / (p["slow_window"] + 1), False)
        indicators = [("_ema(C," + f(p["fast_window"]) + ")", a), ("_ema(C," + f(p["slow_window"]) + ")", b_)]
    elif name == "macd_strategy":
        fast = ema(close, 2 / (p["fast_period"] + 1), True)
        slow = ema(close, 2 / (p["slow_period"] + 1), True)
        a = [fast[i] - slow[i] for i in range(len(close))]
        b_ = ema(a, 2 / (p["signal_period"] + 1), True)
        indicators = [
            ("_macd_line(C," + f(p["fast_period"]) + "," + f(p["slow_period"]) + ")", a),
            ("_signal_l…(C," + f(p["fast_period"]) + "," + f(p["slow_period"]) + "," + f(p["signal_period"]) + ")", b_),
        ]
    elif name == "rsi_strategy":
        a = rsi(close, int(p["rsi_period"]))
        indicators = [("_rsi(C," + f(p["rsi_period"]) + ")", a)]
    elif name == "bollinger_strategy":
        n = int(p["period"])
        a = rolling(close, n, False)
        b_ = rolling(close, n, True)
        warmup = n - 1
        lower = [a[i] - p["std_dev"] * b_[i] for i in range(len(close))]
        indicators = [("SMA(C," + f(p["period"]) + ")", a), ("_std(C," + f(p["period"]) + ")", b_), ("λ", lower)]
    else:
        raise validation("지원하지 않는 전략입니다.")

    n = len(bars)
    cash_at = [initial] * n
    size_at = [0.0] * n
    cash = initial
    pos: Optional[OpenPosition] = None
    order = 0.0
    out = Output(indicators=indicators, first_close=close[min(warmup, n - 1)])
    first = warmup if name == "bollinger_strategy" else warmup + 1
    rsi_period = int(p.get("rsi_period", 0))
    for i in range(first, n):
        if i % 64 == 0:
            check_cancelled()
        if order < 0 and pos is not None:
            exit_price = bars[i].open
            exit_fee = pos.size * exit_price * commission
            cash += pos.size * exit_price - exit_fee
            profit = pos.size * (exit_price - pos.entry_price) - pos.fee - exit_fee
            out.trades.append(ClosedTrade(
                entry_bar=pos.entry_bar, exit_bar=i, entry_date=pos.entry_date, exit_date=bars[i].date,
                entry_price=pos.entry_price, exit_price=exit_price, size=pos.size, entry_fee=pos.fee,
                exit_fee=exit_fee, pnl=profit, ret=profit / (pos.size * pos.entry_price + pos.fee),
            ))
            pos = None
        elif order > 0 and pos is None:
            price = bars[i].open
            fee = order * price * commission
            if order * price + fee <= cash:
                cash -= order * price + fee
                pos = OpenPosition(entry_bar=i, entry_date=bars[i].date, entry_price=price, size=order, fee=fee)
        order = 0.0
        equity = cash
        if pos is not None:
            equity += pos.size * bars[i].close
            size_at[i] = pos.size
        cash_at[i] = cash
        if not _finite(equity) or not _finite(cash) or not _finite(size_at[i]):
            raise validation("계산 결과가 표현 가능한 범위를 벗어났습니다.")
        if name in ("sma_strategy", "ema_strategy", "macd_strategy"):
            buy = a[i - 1] < b_[i - 1] and a[i] > b_[i]
            sell = b_[i - 1] < a[i - 1] and b_[i] > a[i]
        elif name == "rsi_strategy":
            buy = i >= rsi_period and a[i] < p["rsi_oversold"]
            sell = i >= rsi_period and (a[i] > p["rsi_overbought"] or (a[i] >= 50 and a[i - 1] < 50))
        else:
            buy = close[i] < a[i] - p["std_dev"] * b_[i]
            sell = close[i] > a[i] + p["std_dev"] * b_[i] or close[i] >= a[i]
        if pos is not None and sell:
            order = -1.0
        elif pos is None and buy:
            order = equity * 0.95 / (close[i] * (1 + commission))

    bar_dates = [b.date for b in bars]
    out.equity = [0.0] * len(valuations)
    for k, (day, price) in enumerate(valuations):
        j = bisect.bisect_right(bar_dates, day)
        value = initial
        if j > 0:
            value = cash_at[j - 1] + size_at[j - 1] * price
        if not _finite(value):
            raise validation("계산 결과가 표현 가능한 범위를 벗어났습니다.")
        out.equity[k] = value
    out.cash = cash
    out.open = pos
    return out


