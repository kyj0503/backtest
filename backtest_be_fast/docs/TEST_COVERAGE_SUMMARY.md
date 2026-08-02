# Unit Test Coverage Summary

## Overview

Comprehensive unit tests have been created for the following backend modules, following pytest best practices with `@pytest.mark.unit` and `@pytest.mark.asyncio` markers. All external I/O (yfinance, DB) is mocked.

**Total Tests Created: 59** (이 문서가 다루는 4개 모듈 기준)

> 현재 `tests/unit` 전체는 **141건**입니다. 이 문서는 아래 4개 모듈에 한정된 보고서이며, 전체 목록은 [UNIT_TEST_QUICK_REFERENCE.md](./UNIT_TEST_QUICK_REFERENCE.md)를 참고하십시오.
**Test Files: 4**
**All Tests: PASSING ✅**

---

## Test Files Created

### 1. tests/unit/test_backtest_engine.py (10 tests)

Tests the core `BacktestEngine` that wraps backtesting.py library.

#### Test Classes:
- **TestBacktestEngineRunBacktest** (3 tests)
  - `test_run_backtest_success_returns_valid_result` - Verifies successful backtest execution returns valid BacktestResult
  - `test_run_backtest_invalid_result_reraises_as_http_exception` - Tests that invalid results (missing '# Trades' key) now raise HTTPException (recent fix)
  - `test_run_backtest_unknown_exception_reraises` - Confirms unknown exceptions are re-raised as HTTP 500

- **TestBacktestEngineBuildStrategy** (3 tests)
  - `test_build_strategy_no_params_returns_base_class` - Returns base strategy when no params provided
  - `test_build_strategy_with_params_applies_overrides` - Applies parameter overrides correctly
  - `test_build_strategy_ignores_non_attribute_params` - Ignores invalid params that don't exist on base class

- **TestBacktestEngineConvertResultToResponse** (2 tests)
  - `test_convert_result_properly_maps_all_stats_fields` - Maps all backtesting.py stats to BacktestResult
  - `test_convert_result_handles_missing_optional_fields` - Handles missing optional fields gracefully with defaults

- **TestBacktestEngineCreateFallbackResult** (2 tests)
  - `test_create_fallback_result_returns_valid_backtest_result` - Returns valid BacktestResult with correct ticker/dates
  - `test_create_fallback_result_handles_exception_gracefully` - Handles exceptions and returns minimal result

#### Key Coverage:
- Successful backtest execution path
- Fallback logic for invalid results
- Strategy parameter overrides
- Stats mapping to response format
- Error handling and re-raising

---

### 2. tests/unit/test_currency_converter.py (19 tests)

Tests the `CurrencyConverter` for multi-currency support (13 currencies including USD, KRW, JPY, EUR, GBP).

#### Test Classes:
- **TestGetConversionMultiplier** (8 tests)
  - `test_eur_returns_exchange_rate_directly` - EUR (USD-quoted) returns rate directly
  - `test_gbp_returns_exchange_rate_directly` - GBP returns rate directly
  - `test_aud_returns_exchange_rate_directly` - AUD returns rate directly
  - `test_cad_returns_exchange_rate_directly` - CAD returns rate directly
  - `test_chf_returns_exchange_rate_directly` - CHF returns rate directly
  - `test_krw_returns_inverse_rate` - KRW (direct quote) returns 1/rate
  - `test_jpy_returns_inverse_rate` - JPY returns 1/rate
  - `test_zero_exchange_rate_returns_one` - Zero rate returns 1.0 to avoid division by zero

- **TestConvertDataframeToUsd** (4 tests)
  - `test_usd_currency_returns_data_unchanged` - USD data returned unchanged
  - `test_krw_converts_correctly_using_vectorized_operation` - KRW conversion uses pandas vectorization
  - `test_unsupported_currency_returns_data_unchanged` - Unsupported currency logs warning, returns original
  - `test_conversion_error_returns_original_data` - Network errors return original data

- **TestLoadAndPrepareExchangeRates** (5 tests)
  - `test_usd_raises_valueerror` - USD raises ValueError (no conversion needed)
  - `test_unsupported_currency_raises_valueerror` - Unsupported currency raises ValueError
  - `test_successful_load_returns_dataframe` - Successful load returns DataFrame with 'Close' column
  - `test_empty_exchange_data_raises_valueerror` - Empty data raises ValueError
  - `test_none_exchange_data_raises_valueerror` - None data raises ValueError

- **TestCurrencyConverterEdgeCases** (2 tests)
  - `test_empty_exchange_data_in_conversion` - Handles empty exchange data gracefully
  - `test_zero_exchange_rate_edge_case` - Zero exchange rate handled safely

