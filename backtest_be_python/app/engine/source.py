"""시세 조회 진입점 (Go internal/marketdata/source.go).

프로세스 메모리(5분) → 고정 시세(BACKTEST_FIXTURE_FILE, DEBUG 전용) 또는 DB 캐시·Yahoo 순서로 본다.
없는 종목은 404(AppError)이고, load()는 그 종목을 missing으로 돌려 호출자가 경고와 함께 계산에서 뺀다.
"""
from __future__ import annotations

import concurrent.futures
import logging
import math
import threading
import time
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from ..core.cancellation import submit_with_context
from ..core.config import settings
from . import civil
from .errors import AppError, is_not_found, unavailable, validation
from .marketdata import (FX_LOOKBACK_DAYS, Bar, FixtureFetcher, History, Histories, fx_ticker,
                         is_fx, not_found_error, valid_for, valid_prices)

logger = logging.getLogger(__name__)

MAX_RANGE_REPAIR = 0.01


@lru_cache(maxsize=1)
def fixture_fetcher() -> Optional[FixtureFetcher]:
    """고정 시세 모드면 FixtureFetcher, 아니면 None. 설정 검증이 DEBUG 전용임을 보장한다."""
    path = settings.backtest_fixture_file
    if not path:
        return None
    f = FixtureFetcher.load(path)
    logger.warning("using fixture market data instead of Yahoo (DEBUG only): %s", path)
    return f


def fixture_mode() -> bool:
    return bool(settings.backtest_fixture_file)


def repair_range(b: Bar) -> Tuple[Bar, bool]:
    """고가·저가가 시가·종가를 1% 이내로 벗어난 봉은 범위만 넓혀 받는다(G01)."""
    lo = min(b.open, b.high, b.low, b.close)
    hi = max(b.open, b.high, b.low, b.close)
    if b.high < b.low:
        return b, False
    if (b.low - lo) / b.low > MAX_RANGE_REPAIR or (hi - b.high) / b.high > MAX_RANGE_REPAIR:
        return b, False
    fixed = Bar(b.date, b.open, hi, lo, b.close, b.volume)
    return fixed, valid_prices(fixed)


def _finite_positive(v) -> bool:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return math.isfinite(f) and f > 0


def _live_fetch(symbol: str, start: int, end: int) -> History:
    """DB 캐시·Yahoo(data_service)에서 받은 DataFrame을 History로 바꾼다."""
    from ..core.exceptions import DataNotFoundError, YfinanceRateLimitError
    from ..repositories.stock_repository import get_stock_repository
    from ..services.data_service import data_service

    try:
        df = data_service.get_ticker_data_sync(symbol, civil.fmt(start), civil.fmt(end))
    except DataNotFoundError:
        raise not_found_error(symbol)
    except YfinanceRateLimitError:
        raise AppError(429, f"{symbol}: 시세 제공업체가 요청을 제한했습니다.")
    if df is None or df.empty:
        raise not_found_error(symbol)
    try:
        info = get_stock_repository().get_ticker_info(symbol) or {}
    except Exception as e:  # 메타데이터 실패는 시세를 막지 않는다
        logger.warning("ticker info lookup failed: %s - %s", symbol, e)
        info = {}
    bars: List[Bar] = []
    for idx, row in df.iterrows():
        o, h, l, c = row.get("Open"), row.get("High"), row.get("Low"), row.get("Close")
        values = [o, h, l, c]
        if all(v is None or (isinstance(v, float) and math.isnan(v)) for v in values):
            continue
        if is_fx(symbol):
            if not _finite_positive(c):
                raise unavailable(f"{symbol}: 불완전하거나 유효하지 않은 OHLC 시세입니다.")
            cf = float(c)
            o = o if _finite_positive(o) else cf
            h = h if _finite_positive(h) else cf
            l = l if _finite_positive(l) else cf
        elif not all(_finite_positive(v) for v in values):
            raise unavailable(f"{symbol}: 불완전하거나 유효하지 않은 OHLC 시세입니다.")
        d = idx.date() if hasattr(idx, "date") else date.fromisoformat(str(idx)[:10])
        vol = row.get("Volume", 0)
        vol = float(vol) if _finite_positive(vol) else 0.0
        bar = Bar(d.toordinal(), float(o), float(h), float(l), float(c), vol)
        if not valid_for(symbol, bar):
            bar, ok = repair_range(bar)
            if not ok:
                raise unavailable(f"{symbol}: 시세의 OHLC 범위가 일치하지 않습니다.")
            logger.warning("provider OHLC range repaired (G01): %s %s", symbol, civil.fmt(bar.date))
        bars.append(bar)
    bars.sort(key=lambda b: b.date)
    dedup: List[Bar] = []
    for b in bars:
        if dedup and dedup[-1].date == b.date:
            continue
        dedup.append(b)
    ftd = info.get("first_trade_date")
    return History(
        symbol=symbol,
        currency=info.get("currency") or "USD",
        company_name=info.get("company_name") or symbol,
        exchange=info.get("exchange") or "",
        first_trade_date=civil.parse(ftd) if ftd else None,
        bars=dedup,
    )


