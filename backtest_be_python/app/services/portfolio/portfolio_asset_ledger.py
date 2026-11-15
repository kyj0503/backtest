"""Per-asset attribution from the same executions used to value the portfolio.

All amounts and prices are USD. Rebalancing transfers capital between assets;
they are neither outside contributions nor investment profit.
"""
from typing import Dict

import pandas as pd

from app.utils.metrics_math import annualized_volatility, safe_sharpe_ratio


class PortfolioAssetLedger:
    def __init__(self, amounts, dca_info):
        self.info = dca_info
        self.planned = amounts.copy()
        self.contributed = {key: amount if dca_info[key].asset_type == 'cash' else 0.0
                            for key, amount in amounts.items()}
        self.profit = dict.fromkeys(amounts, 0.0)
        self.previous = self.contributed.copy()
        self.returns = {key: [] for key in amounts}
        self.trades = {key: [] for key in amounts}
        self.buy_notional = dict.fromkeys(amounts, 0.0)
        self.buy_sizes = dict.fromkeys(amounts, 0.0)
        self.final_prices = {}
        self.values = self.contributed.copy()

    @staticmethod
    def values_at(shares, cash, prices) -> Dict[str, float]:
        return {**{key: size * prices.get(key, 0.0) for key, size in shares.items()}, **cash}

    def record_purchases(self, day, before_shares, after_shares, prices, counts_before):
        inflows = {}
        for key, size in after_shares.items():
            delta = size - before_shares[key]
            if delta <= 0:
                continue
            info = self.info[key]
            amount = (info.executed_count - counts_before[key]) * info.monthly_amount if info.investment_type == 'dca' else self.planned[key]
            inflows[key] = amount
            self.contributed[key] += amount
            count = info.executed_count - counts_before[key] if info.investment_type == 'dca' else 1
            for _ in range(count):
                self.add_trade(key, day, prices[key], delta / count)
        return inflows

    def add_trade(self, key, day, price, size):
        if abs(size) <= 1e-12:
            return
        self.trades[key].append({
            'EntryTime': day.isoformat(), 'EntryPrice': float(price), 'Size': float(abs(size)),
            'Type': 'BUY' if size > 0 else 'SELL', 'ExitTime': None, 'ExitPrice': None,
            'PnL': None, 'ReturnPct': None, 'Duration': None,
        })
        if size > 0:
            self.buy_notional[key] += float(price * size)
            self.buy_sizes[key] += float(size)

    def record_day(self, before, after, inflows, transfers, prices):
        for key in self.contributed:
            pre = before.get(key, 0.0)
            final = after.get(key, 0.0)
            inflow = inflows.get(key, 0.0)
            transfer = transfers.get(key, 0.0)
            self.profit[key] += final - pre - inflow - transfer
            # Market change before the close, then costs at the close. Transfers
            # are removed, so receiving another asset's proceeds is not a gain.
            capital = pre + inflow
            daily = ((pre / self.previous[key]) * ((final - transfer) / capital) - 1
                     if self.previous[key] > 0 and capital > 0 else 0.0)
            self.returns[key].append(daily)
            self.previous[key] = final
            self.values[key] = final
            if key in prices:
                self.final_prices[key] = float(prices[key])

    def results(self, total):
        individual, details = {}, {}
        for key, info in self.info.items():
            amount = self.contributed[key]
            daily = pd.Series(self.returns[key], dtype=float)
            individual[key] = {
                'symbol': info.symbol, 'weight': amount / total if total else 0.0,
                'amount': amount, 'return': self.profit[key] / amount * 100 if amount else 0.0,
                'start_price': self.buy_notional[key] / self.buy_sizes[key] if self.buy_sizes[key] else (1.0 if info.asset_type == 'cash' else None),
                'end_price': self.final_prices.get(key, 1.0 if info.asset_type == 'cash' else None),
                'investment_type': info.investment_type,
                'dca_periods': info.executed_count if info.investment_type == 'dca' else None,
                'final_value': self.values[key], 'trades': len(self.trades[key]),
                'sharpe_ratio': safe_sharpe_ratio(float(daily.mean()) * 252 * 100, annualized_volatility(daily)),
            }
            if info.asset_type == 'cash':
                individual[key]['asset_type'] = 'cash'
            else:
                details[key] = {'trade_log': self.trades[key]}
        # Keep the public CASH entry aggregated, including duplicate cash names.
        cash_keys = [key for key, info in self.info.items() if info.asset_type == 'cash']
        if cash_keys:
            cash = individual[cash_keys[0]].copy()
            cash['symbol'] = 'CASH'
            cash['asset_type'] = 'cash'
            for field in ('weight', 'amount', 'final_value', 'trades'):
                cash[field] = sum(individual[key][field] for key in cash_keys)
            cash['return'] = sum(self.profit[key] for key in cash_keys) / cash['amount'] * 100 if cash['amount'] else 0.0
            for key in cash_keys:
                del individual[key]
            individual = {'CASH': cash, **individual}
        return individual, details

    def record_market_profit(self, before):
        for key, value in before.items():
            self.profit[key] += value - self.previous[key]
