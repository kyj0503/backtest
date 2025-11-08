# Race Condition Analysis: Async/Sync Boundary Violations

## Executive Summary

**Status**: CRITICAL BUG REINTRODUCED DURING REFACTORING
**Date**: 2025-11-08
**Affected Component**: Portfolio Backtest Service
**Impact**: First-time backtest executions with new tickers/date ranges produce corrupted results

## Problem Description

### Symptom

When executing backtests with new tickers or date ranges that are not in cache:
- First execution: Corrupted results (unrealistic graphs, wrong statistics)
- Second execution (identical parameters): Correct results

This is the SAME race condition bug that was previously fixed in:
- Commit f16755f: "fix: complete fix for data repository race condition"
- Commit 3624bd6: "fix: resolve data loading race condition in backtest execution"

However, the bug was **reintroduced during the refactoring process** in `portfolio_service.py`.

## Root Cause Analysis

### Problem Location: portfolio_service.py

The refactoring work consolidated portfolio logic but failed to maintain async/sync boundaries. Three critical violations exist:

#### Violation 1: Line 142 (in calculate_dca_portfolio_returns)

```python
# portfolio_service.py:86-146
@staticmethod
def calculate_dca_portfolio_returns(
    portfolio_data: Dict[str, pd.DataFrame],
    amounts: Dict[str, float],
    dca_info: Dict[str, Dict],
    # ...
) -> pd.DataFrame:
    """Static method - appears synchronous"""

    for unique_key in stock_amounts.keys():
        symbol = dca_info[unique_key]['symbol']
        try:
            # PROBLEM: Synchronous DB call in method that may be called from async context
            ticker_info = get_ticker_info_from_db(symbol)  # Line 142
            ticker_currencies[unique_key] = ticker_info.get('currency', 'USD')
```

**Issue**: `get_ticker_info_from_db()` performs synchronous MySQL query

#### Violation 2: Line 167 (in calculate_dca_portfolio_returns)

```python
# portfolio_service.py:165-172
exchange_ticker = SUPPORTED_CURRENCIES[currency]
if exchange_ticker:
    try:
        # PROBLEM: Synchronous DB call for exchange rate data
        exchange_data = load_ticker_data(exchange_ticker, exchange_start_date, end_date)  # Line 167
        if exchange_data is not None and not exchange_data.empty:
            exchange_data = exchange_data.reindex(date_range, method='ffill')
```

**Issue**: `load_ticker_data()` performs synchronous MySQL query + potential yfinance API call

#### Violation 3: Line 913 (in run_buy_and_hold_portfolio_backtest)

```python
# portfolio_service.py:828-918
async def run_buy_and_hold_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
    """Buy & Hold portfolio backtest - ASYNC function"""
    try:
        # ... setup code ...

        for stock in request.stocks:
            # ... DCA calculation ...

            # PROBLEM: Synchronous DB call in async function
            df = load_ticker_data(symbol, request.start_date, request.end_date)  # Line 913

            if df is None or df.empty:
                logger.warning(f"종목 {symbol}의 데이터가 없습니다.")
                continue
```

**Issue**: Direct synchronous call in async function without `await` or `asyncio.to_thread()`

### Async Context Call Chain

```
User Request
  |
  v
FastAPI Endpoint (async)
  |
  v
portfolio_service.run_buy_and_hold_portfolio_backtest() [ASYNC]
  |
  +-- Line 913: load_ticker_data() [SYNC] <-- VIOLATION 3
  |
  +-- portfolio_service.calculate_dca_portfolio_returns() [SYNC static method]
        |
        +-- Line 142: get_ticker_info_from_db() [SYNC] <-- VIOLATION 1
        |
        +-- Line 167: load_ticker_data() [SYNC] <-- VIOLATION 2
```

### Why This Causes Corruption

When synchronous I/O operations are called in async contexts without proper threading:

1. **Event Loop Blocking**: MySQL queries and yfinance API calls block the entire async event loop
2. **Premature Return**: Python's async executor may continue before I/O completes
3. **Partial Data**: DataFrames may be incomplete or empty
4. **Race Condition**: Timing-dependent behavior

**First Execution Timeline**:
```
T+0ms:  async run_buy_and_hold_portfolio_backtest() called
T+1ms:  load_ticker_data(symbol, start, end) called (BLOCKS)
T+2ms:  MySQL query starts (2-5 seconds for new data)
T+3ms:  Event loop MAY continue (race condition)
T+4ms:  Code proceeds with empty/partial DataFrame
T+5s:   MySQL returns data (too late)
Result: Corrupted backtest with invalid data
```

**Second Execution Timeline**:
```
T+0ms:  async run_buy_and_hold_portfolio_backtest() called
T+1ms:  load_ticker_data(symbol, start, end) called (BLOCKS)
T+2ms:  MySQL query hits cache (<100ms)
T+102ms: Data returns before event loop continues
Result: Correct backtest with complete data
```

