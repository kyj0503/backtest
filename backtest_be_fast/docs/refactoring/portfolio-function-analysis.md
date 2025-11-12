# Analysis: calculate_dca_portfolio_returns() Function Structure

**Function Location**: `/home/user/backtest/backtest_be_fast/app/services/portfolio_service.py` (lines 86-709)
**Function Signature**: `async def calculate_dca_portfolio_returns(...) -> pd.DataFrame`

---

## 1. MAIN LOGICAL SECTIONS/PHASES

The function consists of **7 major phases**:

### Phase 1: Setup & Initialization (Lines 115-190)
- **Lines 115-121**: Cash processing (separate cash from stocks)
- **Lines 123-140**: Date range setup and parsing
- **Lines 142-156**: Batch ticker currency retrieval (optimized with `asyncio.to_thread()`)
- **Lines 158-187**: Exchange rate loading for multiple currencies
- **Lines 189-190**: Target weights calculation for rebalancing

**Responsibility**: Prepare all configuration and external data before simulation

---

### Phase 2: Variable Initialization (Lines 191-213)
- Initialize tracking dictionaries: `shares`, `portfolio_values`, `daily_returns`
- Initialize rebalancing state: `last_rebalance_date`, `original_rebalance_nth`
- Initialize delisting detection: `last_valid_prices`, `last_price_date`, `delisted_stocks`

**Responsibility**: Set up state containers for the main simulation loop

---

### Phase 3: MAIN DATE LOOP (Lines 215-684)
**This is the core simulation engine** - processes each trading day in chronological order.

Nested components within the loop:

#### 3a. Date Range Filtering (Lines 217-220)
```python
if current_date.date() < start_date_obj.date():
    continue
if current_date.date() > end_date_obj.date():
    break
```

#### 3b. Price Fetching & Currency Conversion (Lines 222-268)
- Extract raw prices from portfolio_data
- Convert to USD using exchange rates
- Cache last valid exchange rate as fallback

#### 3c. Delisting Detection (Lines 270-307)
- Track stocks with no price data for 30+ days
- Mark as delisted, use last valid price
- Restore if price data reappears

#### 3d. Initial Purchase Execution (Lines 310-337)
**First day only**:
- Execute `lump_sum`: invest full amount immediately
- Execute `dca`: invest first period amount

#### 3e. Periodic DCA Purchases (Lines 341-402)
**For subsequent days**:
- Check if current date matches Nth Weekday schedule
- Execute DCA if within period count
- Update `executed_count`, `last_dca_date`

#### 3f. Rebalancing Logic (Lines 404-648)
**Largest nested block**:
- Lines 406-408: Initialize original_nth on first run
- Lines 410-412: Check if rebalancing should occur
- Lines 427-648: Execute rebalancing if triggered
  - Adjust weights for delisted stocks (lines 428-458)
  - Calculate portfolio value (lines 476-482)
  - Execute trades (lines 502-587)
  - Record history (lines 599-648)

#### 3g. Portfolio Metrics Calculation (Lines 650-684)
- Calculate current portfolio value from shares + cash
- Calculate daily return
- Track weight history for frontend

---

### Phase 4: Result Dataframe Creation (Lines 686-709)
- Validate lengths match
- Create DataFrame with Date, Portfolio_Value, Daily_Return, Cumulative_Return
- Attach metadata as dataframe attributes

---

## 2. LOOP STRUCTURES

### Main Loop (Line 215)
```python
for current_date in date_range:  # O(n) where n = number of trading days
```

**Loop contains 5 nested for-loops**:

1. **Lines 227-268**: For each stock → Get price and convert
2. **Lines 271-299**: For each stock → Detect delisting
3. **Lines 342-402**: For each stock → Check DCA eligibility
4. **Lines 487-490**: For each stock → Calculate weights_before (within rebalancing)
5. **Lines 502-587**: For each unique_key, target_weight pair (within rebalancing)

**Time Complexity**: O(n * m) where n = days, m = number of stocks

