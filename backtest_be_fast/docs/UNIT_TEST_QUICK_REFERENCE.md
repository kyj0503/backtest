# Unit Test Quick Reference

## Quick Commands

### Run All Unit Tests
```bash
# From the repository root (the project runs in Docker)
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit -v

# Same command CI runs as a gate
docker build --target test ./backtest_be_fast
```

### Run a Subset
```bash
docker compose -f compose.dev.yaml exec backtest-be-fast \
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

`pytest-watch` is **not** in `requirements-test.txt` — installing it ad hoc works, but it isn't part of the pinned toolchain:
```bash
pip install pytest-watch  # not pinned; not part of the standard dev image
pytest-watch tests/unit
```
Without it, rerun `pytest tests/unit -v` manually, or use your editor's test runner.

---

## Test File Overview

Counts below are `pytest tests/unit --collect-only` item counts (post-parametrize-expansion) for the test files present on `main` as of this writing. This list moves as work lands — treat it as a snapshot, and re-run `pytest tests/unit --collect-only -q` for the current truth rather than trusting this table blindly.

| File | Tests | Coverage |
|------|-------|----------|
| `test_currency_converter.py` | 19 | CurrencyConverter: get_conversion_multiplier, convert_dataframe_to_usd, load_and_prepare_exchange_rates |
| `test_portfolio_manager_helpers.py` | 16 | PortfolioManagerService: _calculate_weighted_stats, _calculate_daily_return_stats, _format_individual_results_list |
| `test_portfolio_schemas.py` | 15 | Portfolio request schema validation |
| `test_nth_weekday.py` | 14 | Nth-weekday date resolution (rebalancing / DCA scheduling) |
| `test_data_repository.py` | 14 | YfinanceDataRepository: get_stock_data (3-tier cache), invalidate_cache, TTLCache behavior |
| `test_dca_schedule_alignment.py` | 14 | DCA payment count matches the actual Nth-weekday purchase schedule, not a "month = 30 days" approximation |
| `test_chart_data_service.py` | 12 | Chart data assembly |
| `test_backtest_engine.py` | 10 | BacktestEngine: run_backtest, _build_strategy, _convert_result_to_response, _create_fallback_result |
| `test_strategy_service.py` | 9 | Strategy resolution and parameter validation |
| `test_nth_weekday_edge_cases.py` | 9 | Nth-weekday boundary cases |
| `test_request_models.py` | 8 | Backtest request model validation |
| `test_rsi_strategy.py` | 6 | RSI strategy requirements |
| `test_rebalancer_delisted.py` | 5 | Delisted-stock rebalancing preserves portfolio value instead of double-counting it |
| `test_strategy_param_override.py` | 5 | Strategy param overrides reach the strategy class attribute for every strategy (guards the SMA `sma_short`/`sma_long` vs `short_window`/`long_window` regression) |
| `test_backtest_engine_strategy_param_validation.py` | 4 | Rejected strategy params raise instead of silently falling back to defaults |
| `test_bollinger_strategy.py` | 4 | Bollinger Bands strategy requirements |
| `test_portfolio_backtest_error_contract.py` | 4 | Portfolio backtest failures return real HTTP status codes, not HTTP 200 with an error body |
| `test_portfolio_calculator_equity_curve.py` | 4 | Equity-curve gaps are forward-filled from the last observed value, not the final value |
| `test_portfolio_manager_fixes.py` | 4 | Weight-mode return denominator and commission propagation |
| `test_yfinance_repository_load_ticker_data.py` | 4 | load_ticker_data retry policy: empty result fails fast, genuine errors still retry with backoff |
| `test_sma_strategy.py` | 2 | SMA strategy requirements |
| `test_macd_strategy.py` | 2 | MACD strategy requirements |
| `test_ema_strategy.py` | 2 | EMA strategy requirements |
| `test_buy_hold_strategy.py` | 2 | Buy & Hold strategy requirements |
| `test_backtest_engine_data_not_found_propagation.py` | 1 | DataNotFoundError propagates as HTTP 404, not re-wrapped as 500 |

**Total: 189 tests** (all passing on `main`; a failure is a regression, not pre-existing noise). This is `tests/unit` only — `tests/integration` (DB-required) is a separate suite not covered by this table or by the CI Quality Gate.

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
- `TestLoadAndPrepareExchangeRates` (5 tests) - Exchange rate loading
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
- `TestFormatIndividualResultsList` (7 tests) - Result formatting

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
======================= 189 passed, 10 warnings in 0.62s ========================
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

이 저장소의 실제 구성입니다 (예시가 아님).

`Dockerfile`에 `test` 스테이지가 있고, `Jenkinsfile`의 `Quality Gate` 스테이지가 이를 호출합니다.

```dockerfile
# backtest_be_fast/Dockerfile
FROM base AS test
COPY app ./app
COPY tests ./tests
COPY pytest.ini ./
RUN pytest tests/unit -q
```

```groovy
// Jenkinsfile
stage('Quality Gate') {
    steps {
        script {
            parallel(
                'Frontend': { sh 'docker build --target test ./backtest_fe' },
                'Backend':  { sh 'docker build --target test ./backtest_be_fast' }
            )
        }
    }
}
```

`test` 스테이지는 최종 이미지의 의존 경로 밖에 있으므로 `docker build`(타깃 미지정)로는 실행되지 않고, 배포 이미지에도 `tests/`가 포함되지 않습니다. DB가 필요한 `tests/integration`은 게이트에 포함하지 않습니다.

게이트가 실패하면 이미지 빌드와 배포에 도달하지 못합니다. 다만 파이프라인이 `*/main`을 체크아웃하므로 이는 **배포 게이트**이지 병합 게이트가 아닙니다.

---

## Troubleshooting

### Issue: Tests fail with "ModuleNotFoundError"
**Solution:** 컨테이너 안에서 실행하십시오. 이 프로젝트는 Docker로 돌아가며, 의존성은 컨테이너의 `/opt/venv`에 설치되어 있습니다.
```bash
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit -v
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
- [CLAUDE.md](../../CLAUDE.md) - Project overview and testing section

---

**Last Updated:** 2026-08-02
**Test Count:** 189
**Status:** ✅ All Passing
