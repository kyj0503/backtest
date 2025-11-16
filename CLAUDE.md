# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**라고할때살걸** is a Korean trading strategy backtesting platform for stocks and cryptocurrencies. The name translates to "I should have bought it then" - helping users test "what if" investment scenarios using historical data.

**Tech Stack:**
- Backend: Python, FastAPI, backtesting.py, SQLAlchemy, pandas, yfinance
- Frontend: TypeScript, React, Vite, Zustand, Recharts, shadcn/ui, Tailwind CSS
- Database: MySQL (dev/prod), SQLite (test)
- Infrastructure: Docker, Docker Compose

## Development Commands

### Running the Application

```bash
# Start all services (backend, frontend, database)
docker compose -f compose.dev.yaml up -d --build

# Access points:
# - Frontend: http://localhost:5173
# - Backend API docs: http://localhost:8000/api/v1/docs

# View logs
docker compose -f compose.dev.yaml logs -f backtest-be-fast
docker compose -f compose.dev.yaml logs -f backtest-fe

# Stop services
docker compose -f compose.dev.yaml down
```

### Backend Development

```bash
# Run all tests
docker compose -f compose.dev.yaml exec backtest-be-fast pytest

# Run specific test markers
docker compose -f compose.dev.yaml exec backtest-be-fast pytest -m unit
docker compose -f compose.dev.yaml exec backtest-be-fast pytest -m integration
docker compose -f compose.dev.yaml exec backtest-be-fast pytest -m db
docker compose -f compose.dev.yaml exec backtest-be-fast pytest -m external

# Run specific test file
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit/test_filename.py

# Run with coverage
docker compose -f compose.dev.yaml exec backtest-be-fast pytest --cov=app

# Backend structure
backtest_be_fast/
├── app/
│   ├── api/           # API endpoints
│   ├── services/      # Business logic (backtest_engine, portfolio_service)
│   ├── repositories/  # Data access layer
│   ├── strategies/    # Trading strategies (SMA, RSI, MACD, etc.)
│   ├── schemas/       # Pydantic models
│   ├── core/          # Database, config
│   └── utils/         # Helper functions
└── tests/
    ├── unit/          # Fast, isolated tests
    ├── integration/   # Tests with DB/external dependencies
    └── fixtures/      # Test data and pytest fixtures
```

### Frontend Development

```bash
# Run all tests
docker compose -f compose.dev.yaml exec backtest-fe npm test

# Run tests in watch mode
docker compose -f compose.dev.yaml exec backtest-fe npm run test:watch

# Run tests with coverage
docker compose -f compose.dev.yaml exec backtest-fe npm run test:coverage

# Run tests with UI
docker compose -f compose.dev.yaml exec backtest-fe npm run test:ui

# E2E tests with Playwright
docker compose -f compose.dev.yaml exec backtest-fe npm run test:e2e
docker compose -f compose.dev.yaml exec backtest-fe npm run test:e2e:ui

# Type checking
docker compose -f compose.dev.yaml exec backtest-fe npm run type-check

# Linting
docker compose -f compose.dev.yaml exec backtest-fe npm run lint
docker compose -f compose.dev.yaml exec backtest-fe npm run lint:fix

# Build
docker compose -f compose.dev.yaml exec backtest-fe npm run build

# Frontend structure (Feature-Sliced Design)
backtest_fe/src/
├── pages/           # Route-level page components
├── features/        # Feature modules (backtest, portfolio, etc.)
│   └── backtest/
│       ├── api/         # API calls for this feature
│       ├── components/  # Feature-specific UI components
│       ├── hooks/       # Business logic hooks
│       ├── model/       # State management (Zustand), types, constants
│       └── services/    # Data transformation logic
└── shared/          # Reusable code across features
    ├── api/         # Common API client setup
    ├── components/  # Reusable composite components
    ├── ui/          # shadcn/ui atomic components
    ├── hooks/       # Generic hooks
    └── utils/       # Pure utility functions
```

## Architecture

### Backend: Backtest Execution Flow

```
API Request
    ↓
Service Layer (backtest_service, portfolio_service)
    ↓
Data Repository (in-memory → MySQL → yfinance API)
    ↓
BacktestEngine (app/services/backtest_engine.py)
    ├─ Currency conversion (all assets to USD)
    ├─ Dynamic strategy class creation
    └─ backtesting.py library execution
    ↓
Result serialization
```

**Key Custom Logic:**

1. **Currency Conversion** (backtest_be_fast/app/services/backtest_engine.py):
   - ALL assets converted to USD before backtesting via `_convert_to_usd()`
   - Enables comparing/combining assets from different currencies (KRW, JPY, EUR, etc.)
   - Exchange rate data cached with same priority as price data

2. **Dynamic Strategy Creation** (`_build_strategy`):
   - User-provided strategy parameters (e.g., `sma_short=15`) applied dynamically
   - Creates new strategy class inheriting from base strategy with overridden parameters

3. **Portfolio Logic** (app/services/portfolio_service.py):
   - **Buy & Hold**: Custom implementation (not using backtesting.py)
   - **DCA (Dollar-Cost Averaging)**: Simulates periodic purchases
   - **Rebalancing**: Simulates periodic portfolio weight adjustments
   - **Delisting Detection**: Auto-adjusts weights when assets stop trading