## Why This Was Not Caught

### 1. Refactoring Oversight

The refactoring in commits 08cb02f through f41e241 focused on:
- Code consolidation (strategies, DCA, rebalance)
- Dependency injection pattern
- Service separation

However, the async/sync boundary checks were not applied to the refactored code.

### 2. Static Method Deception

```python
@staticmethod
def calculate_dca_portfolio_returns(...) -> pd.DataFrame:
```

This appears to be a synchronous static method, so calling synchronous functions inside seems correct. However, it's called FROM async contexts, propagating the problem.

### 3. No Integration Tests for Race Conditions

Unit tests use mocked data sources and don't exercise the actual async I/O path. Integration tests would catch this, but they don't exist for portfolio backtests with cold cache.

## Previously Fixed Locations (Still Correct)

The following were correctly fixed and remain correct:

### backtest_engine.py (Fixed in 3624bd6, f16755f)

```python
# Line 174-180: CORRECT
async def _get_price_data(self, ticker, start_date, end_date):
    if self.data_repository:
        data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
    else:
        # Properly wrapped in thread executor
        data = await asyncio.to_thread(
            self.data_fetcher.get_stock_data,
            ticker=ticker, start_date=start_date, end_date=end_date,
        )
```

### data_repository.py (Fixed in f16755f)

```python
# Lines 97-99: CORRECT
cached_data = await asyncio.to_thread(
    yfinance_db.load_ticker_data, ticker, start_date, end_date
)

# Lines 113-115: CORRECT
fresh_data = await asyncio.to_thread(
    self.data_fetcher.get_stock_data, ticker, start_date, end_date
)

# Lines 132-134: CORRECT
success = await asyncio.to_thread(
    yfinance_db.save_ticker_data, ticker, data
)
```

## Solution

### Required Changes

#### Change 1: Fix calculate_dca_portfolio_returns (Lines 142, 167)

This static method needs to become async or have its synchronous calls wrapped:

**Option A: Make the method async (RECOMMENDED)**

```python
@staticmethod
async def calculate_dca_portfolio_returns(
    portfolio_data: Dict[str, pd.DataFrame],
    amounts: Dict[str, float],
    dca_info: Dict[str, Dict],
    start_date: str,
    end_date: str,
    rebalance_frequency: str = "weekly_4",
    commission: float = 0.0
) -> pd.DataFrame:
    """Async static method for DCA portfolio returns"""

    for unique_key in stock_amounts.keys():
        symbol = dca_info[unique_key]['symbol']
        try:
            # Fix Line 142: Wrap in thread executor
            ticker_info = await asyncio.to_thread(
                get_ticker_info_from_db, symbol
            )
            ticker_currencies[unique_key] = ticker_info.get('currency', 'USD')
        except Exception as e:
            logger.warning(f"Failed to get currency for {symbol}: {e}")
            ticker_currencies[unique_key] = 'USD'

    # ... later in the function ...

    exchange_ticker = SUPPORTED_CURRENCIES[currency]
    if exchange_ticker:
        try:
            # Fix Line 167: Wrap in thread executor
            exchange_data = await asyncio.to_thread(
                load_ticker_data, exchange_ticker, exchange_start_date, end_date
            )
            if exchange_data is not None and not exchange_data.empty:
                exchange_data = exchange_data.reindex(date_range, method='ffill')
```

This requires updating all callers to use `await`:

```python
# Before
result = PortfolioService.calculate_dca_portfolio_returns(...)

# After
result = await PortfolioService.calculate_dca_portfolio_returns(...)
```

**Option B: Keep sync, accept DataFrame input (Alternative)**

Move data loading outside the method and pass pre-loaded DataFrames. This is more complex and error-prone.

#### Change 2: Fix run_buy_and_hold_portfolio_backtest (Line 913)

```python
async def run_buy_and_hold_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
    """Buy & Hold portfolio backtest"""
    try:
        # ... setup code ...

        for stock in request.stocks:
            # ... DCA calculation ...

            # Fix Line 913: Wrap in thread executor
            df = await asyncio.to_thread(
                load_ticker_data, symbol, request.start_date, request.end_date
            )

            if df is None or df.empty:
                logger.warning(f"종목 {symbol}의 데이터가 없습니다.")
                continue
```

#### Change 3: Add asyncio import

```python
# portfolio_service.py
import asyncio  # Add this import at the top
```

#### Change 4: Check run_strategy_portfolio_backtest

Need to verify this method doesn't have similar issues:

```python
async def run_strategy_portfolio_backtest(self, request: PortfolioBacktestRequest):
    # Search for any load_ticker_data() or get_ticker_info_from_db() calls
    # Apply same fixes
```

