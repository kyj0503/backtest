# EXTRACTION SUMMARY TABLE: 8 Helper Functions

| # | Function Name | Lines | Responsibility | Inputs | Return Type | Complexity |
|---|---|---|---|---|---|---|
| 1 | `initialize_portfolio_state()` | 191-213 (23) | Initialize all tracking variables and state containers | `stock_amounts: Dict`, `cash_amount: float`, `amounts: Dict` | `Dict[str, Any]` | Low ✓ |
| 2 | `fetch_and_convert_prices()` | 222-268 (47) | Extract prices from data and convert to USD using exchange rates | `current_date`, `stock_amounts`, `portfolio_data`, `dca_info`, `ticker_currencies`, `exchange_rates_by_currency` | `Tuple[Dict[str, float], Dict[str, float]]` | Medium |
| 3 | `detect_and_update_delisting()` | 270-307 (38) | Detect delisted stocks (30+ days no price) and update state | `current_date`, `stock_amounts`, `current_prices`, `dca_info`, `delisted_stocks` (set), `last_valid_prices` (dict), `last_price_date` (dict) | `None` (side-effects) | Medium |
| 4 | `calculate_adjusted_rebalance_weights()` | 428-458 (31) | Adjust target weights for delisted stocks by redistributing proportionally | `target_weights: Dict`, `delisted_stocks: Set`, `dca_info: Dict` | `Dict[str, float]` | Low-Medium ✓ |
| 5 | `execute_initial_purchases()` | 310-337 (28) | Execute first-day purchases (lump_sum or DCA initial) | `current_date`, `stock_amounts`, `current_prices`, `dca_info`, `shares` (dict), `commission: float` | `Tuple[int, float]` (trades, cash_inflow) | Low-Medium ✓ |
| 6 | `execute_periodic_dca_purchases()` | 341-402 (62) | Execute periodic DCA purchases on Nth Weekday schedule | `current_date`, `prev_date`, `stock_amounts`, `current_prices`, `dca_info` (modified), `shares` (dict), `commission`, `start_date_obj` | `Tuple[int, float]` (trades, cash_inflow) | High |
| 7 | `execute_rebalancing_trades()` | 495-648 (154) | Execute rebalancing trades, apply commission, track history | `current_date`, `adjusted_target_weights`, `shares` (modified), `current_prices`, `available_cash` (modified), `cash_holdings` (modified), `cash_amounts`, `commission`, `total_stock_value`, `dca_info`, `delisted_stocks` | `Dict[str, Any]` (trades, history, weights) | Very High ⚠️ |
| 8 | `calculate_daily_metrics_and_history()` | 650-684 (35) | Calculate daily portfolio value, daily return, and weight history | `current_date`, `shares`, `available_cash`, `current_prices`, `cash_holdings`, `prev_portfolio_value`, `daily_cash_inflow`, `total_amount`, `dca_info` | `Tuple[float, float, Dict]` (value, return, weights) | Low-Medium ✓ |

---

## DETAILED SPECIFICATIONS

### Function 1: initialize_portfolio_state()
```
Purpose: Set up all tracking variables
Lines: 191-213 (23 lines)

Input:
  - stock_amounts: Dict[str, float]
  - cash_amount: float
  - amounts: Dict[str, float]

Output Dict contains:
  - shares: Dict[str, float] = {}
  - portfolio_values: List[float] = []
  - daily_returns: List[float] = []
  - prev_portfolio_value: float = 0
  - prev_date: Optional[pd.Timestamp] = None
  - is_first_day: bool = True
  - available_cash: float = cash_amount
  - cash_holdings: Dict[str, float]
  - total_trades: int = 0
  - rebalance_history: List[Dict] = []
  - weight_history: List[Dict] = []
  - last_rebalance_date: Optional[pd.Timestamp] = None
  - original_rebalance_nth: Optional[int] = None
  - last_valid_prices: Dict[str, float] = {}
  - last_price_date: Dict[str, date] = {}
  - delisted_stocks: Set[str] = set()

Complexity: O(m) where m = number of unique_keys
Testing: Unit test straightforward (no side-effects)
```

---

