# AI Coding Agent Instructions for Backtesting Platform

## Project Overview
**라고할때살걸** - Korean trading strategy backtesting platform for testing "what if" investment scenarios. Supports single stocks, multi-asset portfolios, DCA, and rebalancing strategies.

**Stack:** Python/FastAPI + TypeScript/React/Vite | MySQL (prod) / SQLite (tests) | Docker Compose

## Architecture

### Backend Data Flow
```
FastAPI Endpoint → PortfolioManagerService → PortfolioDataLoader → StockRepository
                                          → BacktestEngine (backtesting.py wrapper)
                                          → CurrencyConverter (USD normalization)
```

**Key Services:**
- [backtest_engine.py](backtest_be_fast/app/services/backtest_engine.py): Wraps `backtesting.py`, handles currency conversion via `_convert_to_usd()`
- [portfolio/portfolio_data_loader.py](backtest_be_fast/app/services/portfolio/portfolio_data_loader.py): Parallel data loading with `asyncio.gather()`
- [unified_data_service.py](backtest_be_fast/app/services/unified_data_service.py): Aggregates prices, news, exchange rates

### Frontend (Feature-Sliced Design)
```
pages/ → features/backtest/ → shared/
```
**Dependency:** `shared` ← `features` ← `pages` (no reverse imports)

**State:** Zustand (global: theme, results) | `useReducer` (complex forms)

## ⚠️ Critical: Async/Sync Boundary

**Problem:** Race conditions when sync I/O runs in async context without thread isolation. Symptom: first run fails, second succeeds.

```python
# ❌ WRONG - causes race conditions
async def fetch_data():
    data = stock_repository.load_stock_data(symbol, start, end)

# ✅ CORRECT - always wrap sync I/O
async def fetch_data():
    data = await asyncio.to_thread(stock_repository.load_stock_data, symbol, start, end)
```

**Verify in:** Any async function calling `StockRepository`, `yfinance`, or DB operations.

## ⚠️ Critical: backtesting.py Version (0.3.3)

**Project uses backtesting==0.3.3** - DO NOT use features from newer versions.

| Feature | 0.3.x | 0.6.x+ | Status |
|---------|-------|--------|--------|
| `finalize_trades` param | ❌ | ✅ | **Don't use** |
| `spread` param | ❌ | ✅ | **Don't use** |
| `commission` | 1x (entry only) | 2x (entry+exit) | Different calculation |
| Kelly Criterion stat | ❌ | ✅ | **Don't use** |

```python
# ❌ WRONG - 0.6.x+ only
bt = Backtest(df, Strategy, cash=10000, finalize_trades=True)

# ✅ CORRECT - 0.3.x compatible
bt = Backtest(df, Strategy, cash=10000, commission=0)
```

**Why 0.3.3?** Stable API, no commission calculation changes, pandas 2.x compatible.

## Strategy Enum Values

**Always use exact enum values from `app/schemas/requests.py`:**
```python
class StrategyType(str, Enum):
    SMA_STRATEGY = "sma_strategy"
    RSI_STRATEGY = "rsi_strategy"
    BOLLINGER_STRATEGY = "bollinger_strategy"
    MACD_STRATEGY = "macd_strategy"
    BUY_HOLD_STRATEGY = "buy_hold_strategy"  # NOT "buy_and_hold"
    EMA_STRATEGY = "ema_strategy"
```

## Currency Handling
- **Storage:** Original currency (KRW, JPY, EUR)
- **Calculations:** All converted to USD in `BacktestEngine._convert_to_usd()`
- **Display:** Original for prices, USD for backtest results

## Development Commands
```bash
# Start services
docker compose -f compose.dev.yaml up -d --build

# Backend tests (markers: @pytest.mark.unit|integration|external|asyncio)
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit

# Frontend tests
docker compose -f compose.dev.yaml exec backtest-fe npm test

# Frontend quality checks (all four run in CI)
docker compose -f compose.dev.yaml exec backtest-fe npm run lint
docker compose -f compose.dev.yaml exec backtest-fe npm run type-check       # prod code
docker compose -f compose.dev.yaml exec backtest-fe npm run type-check:test  # test code
docker compose -f compose.dev.yaml exec backtest-fe npm run test:run

# Reproduce the CI gate exactly
docker build --target test ./backtest_fe
docker build --target test ./backtest_be_fast

# API docs: http://localhost:8000/api/v1/docs
# Frontend: http://localhost:5173
```

## Common Tasks

| Task | Location | Notes |
|------|----------|-------|
| Add strategy | `app/services/strategy_service.py` | Register in `_build_strategy()` |
| Add API endpoint | `app/api/v1/endpoints/` | Use `@handle_portfolio_errors` decorator |
| Add frontend feature | `src/features/backtest/` | Follow hooks/components/api structure |
| Batch DB queries | Use `get_tickers_info_batch()` | Avoid N+1 queries |

## Testing Patterns
- **Backend:** `@pytest.mark.unit` (no DB), `@pytest.mark.asyncio` (async tests)
- **Frontend:** Vitest + RTL for components, Playwright for E2E
- **Mocking:** External APIs (yfinance) in unit tests, real calls in `@pytest.mark.external`
- **Strategy values:** Use `buy_hold_strategy`, NOT `buy_and_hold` in test fixtures
- **Baseline:** BE 141 unit tests, FE 113 tests — all green. A failure is a regression.
- **Test files are type-checked** via `tsconfig.test.json` (`npm run type-check:test`); `tsconfig.build.json` excludes them.
- **Never set `isolate: false`** in `vitest.config.ts` — shared happy-dom + vitest's duration-based file reordering makes the suite flaky.

## Frontend Stack Constraints
- **React 19 / Vite 7 / Recharts 3 / React Router 7 / Tailwind CSS 4.**
- **Tailwind 4 is CSS-first:** no `tailwind.config.js`; config lives in `src/index.css`. Do NOT move theme color literals into `@theme` — `useTheme` injects them at runtime via `root.style.setProperty()`. Use `.app-container`, not `.container`.
- **`VITE_API_BASE_URL` must be empty** — the service layer already passes full `/api/v1/...` paths.

## Documentation
Detailed architecture docs in each service's `docs/` directory:
- [Backend troubleshooting](backtest_be_fast/docs/troubleshooting/race_condition.md)
- [Performance optimizations](backtest_be_fast/docs/performance/optimization-summary.md)
- [Frontend state management](backtest_fe/docs/architecture/state_management.md)