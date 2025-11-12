# Duplicate Data Loading Functions - Phase 2.2 Analysis Report

## Executive Summary
Found **6 duplicate/overlapping data loading functions** with similar DB-first, yfinance-fallback patterns across the backend codebase. These functions can be consolidated into a single unified interface to reduce code duplication, improve maintainability, and prevent inconsistent behavior.

---

## Function 1: DataService.get_ticker_data() - Async Version

**File**: `/home/user/backtest/backtest_be_fast/app/services/data_service.py` (Lines 57-100)

**Signature**:
```python
async def get_ticker_data(
    self,
    ticker: str,
    start_date: Union[date, str],
    end_date: Union[date, str],
    use_db_first: bool = True
) -> pd.DataFrame
```

**What it does**:
- DB-first strategy with yfinance fallback
- Wraps synchronous calls with `asyncio.to_thread()` for async/sync boundary compliance
- Logs at DEBUG (DB cache hit) and INFO (yfinance fetch) levels
- Raises `DataNotFoundError` on failure

**Implementation Details**:
```python
# 1. Try DB cache (wrapped in asyncio.to_thread)
df = await asyncio.to_thread(load_ticker_data, ticker, start_date, end_date)
if df is not None and not df.empty:
    return df  # Cache hit

# 2. Fallback to yfinance (wrapped in asyncio.to_thread)
df = await asyncio.to_thread(self.data_fetcher.get_stock_data, ticker, start_date, end_date)
if df is None or df.empty:
    raise DataNotFoundError(ticker, str(start_date), str(end_date))
return df
```

**Key Characteristics**:
- Async version
- Uses `asyncio.to_thread()` wrapper for thread-safe sync calls
- Has `use_db_first` flag (default True)
- ~43 lines of code

---

## Function 2: DataService.get_ticker_data_sync() - Sync Version

**File**: `/home/user/backtest/backtest_be_fast/app/services/data_service.py` (Lines 102-135)

**Signature**:
```python
def get_ticker_data_sync(
    self,
    ticker: str,
    start_date: Union[date, str],
    end_date: Union[date, str],
    use_db_first: bool = True
) -> pd.DataFrame
```

**What it does**:
- Identical logic to `get_ticker_data()` but synchronous
- Exists for backward compatibility with legacy code
- Direct calls without `asyncio.to_thread()` wrapper

**Implementation Details**:
```python
# 1. Try DB cache (direct sync call)
df = load_ticker_data(ticker, start_date, end_date)
if df is not None and not df.empty:
    return df  # Cache hit

# 2. Fallback to yfinance (direct sync call)
df = self.data_fetcher.get_stock_data(ticker, start_date, end_date)
if df is None or df.empty:
    raise DataNotFoundError(ticker, str(start_date), str(end_date))
return df
```

**Key Differences from Function 1**:
- Synchronous (no `async`/`await`)
- No `asyncio.to_thread()` wrapping
- Same error handling logic
- ~33 lines of code

**ISSUE**: Duplicates async version exactly - only exists for backward compatibility. Should be unified.

---

## Function 3: BacktestEngine._get_price_data() - Async Version

**File**: `/home/user/backtest/backtest_be_fast/app/services/backtest_engine.py` (Lines 169-187)

**Signature**:
```python
async def _get_price_data(
    self, ticker: str, start_date, end_date
) -> pd.DataFrame
```

**What it does**:
- Uses repository pattern if available, otherwise falls back to data_fetcher
- Returns price data for backtest execution
- Used in `run_backtest()` pipeline (line 89)

**Implementation Details**:
```python
if self.data_repository:
    data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
else:
    # Fallback to data_fetcher with asyncio.to_thread
    data = await asyncio.to_thread(
        self.data_fetcher.get_stock_data,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )

if data is None or data.empty:
    raise HTTPException(status_code=404, detail="가격 데이터를 찾을 수 없습니다.")
return data
```

**Key Characteristics**:
- Async with repository pattern support
- Shorter than DataService version (~19 lines)
- More flexible (repository or fetcher)
- Different error handling (HTTPException vs DataNotFoundError)

**Similarity to Function 1**: 
- Same async/sync boundary handling with `asyncio.to_thread()`
- Same fallback pattern

---

## Function 4: ChartDataService._get_price_data() - Sync Version

**File**: `/home/user/backtest/backtest_be_fast/app/services/chart_data_service.py` (Lines 200-214)

**Signature**:
```python
async def _get_price_data(self, ticker, start_date, end_date) -> pd.DataFrame
```

**What it does**:
- Similar to BacktestEngine._get_price_data() but called from chart data generation pipeline
- Used to fetch data for OHLC, equity, and indicator calculations

**Implementation Details**:
```python
if self.data_repository:
    data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
else:
    # **POTENTIAL BUG**: Direct call without asyncio.to_thread()!
    data = self.data_fetcher.get_stock_data(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )

if data is None or data.empty:
    raise ValidationError(f"'{ticker}' 종목의 가격 데이터를 찾을 수 없습니다.")
return data
```

