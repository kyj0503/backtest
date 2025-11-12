# Visual Structure: calculate_dca_portfolio_returns()

## 1. OVERALL FUNCTION FLOW

```
calculate_dca_portfolio_returns(portfolio_data, amounts, dca_info, start_date, end_date, ...)
│
├─ PHASE 1: SETUP & INITIALIZATION (Lines 115-190)
│  ├─ Extract cash holdings [115-121]
│  ├─ Setup date range [123-140]
│  ├─ Load ticker currencies (asyncio.to_thread) [142-156]
│  ├─ Load exchange rates (asyncio.to_thread) [158-187]
│  └─ Calculate target weights [189-190]
│
├─ PHASE 2: INITIALIZE STATE VARIABLES (Lines 191-213)
│  ├─ shares: Dict[str, float] = {}
│  ├─ portfolio_values: List[float] = []
│  ├─ daily_returns: List[float] = []
│  ├─ rebalance_history: List[Dict] = []
│  ├─ weight_history: List[Dict] = []
│  ├─ delisted_stocks: Set[str] = set()
│  └─ other tracking variables
│
├─ PHASE 3: MAIN DATE LOOP (Lines 215-684) ← CORE SIMULATION
│  │
│  └─ for current_date in date_range:
│     ├─ 3a. Date filtering [217-220]
│     │
│     ├─ 3b. PRICE FETCHING & CONVERSION [222-268]
│     │    for unique_key in stock_amounts:
│     │      ├─ Get price from portfolio_data
│     │      ├─ Convert currency → USD (with fallback)
│     │      └─ Store in current_prices
│     │
│     ├─ 3c. DELISTING DETECTION [270-307]
│     │    for unique_key in stock_amounts:
│     │      ├─ Track days without price
│     │      ├─ Mark delisted if >= 30 days
│     │      └─ Maintain last_valid_prices
│     │
│     ├─ 3d. INITIAL PURCHASES [310-337] (First day only)
│     │    if is_first_day:
│     │      for unique_key in stock_amounts:
│     │        ├─ If lump_sum: invest full amount
│     │        └─ If dca: invest first period
│     │
│     ├─ 3e. PERIODIC DCA PURCHASES [341-402]
│     │    if prev_date is not None:
│     │      for symbol in stock_amounts:
│     │        if investment_type == 'dca':
│     │          if current_date matches schedule:
│     │            └─ Execute DCA purchase
│     │
│     ├─ 3f. REBALANCING [404-648] ⚠️ LARGEST & MOST COMPLEX
│     │    if should_rebalance AND len(weights) > 1:
│     │      ├─ Adjust weights for delisted stocks [428-458]
│     │      ├─ Calculate weights_before [485-493]
│     │      ├─ Execute trades [502-587]
│     │      │  for unique_key, target_weight:
│     │      │    ├─ If cash: adjust holdings
│     │      │    └─ If stock: execute buy/sell
│     │      ├─ Apply commission scaling [588-597]
│     │      ├─ Calculate weights_after [599-614]
│     │      └─ Record rebalance_history [616-648]
│     │
│     └─ 3g. DAILY METRICS [650-684]
│          ├─ Calculate current_portfolio_value
│          ├─ Calculate daily_return
│          ├─ Record weight_history
│          └─ Update prev_* tracking
│
└─ PHASE 4: RESULT CREATION (Lines 686-709)
   ├─ Validate length match
   ├─ Create DataFrame with columns:
   │  ├─ Date
   │  ├─ Portfolio_Value
   │  ├─ Daily_Return
   │  └─ Cumulative_Return
   └─ Attach metadata (total_trades, rebalance_history, weight_history)
```

---

## 2. MAIN DATE LOOP - DETAILED BREAKDOWN

