"""기술적 전략 합산 (Go internal/engine/technical.go).

종목별로 전략을 돌리고 평가액을 더한다. 리밸런싱·적립은 없다(검증에서 거부).
신호·체결은 USD 환산 거래일 봉으로, 평가는 모든 달력일의 (직전 현지 종가 × 그날 환율)로 한다(R).
"""
from __future__ import annotations

import bisect
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.cancellation import check_cancelled
from . import civil, strategy
from .errors import validation
from .marketdata import Bar, History, Histories, rate_on
from .request import Request
from .response import ASSUMPTIONS, curves
from .stats import (DAYS_PER_YEAR, daily_returns, go_pow, mean, profit_factor, statistics, stddev)


def _nan_to_none(v: float) -> Optional[float]:
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def _timestamp() -> str:
    """Go time.Now().UTC().Format(time.RFC3339Nano)."""
    now = datetime.now(timezone.utc)
    frac = f"{now.microsecond:06d}".rstrip("0")
    return now.strftime("%Y-%m-%dT%H:%M:%S") + (("." + frac) if frac else "") + "Z"


def drawdown_peaks(equity: List[float]) -> List[float]:
    """고점 회복 구간별 최대 낙폭(비율). 회복 구간이 없으면 0 초과 낙폭 전부."""
    peak = equity[0]
    dd = [0.0] * len(equity)
    recoveries: List[int] = []
    last = len(equity) - 1
    for i, v in enumerate(equity):
        peak = max(peak, v)
        dd[i] = 1 - v / peak
        if dd[i] == 0 or i == last:
            recoveries.append(i)
    peaks: List[float] = []
    for k in range(1, len(recoveries)):
        a, b = recoveries[k - 1], recoveries[k]
        if b > a + 1:
            m = 0.0
            for x in dd[a:b + 1]:
                m = max(m, x)
            peaks.append(m)
    if not peaks:
        peaks = [x for x in dd if x > 0]
    return peaks