### Function 2: fetch_and_convert_prices()
```
Purpose: Extract prices from portfolio_data and convert to USD
Lines: 222-268 (47 lines)

Input:
  - current_date: pd.Timestamp
  - stock_amounts: Dict[str, float]
  - portfolio_data: Dict[str, pd.DataFrame]  (symbol -> OHLC)
  - dca_info: Dict[str, Dict]  (unique_key -> investment info)
  - ticker_currencies: Dict[str, str]  (unique_key -> currency code)
  - exchange_rates_by_currency: Dict[str, Dict[date, float]]

Output:
  - current_prices: Dict[str, float]  (unique_key -> USD price)
  - last_valid_exchange_rates: Dict[str, float]  (currency -> rate, cached for fallback)

Key Logic:
  1. For each stock in stock_amounts:
     - Get most recent price <= current_date from portfolio_data
     - If currency == 'USD': use raw_price as-is
     - Else: lookup exchange_rate, use fallback cache if missing
     - Apply currency_converter.get_conversion_multiplier()
     - Handle missing rates (continue/skip stock)

Complexity: O(m) where m = number of stocks
Testing: Can mock exchange_rates and portfolio_data
Async: No (pure calculations and dict lookups)
```

---

### Function 3: detect_and_update_delisting()
```
Purpose: Track stocks with extended price absence and mark as delisted
Lines: 270-307 (38 lines)

Input:
  - current_date: pd.Timestamp
  - stock_amounts: Dict[str, float]
  - current_prices: Dict[str, float]  (stocks with prices today)
  - dca_info: Dict[str, Dict]  (for symbol lookup)
  - delisted_stocks: Set[str]  (MODIFIED - stocks marked as delisted)
  - last_valid_prices: Dict[str, float]  (MODIFIED - updated from current_prices)
  - last_price_date: Dict[str, date]  (MODIFIED - updated from current_date)

Output: None (side-effects on input collections)

Key Logic:
  1. For stocks WITH prices today:
     - Update last_valid_prices, last_price_date
     - Remove from delisted_stocks if previously marked
  2. For stocks WITHOUT prices today:
     - Check days_without_price >= DELISTING_THRESHOLD_DAYS (30)
     - If yes AND not already delisted: add to delisted_stocks
  3. After loop: maintain delisted prices in current_prices for valuation

Complexity: O(m) where m = number of stocks
Testing: Can mock current_prices, manipulate dates
Side-Effects: Yes (modifies sets/dicts in place)
```

---

### Function 4: calculate_adjusted_rebalance_weights()
```
Purpose: Adjust target weights when some stocks are delisted
Lines: 428-458 (31 lines)

Input:
  - target_weights: Dict[str, float]  (original planned allocations)
  - delisted_stocks: Set[str]  (stocks that can't be traded)
  - dca_info: Dict[str, Dict]  (for logging symbol names)

Output:
  - adjusted_target_weights: Dict[str, float]

Key Logic:
  1. If no delisted stocks: return copy of target_weights
  2. Else:
     - Calculate delisted_weight_sum = sum of weights for delisted stocks
     - Calculate tradeable_weight_sum = 1.0 - delisted_weight_sum
     - Calculate scaling_factor = 1.0 / tradeable_weight_sum
     - For each stock:
       * If delisted: weight = 0.0
       * Else: weight *= scaling_factor  (proportional increase)
  3. Example:
     * Original: A=30%, B=30%, C=40%
     * If C delisted: A'=30%/(30%+30%)=50%, B'=50%, C'=0%

Complexity: O(m) where m = number of stocks
Testing: Pure function, easy to test with examples
Side-Effects: None (returns new dict)
Dependency: logging only
```

---