---

## 3. NESTED LOGIC BLOCKS

### Most Complex: Rebalancing Block (Lines 427-648)
**Nesting Level: 2 deep** (if rebalance AND portfolio_value > 0)

Structure:
```
if should_rebalance AND len(target_weights) > 1:
    if delisted_stocks:
        [Adjust weights - 27 lines]
    
    if total_portfolio_value > 0:
        for unique_key, target_weight in adjusted_target_weights.items():
            if asset_type == 'cash':
                [Adjust cash holdings]
            else:
                if unique_key in delisted_stocks:
                    [Skip trading]
                else:
                    [Execute trades]
        
        [Update shares with commission scaling]
        [Record rebalance history]
```

### DCA Purchase Block (Lines 341-402)
**Nesting Level: 2 deep** (for loop with conditional execution)

Structure:
```
if prev_date is not None:
    for symbol, _ in stock_amounts.items():
        if investment_type == 'dca':
            if current_date >= next_dca_date AND prev_date < next_dca_date:
                if executed_count < dca_periods:
                    if symbol in current_prices:
                        [Execute purchase]
                    else:
                        [Log warning]
```

---

## 4. EXTRACTION CANDIDATES: 8 HELPER FUNCTIONS

### 1. **initialize_portfolio_state()**
**Purpose**: Set up all tracking variables
**Responsibility**: Initialize empty collections and default values
**Lines in Original**: 191-213

**Input Parameters**:
- `stock_amounts: Dict[str, float]`
- `cash_amount: float`
- `amounts: Dict[str, float]`

**Return Type**:
```python
Dict[str, Any] with keys:
- shares: Dict[str, float]
- portfolio_values: List[float]
- daily_returns: List[float]
- rebalance_history: List[Dict]
- weight_history: List[Dict]
- delisted_stocks: Set[str]
- last_valid_prices: Dict[str, float]
- tracking state variables...
```

---

### 2. **fetch_and_convert_prices()**
**Purpose**: Get current prices and convert to USD
**Responsibility**: Extract prices from portfolio data and apply currency conversion
**Lines in Original**: 222-268

**Input Parameters**:
- `current_date: pd.Timestamp`
- `stock_amounts: Dict[str, float]`
- `portfolio_data: Dict[str, pd.DataFrame]`
- `dca_info: Dict[str, Dict]`
- `ticker_currencies: Dict[str, str]`
- `exchange_rates_by_currency: Dict[str, Dict[date, float]]`

**Return Type**:
```python
Tuple[
    Dict[str, float],  # current_prices
    Dict[str, float]   # last_valid_exchange_rates (cache)
]
```

---

### 3. **detect_and_update_delisting()**
**Purpose**: Detect delisted stocks and maintain their pricing
**Responsibility**: Track price absence, update delisted_stocks set
**Lines in Original**: 270-307

**Input Parameters**:
- `current_date: pd.Timestamp`
- `stock_amounts: Dict[str, float]`
- `current_prices: Dict[str, float]`
- `dca_info: Dict[str, Dict]`
- `delisted_stocks: Set[str]` (will be modified)
- `last_valid_prices: Dict[str, float]` (will be modified)
- `last_price_date: Dict[str, date]` (will be modified)

**Return Type**:
```python
None  # Modifies sets/dicts in place
```

---

### 4. **execute_initial_purchases()**
**Purpose**: Execute first-day purchases (lump_sum or DCA initial)
**Responsibility**: Calculate shares from amounts and prices
**Lines in Original**: 310-337

**Input Parameters**:
- `current_date: pd.Timestamp`
- `stock_amounts: Dict[str, float]`
- `current_prices: Dict[str, float]`
- `dca_info: Dict[str, Dict]`
- `shares: Dict[str, float]` (will be modified)
- `commission: float`

**Return Type**:
```python
Tuple[
    int,      # trades executed
    float     # daily_cash_inflow
]
```

---

