# Performance Optimization Plan

## Current Performance Baseline

### Execution Time Breakdown

1. **Cold Cache (first run)**:
   - Data loading: 2-5 seconds (yfinance API)
   - Data validation: 100-200ms
   - Backtest execution: 500ms-2s (depends on data size and strategy)
   - Result serialization: 50-100ms
   - **Total: 3-8 seconds**

2. **Memory Cache Hit (within 1 hour)**:
   - Data loading: <50ms (memory dict lookup)
   - Backtest execution: 500ms-2s
   - Result serialization: 50-100ms
   - **Total: 600ms-2.2 seconds**

3. **MySQL Cache Hit (after 1 hour)**:
   - Data loading: 200-500ms (database query)
   - Backtest execution: 500ms-2s
   - Result serialization: 50-100ms
   - **Total: 750ms-2.6 seconds**

### Performance Bottlenecks

1. **yfinance API** (first load): 60-70% of total time
2. **Backtest execution**: 20-30% of total time
3. **MySQL queries**: 5-10% of total time
4. **Data validation and transformation**: 5-10% of total time

## Optimization Strategies

### 1. Cache Optimization

#### Current State
```python
# data_repository.py:82
self._cache_ttl = 3600  # 1 hour TTL
```

#### Proposed Changes

**A. Increase Memory Cache TTL**

Historical stock data rarely changes. We can safely increase TTL:

```python
# For historical data (dates in past)
self._cache_ttl = 86400  # 24 hours

# For recent data (includes today)
self._cache_ttl = 3600  # 1 hour
```

Implementation:
```python
def _get_cache_ttl(self, end_date) -> int:
    """Determine cache TTL based on date recency"""
    from datetime import date

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    today = date.today()

    # Historical data (ends before today): 24 hour cache
    if end_date < today:
        return 86400

    # Recent data (includes today): 1 hour cache
    return 3600
```

Expected improvement: 10-20% faster for repeated historical backtests

**B. Persistent Cache Warming**

Pre-load popular tickers into memory cache on server startup:

```python
# cache_warmer.py
POPULAR_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
DEFAULT_RANGES = [
    ('2023-01-01', '2023-12-31'),
    ('2022-01-01', '2022-12-31'),
]

async def warm_cache():
    for ticker in POPULAR_TICKERS:
        for start, end in DEFAULT_RANGES:
            try:
                await data_repository.get_stock_data(ticker, start, end)
            except Exception:
                pass
```

Expected improvement: Popular tickers respond instantly (<100ms)

### 2. Database Query Optimization

#### Current MySQL Schema Check

Need to verify indexes exist:

```sql
-- Check current indexes
SHOW INDEX FROM daily_prices;

-- Required indexes
CREATE INDEX idx_ticker_date ON daily_prices(ticker, date);
CREATE INDEX idx_date ON daily_prices(date);
```

Expected improvement: 30-50% faster MySQL cache hits (500ms → 250ms)

### 3. Parallel Data Loading

For portfolio backtests with multiple tickers, load in parallel:

```python
async def load_multiple_tickers(self, tickers, start_date, end_date):
    """Load multiple tickers in parallel"""
    tasks = [
        self.get_stock_data(ticker, start_date, end_date)
        for ticker in tickers
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

Expected improvement: Portfolio backtests 2-3x faster

### 4. Backtest Engine Optimization

#### A. Strategy Parameter Caching

Currently rebuilds strategy class on every request:

```python
# backtest_engine.py:352
configured_name = f"{base_strategy.__name__}Configured_{uuid4().hex[:8]}"
return type(configured_name, (base_strategy,), overrides)
```

Could cache configured strategy classes:

```python
# Add to BacktestEngine
self._strategy_cache = {}

def _build_strategy(self, strategy_name, params):
    cache_key = f"{strategy_name}_{hash(frozenset(params.items()))}"

    if cache_key in self._strategy_cache:
        return self._strategy_cache[cache_key]

    # ... existing logic ...

    self._strategy_cache[cache_key] = configured_class
    return configured_class
```

Expected improvement: 10-50ms saved per backtest

#### B. Result Caching

Cache backtest results for identical requests:

```python
def _generate_cache_key(request: BacktestRequest) -> str:
    """Generate cache key from request parameters"""
    import hashlib
    import json

    data = {
        'ticker': request.ticker,
        'start_date': str(request.start_date),
        'end_date': str(request.end_date),
        'strategy': request.strategy,
        'params': request.strategy_params,
        'cash': request.initial_cash,
        'commission': request.commission,
    }

    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()