#### Key Coverage:
- EUR/GBP (USD-quoted) vs KRW/JPY (direct quote) conversion logic
- Vectorized pandas operations for efficiency
- Error handling and fallback behavior
- Edge cases: zero rates, missing data

---

### 3. tests/unit/test_data_repository.py (14 tests)

Tests the `YfinanceDataRepository` with 3-tier caching: memory (TTLCache) → DB → yfinance.

#### Test Classes:
- **TestYfinanceDataRepositoryGetStockData** (4 tests)
  - `test_memory_cache_hit_returns_cached_data` - Returns from memory cache (TTLCache) when valid
  - `test_memory_miss_db_hit_returns_from_db` - Falls through to DB on memory miss
  - `test_memory_and_db_miss_fetches_from_yfinance` - Falls through to yfinance when both miss
  - `test_db_query_failure_falls_through_to_yfinance` - DB failure doesn't break flow

- **TestYfinanceDataRepositoryInvalidateCache** (2 tests)
  - `test_invalidate_cache_removes_correct_keys` - Removes all keys for a ticker
  - `test_invalidate_cache_handles_nonexistent_ticker` - Handles non-existent ticker gracefully

- **TestYfinanceDataRepositoryTTLCache** (3 tests)
  - `test_ttlcache_initialization_has_correct_params` - TTLCache initialized with maxsize=500, ttl=3600
  - `test_ttlcache_evicts_expired_entries_automatically` - Expired entries auto-evicted
  - `test_ttlcache_maxsize_evicts_oldest_entries` - Maxsize limit evicts LRU entries

- **TestYfinanceDataRepositoryCacheStockData** (3 tests)
  - `test_cache_stock_data_saves_to_db_successfully` - Saves to DB and returns True
  - `test_cache_stock_data_returns_false_on_zero_rows` - Returns False when no rows saved
  - `test_cache_stock_data_handles_exception` - Handles exceptions gracefully

- **TestYfinanceDataRepositoryGetCacheStats** (2 tests)
  - `test_get_cache_stats_returns_memory_stats` - Returns memory cache stats
  - `test_get_cache_stats_includes_mysql_placeholder` - Includes MySQL cache placeholder

#### Key Coverage:
- 3-tier caching strategy (memory → DB → yfinance)
- TTLCache automatic expiration and LRU eviction
- Cache invalidation logic
- Error handling and fallback behavior
- Cache statistics

---

### 4. tests/unit/test_portfolio_manager_helpers.py (16 tests)

Tests static helper methods in `PortfolioManagerService` (pure functions, no I/O).

#### Test Classes:
- **TestCalculateWeightedStats** (4 tests)
  - `test_calculate_weighted_stats_with_valid_portfolio` - Correct weighted averages from portfolio results
  - `test_calculate_weighted_stats_with_three_assets` - Weighted stats with three assets
  - `test_calculate_weighted_stats_with_missing_fields` - Missing fields default to 0
  - `test_calculate_weighted_stats_with_equal_weights` - Equal weights produce simple average

- **TestCalculateDailyReturnStats** (5 tests)
  - `test_calculate_daily_return_stats_with_mixed_returns` - Correct volatility, profit factor from mixed returns
  - `test_calculate_daily_return_stats_all_positive` - All positive returns handled correctly
  - `test_calculate_daily_return_stats_all_negative` - All negative returns handled correctly
  - `test_calculate_daily_return_stats_single_return` - Single return edge case (volatility = 0)
  - `test_calculate_daily_return_stats_with_zeros` - Zero returns don't count as positive/negative

- **TestFormatIndividualResultsList** (7 tests)
  - `test_format_strategy_mode_returns_correct_structure` - Correct format for 'strategy' mode
  - `test_format_buy_hold_mode_returns_correct_structure` - Correct format for 'buy_hold' mode
  - `test_format_buy_hold_mode_with_negative_return` - Negative return handled correctly
  - `test_format_buy_hold_mode_with_cash` - Cash asset handled correctly
  - `test_format_strategy_mode_without_portfolio_results` - Sharpe defaults to 0 when no portfolio_results
  - `test_format_empty_individual_returns` - Empty input returns empty list
  - `test_format_multiple_assets_preserves_all` - All assets preserved in output

#### Key Coverage:
- Weighted statistics calculations
- Daily return statistics (volatility, profit factor)
- Individual results formatting for both strategy and buy_hold modes
- Edge cases: missing fields, zero returns, empty data

---

## Test Execution

