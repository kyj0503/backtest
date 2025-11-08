# Backend Refactoring Checklist

## Quick Navigation

**Start Here:**
1. Read `REFACTORING_SUMMARY.txt` (5 min) - Overview and timeline
2. Review `REFACTORING_ANALYSIS.md` (20 min) - Detailed issues with line numbers
3. Use this checklist to track progress

---

## Phase 1: Critical Issues (Week 1) - 8 hours total

### 1.1 Extract Strategy Position Sizing Logic
- [ ] Create `app/strategies/base_strategy.py`
- [ ] Add `PositionSizingMixin` class
- [ ] Update all 5 strategy files to inherit from mixin
- [ ] Test each strategy with sample data
- **Files Affected:** `app/strategies/*.py` (5 files)
- **Effort:** 4 hours
- **Verification:** No duplicate position sizing code

### 1.2 Centralize Currency Configuration
- [ ] Create `app/constants/currencies.py`
- [ ] Copy `SUPPORTED_CURRENCIES` dict (once)
- [ ] Update `backtest_engine.py` to import from constants
- [ ] Update `portfolio_service.py` to import from constants
- [ ] Verify exchange rate conversion still works
- **Files Affected:** 2 services + 1 new file
- **Effort:** 1 hour
- **Verification:** Tests pass with unified currency handling

### 1.3 Create Converters Utility Module
- [ ] Create `app/utils/converters.py`
- [ ] Add `safe_float()` function
- [ ] Add `safe_int()` function
- [ ] Update `backtest_engine.py` to import functions
- [ ] Update `validation_service.py` to import functions
- [ ] Update `backtest_service.py` to import functions
- [ ] Remove local implementations
- **Files Affected:** 3 services + 1 new file
- **Effort:** 2 hours
- **Verification:** No duplicate function definitions

### 1.4 Clean Up Unused Imports
- [ ] Run `pylint` on all service files
- [ ] Remove `import signal` from `backtest_engine.py` (line 29)
- [ ] Remove `from decimal import Decimal` (line 37)
- [ ] Remove `import time` from `backtest_service.py`
- [ ] Remove `import traceback` from `backtest_service.py`
- [ ] Verify all tests still pass
- **Files Affected:** 2 services
- **Effort:** 1 hour
- **Verification:** No warnings from linter

---

## Phase 2: Architecture Improvements (Week 2) - 13 hours total

### 2.1 Create DataSource Interface
- [ ] Create `app/interfaces/data_source.py`
- [ ] Define abstract `DataSource` class
- [ ] Implement `YFinanceDataSource` wrapper
- [ ] Implement `CachedDataSource` decorator
- [ ] Update imports in services
- **Files Affected:** 3 new files + multiple services
- **Effort:** 3 hours
- **Verification:** Services use DI, can swap implementations

### 2.2 Implement Dependency Injection Container
- [ ] Create `app/di/container.py`
- [ ] Define `ServiceContainer` class
- [ ] Register all services with proper dependencies
- [ ] Update endpoints to use container
- [ ] Test initialization order
- **Files Affected:** 1 new file + api endpoints
- **Effort:** 3 hours
- **Verification:** No circular imports, clean startup

### 2.3 Split Portfolio Service
- [ ] Create `app/services/dca_service.py`
- [ ] Create `app/services/rebalance_service.py`
- [ ] Create `app/services/portfolio_calculator_service.py`
- [ ] Extract methods from `portfolio_service.py` (lines 95-151, 153-199, 690-752)
- [ ] Create `PortfolioFacade` that orchestrates the above
- [ ] Update API endpoints to use new services
- [ ] Add tests for each new service
- [ ] Verify existing functionality unchanged
- **Files Affected:** portfolio_service.py split into 4 files
- **Effort:** 8 hours
- **Verification:** portfolio_service.py < 500 lines, all tests pass

---

## Phase 3: Robustness (Week 3-4) - 9 hours total