```
for current_date in date_range:  [O(n) iterations]
   │
   ├─ PRICE CONVERSION LOOP [O(m) iterations]
   │  └─ for unique_key in stock_amounts:
   │     ├─ [LOW] df.index.date <= current_date.date() → get price
   │     ├─ [MEDIUM] Currency conversion with exchange rate
   │     └─ [MEDIUM] Fallback cache for missing rates
   │
   ├─ DELISTING DETECTION LOOP [O(m) iterations]
   │  └─ for unique_key in stock_amounts:
   │     ├─ If has price: update last_valid_prices, last_price_date
   │     └─ Else: check days_without_price >= 30 days
   │
   ├─ INITIAL PURCHASE BLOCK [O(m) iterations, first day only]
   │  └─ for unique_key, amount in stock_amounts:
   │     ├─ [LINEAR] shares[unique_key] = amount / price
   │     └─ [LINEAR] total_trades += 1
   │
   ├─ PERIODIC DCA BLOCK [O(m) iterations, subsequent days]
   │  └─ for symbol, _ in stock_amounts:
   │     ├─ If not DCA: skip
   │     ├─ Calculate next_dca_date [get_next_nth_weekday]
   │     └─ If current_date matches schedule:
   │        └─ shares[symbol] += invest_amount / price
   │
   ├─ REBALANCING BLOCK [O(m) to O(m²) complexity] ⚠️ CRITICAL
   │  └─ if should_rebalance AND len(weights) > 1:
   │     │
   │     ├─ Adjust weights [O(m) nested loops]
   │     │  └─ for unique_key in delisted_stocks:
   │     │     └─ scaling_factor = 1.0 / tradeable_weight_sum
   │     │
   │     ├─ Calculate weights_before [O(m)]
   │     │  └─ for unique_key in shares: calculate weight
   │     │
   │     ├─ Execute trades [O(m) but with conditional logic]
   │     │  └─ for unique_key, target_weight:
   │     │     ├─ If delisted_stocks:
   │     │     │  └─ Skip (don't trade)
   │     │     └─ Else:
   │     │        ├─ Calculate shares_diff
   │     │        ├─ Record BUY/SELL trade
   │     │        └─ Add commission cost
   │     │
   │     ├─ Scaling [O(m)]
   │     │  └─ shares *= (1 - commission_cost / value)
   │     │
   │     └─ Calculate weights_after [O(m)]
   │        └─ for unique_key in shares: calculate new weight
   │
   └─ DAILY METRICS [O(m) calculations]
      ├─ current_portfolio_value = sum(shares * prices) + cash
      ├─ daily_return = (value - prev_value - inflow) / prev_value
      ├─ current_weights = {symbol: allocation}
      └─ Append to portfolio_values, daily_returns
```

**Time Complexity**: O(n × m) where n = trading days, m = stocks

---

## 3. REBALANCING LOGIC - MOST COMPLEX BLOCK