### Function 5: execute_initial_purchases()
```
Purpose: Execute first-day stock purchases (lump_sum or DCA initial)
Lines: 310-337 (28 lines)

Input:
  - current_date: pd.Timestamp
  - stock_amounts: Dict[str, float]  (total investment amount per stock)
  - current_prices: Dict[str, float]  (USD prices by unique_key)
  - dca_info: Dict[str, Dict]  (with investment_type, monthly_amount)
  - shares: Dict[str, float]  (MODIFIED - updated with purchased shares)
  - commission: float  (e.g., 0.002 = 0.2%)

Output:
  - trades_executed: int
  - daily_cash_inflow: float

Key Logic:
  1. For each stock in stock_amounts:
     - Skip if price not available
     - If investment_type == 'lump_sum':
       * invest_amount = amount * (1 - commission)
       * shares[unique_key] = invest_amount / price
     - Else (DCA):
       * invest_amount = monthly_amount * (1 - commission)
       * shares[unique_key] = invest_amount / price
     - Increment trades_executed
     - Add to daily_cash_inflow

Complexity: O(m) where m = number of stocks
Testing: Can mock current_prices, dca_info
Side-Effects: Yes (modifies shares dict)
```

---

### Function 6: execute_periodic_dca_purchases()
```
Purpose: Execute periodic DCA investments on schedule
Lines: 341-402 (62 lines)

Input:
  - current_date: pd.Timestamp
  - prev_date: pd.Timestamp
  - stock_amounts: Dict[str, float]
  - current_prices: Dict[str, float]
  - dca_info: Dict[str, Dict]  (MODIFIED - executed_count, last_dca_date)
  - shares: Dict[str, float]  (MODIFIED - accumulated shares)
  - commission: float
  - start_date_obj: datetime

Output:
  - trades_executed: int
  - daily_cash_inflow: float

Key Logic:
  1. For each stock with investment_type == 'dca':
     - Initialize original_nth_weekday on first run
     - Calculate next_dca_date using get_next_nth_weekday()
     - Check: current_date >= next_dca_date AND prev_date < next_dca_date?
       * If yes AND executed_count < dca_periods:
         * price = current_prices[symbol]
         * invest_amount = monthly_amount * (1 - commission)
         * shares[symbol] += invest_amount / price
         * Update dca_info[symbol]:
           - executed_count += 1
           - last_dca_date = current_date
         * Increment trades_executed

Complexity: O(m) where m = number of stocks
Testing: Requires mocking dates and get_next_nth_weekday()
Side-Effects: Yes (modifies dca_info, shares)
Dependencies: get_next_nth_weekday(), get_weekday_occurrence(), FREQUENCY_MAP
```

---

### Function 7: execute_rebalancing_trades()
```
Purpose: Execute rebalancing trades and record history
Lines: 495-648 (154 lines) [LARGEST AND MOST COMPLEX]

Input:
  - current_date: pd.Timestamp
  - adjusted_target_weights: Dict[str, float]
  - shares: Dict[str, float]  (MODIFIED)
  - current_prices: Dict[str, float]
  - available_cash: float  (MODIFIED)
  - cash_holdings: Dict[str, float]  (MODIFIED)
  - cash_amounts: Dict[str, float]  (for reference)
  - commission: float
  - total_stock_value: float  (pre-calculated)
  - dca_info: Dict[str, Dict]  (for asset_type, symbol lookup)
  - delisted_stocks: Set[str]  (skip these in trading)

Output Dict:
  - trades_executed: int
  - rebalance_trades: List[Dict]  (trade records for history)
  - weights_before: Dict[str, float]  (pre-rebalance allocations)
  - weights_after: Dict[str, float]  (post-rebalance allocations)
  - commission_cost: float  (total cost)

Key Logic:
  1. Calculate weights_before from current shares & cash
  2. For each (unique_key, target_weight) in adjusted_target_weights:
     - target_value = total_portfolio_value * target_weight
     - If asset_type == 'cash':
       * Adjust cash_holdings[unique_key] to target_value
       * Track trade if diff > threshold
     - Else:
       * If delisted: skip (maintain current holdings)
       * Else:
         * Calculate shares_diff needed
         * Record BUY/SELL trade
         * Apply commission
  3. After all trades:
     - Apply commission scaling: shares *= (1 - total_commission_cost/total_value)
  4. Calculate weights_after
  5. Record in rebalance_history

Complexity: O(m²) worst case (m iterations × m stock checks for delisting)
Testing: Very difficult - many dependencies, side-effects
Side-Effects: Yes (modifies shares, cash_holdings, available_cash, history lists)
⚠️ CRITICAL: This function contains the most complex logic
```

---