**CRITICAL ISSUE**: 
- Function signature is `async def` but the fallback case doesn't use `await asyncio.to_thread()`
- This violates CLAUDE.md's critical async/sync boundary management rules
- Can cause race conditions on first execution with synchronous I/O
- ~14 lines of code

**Key Differences from Function 3**:
- Missing `await asyncio.to_thread()` wrapper - **MAJOR BUG**
- Uses `ValidationError` instead of `HTTPException`
- Called from chart generation instead of backtest engine

---

## Function 5: YFinanceDataRepository.get_stock_data() - 3-Layer Cache

**File**: `/home/user/backtest/backtest_be_fast/app/repositories/data_repository.py` (Lines 106-151)

**Signature**:
```python
async def get_stock_data(self, ticker: str, start_date: Union[date, str],
                       end_date: Union[date, str]) -> pd.DataFrame
```

**What it does**:
- Implements 3-layer caching strategy: Memory → MySQL → yfinance
- Uses dynamic TTL (24h for historical, 1h for recent data)
- More sophisticated than other implementations

**Implementation Pipeline**:
```
1. Check memory cache
   ↓ (if miss)
2. Query MySQL (via yfinance_db.load_ticker_data)
   ↓ (if miss)
3. Fetch fresh data (via data_fetcher.get_stock_data)
   ↓
4. Save to memory cache + return
```

**Implementation Details**:
```python
# 1. Memory cache check
if self._is_cache_valid(cache_key, end_date):
    return self._memory_cache[cache_key]['data']

# 2. MySQL cache check (wrapped in asyncio.to_thread)
try:
    cached_data = await asyncio.to_thread(
        yfinance_db.load_ticker_data, ticker, start_date, end_date
    )
    if cached_data is not None and not cached_data.empty:
        self._memory_cache[cache_key] = {...}
        return cached_data
except Exception as e:
    logger.warning(...)

# 3. Fresh fetch from yfinance (wrapped in asyncio.to_thread)
fresh_data = await asyncio.to_thread(
    self.data_fetcher.get_stock_data, ticker, start_date, end_date
)

# 4. Save to cache
await self.cache_stock_data(ticker, fresh_data)
self._memory_cache[cache_key] = {...}
return fresh_data
```

**Key Characteristics**:
- Async with proper `asyncio.to_thread()` wrapping
- Sophisticated caching strategy
- Dynamic TTL based on data recency
- ~45 lines of code
- Part of Repository Pattern implementation

**Key Differences from Functions 1-4**:
- **3-layer caching** (memory + MySQL + API) vs 2-layer
- **Dynamic TTL** instead of fixed cache time
- **Memory cache built-in** vs relying on external sources
- **No separate sync version** - only async

---

## Function 6: yfinance_db._load_ticker_data_internal() - Core DB Logic

**File**: `/home/user/backtest/backtest_be_fast/app/services/yfinance_db.py` (Lines 767-813)

**Signature**:
```python
def _load_ticker_data_internal(ticker: str, start_date=None, end_date=None) -> pd.DataFrame
```

**What it does**:
- **Core internal implementation** for DB-first strategy
- Handles complex flow: normalize dates → ensure stock exists → check coverage → fetch missing → format
- Called by `load_ticker_data()` wrapper (line 278)
- Split into 5 helper functions for SRP:

1. `_normalize_date_params()` (Lines 491-532) - Normalize date formats
2. `_ensure_stock_exists()` (Lines 535-579) - Get or create stock record
3. `_get_date_coverage()` (Lines 582-604) - Check existing data range
4. `_fetch_and_save_missing_data()` (Lines 607-695) - Fill data gaps
5. `_query_and_format_dataframe()` (Lines 698-764) - Format final result

**Complex Pipeline**:
```
1. Normalize date parameters
   ↓
2. Ensure stock exists in DB (fetch from yfinance if needed)
   ↓
3. Query DB for existing data coverage
   ↓
4. Identify missing date ranges
   ↓
5. For each missing range:
   - Try consolidated fetch with padding
   - Fall back to individual range fetches
   ↓
6. Query final date range and format DataFrame
```

**Key Characteristics**:
- Synchronous (used by async callers via `asyncio.to_thread()`)
- **46 lines** in main function + 250+ lines in helpers
- **Most complex data loading implementation**
- Handles gaps intelligently with fallback strategies
- Connection pooling and transaction management

---

## Function 7: yfinance_db.load_ticker_data() - Wrapper with Retries

**File**: `/home/user/backtest/backtest_be_fast/app/services/yfinance_db.py` (Lines 252-302)

**Signature**:
```python
def load_ticker_data(ticker: str, start_date=None, end_date=None, 
                     max_retries: int = 3, retry_delay: float = 2.0) -> pd.DataFrame
```

**What it does**:
- Wrapper around `_load_ticker_data_internal()` with retry logic
- Retries up to 3 times with exponential backoff (2s, 4s, 6s)
- Logs attempts and failures
- ~50 lines including error handling