@dataclass
class _Entry:
    symbol: str
    at: float
    h: History


@dataclass
class Loaded:
    histories: Histories = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)


class Source:
    def __init__(self, ttl: float = 300.0, cap: int = 128):
        self.ttl = ttl
        self.cap = cap
        self._lock = threading.Lock()
        self._entries: Dict[str, _Entry] = {}

    def _get(self, key: str) -> Optional[History]:
        with self._lock:
            e = self._entries.get(key)
            if e is None or time.monotonic() - e.at >= self.ttl:
                return None
            return e.h

    def _put(self, symbol: str, key: str, h: History) -> None:
        with self._lock:
            now = time.monotonic()
            for k in [k for k, e in self._entries.items() if e.symbol == symbol or now - e.at >= self.ttl]:
                del self._entries[k]
            if len(self._entries) >= self.cap:
                oldest = min(self._entries, key=lambda k: self._entries[k].at)
                del self._entries[oldest]
            self._entries[key] = _Entry(symbol, now, h)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def history(self, symbol: str, start: int, end: int) -> History:
        """[start, end]의 시세. 데이터가 없으면 404 AppError."""
        key = f"{symbol}|{start}|{end}"
        cached = self._get(key)
        if cached is not None:
            return cached
        h = self._load(symbol, start, end)
        self._put(symbol, key, h)
        return h

    def _load(self, symbol: str, start: int, end: int) -> History:
        fixtures = fixture_fetcher()
        h = fixtures.fetch(symbol, start, end) if fixtures is not None else _live_fetch(symbol, start, end)
        for b in h.bars:
            if not valid_for(symbol, b):
                raise unavailable(f"{symbol}: 시세의 OHLC 값이 유효하지 않습니다.")
        h = h.between(start, end)
        if not h.bars:
            raise not_found_error(symbol)
        return h

    def load(self, symbols: List[str], start: int, end: int) -> Loaded:
        """종목들의 시세(최대 4개 동시)와 필요한 환율. 404가 아닌 오류는 전체 실패다."""
        out = Loaded()
        if symbols:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(symbols))) as ex:
                futures = [(s, submit_with_context(ex, self.history, s, start, end)) for s in symbols]
                errors: List[BaseException] = []
                for s, fut in futures:
                    try:
                        out.histories[s] = fut.result()
                    except AppError as e:
                        if is_not_found(e):
                            out.missing.append(s)
                        else:
                            errors.append(e)
                    except BaseException as e:  # 취소 포함
                        errors.append(e)
                if errors:
                    raise errors[0]
        out.missing.sort()
        currencies = sorted({h.currency for h in out.histories.values() if h.currency != "USD"})
        for currency in currencies:
            ticker, ok = fx_ticker(currency)
            if not ok:
                raise validation(f"지원하지 않거나 확인할 수 없는 통화: {currency}")
            try:
                out.histories[ticker] = self.history(ticker, start - FX_LOOKBACK_DAYS, end)
            except AppError as e:
                if is_not_found(e):
                    raise validation(f"{currency}: 환율 데이터를 가져올 수 없습니다.")
                raise
        return out


source = Source()