### Run All New Tests:
```bash
# 저장소 루트에서 (이 프로젝트는 Docker로 실행됩니다)
docker compose -f compose.dev.yaml exec backtest-be-fast \
  pytest tests/unit/test_backtest_engine.py \
         tests/unit/test_currency_converter.py \
         tests/unit/test_data_repository.py \
         tests/unit/test_portfolio_manager_helpers.py \
         -v --tb=short
```

### Results:
```
======================== 59 passed, 2 warnings in 0.39s ========================
```

---

## Testing Patterns Used

### 1. Pytest Markers
- `@pytest.mark.unit` - Fast, isolated tests with no external dependencies
- `@pytest.mark.asyncio` - Async tests with strict mode

### 2. Fixtures
- `@pytest.fixture` for reusable test data
- Mock objects for external dependencies (data_repository, yfinance, DB)
- Sample data generators (DataFrames, dates, prices)

### 3. Mocking Strategy
- `unittest.mock.Mock` for synchronous dependencies
- `unittest.mock.AsyncMock` for async dependencies
- `patch` decorator for temporary mocking
- All external I/O mocked (yfinance, DB, file I/O)

### 4. Assertions
- Direct equality checks (`assert x == y`)
- `pytest.approx()` for floating-point comparisons
- `pytest.raises()` for exception testing
- `pd.testing.assert_frame_equal()` for DataFrame comparisons

### 5. Test Organization
- Test classes group related tests
- Descriptive test names following pattern: `test_<method>_<scenario>_<expected>`
- Docstrings explain test purpose

---

## Code Coverage

### Modules Tested:
1. `app/services/backtest_engine.py`
   - `run_backtest()` - Main execution flow
   - `_build_strategy()` - Strategy parameter overrides
   - `_convert_result_to_response()` - Stats mapping
   - `_create_fallback_result()` - Fallback generation

2. `app/utils/currency_converter.py`
   - `get_conversion_multiplier()` - Currency-specific multipliers
   - `convert_dataframe_to_usd()` - Vectorized conversion
   - `load_and_prepare_exchange_rates()` - Exchange rate loading

3. `app/repositories/data_repository.py`
   - `get_stock_data()` - 3-tier caching strategy
   - `invalidate_cache()` - Cache invalidation
   - `cache_stock_data()` - DB caching
   - `get_cache_stats()` - Cache statistics

4. `app/services/portfolio_manager_service.py`
   - `_calculate_weighted_stats()` - Weighted averages
   - `_calculate_daily_return_stats()` - Volatility, profit factor
   - `_format_individual_results_list()` - Result formatting

### Coverage Highlights:
- ✅ Happy path scenarios
- ✅ Error handling and exceptions
- ✅ Edge cases (empty data, zero values, None)
- ✅ Async/sync boundary handling
- ✅ TTLCache behavior (expiration, LRU eviction)
- ✅ Currency conversion logic (13 currencies)
- ✅ Fallback mechanisms

---

## Key Testing Principles Applied

1. **Unit Testing Best Practices**
   - Tests are fast (<0.5s total for these 59 tests; 전체 141건도 0.5초 내)
   - Tests are isolated (no shared state)
   - Tests are deterministic (no random data)
   - Each test has a single responsibility

2. **Mocking External Dependencies**
   - All database calls mocked
   - All yfinance API calls mocked
   - All file I/O mocked
   - Tests run without network or DB

3. **Async/Sync Boundary Testing**
   - Tests verify `asyncio.to_thread()` usage
   - Tests use `AsyncMock` for async methods
   - Tests follow `asyncio_mode = strict` from pytest.ini

4. **Recent Bug Fixes Verified**
   - Invalid backtest result now raises HTTPException (not silent fallback)
   - Unknown exceptions re-raised (not caught silently)
   - TTLCache replaces plain dict (automatic expiration)

---

## Next Steps

### Additional Testing (Optional):
1. **Integration Tests** - Test with real DB and API calls (marked with `@pytest.mark.integration`)
2. **Property-Based Tests** - Use Hypothesis for random input testing
3. **Performance Tests** - Verify caching performance improvements
4. **E2E Tests** - Full workflow tests with Playwright

### Test Maintenance:
- Update tests when business logic changes
- Add tests for new features
- Monitor test execution time
- Review test coverage reports with `pytest --cov`

---

## Summary

이 문서가 다루는 4개 모듈의 59건은 모두 통과합니다. `tests/unit` 전체 **141건**도 모두 통과하며, CI의 `Quality Gate` 스테이지(`docker build --target test ./backtest_be_fast`)가 이를 강제합니다. 실패가 보이면 회귀입니다.

**Status: ✅ COMPLETE AND PASSING**
