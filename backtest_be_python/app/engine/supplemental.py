"""POST /api/v1/backtest의 include_* 부가 데이터 (Go internal/api/reference.go supplemental).

계산 결과와 독립이며, 각 섹션은 시간 예산 안에서 따로 성공·실패한다. 외부 장애가 계산 결과를 막거나
실패시키지 않는다(A-08). 끈 섹션은 "skipped", 시간 초과는 "timeout", 그 밖의 실패는 "error"다.
"""
from __future__ import annotations

import concurrent.futures
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..core.cancellation import submit_with_context
from ..core.config import settings
from . import civil
from .marketdata import Bar, History, Histories
from .request import Request
from .source import source

logger = logging.getLogger(__name__)

SECTION_FIELDS = {
    "prices": ["ticker_info", "stock_data", "volatility_events"],
    "exchange-rates": ["exchange_rates", "exchange_stats"],
    "benchmarks": ["sp500_benchmark", "nasdaq_benchmark"],
    "news": ["latest_news"],
}
SECTION_STATUSES = {
    "prices": ["ticker_info", "stock_data", "volatility_events"],
    "exchange-rates": ["exchange_rates"],
    "benchmarks": ["benchmarks"],
    "news": ["news"],
}
STATUS_ORDER = ["ticker_info", "stock_data", "volatility_events", "exchange_rates", "benchmarks", "news"]


def _empty_value(key: str) -> Any:
    if key in ("exchange_rates", "sp500_benchmark", "nasdaq_benchmark"):
        return []
    return {}


def _empty_section(section: str, outcome: str) -> Tuple[Dict[str, Any], Dict[str, str], Optional[float]]:
    fields = {k: _empty_value(k) for k in SECTION_FIELDS[section]}
    status = {k: outcome for k in SECTION_STATUSES[section]}
    return fields, status, None


def _ok(non_empty: bool) -> str:
    return "ok" if non_empty else "empty"


def ticker_info(h: History) -> Dict[str, Any]:
    return {
        "symbol": h.symbol,
        "currency": h.currency,
        "company_name": h.company_name or h.symbol,
        "exchange": h.exchange,
        "first_trade_date": civil.fmt(h.first_trade_date) if h.first_trade_date is not None else None,
    }


def unknown_info(symbol: str) -> Dict[str, Any]:
    """시세를 찾지 못한 종목의 정보(stocks 테이블 미등록 종목과 같은 모양)."""
    return {"symbol": symbol, "currency": None, "company_name": symbol, "exchange": "Unknown",
            "first_trade_date": None}


def volatility(bars: List[Bar], threshold: float) -> List[Dict[str, Any]]:
    """일간 변동률 절댓값이 threshold% 이상인 날. 최근 10건, 최신순."""
    out: List[Dict[str, Any]] = []
    i = len(bars) - 1
    while i >= 1 and len(out) < 10:
        r = (bars[i].close / bars[i - 1].close - 1) * 100
        if abs(r) >= threshold:
            out.append({"date": civil.fmt(bars[i].date), "daily_return": r, "close_price": bars[i].close,
                        "volume": bars[i].volume, "event_type": "급등" if r > 0 else "급락"})
        i -= 1
    return out


def benchmark(h: History, start: int, end: int) -> List[Dict[str, Any]]:
    """요청 기간의 모든 달력일 지수 값(직전 종가 유지)과 전일 대비 수익률."""
    out: List[Dict[str, Any]] = []
    if not h.bars:
        return out
    idx, prev = 0, h.bars[0].close
    for d in range(start, end + 1):
        while idx + 1 < len(h.bars) and h.bars[idx + 1].date <= d:
            idx += 1
        c = h.bars[idx].close
        out.append({"date": civil.fmt(d), "close": c, "return_pct": (c / prev - 1) * 100})
        prev = c
    return out