```
if should_rebalance AND len(target_weights) > 1:  [Lines 427-648]
│
├─────────────────────────────────────────────────────────────────
│ STEP 1: WEIGHT ADJUSTMENT FOR DELISTED STOCKS [Lines 428-458]
├─────────────────────────────────────────────────────────────────
│
└─ if delisted_stocks exists:
   │
   ├─ Calculate delisted_weight_sum
   │  └─ sum(target_weights[key] for key in delisted_stocks)
   │
   ├─ Calculate scaling_factor
   │  └─ 1.0 / (1.0 - delisted_weight_sum)
   │
   └─ for unique_key, original_weight in target_weights.items():
      ├─ If delisted: adjusted_weight = 0.0
      └─ Else: adjusted_weight = original_weight * scaling_factor
   │
   │ EXAMPLE:
   │ --------
   │ Original:    A=30%, B=30%, C=40%
   │ If C delisted (40%):
   │   - tradeable = 30% + 30% = 60%
   │   - scaling = 1.0 / 0.6 = 1.667
   │   - A' = 30% * 1.667 = 50%
   │   - B' = 30% * 1.667 = 50%
   │   - C' = 0%
   │
├─────────────────────────────────────────────────────────────────
│ STEP 2: CALCULATE WEIGHTS_BEFORE [Lines 485-493]
├─────────────────────────────────────────────────────────────────
│
├─ for unique_key in shares:
│  └─ weight_before[symbol] = (shares * price) / total_value
│
├─ for unique_key in cash_holdings:
│  └─ weight_before[symbol] = cash_amount / total_value
│
├─────────────────────────────────────────────────────────────────
│ STEP 3: EXECUTE TRADES [Lines 502-587]
├─────────────────────────────────────────────────────────────────
│
└─ for unique_key, target_weight in adjusted_target_weights.items():
   │
   ├─ target_value = total_portfolio_value * target_weight
   │
   ├─ CASE 1: CASH ASSET [Lines 506-528]
   │  │
   │  └─ if asset_type == 'cash':
   │     ├─ new_cash_holdings[key] = target_value
   │     └─ if |diff| > THRESHOLD: record in rebalance_trades
   │
   └─ CASE 2: STOCK ASSET [Lines 531-587]
      │
      └─ if asset_type == 'stock':
         │
         ├─ SUBCASE 2a: DELISTED STOCK [Lines 533-549]
         │  │
         │  └─ if key in delisted_stocks:
         │     ├─ new_shares[key] = shares[key]  ← Keep unchanged
         │     └─ Skip trading (can't buy/sell)
         │
         └─ SUBCASE 2b: TRADEABLE STOCK [Lines 551-586]
            │
            └─ else:
               ├─ current_value = shares[key] * price
               │
               ├─ if |target - current| > THRESHOLD:
               │  │
               │  ├─ shares_diff = (target_value / price) - shares[key]
               │  │
               │  ├─ if shares_diff > 0: record BUY
               │  │  └─ rebalance_trades.append({'symbol': ..., 'action': 'buy'})
               │  │
               │  └─ else: record SELL
               │     └─ rebalance_trades.append({'symbol': ..., 'action': 'sell'})
               │
               ├─ trade_value = |target_value - current_value|
               ├─ commission_cost = trade_value * commission
               └─ new_shares[key] = target_value / price
   │
   │
   ├─────────────────────────────────────────────────────────────
   │ STEP 4: APPLY COMMISSION SCALING [Lines 588-597]
   ├─────────────────────────────────────────────────────────────
   │
   ├─ scale_factor = (total_value - total_commission) / total_value
   │
   └─ shares = {k: v * scale_factor for k, v in new_shares.items()}
      cash_holdings = {k: v * scale_factor for k, v in new_cash_holdings.items()}
   │
   │
   ├─────────────────────────────────────────────────────────────
   │ STEP 5: CALCULATE WEIGHTS_AFTER [Lines 599-614]
   ├─────────────────────────────────────────────────────────────
   │
   ├─ for unique_key in shares:
   │  └─ weight_after[symbol] = (shares * price) / new_total_value
   │
   └─ for unique_key in cash_holdings:
      └─ weight_after[symbol] = cash_amount / new_total_value
   │
   │
   └─────────────────────────────────────────────────────────────
     STEP 6: RECORD REBALANCE HISTORY [Lines 616-648]
     ─────────────────────────────────────────────────────────
     
     if rebalance_trades:
       └─ rebalance_history.append({
            'date': current_date,
            'trades': rebalance_trades,
            'weights_before': weights_before,
            'weights_after': weights_after,
            'commission_cost': total_commission_cost
          })
```

---

## 4. LOOP NESTING STRUCTURE