**Implementation Details**:
```python
for attempt in range(1, max_retries + 1):
    try:
        df = _load_ticker_data_internal(ticker, start_date, end_date)
        if df is not None and not df.empty:
            return df
    except Exception as e:
        last_exception = e
    
    # Progressive backoff
    if attempt < max_retries:
        wait_time = retry_delay * attempt  # 2s, 4s, 6s
        time.sleep(wait_time)

# Raise error after all retries exhausted
raise ValueError(...)
```

---

## Summary Table of Duplicates

| # | Function | File | Lines | Type | Cache Layer | Key Issue |
|---|----------|------|-------|------|-------------|-----------|
| 1 | `DataService.get_ticker_data()` | data_service.py | 57-100 | Async | DB + yfinance | Duplicates with #2 |
| 2 | `DataService.get_ticker_data_sync()` | data_service.py | 102-135 | Sync | DB + yfinance | Duplicates with #1 |
| 3 | `BacktestEngine._get_price_data()` | backtest_engine.py | 169-187 | Async | Repo/yfinance | Similar to #4 |
| 4 | `ChartDataService._get_price_data()` | chart_data_service.py | 200-214 | Async | Repo/yfinance | **Missing asyncio.to_thread()** |
| 5 | `YFinanceDataRepository.get_stock_data()` | data_repository.py | 106-151 | Async | 3-layer cache | Most sophisticated |
| 6 | `yfinance_db._load_ticker_data_internal()` | yfinance_db.py | 767-813 | Sync | DB only | Core implementation |

---

## Code Duplication Metrics

**Total Lines of Data Loading Code**: ~360 lines

**Breakdown by Category**:
- DB-first strategy logic: ~100 lines (Duplicated 4x)
- yfinance fallback: ~60 lines (Duplicated 3x)
- Error handling: ~40 lines (Duplicated 3x)
- Logging: ~30 lines (Duplicated 3x)
- Retry logic: ~50 lines (Unique to yfinance_db)
- Caching logic: ~40 lines (Unique to repository)

**Estimated Reduction Potential**: 40-50% code reduction (140-180 lines)

---

## Consolidation Recommendations

### Recommended Architecture

Create a **unified `DataLoadingService`** that:

1. **Centralizes all loading logic** in one place
2. **Supports both async and sync** via wrapper pattern
3. **Implements 3-layer caching** (memory + DB + API)
4. **Provides consistent error handling**
5. **Handles retries and date normalization**

### Migration Path

**Phase 1 - Create Base Service**:
```python
# app/services/data_loading_service.py
class DataLoadingService:
    async def get_stock_data_async(...)  # Primary async method
    def get_stock_data_sync(...)  # Sync wrapper
    async def _fetch_with_retries(...)  # Common retry logic
    async def _ensure_valid_dates(...)  # Common date normalization
```

**Phase 2 - Migrate Callers**:
- Replace `DataService.get_ticker_data()` with new service
- Replace `BacktestEngine._get_price_data()` with new service
- **Fix ChartDataService._get_price_data()** async/sync boundary issue
- Replace `YFinanceDataRepository` with new service

**Phase 3 - Deprecate Old Functions**:
- Mark functions as deprecated
- Maintain compatibility wrappers for 1-2 releases
- Remove after full migration

---

## Identified Bugs

### Bug 1: ChartDataService._get_price_data() Missing asyncio.to_thread()

**Location**: `/home/user/backtest/backtest_be_fast/app/services/chart_data_service.py`, Line 205

**Issue**: 
```python
# WRONG - This is in an async function but calls sync code directly!
async def _get_price_data(self, ticker, start_date, end_date) -> pd.DataFrame:
    if self.data_repository:
        data = await self.data_repository.get_stock_data(...)  # OK
    else:
        # BUG: Direct sync call in async context!
        data = self.data_fetcher.get_stock_data(...)  # MISSING await asyncio.to_thread()
```

**Impact**: Can cause race conditions and data corruption on first execution

**Fix**:
```python
# CORRECT
data = await asyncio.to_thread(
    self.data_fetcher.get_stock_data,
    ticker=ticker,
    start_date=start_date,
    end_date=end_date
)
```

---

## Files Affected by Duplication

1. **app/services/data_service.py** - Contains 2 duplicate functions
2. **app/services/backtest_engine.py** - Uses data loading (calls _get_price_data)
3. **app/services/chart_data_service.py** - Duplicates backtest_engine logic + has bug
4. **app/repositories/data_repository.py** - Alternative 3-layer implementation
5. **app/services/yfinance_db.py** - Core DB implementation
6. **app/services/unified_data_service.py** - Uses data_service.get_ticker_data_sync()

---

## Conclusion

The backend has **6 overlapping data loading functions** with similar DB-first, yfinance-fallback patterns. These can be consolidated into a single unified service, reducing code duplication by 40-50% and fixing the critical async/sync boundary bug in ChartDataService.

**Priority**: 
1. **CRITICAL**: Fix ChartDataService._get_price_data() async/sync bug
2. **HIGH**: Consolidate data loading functions
3. **MEDIUM**: Clean up yfinance_db.py (keep only core helpers)
