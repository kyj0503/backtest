"""buy&hold 일별 시뮬레이션 (Go internal/engine/buyhold.go).

요청 기간의 모든 달력일을 평가한다.
  - 납입: 시작일과 실제 예정일에만 한다(F04). 휴장일·상장 전 납입금은 현금으로 기다렸다가 다음 거래
    가능일에 매수한다. 매수 예산 B, 수수료율 c이면 매수 금액은 B/(1+c)다(F02).
  - 평가: 수량 × 직전 현지 종가 × 그날 환율 + 대기 현금(R).
  - 리밸런싱: 예정일이 휴장이면 보류하고, 자금이 있는 모든 주식이 거래 가능한 다음 날 실행한다.
    수수료는 실제 회전 금액 기준이고 원장과 같다(F06).
  - 일간 수익률: 납입 전후를 나눈 시간가중 수익률(TWR). 최초 매수 수수료도 첫 수익률에 들어간다(S02).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from ..core.cancellation import check_cancelled
from . import civil, schedule
from .errors import validation
from .marketdata import History, Histories, rate_on
from .request import Asset, Request
from .stats import clean_return, sharpe, statistics
from .response import ASSUMPTIONS, curves


class _Holding:
    __slots__ = ("asset", "key", "history", "cursor", "planned", "per_period", "plan", "executed",
                 "shares", "cash", "price", "has_price", "tradeable", "contributed", "profit", "previous",
                 "returns", "trades", "buy_size", "buy_notional")

    def __init__(self, asset: Asset, key: str):
        self.asset = asset
        self.key = key
        self.history: Optional[History] = None
        self.cursor = 0
        self.planned = 0.0
        self.per_period = 0.0
        self.plan: List[int] = []
        self.executed = 0
        self.shares = 0.0
        self.cash = 0.0
        self.price = 0.0
        self.has_price = False
        self.tradeable = False
        self.contributed = 0.0
        self.profit = 0.0
        self.previous = 0.0
        self.returns: List[float] = []
        self.trades: List[Dict[str, Any]] = []
        self.buy_size = 0.0
        self.buy_notional = 0.0

    def value(self) -> float:
        if not self.has_price:
            return self.cash
        return self.cash + self.shares * self.price

    def trade(self, day: int, size: float, commission: float, native_price: float) -> None:
        if abs(size) <= 1e-12:
            return
        typ = "SELL" if size < 0 else "BUY"
        self.trades.append({
            "EntryTime": civil.fmt(day) + "T00:00:00",
            "EntryPrice": self.price,
            "Size": abs(size),
            "Commission": abs(size) * self.price * commission,
            "Type": typ,
            "ExitTime": None,
            "ExitPrice": None,
            "PnL": None,
            "ReturnPct": None,
            "Duration": None,
            "PriceCurrency": "USD",
            "NativeCurrency": self.history.currency,
            "QuantityUnit": "fractional_adjusted_unit",
            "EntryPriceNative": native_price,
        })
        if size > 0:
            self.buy_size += size
            self.buy_notional += size * self.price


def group_thousands(v: float) -> str:
    """1234567.891 → "1,234,567.89" (Go strconv 'f' 2자리 반올림과 같다)."""
    return f"{v:,.2f}"


def run(req: Request, data: Histories) -> Dict[str, Any]:
    holdings: List[_Holding] = []
    warnings: List[str] = []
    for idx, a in enumerate(req.portfolio):
        h = _Holding(a, a.id(idx))
        if not a.cash:
            hist = data.get(a.symbol)
            if hist is None or len(hist.bars) == 0:
                warnings.append(f"종목 {a.symbol}의 가격 데이터를 불러오지 못해 백테스트에서 제외했습니다 "
                                f"(투자금 ${group_thousands(a.base())}는 수익률 계산에 포함되지 않음).")
                continue
            h.history = hist
        h.plan = [req.start]
        if a.dca:
            h.plan.extend(schedule.dates(req.start, req.end, a.dca_frequency))
        n = float(len(h.plan))
        if a.total_amount is not None:
            h.planned = a.total_amount
            h.per_period = math.floor(h.planned * 100 / n) / 100  # 센트 단위 기본 회차, 마지막 회차가 잔액
        elif a.weight is not None:
            h.planned = a.base()
            h.per_period = h.planned / n
        else:
            h.planned = a.base() * n
            h.per_period = a.base()
        holdings.append(h)
    if not holdings:
        raise validation("[ValidationError] 포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다.")

    days = req.end - req.start + 1
    dates = [req.start + i for i in range(days)]
    planned_total = 0.0
    for h in holdings:
        planned_total += h.planned
    c = req.commission
    rebalance_days = schedule.dates(req.start, req.end, req.rebalance())
    rebalance_idx, rebalance_pending = 0, False
    equity: List[float] = []
    returns: List[float] = []
    weights: List[Dict[str, Any]] = []
    rebalances: List[Dict[str, Any]] = []
    trade_count = 0
    previous = 0.0

    nh = len(holdings)
    before = [0.0] * nh
    inflows = [0.0] * nh
    transfers = [0.0] * nh
    natives = [0.0] * nh

    for di, day in enumerate(dates):
        if di % 32 == 0:
            check_cancelled()
        for i, h in enumerate(holdings):
            if h.asset.cash:
                continue
            bars = h.history.bars
            while h.cursor < len(bars) and bars[h.cursor].date <= day:
                h.cursor += 1
            h.tradeable = False
            if h.cursor > 0:
                bar = bars[h.cursor - 1]
                if bar.close > 0 and not math.isinf(bar.close):
                    rate = rate_on(h.history.currency, day, data)
                    h.price, h.has_price = bar.close * rate, True
                    h.tradeable = bar.date == day
                    natives[i] = h.price / rate
        pre_flow = 0.0
        for i, h in enumerate(holdings):
            before[i] = h.value()
            pre_flow += before[i]
            inflows[i], transfers[i] = 0.0, 0.0
        for i, h in enumerate(holdings):
            h.profit += before[i] - h.previous
            while h.executed < len(h.plan) and h.plan[h.executed] <= day:
                amount = h.per_period
                if h.asset.total_amount is not None and h.executed + 1 == len(h.plan):
                    amount = h.planned - h.contributed
                h.cash += amount
                h.contributed += amount
                inflows[i] += amount
                h.executed += 1
            if not h.asset.cash and h.tradeable and h.cash > 0:
                size = h.cash / (h.price * (1 + c))
                h.shares += size
                h.cash = 0.0
                trade_count += 1
                h.trade(day, size, c, natives[i])
        while rebalance_idx < len(rebalance_days) and rebalance_days[rebalance_idx] <= day:
            rebalance_pending = len(equity) > 0
            rebalance_idx += 1
        if rebalance_pending and nh > 1 and _all_funded_tradeable(holdings):
            rebalance_pending = False
            ev, n_trades = _rebalance(holdings, day, c, planned_total, transfers, natives)
            trade_count += n_trades
            if ev is not None:
                rebalances.append(ev)

        value = inflow = 0.0
        for i, h in enumerate(holdings):
            value += h.value()
            inflow += inflows[i]
        if previous > 0 and inflow > 0:
            daily = pre_flow / previous * (value / (pre_flow + inflow)) - 1
        elif previous > 0:
            daily = (value - previous - inflow) / previous
        elif inflow > 0:
            daily = value / inflow - 1
        else:
            daily = 0.0
        row: Dict[str, Any] = {"date": civil.fmt(day)}
        for i, h in enumerate(holdings):
            after = h.value()
            h.profit += after - before[i] - inflows[i] - transfers[i]
            if h.previous > 0 and before[i] + inflows[i] > 0:
                r = before[i] / h.previous * ((after - transfers[i]) / (before[i] + inflows[i])) - 1
            elif inflows[i] > 0:
                r = (after - transfers[i]) / inflows[i] - 1
            else:
                r = 0.0
            h.returns.append(clean_return(r))
            h.previous = after
            if value > 0:
                k = h.key if h.asset.cash else h.asset.symbol
                prev = row.get(k)
                if not isinstance(prev, float):
                    prev = 0.0
                row[k] = prev + after / value
        weights.append(row)
        equity.append(value)
        returns.append(clean_return(daily))
        previous = value

    contributed = 0.0
    for h in holdings:
        contributed += h.contributed
    if contributed <= 0:
        raise validation("기간 내에 실행된 투자가 없습니다.")
    stats = statistics(req.start, req.end, equity, returns, contributed, 1.0, trade_count)

    individual_returns: Dict[str, Any] = {}
    individual_results: List[Dict[str, Any]] = []
    composition: List[Dict[str, Any]] = []
    strategy_details: Dict[str, Any] = {}
    for h in holdings:
        if h.buy_size > 0:
            start_price: Optional[float] = h.buy_notional / h.buy_size
        elif h.asset.cash:
            start_price = 1.0
        else:
            start_price = None
        if h.asset.cash:
            end_price: Optional[float] = 1.0
        elif h.has_price:
            end_price = h.price
        else:
            end_price = None
        periods = h.executed if h.asset.dca else None
        ret = h.profit / h.contributed * 100 if h.contributed > 0 else 0.0
        weight = h.contributed / contributed
        final_value = h.value()
        sharpe_ratio = sharpe(h.returns)
        individual_returns[h.key] = {
            "asset_id": h.key,
            "symbol": h.asset.symbol,
            "weight": weight,
            "amount": h.contributed,
            "return": ret,
            "start_price": start_price,
            "end_price": end_price,
            "investment_type": h.asset.investment_type,
            "dca_periods": periods,
            "final_value": final_value,
            "trades": len(h.trades),
            "sharpe_ratio": sharpe_ratio,
            "asset_type": h.asset.asset_type,
        }
        if not h.asset.cash:
            strategy_details[h.key] = {"trade_log": h.trades, "open_positions": None}
        individual_results.append({
            "asset_id": h.key,
            "asset_type": h.asset.asset_type,
            "ticker": h.asset.symbol,
            "final_equity": final_value,
            "total_return_pct": ret,
            "sharpe_ratio": sharpe_ratio,
            "weight": weight,
            "amount": h.contributed,
            "trades": len(h.trades),
            "win_rate": None,
        })
        composition.append({
            "asset_id": h.key,
            "symbol": h.asset.symbol,
            "weight": weight,
            "amount": h.contributed,
            "investment_type": h.asset.investment_type,
            "dca_periods": periods,
            "asset_type": h.asset.asset_type,
        })
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
        "rebalance_history": rebalances,
        "weight_history": weights,
        "warnings": warnings,
        "calculation_assumptions": dict(ASSUMPTIONS),
    }


def _all_funded_tradeable(hs: List[_Holding]) -> bool:
    for h in hs:
        if not h.asset.cash and h.planned != 0 and not h.tradeable:
            return False
    return True


def _rebalance(hs: List[_Holding], day: int, c: float, planned_total: float, transfers: List[float],
               natives: List[float]):
    """목표 비중(계획 예산 비율)으로 맞춘다. 수수료 차감 후 총액 V가 V + fees(V) = V_before를 만족하도록
    이분법으로 푼다(c < 0.1이라 단조). transfers에는 항목별 (목표 − 현재 + 수수료)를 기록한다."""
    n = len(hs)
    current = [0.0] * n
    eligible = [False] * n
    total = allocated = target_sum = 0.0
    for i, h in enumerate(hs):
        current[i] = h.value()
        total += current[i]
        eligible[i] = h.asset.cash or h.tradeable
        if eligible[i]:
            allocated += current[i]
            target_sum += h.planned / planned_total
    if total <= 0 or target_sum <= 0:
        return None, 0
    weights = [h.planned / planned_total / target_sum for h in hs]
    lo, hi = 0.0, allocated
    for _ in range(80):
        mid = (lo + hi) / 2
        fees = 0.0
        for i, h in enumerate(hs):
            if eligible[i] and not h.asset.cash:
                fees += abs(mid * weights[i] - current[i]) * c
        if mid + fees > allocated:
            hi = mid
        else:
            lo = mid
    net = (lo + hi) / 2
    weights_before: Dict[str, float] = {}
    trades: List[Dict[str, Any]] = []
    commission_cost = 0.0
    n_trades = 0
    for i, h in enumerate(hs):
        weights_before[h.key] = current[i] / total
        if not eligible[i]:
            continue
        target = net * weights[i]
        diff = target - current[i]
        fee = 0.0
        if not h.asset.cash:
            fee = abs(diff) * c
        commission_cost += fee
        transfers[i] = diff + fee
        if h.asset.cash:
            h.cash = target
            if abs(diff) > 1e-9:
                trades.append({"asset_id": h.key, "symbol": h.asset.symbol,
                               "action": "increase" if diff > 0 else "decrease",
                               "amount": abs(diff), "price": 1.0, "commission": 0.0})
            continue
        shares = target / h.price
        size = shares - h.shares
        if abs(size) > 1e-12:
            n_trades += 1
            h.trade(day, size, c, natives[i])
            trades.append({"asset_id": h.key, "symbol": h.asset.symbol,
                           "action": "buy" if size > 0 else "sell",
                           "shares": abs(size), "price": h.price, "commission": fee})
        h.shares = shares
    after_total = 0.0
    for h in hs:
        after_total += h.value()
    weights_after = {h.key: h.value() / after_total for h in hs}
    if not trades:
        return None, n_trades
    return {
        "date": civil.fmt(day),
        "trades": trades,
        "weights_before": weights_before,
        "weights_after": weights_after,
        "commission_cost": commission_cost,
    }, n_trades