```
Main Loop (Line 215): for current_date in date_range
│
├─ Loop 1 (Line 227): for unique_key in stock_amounts [Price Fetching]
│  ├─ Depth 2 - MEDIUM COMPLEXITY (currency conversion with fallback)
│  └─ Time: O(m)
│
├─ Loop 2 (Line 271): for unique_key in stock_amounts [Delisting Detection]
│  ├─ Depth 2
│  └─ Time: O(m)
│
├─ Conditional 1 (Line 310): if is_first_day
│  ├─ Loop 3 (Line 311): for unique_key in stock_amounts [Initial Purchase]
│  ├─ Depth 2
│  └─ Time: O(m), First iteration only
│
├─ Conditional 2 (Line 341): if prev_date is not None
│  ├─ Loop 4 (Line 342): for symbol in stock_amounts [DCA Check]
│  ├─ Nested If (Line 348): if investment_type == 'dca'
│  ├─ Depth 3 - MEDIUM-HIGH COMPLEXITY
│  └─ Time: O(m) × O(1)
│
├─ Conditional 3 (Line 427): if should_rebalance AND len(weights) > 1
│  │
│  ├─ Conditional 3a (Line 431): if delisted_stocks
│  │  ├─ Loop (Line 446): for unique_key, original_weight
│  │  ├─ Depth 2-3
│  │  └─ Time: O(m)
│  │
│  ├─ Conditional 3b (Line 484): if total_portfolio_value > 0
│  │  │
│  │  ├─ Loop 5 (Line 487): for unique_key in shares [weights_before]
│  │  ├─ Time: O(m)
│  │  │
│  │  ├─ Loop 6 (Line 502): for unique_key, target_weight [Execute Trades]
│  │  ├─ Nested If (Line 506/531/533): asset type branching
│  │  ├─ Depth 3-4 - VERY HIGH COMPLEXITY ⚠️
│  │  ├─ Time: O(m²) worst case (checks delisted_stocks for each item)
│  │  │
│  │  └─ Loop 7 (Line 608): for unique_key in shares [weights_after]
│  │     └─ Time: O(m)
│  │
│  └─ Record history (no loops)
│
└─ Final calculations (Line 650): no additional loops, just aggregation

TOTAL TIME COMPLEXITY: O(n × m)
  where n = number of trading days
        m = number of stocks
```

---

## 5. EXTRACTION CANDIDATES - DEPENDENCY GRAPH

```
Phase 1: SETUP & INITIALIZATION (Phase 1 only, not extracted)
│
Phase 2: INITIALIZE STATE
│
├──→ Helper 1: initialize_portfolio_state() ✓ PURE
│    Input: stock_amounts, cash_amount, amounts
│    Output: Dict with all state variables
│    Dependencies: None
│
├──→ Helper 4: calculate_adjusted_rebalance_weights() ✓ PURE
│    Input: target_weights, delisted_stocks, dca_info
│    Output: adjusted_target_weights
│    Dependencies: logging only
│
Phase 3: MAIN DATE LOOP
│
├──→ Helper 2: fetch_and_convert_prices()
│    Input: current_date, stock_amounts, portfolio_data, ...
│    Output: current_prices, last_valid_exchange_rates
│    Dependencies: currency_converter, logger
│    ├─ Used by: Helper 3, 5, 6, 7, 8
│    └─ Time: O(m)
│
├──→ Helper 3: detect_and_update_delisting()
│    Input: current_date, stock_amounts, current_prices, ...
│    Output: None (side-effects)
│    Dependencies: Helper 2 (current_prices), TradingThresholds
│    ├─ Used by: Main loop (updates delisted_stocks)
│    └─ Time: O(m)
│
├──→ Helper 5: execute_initial_purchases()
│    Input: current_date, stock_amounts, current_prices, ...
│    Output: trades_executed, daily_cash_inflow
│    Dependencies: Helper 2 (current_prices), logging
│    ├─ Used by: Main loop (accumulates trades/inflow)
│    └─ Time: O(m)
│
├──→ Helper 6: execute_periodic_dca_purchases()
│    Input: current_date, prev_date, stock_amounts, ...
│    Output: trades_executed, daily_cash_inflow
│    Dependencies: get_next_nth_weekday(), get_weekday_occurrence()
│    ├─ Used by: Main loop (accumulates trades/inflow)
│    └─ Time: O(m)
│
├──→ Helper 7: execute_rebalancing_trades() ⚠️ MOST COMPLEX
│    Input: current_date, adjusted_target_weights, shares, ...
│    Output: Dict with trades, history, weights
│    Dependencies: Helper 4 (adjusted_target_weights), TradingThresholds
│    ├─ Used by: Main loop (updates shares, records history)
│    └─ Time: O(m²) worst case
│
├──→ Helper 8: calculate_daily_metrics_and_history()
│    Input: current_date, shares, available_cash, ...
│    Output: current_portfolio_value, daily_return, current_weights
│    Dependencies: Helper 2 (current_prices)
│    ├─ Used by: Main loop (accumulates metrics)
│    └─ Time: O(m)
│
Phase 4: RESULT CREATION (not extracted, too simple)
```