### Function 8: calculate_daily_metrics_and_history()
```
Purpose: Calculate daily portfolio metrics and history
Lines: 650-684 (35 lines)

Input:
  - current_date: pd.Timestamp
  - shares: Dict[str, float]  (current holdings)
  - available_cash: float
  - current_prices: Dict[str, float]
  - cash_holdings: Dict[str, float]
  - prev_portfolio_value: float
  - daily_cash_inflow: float  (DCA + rebalancing inflows)
  - total_amount: float  (initial investment)
  - dca_info: Dict[str, Dict]  (for symbol lookup)

Output Tuple:
  - current_portfolio_value: float  (normalized by total_amount)
  - daily_return: float  (percentage change)
  - current_weights: Dict[str, float]  (allocation by symbol)

Key Logic:
  1. Calculate current_portfolio_value:
     - sum(shares[key] * current_prices[key]) + available_cash
  2. Calculate daily_return:
     - If prev_portfolio_value > 0:
       * net_change = current_value - prev_value - daily_cash_inflow
       * daily_return = net_change / prev_value
     - Else: daily_return = 0.0
  3. Calculate current_weights:
     - For each stock: weight = (shares * price) / current_portfolio_value
     - For each cash: weight = amount / current_portfolio_value
     - Handle duplicate symbols by summing weights
  4. Return normalized portfolio_value (divide by total_amount)

Complexity: O(m) where m = number of assets
Testing: Straightforward unit testing
Side-Effects: None (pure calculations)
Dependency: dca_info for symbol lookup
```

---

## KEY ARCHITECTURAL PATTERNS

### 1. Mutable State Pattern
Several functions modify input dictionaries/sets in place:
- `detect_and_update_delisting()`: modifies delisted_stocks, last_valid_prices
- `execute_initial_purchases()`: modifies shares
- `execute_periodic_dca_purchases()`: modifies dca_info, shares
- `execute_rebalancing_trades()`: modifies shares, cash_holdings, available_cash

**Recommendation**: Consider using immutable data structures or returning new dicts for clarity.

### 2. Date-Based Scheduling
- `execute_periodic_dca_purchases()` uses Nth Weekday logic
- `detect_and_update_delisting()` uses day counts
- **Dependencies**: `get_next_nth_weekday()`, `get_weekday_occurrence()`, `FREQUENCY_MAP`

### 3. Fallback Logic
- `fetch_and_convert_prices()` has fallback exchange rate cache
- `detect_and_update_delisting()` uses last_valid_prices as fallback

### 4. Threshold-Based Decisions
- Delisting: 30+ days without price (DELISTING_THRESHOLD_DAYS)
- Rebalancing trades: >0.01% difference (REBALANCING_THRESHOLD_PCT)

---

## RECOMMENDED EXTRACTION ORDER

For minimal complexity and maximum independent testability:

1. **`initialize_portfolio_state()`** ✓ Pure setup, no dependencies
2. **`calculate_adjusted_rebalance_weights()`** ✓ Pure function, single responsibility
3. **`fetch_and_convert_prices()`** Medium complexity, few dependencies
4. **`execute_initial_purchases()`** Modifies shares but simple logic
5. **`calculate_daily_metrics_and_history()`** Pure calculations, stable
6. **`detect_and_update_delisting()`** Side-effects but isolated logic
7. **`execute_periodic_dca_purchases()`** High complexity, date scheduling
8. **`execute_rebalancing_trades()`** ⚠️ Extract LAST (most complex, many dependencies)

---

## REFACTORING IMPACT ANALYSIS

### Code Quality Improvements
- **Cyclomatic Complexity**: 625-line function → 8 focused functions (avg 78 lines)
- **Test Coverage**: Single integration test → 8 unit tests + 1 integration test
- **Readability**: Highly nested code → Clear function names document intent
- **Maintainability**: Single point of change → Isolated, targeted modifications

### Performance Considerations
- **No change**: All operations remain O(n*m) (days × stocks)
- **Potential improvement**: Memoization of currency conversion multipliers
- **Potential improvement**: Vectorization of weight calculations

### Async/Threading Considerations
- **Current**: `fetch_and_convert_prices()` is synchronous (pure calc)
- **Optimization**: Could parallelize currency conversion per stock
- **Risk**: Must maintain atomic transaction boundaries for correctness