def run(req: Request, data: Histories) -> Dict[str, Any]:
    days = req.end - req.start + 1
    dates = [req.start + i for i in range(days)]
    strategy_details: Dict[str, Any] = {}
    individual_returns: Dict[str, Any] = {}
    warnings: List[str] = []
    assets: List[tuple] = []  # (key, asset, amount, equity 또는 None)
    wins = trades = 0
    realized: List[float] = []
    for idx, a in enumerate(req.portfolio):
        check_cancelled()
        amount = a.base()
        if amount <= 0:
            warnings.append(f"종목 {a.symbol} 백테스트 실패: 투자금액은 0보다 커야 합니다.")
            continue
        key = a.id(idx)
        if a.cash:
            strategy_details[key] = {"total_trades": 0, "win_rate_pct": 0.0, "max_drawdown_pct": 0.0,
                                     "sharpe_ratio": 0.0, "final_equity": amount}
            individual_returns[key] = {"asset_id": key, "asset_type": a.asset_type, "symbol": a.symbol,
                                       "weight": 0.0, "amount": amount, "return": 0.0, "initial_value": amount,
                                       "final_value": amount, "trades": 0, "win_rate": None}
            assets.append((key, a, amount, None))
            continue
        h = data.get(a.symbol)
        if h is None:
            warnings.append(f"종목 {a.symbol} 백테스트 실패: 가격 데이터가 없습니다.")
            continue
        began = time.perf_counter()
        st, out = _run_strategy(req, h, data, dates, amount)
        st["execution_time_seconds"] = time.perf_counter() - began
        for t in out.trades:
            realized.append(t.pnl)
            if t.pnl > 0:
                wins += 1
        n = len(out.trades)
        trades += n
        win_rate = float(st["win_rate_pct"]) if n > 0 else None
        strategy_details[key] = st
        individual_returns[key] = {"asset_id": key, "asset_type": a.asset_type, "symbol": a.symbol,
                                   "weight": 0.0, "amount": amount, "return": (st["final_equity"] / amount - 1) * 100,
                                   "initial_value": amount, "final_value": st["final_equity"], "trades": n,
                                   "win_rate": win_rate}
        assets.append((key, a, amount, out.equity))
    total = 0.0
    for _, _, amount, _ in assets:
        total += amount
    if total <= 0:
        raise validation("모든 종목의 백테스트가 실패했습니다.")

    equity = [0.0] * days
    weight_history: List[Dict[str, Any]] = []
    values = [0.0] * len(assets)
    for i, day in enumerate(dates):
        s = 0.0
        for k, (_, _, amount, eq) in enumerate(assets):
            values[k] = amount if eq is None else eq[i]
            s += values[k]
        equity[i] = s
        row: Dict[str, Any] = {"date": civil.fmt(day)}
        for k, (key, _, _, _) in enumerate(assets):
            row[key] = values[k] / s if s > 0 else 0.0
        weight_history.append(row)
    returns = daily_returns(equity)
    stats = statistics(req.start, req.end, equity, returns, total, equity[0] / total, trades)
    duration = req.end - req.start
    stats["Annual_Return"] = go_pow(equity[days - 1] / total, 365.25 / duration) * 100 - 100
    stats["Trade_Win_Rate"] = wins / trades * 100 if trades > 0 else None
    stats["Profit_Factor"] = profit_factor(realized)

    individual_results: List[Dict[str, Any]] = []
    composition: List[Dict[str, Any]] = []
    for key, a, amount, _ in assets:
        item = individual_returns[key]
        item["weight"] = amount / total
        detail = strategy_details.get(key)
        sharpe_ratio = detail["sharpe_ratio"] if detail is not None and "initial_cash" in detail else 0.0
        individual_results.append({
            "asset_id": key, "asset_type": a.asset_type, "ticker": a.symbol, "final_equity": item["final_value"],
            "total_return_pct": item["return"], "sharpe_ratio": sharpe_ratio, "weight": item["weight"],
            "amount": item["amount"], "trades": item["trades"], "win_rate": item["win_rate"],
        })
        composition.append({"asset_id": key, "symbol": a.symbol, "weight": item["weight"],
                            "amount": item["amount"], "asset_type": a.asset_type})
    equity_curve, daily_curve = curves(req.start, equity, returns)
    return {
        "portfolio_statistics": stats,
        "individual_returns": individual_returns,
        "individual_results": individual_results,
        "portfolio_result": {"total_equity": stats["Final_Value"], "total_return_pct": stats["Total_Return"]},
        "portfolio_composition": composition,
        "equity_curve": equity_curve,
        "daily_returns": daily_curve,
        "strategy_details": strategy_details,
        "rebalance_history": [],
        "weight_history": weight_history,
        "warnings": warnings,
        "calculation_assumptions": dict(ASSUMPTIONS),
    }