def _collect(section: str, symbols: List[str], start: int, end: int, limit: int):
    fields: Dict[str, Any] = {}
    status: Dict[str, str] = {}
    sp500: Optional[float] = None
    if section == "prices":
        infos: Dict[str, Any] = {}
        prices: Dict[str, Any] = {}
        events: Dict[str, Any] = {}
        has_prices = has_events = False
        for sym in symbols:
            try:
                h = source.history(sym, start, end)
                info = ticker_info(h)
            except Exception as e:
                # 종목별 실패는 빈 목록과 기본 종목 정보로 남기고 다른 종목은 계속 돌려준다.
                logger.warning("price history failed: %s - %s", sym, e)
                h = History(symbol=sym)
                info = unknown_info(sym)
            infos[h.symbol] = info
            pts = [{"date": civil.fmt(b.date), "price": b.close, "volume": b.volume} for b in h.bars]
            prices[h.symbol] = pts
            has_prices = has_prices or len(pts) > 0
            ev = volatility(h.bars, settings.volatility_threshold_pct)
            events[h.symbol] = ev
            has_events = has_events or len(ev) > 0
        fields.update(ticker_info=infos, stock_data=prices, volatility_events=events)
        status.update(ticker_info=_ok(len(infos) > 0), stock_data=_ok(has_prices),
                      volatility_events=_ok(has_events))
    elif section == "exchange-rates":
        h = source.history(settings.exchange_rate_ticker, start, end)
        pts = [{"date": civil.fmt(b.date), "rate": b.close} for b in h.bars]
        stats: Dict[str, Any] = {}
        if pts:
            hi = lo = pts[0]
            for p in pts:
                if p["rate"] > hi["rate"]:
                    hi = p
                if p["rate"] < lo["rate"]:
                    lo = p
            stats = {"start_point": pts[0], "end_point": pts[-1], "high_point": hi, "low_point": lo}
        fields.update(exchange_rates=pts, exchange_stats=stats)
        status["exchange_rates"] = _ok(len(pts) > 0)
    elif section == "benchmarks":
        sp = source.history("^GSPC", start, end)
        nq = source.history("^IXIC", start, end)
        fields.update(sp500_benchmark=benchmark(sp, start, end), nasdaq_benchmark=benchmark(nq, start, end))
        if len(sp.bars) >= 2:
            sp500 = (sp.bars[-1].close / sp.bars[0].close - 1) * 100
        status["benchmarks"] = _ok(len(sp.bars) > 0 or len(nq.bars) > 0)
    elif section == "news":
        from ..services.unified_data_service import unified_data_service
        latest = unified_data_service.collect_latest_news(symbols, display=limit)
        ordered = {sym: latest.get(sym, []) for sym in symbols}
        fields["latest_news"] = ordered
        status["news"] = _ok(any(len(v) > 0 for v in ordered.values()))
    return fields, status, sp500


def attach(req: Request, data: Dict[str, Any], loaded: Histories) -> None:
    """include_*에 따라 섹션을 병렬로 모아 data 뒤에 붙인다(Go와 같은 키 순서)."""
    symbols = sorted({a.symbol for a in req.portfolio if not a.cash})
    enabled = {
        "prices": len(symbols) > 0 and (req.include_stock_data or req.include_volatility_events),
        "exchange-rates": req.include_exchange_rates,
        "benchmarks": req.include_benchmarks,
        "news": req.include_news and len(symbols) > 0,
    }
    fields: Dict[str, Any] = {}
    status: Dict[str, str] = {}
    for section in ("prices", "exchange-rates", "benchmarks", "news"):
        f, s, _ = _empty_section(section, "skipped")
        fields.update(f)
        status.update(s)
    # 계산에 쓴 시세로 종목 정보를 채운다(prices 섹션을 끈 경우에도 정확한 통화·이름을 준다).
    fields["ticker_info"] = {sym: ticker_info(loaded[sym]) for sym in symbols if sym in loaded}

    sp500: Optional[float] = None
    budget = settings.supplemental_data_timeout_seconds
    sections = [s for s in ("prices", "exchange-rates", "benchmarks", "news") if enabled[s]]
    if sections:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(sections))
        try:
            futures = {s: submit_with_context(executor, _collect, s, symbols, req.start, req.end, 15)
                       for s in sections}
            _, not_done = concurrent.futures.wait(futures.values(), timeout=budget)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        for section in sections:
            fut = futures[section]
            if fut in not_done:
                logger.warning("reference section timed out: %s", section)
                result = _empty_section(section, "timeout")
            else:
                try:
                    result = fut.result()
                except Exception as e:
                    logger.warning("reference section failed: %s - %s: %s", section, type(e).__name__, e)
                    result = _empty_section(section, "error")
            f, s, sp = result
            fields.update(f)
            status.update(s)
            if section == "benchmarks":
                sp500 = sp
    if not req.include_stock_data:
        fields["stock_data"], status["stock_data"] = {}, "skipped"
    if not req.include_volatility_events:
        fields["volatility_events"], status["volatility_events"] = {}, "skipped"
    if sp500 is not None:
        stats = data["portfolio_statistics"]
        stats["sp500_total_return_pct"] = sp500
        stats["alpha_vs_sp500_pct"] = stats["Time_Weighted_Return"] - sp500
    fields["supplemental_status"] = {k: status[k] for k in STATUS_ORDER}
    from ..monitoring.custom_metrics import record_supplemental_outcome
    for k in STATUS_ORDER:
        record_supplemental_outcome(k, status[k])
    for k in ("ticker_info", "stock_data", "exchange_rates", "exchange_stats", "volatility_events",
              "sp500_benchmark", "nasdaq_benchmark", "latest_news", "supplemental_status"):
        data[k] = fields[k]