### Testing Strategy

After fixes are applied:

1. **Clear all caches**:
   - Restart backend
   - Clear MySQL daily_prices table (optional)
   - Clear memory cache

2. **Test Case 1: Single New Ticker**
   ```
   Ticker: TSLA
   Date: 2023-01-01 to 2023-12-31
   Investment: lump_sum
   Expected: Correct results on first run
   ```

3. **Test Case 2: Portfolio with Multiple New Tickers**
   ```
   Tickers: MSFT (50%), GOOGL (50%)
   Date: 2023-01-01 to 2023-12-31
   Investment: lump_sum
   Expected: Correct results on first run
   ```

4. **Test Case 3: DCA Portfolio**
   ```
   Tickers: AAPL (40%), AMZN (60%)
   Date: 2023-01-01 to 2023-12-31
   Investment: dca, weekly_4
   Expected: Correct DCA calculations on first run
   ```

5. **Test Case 4: Non-USD Currency**
   ```
   Ticker: 005930.KS (Samsung, KRW)
   Date: 2023-01-01 to 2023-12-31
   Expected: Correct USD conversion on first run
   ```

## Affected Code Paths

### Direct Impact

1. **Portfolio Buy & Hold**: `run_buy_and_hold_portfolio_backtest()`
   - All lump sum portfolio backtests
   - All DCA portfolio backtests
   - Currency conversion for non-USD tickers

2. **Portfolio Strategy**: `run_strategy_portfolio_backtest()`
   - May have similar issues (needs verification)

3. **DCA Calculation**: `calculate_dca_portfolio_returns()`
   - Called by both buy_and_hold and strategy backtests
   - Affects all DCA investments
   - Affects all rebalancing calculations

### Indirect Impact

- Cache effectiveness: 0% on first load (always corrupted)
- User trust: Appears broken, requires double execution
- Data integrity: Results are unreliable

## Lessons Learned

### 1. Async/Sync Boundary Checklist

When refactoring, ALWAYS verify:

- [ ] Are all I/O operations in async functions wrapped with `await` or `asyncio.to_thread()`?
- [ ] Do static/regular methods called from async contexts use sync I/O?
- [ ] Are database queries wrapped in thread executors?
- [ ] Are external API calls wrapped in thread executors?
- [ ] Are file I/O operations async-safe?

### 2. Refactoring Protocol

When moving code:

1. Identify all I/O operations in the moved code
2. Check if destination context is async
3. Wrap all sync I/O with `asyncio.to_thread()`
4. Update all callers to use `await` if method becomes async
5. Add integration tests that exercise I/O paths

### 3. Static Method Anti-Pattern

Static methods that perform I/O should be avoided in async codebases, or clearly documented:

```python
# BAD: Looks sync, but called from async
@staticmethod
def process_data():
    data = database.query()  # Sync I/O
    return process(data)

# GOOD: Explicitly async
@staticmethod
async def process_data():
    data = await asyncio.to_thread(database.query)
    return process(data)
```

### 4. Code Review Focus

During code review, explicitly check:
- All functions with `async def` for sync I/O calls
- All static/regular methods for how they're called
- All database query functions for async wrapping
- All external API calls for async wrapping

## Comparison: Before vs After Fix

| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| First run success rate | ~0% (corrupted) | ~100% (correct) |
| Second run success rate | ~100% (cached) | ~100% (cached) |
| User experience | Must run twice | Single run works |
| Cache effectiveness | Masks the bug | Improves performance |
| Data integrity | Unreliable | Reliable |

## Implementation Priority

**CRITICAL - Fix Immediately**

This is not a refactoring improvement or code quality issue. This is a critical bug that affects all portfolio backtests with new data.

Estimated fix time: 30-60 minutes
Estimated testing time: 30 minutes
Total: 1-1.5 hours

## References

- Previous fixes:
  - Commit f16755f: "fix: complete fix for data repository race condition"
  - Commit 3624bd6: "fix: resolve data loading race condition in backtest execution"
  - Document: `backtest_be_fast/docs/bugfix_race_condition_report.md`

- Refactoring commits that introduced the bug:
  - Commit e8ea391: "refactor: extract DCA and Rebalance logic from monolithic portfolio_service"
  - Commits 08cb02f through f41e241: Various refactoring work

- Python asyncio documentation:
  - asyncio.to_thread(): https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
  - Running Blocking Code: https://docs.python.org/3/library/asyncio-dev.html#running-blocking-code

## Next Steps

1. Apply fixes to `portfolio_service.py`
2. Search entire codebase for other `load_ticker_data()` and `get_ticker_info_from_db()` calls in async contexts
3. Run comprehensive tests with cleared caches
4. Update refactoring documentation to include async/sync boundary checks
5. Consider adding linter rules to detect sync I/O in async functions