def _run_strategy(req: Request, h: History, data: Histories, dates: List[int], amount: float):
    bars: List[Bar] = []
    for b in h.bars:
        if b.date < req.start or b.date > req.end:
            continue
        rate = rate_on(h.currency, b.date, data)
        bars.append(Bar(b.date, b.open * rate, b.high * rate, b.low * rate, b.close * rate, b.volume))
    hist_dates = h.dates
    valuations = []
    for day in dates:
        j = bisect.bisect_right(hist_dates, day)
        price = 0.0
        if j > 0:
            rate = rate_on(h.currency, day, data)
            price = h.bars[j - 1].close * rate
        valuations.append((day, price))
    out = strategy.run(req.strategy, req.strategy_params, bars, valuations, amount, req.commission)

    eq = out.equity
    last = len(eq) - 1
    final_price = valuations[last][1]
    headline = statistics(req.start, req.end, eq, daily_returns(eq), amount, 1.0, len(out.trades))
    for v in (headline["Annual_Return"], headline["Annual_Volatility"]):
        if math.isnan(v) or math.isinf(v):
            raise validation("계산 결과가 표현 가능한 범위를 벗어났습니다.")
    annual = headline["Annual_Return"] / 100
    cal_ret = daily_returns(eq)
    down = 0.0
    for r in cal_ret:
        m = min(r, 0.0)
        down += m * m
    downside = math.sqrt(down / len(cal_ret)) * math.sqrt(DAYS_PER_YEAR)

    pnl = [t.pnl for t in out.trades]
    rets = [t.ret for t in out.trades]
    wins = sum(1 for t in out.trades if t.pnl > 0)
    n = len(out.trades)
    sortino = annual / downside if downside > 0 else 0.0
    calmar = annual / (-headline["Max_Drawdown"] / 100) if headline["Max_Drawdown"] < 0 else 0.0
    win_rate_pct = avg_trade = best = worst = 0.0
    if n > 0:
        win_rate_pct = wins / n * 100
        g = 1.0
        best_r, worst_r = -math.inf, math.inf
        for r in rets:
            g *= 1 + r
            best_r, worst_r = max(best_r, r), min(worst_r, r)
        avg_trade = (go_pow(g, 1 / n) - 1) * 100
        best, worst = best_r * 100, worst_r * 100
    sd = stddev(pnl)
    sqn = math.sqrt(n) * mean(pnl) / sd if sd > 0 else 0.0
    keys = civil.date_keys(req.start, len(dates))

    def native(usd: float, day: int) -> float:
        return usd / rate_on(h.currency, day, data)

    trade_log: List[Dict[str, Any]] = []
    for t in out.trades:
        row: Dict[str, Any] = {
            "Size": t.size, "EntryBar": t.entry_bar, "ExitBar": t.exit_bar, "EntryPrice": t.entry_price,
            "ExitPrice": t.exit_price, "SL": 0.0, "TP": 0.0, "PnL": t.pnl,
            "Commission": t.entry_fee + t.exit_fee, "ReturnPct": t.ret,
            "EntryTime": civil.fmt(t.entry_date) + "T00:00:00", "ExitTime": civil.fmt(t.exit_date) + "T00:00:00",
            "Duration": f"P{t.exit_date - t.entry_date}DT0H0M0S", "Tag": 0.0,
        }
        for prefix, bar in (("Entry", t.entry_bar), ("Exit", t.exit_bar)):
            for name, vals in out.indicators:
                row[prefix + "_" + name] = _nan_to_none(vals[bar])
        row["PriceCurrency"] = "USD"
        row["NativeCurrency"] = h.currency
        row["QuantityUnit"] = "fractional_adjusted_unit"
        row["EntryPriceNative"] = native(t.entry_price, t.entry_date)
        row["ExitPriceNative"] = native(t.exit_price, t.exit_date)
        trade_log.append(row)
    open_positions: List[Dict[str, Any]] = []
    p = out.open
    if p is not None:
        open_positions.append({
            "EntryTime": civil.fmt(p.entry_date), "EntryPrice": p.entry_price, "Size": p.size,
            "Commission": p.fee, "MarketPrice": final_price, "MarketValue": p.size * final_price,
            "PriceCurrency": "USD", "NativeCurrency": h.currency, "QuantityUnit": "fractional_adjusted_unit",
            "EntryPriceNative": native(p.entry_price, p.entry_date),
        })
    st = {
        "initial_cash": amount,
        "final_equity": eq[last],
        "total_return_pct": (eq[last] / amount - 1) * 100,
        "annualized_return_pct": annual * 100,
        "cagr_pct": annual * 100,
        "buy_and_hold_return_pct": (final_price / out.first_close - 1) * 100,
        "volatility_pct": headline["Annual_Volatility"],
        "sharpe_ratio": headline["Sharpe_Ratio"],
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "max_drawdown_pct": headline["Max_Drawdown"],
        "avg_drawdown_pct": -mean(drawdown_peaks(eq)) * 100,
        "total_trades": n,
        "win_rate_pct": win_rate_pct,
        "profit_factor": profit_factor(pnl),
        "avg_trade_pct": avg_trade,
        "best_trade_pct": best,
        "worst_trade_pct": worst,
        "sqn": sqn,
        "alpha_pct": None,
        "beta": None,
        "kelly_criterion": None,
        "trade_log": trade_log,
        "open_positions": open_positions,
        "cash": out.cash,
        "equity_curve": dict(zip(keys, eq)),
        "ticker": h.symbol,
        "strategy": req.strategy,
        "start_date": civil.fmt(req.start),
        "end_date": civil.fmt(req.end),
        "duration_days": req.end - req.start,
        "execution_time_seconds": 0.0,
        "timestamp": _timestamp(),
    }
    return st, out
