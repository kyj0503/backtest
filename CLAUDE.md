# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**라고할때살걸** - Trading strategy backtesting platform (v1.6.10)
- **Backend**: FastAPI + Python 3.x, wraps backtesting.py library
- **Frontend**: React 18 + TypeScript + Vite, shadcn/ui components
- **Deployment**: Docker Compose for dev/prod environments

## Common Commands

### Docker Development (Recommended)
```bash
# Build and run full stack with hot reload
docker compose -f compose.dev.yaml up -d --build

# View backend logs
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# Stop services
docker compose -f compose.dev.yaml down
```

**Access points**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

### Backend Testing (pytest)
```bash
cd backtest_be_fast

# Run unit tests (fast)
pytest -m unit

# Run integration tests
pytest -m integration

# Run specific test file with verbose output
pytest tests/unit/test_sma_strategy.py -v

# Run all tests with coverage
pytest --cov=app --cov-report=html
```

Test markers are defined in `pytest.ini`: `unit`, `integration`, `e2e`, `slow`, `db`, `external`

### Frontend Development
```bash
cd backtest_fe

# Development server (outside Docker)
npm run dev

# Type checking without build
npm run type-check

# Build for production
npm run build

# Run tests (Vitest)
npm run test

# Run tests with UI
npm run test:ui

# Lint and fix
npm run lint:fix
```

## Architecture

### Backend Service Layer Flow
```
API Layer (app/api/v1/)
  → Service Layer (app/services/*_service.py, app/services/*_calculator.py, app/services/*_helper.py)
  → Repository Layer (app/repositories/)
  → Strategy Layer (app/strategies/strategies.py)
```

**Core services chain**:
1. `backtest_service.py` - Single stock backtest orchestration
2. `portfolio_service.py` - Multi-stock portfolios, DCA strategies, rebalancing
3. `backtest_engine.py` - Wraps backtesting.py, executes backtests
4. `chart_data_service.py` - Serializes chart data for frontend
5. `strategy_service.py` - Strategy class management and parameter validation

**Helper/Calculator services**:
6. `dca_calculator.py` - DCA share and return calculations
7. `rebalance_helper.py` - Rebalancing schedule and weight calculations

**Strategy implementations** (consolidated in single file):
- `strategies.py` - All 6 backtesting strategies + PositionSizingMixin

**Singleton pattern**: All services are provided as module-level instances (e.g., `strategy_service`, `validation_service`)

### Currency Policy (Critical!)
- **DB storage**: Original currency (KRW, JPY, EUR, GBP, etc.)
- **Backtest calculation**: All prices converted to USD (13 major currencies supported)
  - Direct rates: `KRW=X`, `JPY=X` (1 USD = X currency)
  - USD rates: `EURUSD=X`, `GBPUSD=X` (1 currency = X USD)
- **Frontend display**: Individual stock market data shows original currency, backtest results show USD

### Frontend Architecture
```
src/
  features/         # Feature modules (backtest, portfolio, etc.)
    backtest/
      api/          # API call logic
      components/   # Backtest UI components
      hooks/        # Custom hooks
  shared/           # Common resources
    ui/             # shadcn/ui components (import via @/shared/ui/*)
    hooks/          # Global hooks (useTheme, etc.)
    api/            # Common API utilities
  pages/            # Route pages
  themes/           # Theme JSON files (4 themes supported)
```

**Routing**: Uses `react-router-dom`, main page at `/backtest`

**Import aliases**: Uses `@/*` alias configured in `tsconfig.json` and `vite.config.ts`
```typescript
import { Button } from '@/shared/ui/button';
import { useTheme } from '@/shared/hooks/useTheme';
import { backtestApi } from '@/features/backtest/api/backtestApi';
```

## CRITICAL: Async/Sync Boundary Management (Prevent Race Conditions)

**Severity**: CRITICAL - Directly impacts backtest result accuracy

### Problem Pattern

FastAPI is async, but many libraries (yfinance, SQLAlchemy) use synchronous I/O. Calling synchronous functions directly in async contexts causes **race conditions** that corrupt data on first execution.

**Symptoms**:
- First run: Wrong results (graph crashes, incorrect statistics)
- Second run (same parameters): Correct results
- Repeats with new tickers/date ranges

### Required Rules

**NEVER: Call synchronous I/O directly in async functions**
```python
# WRONG - Blocks event loop, causes race conditions
async def process():
    data = load_ticker_data(ticker, start, end)  # Sync function
    return data
```

**ALWAYS: Wrap with asyncio.to_thread()**
```python
# CORRECT - Safely executes in thread pool
import asyncio

async def process():
    data = await asyncio.to_thread(
        load_ticker_data, ticker, start, end
    )
    return data
```

### Functions Requiring Wrapping

**Database calls** (synchronous):
- `yfinance_db.load_ticker_data()`
- `yfinance_db.save_ticker_data()`
- `yfinance_db.get_ticker_info_from_db()`

**External API calls** (synchronous):
- `data_fetcher.get_stock_data()`
- `yf.Ticker().history()`
- `yf.download()`

**All must be wrapped with `asyncio.to_thread()`!**

### Checklist

When writing/reviewing code, verify:
- [ ] All I/O calls in async functions start with `await`?
- [ ] Synchronous I/O functions wrapped with `asyncio.to_thread()`?
- [ ] Static methods/regular functions called from async contexts don't contain synchronous I/O?
- [ ] Async/sync boundaries maintained during refactoring?