---

## 6. COMPLEXITY COMPARISON

### Before Extraction
```
Single Function: calculate_dca_portfolio_returns()
├─ Lines: 625 (86-709)
├─ Cyclomatic Complexity: Very High (10+)
├─ Max Nesting Depth: 4 levels
│  1. for current_date in date_range
│  2. for unique_key in stock_amounts
│  3. if should_rebalance
│  4. for unique_key, target_weight in adjusted_target_weights.items()
├─ Branches: 8+ major conditional blocks
├─ Test Coverage: Requires full integration test
└─ Reusability: None
```

### After Extraction (Proposed)
```
Main Function: calculate_dca_portfolio_returns()  [Refactored]
├─ Lines: ~150 (setup + loop orchestration)
├─ Cyclomatic Complexity: Reduced to 3-4
├─ Max Nesting Depth: 2 levels (loop + conditional)
└─ Calls: 8 helper functions in sequence

Helper 1: initialize_portfolio_state()  [23 lines, Low complexity]
Helper 2: fetch_and_convert_prices()  [47 lines, Medium complexity]
Helper 3: detect_and_update_delisting()  [38 lines, Medium complexity]
Helper 4: calculate_adjusted_rebalance_weights()  [31 lines, Low complexity]
Helper 5: execute_initial_purchases()  [28 lines, Low complexity]
Helper 6: execute_periodic_dca_purchases()  [62 lines, High complexity]
Helper 7: execute_rebalancing_trades()  [154 lines, Very High complexity]
Helper 8: calculate_daily_metrics_and_history()  [35 lines, Low complexity]

Total Lines: 625 (same total, but better organized)
Avg Helper Size: 53 lines
Test Approach: 8 unit tests + 1 integration test
Reusability: Each helper can be used independently
```

---

## 7. KEY DECISION POINTS

```
Main Date Loop Processing Order:
═════════════════════════════════════

for current_date in date_range:
   │
   ├─ 1. FILTER DATE RANGE [217-220]
   │  └─ Skip if before start_date, break if after end_date
   │
   ├─ 2. GET PRICES & CONVERT [222-268]  ← Must be first
   │  └─ Needed by all downstream steps
   │
   ├─ 3. DETECT DELISTING [270-307]  ← Depends on (2)
   │  └─ Marks stocks as delisted if no price for 30 days
   │
   ├─ 4. INITIAL PURCHASE [310-337]  ← First day only
   │  └─ Lump_sum or DCA initial investment
   │
   ├─ 5. PERIODIC DCA [341-402]  ← Subsequent days
   │  └─ Schedule-based purchases
   │
   ├─ 6. REBALANCING [404-648]  ← Depends on (2), (3), (5)
   │  └─ Adjusts portfolio to target weights
   │  └─ Skips delisted stocks
   │
   └─ 7. DAILY METRICS [650-684]  ← Depends on all above
      └─ Records portfolio state for this day

CRITICAL DEPENDENCIES:
  - (2) must execute before (3), (5), (6), (7)
  - (3) must execute before (6)
  - (5) must execute before (6) to know portfolio value
  - (6) must execute before (7) to get updated positions
  - (4) sets shares, used by all downstream
```

