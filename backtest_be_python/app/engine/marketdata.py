"""일봉·시세 묶음·환율 (Go internal/marketdata types.go, fx.go, fixtures.go).

모든 가격은 원래 통화 그대로 둔다. USD 변환은 계산 시점에 rate_on으로 한다.
"""
from __future__ import annotations

import bisect
import json
import math
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional

from . import civil
from .errors import not_found, validation

EPS8 = 2.220446049250313e-16 * 8

# 환율을 시작일보다 이만큼 앞에서부터 가져온다(시작일이 환율 휴장일이어도 직전 값이 있도록).
FX_LOOKBACK_DAYS = 60


@dataclass
class Bar:
    date: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


def _positive(v: float) -> bool:
    return isinstance(v, float) and math.isfinite(v) and v > 0


def valid_rate(b: Bar) -> bool:
    """환율 하루치는 일별 기준값(종가)만 본다."""
    return _positive(b.close)


def valid_prices(b: Bar) -> bool:
    """OHLC가 모두 양의 유한수이고 서로 모순되지 않는다(경계에서 몇 ulp 허용)."""
    if not (_positive(b.open) and _positive(b.high) and _positive(b.low) and _positive(b.close)):
        return False
    tol = max(b.high, b.close, b.open) * EPS8
    return (b.high >= b.low
            and min(b.open, b.close) >= b.low - tol
            and max(b.open, b.close) <= b.high + tol)


def is_fx(symbol: str) -> bool:
    return symbol.endswith("=X")


def valid_for(symbol: str, b: Bar) -> bool:
    return valid_rate(b) if is_fx(symbol) else valid_prices(b)


@dataclass
class History:
    """한 종목의 시세와 메타데이터. bars는 날짜 오름차순이고 날짜가 겹치지 않는다."""
    symbol: str
    currency: str = "USD"
    company_name: str = ""
    exchange: str = ""
    first_trade_date: Optional[int] = None
    bars: List[Bar] = field(default_factory=list)
    _dates: Optional[List[int]] = field(default=None, repr=False, compare=False)

    @property
    def dates(self) -> List[int]:
        if self._dates is None or len(self._dates) != len(self.bars):
            self._dates = [b.date for b in self.bars]
        return self._dates

    def between(self, start: int, end: int) -> "History":
        return replace(self, bars=[b for b in self.bars if start <= b.date <= end], _dates=None)


Histories = Dict[str, History]


# Python app/constants/currencies.py와 같은 통화. multiply가 참이면 "1 통화 = X USD"(EURUSD=X 등).
SUPPORTED_FX = {
    "KRW": ("KRW=X", False),
    "JPY": ("JPY=X", False),
    "EUR": ("EURUSD=X", True),
    "GBP": ("GBPUSD=X", True),
    "CNY": ("CNY=X", False),
    "HKD": ("HKD=X", False),
    "TWD": ("TWD=X", False),
    "SGD": ("SGD=X", False),
    "AUD": ("AUDUSD=X", True),
    "CAD": ("CADUSD=X", True),
    "CHF": ("CHFUSD=X", True),
    "INR": ("INR=X", False),
}


def fx_ticker(currency: str):
    """(티커, 지원 여부). USD는 ("", True)."""
    if currency == "USD":
        return "", True
    p = SUPPORTED_FX.get(currency)
    if p is None:
        return "", False
    return p[0], True


def rate_on(currency: str, day: int, data: Histories) -> float:
    """day의 "1 통화 = ? USD". 당일 또는 그 이전 가장 최근 환율만 쓴다(뒤 채우기 금지)."""
    if currency == "USD":
        return 1.0
    p = SUPPORTED_FX.get(currency)
    if p is None:
        raise validation(f"지원하지 않거나 확인할 수 없는 통화: {currency}")
    rates = data.get(p[0])
    if rates is None:
        raise validation(f"{currency}: 환율이 없습니다.")
    i = bisect.bisect_right(rates.dates, day)
    if i == 0 or not valid_rate(rates.bars[i - 1]):
        raise validation(f"{currency}: {civil.fmt(day)} 이전의 유효한 환율이 없습니다.")
    r = rates.bars[i - 1].close
    if p[1]:
        return r
    return 1 / r


def not_found_error(symbol: str):
    return not_found(f"가격 데이터가 없습니다: {symbol}")


# ---------------------------------------------------------------------------
# 고정 시세 (BACKTEST_FIXTURE_FILE, DEBUG 전용)
# ---------------------------------------------------------------------------

def _num(v) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"not a number: {v!r}")
    return float(v)


def parse_histories(raw: dict) -> Histories:
    """backtest_be_go/testdata/rust/histories.json 형식을 읽는다."""
    out: Histories = {}
    for symbol, h in raw.items():
        bars = []
        for b in h.get("bars") or []:
            d = civil.parse(b["date"])
            if d is None:
                raise ValueError(f"fixture {symbol}: invalid date {b['date']!r}")
            bars.append(Bar(d, _num(b["open"]), _num(b["high"]), _num(b["low"]), _num(b["close"]),
                            _num(b.get("volume", 0))))
        ftd = h.get("first_trade_date")
        out[symbol] = History(
            symbol=h.get("symbol") or "",
            currency=h.get("currency") or "",
            company_name=h.get("company_name") or "",
            exchange=h.get("exchange") or "",
            first_trade_date=civil.parse(ftd) if ftd else None,
            bars=bars,
        )
    return out


class FixtureFetcher:
    """고정 시세를 외부 조회 대신 돌려준다. 모르는 심볼은 404."""

    def __init__(self, data: Histories):
        self.data = data

    @classmethod
    def load(cls, path: str) -> "FixtureFetcher":
        with open(path, encoding="utf-8") as f:
            data = parse_histories(json.load(f))
        for symbol, h in data.items():
            for b in h.bars:
                if not valid_for(symbol, b):
                    raise ValueError(f"fixture {symbol} has an invalid bar on {civil.fmt(b.date)}")
        return cls(data)

    def fetch(self, symbol: str, start: int, end: int) -> History:
        h = self.data.get(symbol)
        if h is None:
            raise not_found_error(symbol)
        return h.between(start, end)