### 3.1 Centralized Exception Handling
- [ ] Create `app/core/exception_handlers.py`
- [ ] Define `EXCEPTION_STATUS_CODES` mapping
- [ ] Add `map_exception_to_status_code()` function
- [ ] Update `backtest_engine.py` error handling (lines 139-165)
- [ ] Update API decorators to use centralized mapping
- [ ] Remove dynamic imports from exception handlers
- [ ] Test all exception paths
- **Files Affected:** 1 new file + 2 services
- **Effort:** 3 hours
- **Verification:** No dynamic imports in exception handlers

### 3.2 Refactor Nested Try-Excepts
- [ ] Extract `_get_ticker_currency()` method
- [ ] Extract `_get_exchange_data()` method
- [ ] Extract `_apply_exchange_rate()` method
- [ ] Rewrite `_convert_to_usd()` with early returns (lines 187-318)
- [ ] Reduce nesting to max 2 levels
- [ ] Test currency conversion with various currencies
- **Files Affected:** backtest_engine.py
- **Effort:** 4 hours
- **Verification:** Method < 100 lines, clear flow

### 3.3 Add Strategy Logging
- [ ] Add logger to each strategy class
- [ ] Log entry signals (crossovers, threshold breaks)
- [ ] Log buy/sell decisions with prices and signals
- [ ] Log position changes and sizes
- [ ] Test logging output
- **Files Affected:** All 5 strategy files
- **Effort:** 2 hours
- **Verification:** Strategy behavior visible in logs

---

## Phase 4: Polish (Week 4-5) - 13 hours total

### 4.1 Add Type Hints
- [ ] Run `mypy` on codebase
- [ ] Add return types to all public methods
- [ ] Add parameter types to all public methods
- [ ] Update complex type hints to use `typing` module
- [ ] Fix `Union[date, str]` inconsistencies
- [ ] Add Optional hints where needed
- [ ] Update README with type hint guidelines
- **Files Affected:** All service and strategy files
- **Effort:** 5 hours
- **Verification:** mypy passes with 0 errors

### 4.2 Replace Monkey Patching
- [ ] Create `app/integrations/backtesting_wrapper.py`
- [ ] Implement `BacktestingWrapper` class
- [ ] Move `_patch_backtesting_stats()` logic into wrapper
- [ ] Remove module-level patch (lines 44-110)
- [ ] Update `backtest_engine.py` to use wrapper
- [ ] Test with various data scenarios
- **Files Affected:** 1 new file + 1 service
- **Effort:** 3 hours
- **Verification:** No monkey patching in codebase

### 4.3 Centralize Configuration
- [ ] Create `app/config/constants.py`
- [ ] Define `StrategyConstants` class
- [ ] Define `DataConstants` class
- [ ] Define `PortfolioConstants` class
- [ ] Update all files to import from config
- [ ] Remove hardcoded values throughout codebase
- **Files Affected:** 1 new file + multiple services
- **Effort:** 3 hours
- **Verification:** All magic numbers removed

### 4.4 Final Testing & Validation
- [ ] Run all unit tests
- [ ] Run all integration tests
- [ ] Check code coverage (target: >70%)
- [ ] Run static analysis tools
- [ ] Manual testing of key features
- [ ] Performance regression testing
- **Effort:** 2 hours
- **Verification:** All tests pass, coverage > 70%

---

## Success Metrics

Track these metrics before and after refactoring:

### Code Quality
- [ ] Code duplication rate: 25% → 5%
- [ ] Average method lines: 180 → 80
- [ ] Cyclomatic complexity: 12 → 7
- [ ] Nesting depth: 5 → 2

### Test Quality
- [ ] Unit test coverage: 30% → 70%
- [ ] Type hint coverage: 20% → 90%
- [ ] Unused import count: 5+ → 0
- [ ] God objects (>500 lines): 1 → 0