### 5. **execute_periodic_dca_purchases()**
**Purpose**: Execute subsequent periodic DCA purchases
**Responsibility**: Check schedule and execute DCA on matching dates
**Lines in Original**: 341-402

**Input Parameters**:
- `current_date: pd.Timestamp`
- `prev_date: pd.Timestamp`
- `stock_amounts: Dict[str, float]`
- `current_prices: Dict[str, float]`
- `dca_info: Dict[str, Dict]` (will be modified for execution tracking)
- `shares: Dict[str, float]` (will be modified)
- `commission: float`
- `start_date_obj: datetime`

**Return Type**:
```python
Tuple[
    int,      # trades executed
    float     # daily_cash_inflow
]
```

---

### 6. **calculate_adjusted_rebalance_weights()**
**Purpose**: Adjust target weights for delisted stocks
**Responsibility**: Proportionally redistribute weights away from delisted stocks
**Lines in Original**: 428-458

**Input Parameters**:
- `target_weights: Dict[str, float]`
- `delisted_stocks: Set[str]`
- `dca_info: Dict[str, Dict]`

**Return Type**:
```python
Dict[str, float]  # adjusted_target_weights
```

---

### 7. **execute_rebalancing_trades()**
**Purpose**: Execute rebalancing trades and update positions
**Responsibility**: Calculate new share quantities, apply commission, track trades
**Lines in Original**: 495-648

**Input Parameters**:
- `current_date: pd.Timestamp`
- `adjusted_target_weights: Dict[str, float]`
- `shares: Dict[str, float]` (will be modified)
- `current_prices: Dict[str, float]`
- `available_cash: float` (will be modified)
- `cash_holdings: Dict[str, float]` (will be modified)
- `cash_amounts: Dict[str, float]`
- `commission: float`
- `total_stock_value: float`
- `dca_info: Dict[str, Dict]`
- `delisted_stocks: Set[str]`

**Return Type**:
```python
Dict[str, Any] with keys:
- trades_executed: int
- rebalance_trades: List[Dict]  # trade records
- weights_before: Dict[str, float]
- weights_after: Dict[str, float]
- commission_cost: float
```

---

### 8. **calculate_daily_metrics_and_history()**
**Purpose**: Calculate daily portfolio metrics and record history
**Responsibility**: Portfolio value, daily return, weight tracking
**Lines in Original**: 650-684

**Input Parameters**:
- `current_date: pd.Timestamp`
- `shares: Dict[str, float]`
- `available_cash: float`
- `current_prices: Dict[str, float]`
- `cash_holdings: Dict[str, float]`
- `prev_portfolio_value: float`
- `daily_cash_inflow: float`
- `total_amount: float`
- `dca_info: Dict[str, Dict]`

**Return Type**:
```python
Tuple[
    float,           # current_portfolio_value
    float,           # daily_return
    Dict[str, float] # current_weights
]
```

---

## REFACTORING SUMMARY

### Before Refactoring
- **Single function**: 625 lines
- **Max nesting depth**: 3 levels (loops + conditionals)
- **Cognitive complexity**: Very high
- **Code reusability**: None
- **Testing difficulty**: Requires full integration test

### After Refactoring
- **Main function**: ~150 lines (setup + loop orchestration)
- **Helper functions**: 8 focused, single-responsibility functions
- **Max nesting depth**: 1-2 levels per helper
- **Code reusability**: Each helper can be tested independently
- **Testing**: Unit tests for each helper + integration tests

### Extraction Order (Recommended)
1. `initialize_portfolio_state()` - Most straightforward
2. `fetch_and_convert_prices()` - Independent operation
3. `detect_and_update_delisting()` - Independent side-effects
4. `calculate_adjusted_rebalance_weights()` - Pure function
5. `execute_initial_purchases()` - Modifies shared state
6. `execute_periodic_dca_purchases()` - Modifies shared state
7. `execute_rebalancing_trades()` - Most complex, many dependencies
8. `calculate_daily_metrics_and_history()` - Final calculation

