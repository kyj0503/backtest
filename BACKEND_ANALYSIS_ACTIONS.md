# Backend Analysis - Detailed Action Items

## CRITICAL: FIX IMMEDIATELY (< 1 hour)

### Action 1: Fix Async/Sync Boundary in backtest_engine.py
**File**: `/home/user/backtest/backtest_be_fast/app/services/backtest_engine.py`
**Lines**: 418-424
**Severity**: CRITICAL (P0)

**Current Code**:
```python
418 | if getattr(request, 'benchmark_ticker', None):
419 |     try:
420 |         benchmark = self.data_fetcher.get_stock_data(  # ❌ BLOCKING CALL
421 |             ticker=request.benchmark_ticker,
422 |             start_date=start_date,
423 |             end_date=end_date
424 |         )
```

**Fixed Code**:
```python
if getattr(request, 'benchmark_ticker', None):
    try:
        benchmark = await asyncio.to_thread(  # ✅ Wrap in thread pool
            self.data_fetcher.get_stock_data,
            ticker=request.benchmark_ticker,
            start_date=start_date,
            end_date=end_date
        )
```

**Testing**:
```bash
# Test with benchmark_ticker parameter
curl -X POST http://localhost:8000/api/v1/backtest \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","start_date":"2023-01-01","end_date":"2023-12-31","benchmark_ticker":"^GSPC"}'
```

---

### Action 2: Fix Variable Name Collision in portfolio_service.py
**File**: `/home/user/backtest/backtest_be_fast/app/services/portfolio_service.py`
**Lines**: 323-327
**Severity**: HIGH (P1)

**Current Code**:
```python
323 | for symbol, amount in stock_amounts.items():  # ❌ Wrong variable name
324 |     if symbol not in dca_info:
325 |         logger.error(f"DCA 정보 없음: {symbol}")
326 |         continue
327 |
328 |     info = dca_info[symbol]  # ❌ KeyError when symbol has duplicates
```

**Fixed Code**:
```python
for unique_key, amount in stock_amounts.items():  # ✅ Correct variable
    if unique_key not in dca_info:
        logger.error(f"DCA 정보 없음: {unique_key}")
        continue
    
    info = dca_info[unique_key]  # ✅ Correct lookup
    symbol = info['symbol']  # Get actual symbol
```

**Testing**:
```python
# Test DCA calculation with duplicate stocks
request = {
    "portfolio": [
        {"symbol": "AAPL", "amount": 5000, "investment_type": "dca"},
        {"symbol": "AAPL", "amount": 5000, "investment_type": "dca"}  # Duplicate
    ]
}
# Should not raise KeyError
```

---

## HIGH PRIORITY: FIX WITHIN WEEK 1 (< 2 hours each)

### Action 3: Extract Safe Type Converters to Utils
**Files to Modify**: 
- `/home/user/backtest/backtest_be_fast/app/services/chart_data_service.py`
- `/home/user/backtest/backtest_be_fast/app/services/backtest_engine.py`

**Steps**:

1. Create new file `app/utils/type_converters.py`:
```python
"""Type conversion utilities for safe value handling"""
import pandas as pd
import numpy as np
from typing import Any

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, returning default on failure"""
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int, returning default on failure"""
    try:
        if pd.isna(value) or value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_str(value: Any, default: str = "") -> str:
    """Safely convert value to string"""
    try:
        if value is None:
            return default
        return str(value)
    except Exception:
        return default
```

2. Remove methods from `chart_data_service.py` (lines 623-639)

3. Update `chart_data_service.py`:
```python
# Add import
from app.utils.type_converters import safe_float, safe_int

# Remove self.safe_float = ... and self.safe_int = ... methods
# Update calls from self.safe_float() to safe_float()
```

4. Update `backtest_engine.py`:
```python
# Add import
from app.utils.type_converters import safe_float, safe_int

# Remove the nested function definitions (lines 368-384)
# Update calls from safe_float(key) to safe_float(stats.get(key))
```