### Frontend: State Management

**Global State (Zustand):**
- Used for data shared across pages/components
- Examples: theme, backtest results, authentication (future)
- Simple, minimal boilerplate vs Redux

**Local State:**
- `useState`: Simple component-internal state (modals, form inputs)
- `useReducer`: Complex form state with interdependent fields (e.g., BacktestForm)
  - Portfolio weights that must rebalance when one changes
  - Centralized update logic in reducer function
  - Easy to test (pure functions)

**Dependency Rule (Feature-Sliced Design):**
```
pages → features → shared
```
- `shared` depends on nothing
- `features` can only depend on `shared`
- `pages` can depend on `features` and `shared`
- Prevents circular dependencies

## Critical Implementation Details

### Async/Sync Boundary (CRITICAL)

**Problem:** Race conditions occur when synchronous I/O (DB queries, yfinance API) is called directly from async context without `asyncio.to_thread()`.

**Symptoms:**
- First backtest with new ticker/date range: corrupted results
- Second run with same parameters: works correctly
- Root cause: Incomplete data used before I/O completes

**Solution:** ALL synchronous I/O calls MUST be wrapped:
```python
# ❌ WRONG - causes race conditions
async def some_function():
    data = load_ticker_data(symbol, start, end)  # Sync I/O in async context

# ✅ CORRECT
async def some_function():
    data = await asyncio.to_thread(load_ticker_data, symbol, start, end)
```

**Where to check:**
- `portfolio_service.py`: All DB queries and data loading
- `backtest_engine.py`: All `_get_price_data()` calls
- Any async function calling sync DB/API operations

See: `backtest_be_fast/docs/troubleshooting/race_condition.md`

### Database Transaction Isolation

**Problem:** Saving data then immediately querying it in same request can fail due to transaction snapshot isolation.

**Solution:** Explicit transaction commit + refresh, or fetch within same transaction.

See: `backtest_be_fast/docs/troubleshooting/transaction_isolation.md`

### Performance Optimizations

**Backend:**
- N+1 query pattern eliminated (10x speedup)
- Parallel data loading for portfolios
- Caching strategy: in-memory → MySQL → yfinance API

See: `backtest_be_fast/docs/performance/optimization-summary.md`

**Frontend:**
- Chart re-rendering optimized with `memo`, `useMemo`, `useCallback`
- Smart data sampling for long-term backtests (daily → weekly → monthly)

See: `backtest_fe/docs/optimization/chart_performance.md`, `data_sampling.md`

### Date Calculation for DCA/Rebalancing

Complex logic for "Nth specific weekday of month" (e.g., "2nd Friday"):
- Handles months without 5th week
- Proper edge case handling

See: `backtest_be_fast/docs/architecture/date_calculation.md`

## Testing Strategy

### Backend (pytest)

**Test Markers:**
- `@pytest.mark.unit`: Fast, isolated tests (no DB/external APIs)
- `@pytest.mark.integration`: Tests with database
- `@pytest.mark.external`: Tests calling yfinance/external APIs
- `@pytest.mark.e2e`: Full workflow tests
- `@pytest.mark.slow`: Long-running tests

**Async Testing:**
- Uses `pytest-asyncio` with `strict` mode
- All async tests must be marked with `@pytest.mark.asyncio`

**Fixtures:**
- Database fixtures create/teardown SQLite test DB
- Mock data fixtures for common test scenarios

See: `backtest_be_fast/docs/testing/README.md`

### Frontend (Vitest + React Testing Library)

**Test Types:**
- Unit tests: Pure functions, utilities, reducers
- Component tests: React component behavior, user interactions
- E2E tests: Full user workflows (Playwright)

**Testing Patterns:**
- Test user behavior, not implementation details
- Mock API calls with MSW (Mock Service Worker)
- Test reducers as pure functions
- Use `userEvent` for realistic interactions

See: `backtest_fe/docs/testing/README.md`

## Common Pitfalls

1. **Adding async I/O without `asyncio.to_thread()`** → Race conditions on first run
2. **Modifying backtesting.py directly** → Use `BacktestEngine` wrapper instead
3. **Breaking Feature-Sliced Design dependency rules** → `shared` importing from `features`
4. **Unnecessary re-renders in charts** → Wrap with `memo`, use `useMemo` for data transformations
5. **Testing implementation over behavior** → Test what users see, not internal state

## Documentation

Detailed architecture docs in each service's `docs/` directory:
- [Backend docs](./backtest_be_fast/docs/README.md)
- [Frontend docs](./backtest_fe/docs/README.md)

Key architectural documents:
- `backtest_be_fast/docs/architecture/backtest_logic.md` - How backtesting.py is wrapped
- `backtest_be_fast/docs/troubleshooting/race_condition.md` - Async/sync boundary issues
- `backtest_fe/docs/architecture/codebase_structure.md` - Feature-Sliced Design
- `backtest_fe/docs/architecture/state_management.md` - Zustand + useReducer patterns