```

Expected improvement: Instant response (<50ms) for duplicate requests

### 5. Data Validation Optimization

#### Current Validation

Multiple pandas operations in series:

```python
# data_fetcher.py:215-220
data = data.replace([np.inf, -np.inf], np.nan)
data = data.dropna()
```

#### Optimized Validation

Combine operations:

```python
# Single-pass validation
data = data.replace([np.inf, -np.inf], np.nan).dropna()
```

Expected improvement: 20-30ms saved

### 6. Response Serialization Optimization

#### Current Approach

Convert entire equity curve to dict:

```python
# backtest_engine.py:501-507
equity_curve_dict = {}
for idx, row in equity_curve_df.iterrows():
    date_str = idx.strftime('%Y-%m-%d')
    equity_curve_dict[date_str] = float(row['Equity'])
```

#### Optimized Approach

Use pandas built-in serialization:

```python
# Convert directly to records format
equity_curve_dict = equity_curve_df['Equity'].to_dict()
equity_curve_dict = {
    k.strftime('%Y-%m-%d'): float(v)
    for k, v in equity_curve_dict.items()
}
```

Expected improvement: 20-50ms saved for large datasets

### 7. Connection Pool Tuning

#### MySQL Connection Pool

Check current settings:

```python
# yfinance_db.py
engine = create_engine(
    database_url,
    pool_size=5,        # Default: 5
    max_overflow=10,    # Default: 10
    pool_pre_ping=True,
)
```

Increase for high concurrency:

```python
engine = create_engine(
    database_url,
    pool_size=20,       # Increased
    max_overflow=30,    # Increased
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
)
```

Expected improvement: 10-20% faster under load

## Implementation Priority

### High Priority (Quick Wins)

1. **Increase cache TTL for historical data**: 5 min implementation, 10-20% improvement
2. **Database index verification**: 5 min implementation, 30-50% faster cache hits
3. **Combine pandas operations**: 10 min implementation, 20-30ms saved

Total expected: 15-30% overall speed improvement with 20 minutes work

### Medium Priority (Moderate Effort)

4. **Cache warming for popular tickers**: 1 hour implementation, instant response for popular stocks
5. **Result caching**: 1-2 hours implementation, instant response for duplicate requests
6. **Strategy class caching**: 30 min implementation, 10-50ms per backtest

Total expected: Additional 20-30% improvement with 3-4 hours work

### Low Priority (Major Refactoring)

7. **Parallel portfolio loading**: 2-3 hours implementation, 2-3x faster portfolios
8. **Connection pool tuning**: 30 min implementation, 10-20% under load
9. **Async SQLAlchemy migration**: 8-16 hours, 20-30% faster database operations

## Recommended Implementation Plan

### Phase 1: Quick Wins (Week 1)

Implement items 1-3 from high priority list:
- Expected improvement: 15-30% faster
- Implementation time: 20 minutes
- Risk: Very low

### Phase 2: Caching Layer (Week 2)

Implement items 4-6 from medium priority list:
- Expected improvement: Additional 20-30%
- Implementation time: 3-4 hours
- Risk: Low

### Phase 3: Advanced Optimization (Future)

Implement parallel loading and async database:
- Expected improvement: 2-3x for specific use cases
- Implementation time: 1-2 weeks
- Risk: Medium (requires testing)

## Expected Final Performance

After Phase 1 + Phase 2 implementation:

| Scenario | Current | Optimized | Improvement |
|----------|---------|-----------|-------------|
| Cold cache (first run) | 3-8s | 2-5s | 37-50% |
| Memory cache hit | 600ms-2.2s | 400ms-1.5s | 33-40% |
| MySQL cache hit | 750ms-2.6s | 400ms-1.8s | 46-53% |
| Duplicate request | 600ms-2.2s | <50ms | 95%+ |
| Popular ticker | 3-8s | <100ms | 98%+ |

## Monitoring and Metrics

Add performance logging:

```python
import time

@contextmanager
def timer(operation_name):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info(f"{operation_name}: {elapsed*1000:.2f}ms")

# Usage
with timer("Data loading"):
    data = await self.get_stock_data(ticker, start, end)

with timer("Backtest execution"):
    result = bt.run()
```

Track key metrics:
- Cache hit rate (memory/MySQL/miss)
- Average response time per endpoint
- P50, P95, P99 latencies
- Slowest queries

## Conclusion

Realistic improvements achievable:
- **Short term (Phase 1)**: 15-30% faster, 20 min work
- **Medium term (Phase 2)**: 40-60% overall improvement, 4 hours work
- **Long term (Phase 3)**: 2-3x for specific use cases, 1-2 weeks work

Most impactful optimizations are the quick wins in Phase 1, which should be implemented immediately. Phase 2 provides significant additional benefits with moderate effort. Phase 3 should be evaluated based on actual usage patterns and user feedback.