**Verification**:
```bash
cd /home/user/backtest/backtest_be_fast
pytest tests/unit/test_type_converters.py -v
```

---

### Action 4: Consolidate Data Fetching Pattern
**Files to Modify**:
- `/home/user/backtest/backtest_be_fast/app/services/backtest_engine.py`
- `/home/user/backtest/backtest_be_fast/app/services/chart_data_service.py`
- `/home/user/backtest/backtest_be_fast/app/utils/currency_converter.py`

**Steps**:

1. Create `app/services/base_async_service.py`:
```python
"""Base class for async services with common patterns"""
import asyncio
import pandas as pd
from typing import Optional

class BaseAsyncService:
    def __init__(self, data_repository=None, data_fetcher=None):
        self.data_repository = data_repository
        self.data_fetcher = data_fetcher
    
    async def get_or_fetch_stock_data(
        self,
        ticker: str,
        start_date,
        end_date
    ) -> Optional[pd.DataFrame]:
        """
        Get stock data - tries repository first, then fetcher
        
        Returns None if data not found
        """
        if self.data_repository:
            data = await self.data_repository.get_stock_data(
                ticker, start_date, end_date
            )
        else:
            data = await asyncio.to_thread(
                self.data_fetcher.get_stock_data,
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )
        return data if (data is not None and not data.empty) else None
```

2. Update service classes to inherit from `BaseAsyncService`
3. Replace all `_get_price_data()` implementations with call to inherited method

---

### Action 5: Create Error Handler Decorator
**File to Create**: `/home/user/backtest/backtest_be_fast/app/utils/error_handlers.py`

```python
"""Consistent error handling for services"""
import functools
import logging
from typing import Callable, Any
from fastapi import HTTPException
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

def consistent_error_handler(service_name: str):
    """Decorator for consistent error handling across services"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"{service_name}.{func.__name__} validation error: {str(e)}")
                raise HTTPException(status_code=422, detail=str(e))
            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                logger.error(f"{service_name}.{func.__name__} unexpected error: {str(e)}", 
                           exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"{service_name} internal error"
                )
        return wrapper
    return decorator
```

---

## MEDIUM PRIORITY: REFACTORING (Week 1-2)

### Action 6: Refactor Large Function `calculate_dca_portfolio_returns()`
**File**: `/home/user/backtest/backtest_be_fast/app/services/portfolio_service.py`
**Lines**: 93-662

**Breakdown Strategy**:
1. Extract `_load_portfolio_data()` - lines 122-164
2. Extract `_initialize_portfolio()` - lines 176-200
3. Extract `_simulate_daily_iteration()` - lines 202-600
4. Extract `_check_and_process_delisting()` - lines 257-289
5. Extract `_execute_rebalancing()` - lines 386-602
6. Extract `_format_results()` - lines 640-662

**Result Structure**:
```python
async def calculate_dca_portfolio_returns(self, ...):
    # Load data
    portfolio_data, dca_info = await self._load_portfolio_data(...)
    
    # Initialize
    shares, cash = self._initialize_portfolio(...)
    
    # Simulate
    portfolio_values, daily_returns = await self._simulate_daily_iteration(...)
    
    # Format
    result = self._format_results(...)
    
    return result
```

**Testing**:
Each extracted method should have unit tests verifying individual behavior.

---

### Action 7: Add Type Hints to Service Methods
**Files**: All service files
**Priority**: High for critical paths

**Example**:
```python
# Before
async def run_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
    pass

# After
async def run_portfolio_backtest(
    self, 
    request: PortfolioBacktestRequest
) -> PortfolioBacktestResult:
    pass
```

---

## LONG-TERM IMPROVEMENTS (Week 2-3)

### Action 8: Implement Data Source Abstraction
**Files to Create**:
- `/home/user/backtest/backtest_be_fast/app/services/data_sources.py`