### Architecture
- [ ] Circular dependencies: Yes → No
- [ ] Monkey patches: 1 → 0
- [ ] Hardcoded values: 15+ → 0
- [ ] Services using DI: 50% → 100%

---

## Running Tests

```bash
# Unit tests
pytest app/tests/unit -v

# Integration tests
pytest app/tests/integration -v

# Coverage report
pytest --cov=app --cov-report=html

# Static analysis
pylint app/**/*.py
flake8 app/
mypy app/

# Code metrics
radon cc app/ -a
radon mi app/
```

---

## Commit Strategy

Each phase should result in small, focused commits:

```bash
# Phase 1
git commit -m "refactor: extract strategy position sizing mixin"
git commit -m "refactor: centralize currency configuration"
git commit -m "refactor: create converters utility module"
git commit -m "refactor: remove unused imports"

# Phase 2
git commit -m "refactor: create DataSource interface"
git commit -m "refactor: implement dependency injection container"
git commit -m "refactor: split portfolio service into focused classes"

# Phase 3
git commit -m "refactor: centralize exception handling"
git commit -m "refactor: reduce nesting in currency conversion"
git commit -m "refactor: add logging to strategies"

# Phase 4
git commit -m "refactor: add comprehensive type hints"
git commit -m "refactor: replace monkey patching with wrapper"
git commit -m "refactor: centralize configuration values"
git commit -m "test: update tests for refactored code"
```

---

## Risk Mitigation

1. **Backward Compatibility:** All changes are internal refactoring
   - No API changes
   - No behavior changes
   - No configuration changes needed

2. **Testing:** Write tests before and during refactoring
   - Keep existing tests passing
   - Add new tests for extracted components
   - Use integration tests to verify end-to-end flow

3. **Code Review:** Have changes reviewed by team
   - One phase at a time
   - Each PR should be <500 lines
   - Include explanation of changes

4. **Rollback Plan:** Keep original branch until confident
   - Don't delete feature branches
   - Tag release before major changes
   - Keep ability to revert if needed

---

## Key Files to Know

| File | Purpose | Refactoring Impact |
|------|---------|-------------------|
| `app/strategies/*.py` | Trading strategies | HIGH - duplication issue |
| `app/services/portfolio_service.py` | Portfolio logic | HIGH - god object |
| `app/services/backtest_engine.py` | Backtest execution | HIGH - nested code |
| `app/utils/data_fetcher.py` | Data fetching | MEDIUM - tight coupling |
| `app/services/validation_service.py` | Validation logic | MEDIUM - duplicates |
| `app/core/exceptions.py` | Error handling | MEDIUM - inconsistent |
| `app/api/v1/endpoints/backtest.py` | API routes | LOW - mostly clean |

---

## Helpful Commands

```bash
# Find all instances of pattern
grep -r "position_size = 0.95" app/

# Find all imports of a module
grep -r "from app.utils.data_fetcher import" app/

# Count lines in file
wc -l app/services/portfolio_service.py

# List files by size
find app -name "*.py" -exec wc -l {} + | sort -n

# Check for code duplication
pylint --disable=all --enable=duplicate-code app/

# Find unused imports
vulture app/
```

---

## Timeline Summary

| Phase | Focus | Duration | Impact |
|-------|-------|----------|--------|
| Phase 1 | Critical code cleanup | 1 week | 40% improvement |
| Phase 2 | Architecture refactoring | 1 week | 60% improvement |
| Phase 3 | Robustness & logging | 1-2 weeks | 70% improvement |
| Phase 4 | Type hints & polish | 1 week | 100% improvement |
| **Total** | **Full refactoring** | **3-4 weeks** | **40-50% gain** |

---

## Questions?

Refer to:
- `REFACTORING_ANALYSIS.md` for detailed issue descriptions
- `REFACTORING_SUMMARY.txt` for executive overview
- Specific file locations with line numbers provided for each issue
