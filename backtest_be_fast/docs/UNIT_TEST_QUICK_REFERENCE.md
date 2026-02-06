# Unit Test Quick Reference

## Quick Commands

### Run All New Unit Tests
```bash
cd /home/coontec/source/backtest/backtest_be_fast
source venv/bin/activate
pytest tests/unit/test_backtest_engine.py \
       tests/unit/test_currency_converter.py \
       tests/unit/test_data_repository.py \
       tests/unit/test_portfolio_manager_helpers.py \
       -v --tb=short
```

### Run Individual Test Files
```bash
# BacktestEngine tests
pytest tests/unit/test_backtest_engine.py -v

# CurrencyConverter tests
pytest tests/unit/test_currency_converter.py -v

# DataRepository tests
pytest tests/unit/test_data_repository.py -v

# PortfolioManager helpers tests
pytest tests/unit/test_portfolio_manager_helpers.py -v
```

### Run Specific Test Class or Method
```bash
# Run specific test class
pytest tests/unit/test_backtest_engine.py::TestBacktestEngineRunBacktest -v

# Run specific test method
pytest tests/unit/test_backtest_engine.py::TestBacktestEngineRunBacktest::test_run_backtest_success_returns_valid_result -v
```

### Run All Unit Tests (Including Existing)
```bash
pytest tests/unit -v
```

### Run with Coverage
```bash
pytest tests/unit/test_backtest_engine.py \
       tests/unit/test_currency_converter.py \
       tests/unit/test_data_repository.py \
       tests/unit/test_portfolio_manager_helpers.py \
       --cov=app --cov-report=html
```

### Run Only Failed Tests
```bash
pytest --lf -v
```

### Run in Watch Mode
```bash
pytest-watch tests/unit
```

---

## Test File Overview

| File | Tests | Coverage |
|------|-------|----------|
| `test_backtest_engine.py` | 10 | BacktestEngine: run_backtest, _build_strategy, _convert_result_to_response, _create_fallback_result |
| `test_currency_converter.py` | 18 | CurrencyConverter: get_conversion_multiplier, convert_dataframe_to_usd, load_and_prepare_exchange_rates |
| `test_data_repository.py` | 17 | YfinanceDataRepository: get_stock_data (3-tier cache), invalidate_cache, TTLCache behavior |
| `test_portfolio_manager_helpers.py` | 14 | PortfolioManagerService: _calculate_weighted_stats, _calculate_daily_return_stats, _format_individual_results_list |

**Total: 59 tests**

---

## Test Class Breakdown

### test_backtest_engine.py
- `TestBacktestEngineRunBacktest` (3 tests) - Main execution flow
- `TestBacktestEngineBuildStrategy` (3 tests) - Strategy parameter overrides
- `TestBacktestEngineConvertResultToResponse` (2 tests) - Stats mapping
- `TestBacktestEngineCreateFallbackResult` (2 tests) - Fallback generation

### test_currency_converter.py
- `TestGetConversionMultiplier` (8 tests) - Currency-specific multipliers
- `TestConvertDataframeToUsd` (4 tests) - Vectorized conversion
- `TestLoadAndPrepareExchangeRates` (4 tests) - Exchange rate loading
- `TestCurrencyConverterEdgeCases` (2 tests) - Edge cases

### test_data_repository.py
- `TestYfinanceDataRepositoryGetStockData` (4 tests) - 3-tier caching
- `TestYfinanceDataRepositoryInvalidateCache` (2 tests) - Cache invalidation
- `TestYfinanceDataRepositoryTTLCache` (3 tests) - TTLCache behavior
- `TestYfinanceDataRepositoryCacheStockData` (3 tests) - DB caching
- `TestYfinanceDataRepositoryGetCacheStats` (2 tests) - Cache statistics

### test_portfolio_manager_helpers.py
- `TestCalculateWeightedStats` (4 tests) - Weighted statistics
- `TestCalculateDailyReturnStats` (5 tests) - Volatility, profit factor
- `TestFormatIndividualResultsList` (5 tests) - Result formatting

---

## Common Test Patterns

### Testing Async Functions
```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await some_async_function()
    assert result == expected
```

### Mocking External Dependencies
```python
@pytest.fixture
def mock_repository(self):
    repo = Mock()
    repo.get_data = AsyncMock(return_value=sample_data)
    return repo
```

### Testing Exceptions
```python
def test_raises_exception(self):
    with pytest.raises(ValueError, match="error message"):
        function_that_raises()
```

### Floating Point Comparisons
```python
def test_float_comparison(self):
    assert result == pytest.approx(expected, rel=0.01)
```

---

## Pytest Markers Used

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.asyncio` - Async tests with strict mode

---

## Expected Output

### Successful Run
```
======================== 59 passed, 2 warnings in 0.39s ========================
```

### Failed Test Example
```
FAILED tests/unit/test_backtest_engine.py::test_example - AssertionError: assert 10 == 20
```

---

## Debugging Failed Tests

### Verbose Output
```bash
pytest tests/unit/test_backtest_engine.py -vv
```

### Show Local Variables
```bash
pytest tests/unit/test_backtest_engine.py --showlocals
```

### Full Traceback
```bash
pytest tests/unit/test_backtest_engine.py --tb=long
```

### Print Statements
```bash
pytest tests/unit/test_backtest_engine.py -s
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run unit tests
  run: |
    source venv/bin/activate
    pytest tests/unit -v --tb=short
```

### Jenkins Pipeline Example
```groovy
stage('Unit Tests') {
    steps {
        sh '''
            source venv/bin/activate
            pytest tests/unit -v --tb=short --junitxml=test-results.xml
        '''
    }
}
```

---

## Troubleshooting

### Issue: Tests fail with "ModuleNotFoundError"
**Solution:** Activate virtual environment
```bash
source venv/bin/activate
```

### Issue: Tests fail with "asyncio.exceptions.TimeoutError"
**Solution:** Increase timeout or check async/await usage
```python
@pytest.mark.asyncio(timeout=10)
async def test_long_running():
    ...
```

### Issue: Tests fail with "fixture not found"
**Solution:** Check fixture is defined in conftest.py or test file

### Issue: Mocks not working
**Solution:** Ensure correct import path in patch
```python
# Correct
with patch('app.services.backtest_engine.currency_converter'):
    ...

# Wrong
with patch('app.utils.currency_converter.currency_converter'):
    ...
```

---

## Next Steps

1. **Run tests locally** to verify environment
2. **Add to CI/CD** pipeline for continuous testing
3. **Monitor coverage** with `--cov` flag
4. **Maintain tests** as code evolves

---

## Related Documentation

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Test Coverage Summary](./TEST_COVERAGE_SUMMARY.md)
- [CLAUDE.md](../CLAUDE.md) - Project overview and testing section

---

**Last Updated:** 2026-02-06
**Test Count:** 59
**Status:** ✅ All Passing