**Structure**:
```python
from abc import ABC, abstractmethod
import pandas as pd

class DataSource(ABC):
    @abstractmethod
    async def get_stock_data(self, ticker: str, start_date, end_date) -> pd.DataFrame:
        pass

class YFinanceDataSource(DataSource):
    async def get_stock_data(self, ticker, start_date, end_date):
        return await asyncio.to_thread(
            self.data_fetcher.get_stock_data,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )

class CachedDataSource(DataSource):
    async def get_stock_data(self, ticker, start_date, end_date):
        return await self.data_repository.get_stock_data(ticker, start_date, end_date)

class CompositeDataSource(DataSource):
    # Cache-first strategy
```

---

### Action 9: Refactor Portfolio Service into Smaller Classes
**New Files to Create**:
- `portfolio_dca_calculator.py`
- `portfolio_rebalancer.py`
- `portfolio_statistics.py`

**Responsibility Distribution**:
- `PortfolioService`: Orchestrator only
- `PortfolioDCACalculator`: DCA logic
- `PortfolioRebalancer`: Rebalancing logic
- `PortfolioStatistics`: Statistics calculation

---

## TESTING CHECKLIST

### Unit Tests to Add
- [ ] `test_safe_float()` in `test_type_converters.py`
- [ ] `test_safe_int()` in `test_type_converters.py`
- [ ] `test_currency_conversion_multiplier()` in `test_currency_converter.py`
- [ ] `test_dca_share_calculation()` in `test_dca_calculator.py`
- [ ] `test_rebalancing_weights()` in `test_rebalance_helper.py`

### Integration Tests to Verify
- [ ] Portfolio backtest with benchmark ticker (Action 1 test)
- [ ] Portfolio backtest with duplicate stocks (Action 2 test)
- [ ] Multi-currency portfolio conversion
- [ ] DCA vs lump-sum comparison
- [ ] Rebalancing execution flow

### Performance Tests
- [ ] Large portfolio (10+ stocks, 10+ years) execution time
- [ ] Memory usage under load
- [ ] Concurrent backtest requests

---

## GIT COMMIT STRATEGY

### Commit 1: Critical Bug Fixes
```bash
git commit -m "fix: Critical async/sync boundary bugs in backtest_engine and portfolio_service

- Fix blocking data_fetcher call without asyncio.to_thread() (P0)
- Fix variable name collision in DCA calculation loop (P1)

Fixes race conditions that could corrupt backtest results"
```

### Commit 2: Code Deduplication
```bash
git commit -m "refactor: Extract duplicate type converters and data fetching patterns

- Create app/utils/type_converters.py with safe_float/safe_int
- Create BaseAsyncService for shared async patterns
- Remove 100+ lines of duplicate code

No functional changes, improves maintainability"
```

### Commit 3: Add Error Handler
```bash
git commit -m "refactor: Implement consistent error handling decorator

- Create app/utils/error_handlers.py
- Apply @consistent_error_handler to service methods
- Standardize error responses across services"
```

---

## VERIFICATION COMMANDS

```bash
# Run all tests
cd /home/user/backtest/backtest_be_fast
pytest -v

# Check code duplication (using radon)
radon cc app/services/ --min B

# Check type hints
mypy app/services/ --ignore-missing-imports

# Check for unused imports
flake8 app/ --select=F401

# Code coverage
pytest --cov=app --cov-report=html
```

---

## TIMELINE ESTIMATE

**Immediate (Today)**: 1 hour
- Action 1: Fix async/sync boundary - 5 min
- Action 2: Fix variable collision - 10 min
- Testing and verification - 45 min

**Week 1**: 6 hours
- Action 3: Extract type converters - 1 hour
- Action 4: Consolidate data fetching - 1.5 hours
- Action 5: Error handler decorator - 1 hour
- Testing and integration - 2.5 hours

**Week 2**: 8 hours
- Action 6: Large function refactoring - 4 hours
- Action 7: Add type hints - 2 hours
- Testing - 2 hours

**Week 3**: 4 hours
- Action 8: Data source abstraction - 2 hours
- Action 9: Split portfolio service - 2 hours

**Total**: 19 hours over 3 weeks