### Reference Documents

Detailed analysis: `backtest_be_fast/docs/race_condition_reintroduced_analysis.md`

## Code Conventions

### Python Backend

**Docstring pattern** (required for modules, classes, core functions):
```python
"""
[Module/Function Name]

**Role**:
- Core responsibility 1
- Core responsibility 2

**Key Features**:
1. method_name(): description

**Dependencies**:
- app/path/to/module.py: description

**Related Components**:
- Backend: app/...
- Frontend: src/...
"""
```
See examples in `app/main.py`, `app/services/backtest_engine.py`, `app/strategies/sma_strategy.py`

**Strategy implementation**: Located in `app/strategies/strategies.py`
- All 6 strategies (SMA, EMA, RSI, Bollinger, MACD, BuyHold) in single file
- Inherit from `backtesting.Strategy` and `PositionSizingMixin`
- Implement `init()` and `next()` methods
- Parameters defined as class attributes (e.g., `sma_short = 10`)
- Register in `STRATEGY_CLASSES` dict in `strategy_service.py`
- Use `calculate_and_buy()` from PositionSizingMixin for consistent position sizing

**Error handling**: Use custom exceptions from `app/core/exceptions.py`, includes error ID generation

**Logging**: Standard `logging` module with `logger = logging.getLogger(__name__)`
- INFO: Backtest start/end, data loading
- DEBUG: Data columns, detailed flow
- ERROR: Exception conditions

### TypeScript Frontend

**shadcn/ui components**: Import from `@/shared/ui/*` (configured in `components.json`)
- Add new components: `npx shadcn@latest add <component-name>`
- Custom components go in `@/components/*` or `@/features/*/components/*`

**API calls**: Fetch-based, uses Vite proxy (`/api/v1/backtest` → FastAPI)
- Error handling: `ApiError` type, status-based classification
- See example in `src/features/backtest/api/backtestApi.ts`

**Theme system**: `useTheme()` hook, JSON-based theme definitions (`src/themes/`)
- Dynamic CSS variables, localStorage persistence
- Dark mode support via `dark` class toggle

## Key Patterns

### Backtest Execution Flow
1. API request → `backtest.py` endpoint
2. `validation_service` → Validates input (date range, tickers, strategy params)
3. `backtest_service` or `portfolio_service` → Logic branching
4. `backtest_engine` → Executes backtesting.py, currency conversion (`_convert_to_usd`)
5. `chart_data_service` → Serialization (`_serialize_numpy`, datetime → ISO 8601)
6. Return response (backtest results + chart data + statistics)

### Adding New Strategy
1. Create `app/strategies/new_strategy.py`:
   ```python
   class NewStrategy(Strategy):
       param1 = 10  # default value

       def init(self):
           self.indicator = self.I(SomeIndicator, self.data.Close, self.param1)

       def next(self):
           if self.should_buy:
               self.buy()
           elif self.should_sell:
               self.sell()
   ```

2. Add to `StrategyType` Enum in `app/schemas/requests.py`

3. Register in `app/services/strategy_service.py`:
   ```python
   STRATEGY_CLASSES = {
       "new_strategy": NewStrategy,
   }
   ```

4. Add UI in frontend `StrategySelector.tsx`

### Data Serialization Requirements
- **Numpy types**: Use `_serialize_numpy()` to convert to Python native types
- **Datetime**: Use `.isoformat()` for ISO 8601 strings
- **NaN/Infinity**: Replace with `None` or remove

### Duplicate Stock Prevention
- **Policy**: Cannot add same stock multiple times to portfolio (cash excluded)
- **Reason**: Reduces UI complexity, matches real investment patterns, simplifies code
- **Implementation**:
  - Frontend: `validatePortfolio()` in `backtestFormReducer.ts`
  - Backend: `PortfolioBacktestRequest.validate_portfolio()` in `app/schemas/schemas.py`
- **Alternative**: To increase weight in same stock, adjust `amount` or `weight`

## Testing

### Backend Test Structure
- **Fixtures**: Global fixtures in `tests/conftest.py`, factory patterns in `tests/fixtures/`
- **Async tests**: `asyncio_mode = strict`, use `async def test_*` format
- **Markers**: Use pytest markers for test categorization (see `pytest.ini`)

### Frontend Testing
- **Framework**: Vitest with React Testing Library
- **Mock server**: MSW configured in `src/test/mocks/`
- **Setup**: Global test setup in `src/test/setup.ts`

## Configuration

### Environment Variables
- Root `.env` file for shared variables
- Backend/frontend reference variables from `compose.dev.yaml`

### CORS Settings
- Configured in `app/core/config.py` via `backend_cors_origins`
- Default: `localhost:5173`, `localhost:8000`, production domains
- Accepts JSON array or comma-separated values

## Key Files Reference
- **Architecture**: `app/main.py`, `app/api/v1/api.py`
- **Core logic**: `app/services/portfolio_service.py`, `app/services/backtest_engine.py`
- **Config**: `app/core/config.py`, `compose.dev.yaml`
- **Testing**: `backtest_be_fast/pytest.ini`, `tests/conftest.py`
- **UI**: `backtest_fe/components.json`, `src/App.tsx`
