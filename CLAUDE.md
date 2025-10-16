# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Full-stack financial backtesting platform with FastAPI backend (`backtest_be_fast`) and React/TypeScript frontend (`backtest_fe`). The system supports portfolio backtesting with multiple trading strategies, DCA/Lump-sum investment methods, rebalancing, and integrates Yahoo Finance data with MySQL caching.

## Architecture

### Backend (FastAPI)
- **Entry Point**: `app/main.py` - CORS configuration, API router registration, health check
- **API Structure**: `/api/v1` prefix, unified backtest endpoint pattern
- **Core Library**: `backtesting.py` external library (requires Monkey Patch - see Gotchas)
- **Data Sources**: Yahoo Finance via `yfinance` + MySQL caching (`database/schema.sql`)
- **Singleton Settings**: `app/core/config.py` - Pydantic Settings loads environment variables globally via `settings` object

### Frontend (React/TypeScript)
- **Build Tool**: Vite with HMR, API proxy to backend (`/api/v1/*`)
- **UI Framework**: Radix UI, Tailwind CSS, Recharts for charts
- **Routing**: React Router - `/` (Home), `/backtest` (Portfolio)
- **State**: React Hook Form + Zod validation, local state management
- **Feature Structure**: `src/features/backtest/` - components, api, hooks, services, model

### Development Environment
- **Always use Docker Compose** for development: `docker compose -f compose.dev.yaml up -d --build`
- Backend: http://localhost:8000 (API docs at `/api/v1/docs`)
- Frontend: http://localhost:5173 (proxies API calls to backend)
- Hot reload enabled for both services via volume mounts
- Database: MySQL at `stock_data_cache` (schema in `database/schema.sql`)

## Essential Commands

### Development Workflow
```bash
# Start all services with hot reload
docker compose -f compose.dev.yaml up -d --build

# View backend logs
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# View frontend logs
docker compose -f compose.dev.yaml logs -f backtest-fe

# Stop services
docker compose -f compose.dev.yaml down

# Rebuild specific service
docker compose -f compose.dev.yaml up -d --build backtest-be-fast
```

### Backend Testing
```bash
# Inside Docker container
docker compose -f compose.dev.yaml exec backtest-be-fast pytest

# Or locally if you have Python environment
cd backtest_be_fast

# Run all tests
pytest

# Run by test category (pytest markers)
pytest tests/unit -v              # Fast, isolated unit tests
pytest tests/integration -v       # Tests with external dependencies (DB, API)
pytest tests/e2e -v              # Full workflow end-to-end tests
pytest -m "not slow" -v          # Skip slow-running tests
pytest -m "db" -v                # Database-dependent tests only
pytest -m "external" -v          # Tests calling external APIs

# Run specific test file
pytest tests/unit/test_rsi_strategy.py -v

# Run specific test function
pytest tests/unit/test_validation_service.py::test_validate_date_range -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests with detailed output
pytest -vv --showlocals
```

### Frontend Development
```bash
# Inside container or locally after npm install
cd backtest_fe

npm run dev              # Development server (Vite)
npm run build            # TypeScript compile + production build
npm run preview          # Preview production build
npm run lint             # ESLint check
npm run lint:fix         # ESLint auto-fix
npm run type-check       # TypeScript validation without emit
npm run test             # Vitest unit tests (watch mode)
npm run test:run         # Run tests once (CI mode)
npm run test:coverage    # Run with coverage report
npm run test:ui          # Vitest UI for debugging tests
npm run clean            # Remove dist and Vite cache
```

## Critical Patterns

### 1. Repository Pattern (Backend)
All data access must go through repository layer:
```python
from app.repositories import data_repository  # Singleton instance
data = await data_repository.get_stock_data(ticker, start_date, end_date)
```
- **YFinanceDataRepository**: Production data source (3-tier caching: memory → MySQL → yfinance API)
- **MockDataRepository**: Testing only
- Factory pattern via `DataRepositoryFactory`
- Caching strategy: 1-hour TTL for memory cache, persistent MySQL cache

### 2. Strategy Pattern (Backtesting)
Trading strategies inherit from `backtesting.Strategy`, implement `init()` and `next()`:
```python
class MyStrategy(Strategy):
    def init(self):
        # Setup indicators - use self.I() to register
        self.sma = self.I(SMA, self.data.Close, 20)

    def next(self):
        # Trading logic executed per bar
        if crossover(self.data.Close, self.sma):
            self.buy()
```
- All strategies in `app/strategies/` directory
- Validated and instantiated via `strategy_service.py` factory
- Supported: `sma_strategy`, `rsi_strategy`, `bollinger_strategy`, `macd_strategy`, `ema_strategy`, `buy_hold_strategy`

### 3. Service Layer Architecture
Services are singletons imported from modules:
```python
from app.services.backtest_service import backtest_service
from app.services.portfolio_service import portfolio_service
```
- **backtest_service**: Single-asset backtest execution, applies `backtesting.py` compatibility patches
- **portfolio_service**: Multi-asset portfolios, DCA/Lump-sum, rebalancing
- **validation_service**: Request validation (dates, parameters, tickers)
- **chart_data_service**: Frontend chart data transformation (JSON serialization)
- **data_service**: Data fetching coordination
- **unified_data_service**: Aggregates all frontend-required data (prices, exchange rates, news, benchmarks)

### 4. Pydantic Models (API Contract)
- **Request**: `app/schemas/requests.py` - `BacktestRequest`, `StrategyType` enum
- **Response**: `app/schemas/responses.py` - Frontend-expected exact format
- **Internal**: `app/schemas/schemas.py` - `PortfolioBacktestRequest`, internal models
- Dates: `Union[date, str]` with `field_validator` for automatic parsing

### 5. Frontend API Layer
- `src/features/backtest/api/backtestApi.ts` - Centralized API calls
- Axios-based, structured error handling (network, validation, server, rate_limit types)
- Environment variable: `VITE_API_BASE_URL` (default `/api`)

## Common Gotchas

### backtesting.py Compatibility
**CRITICAL**: The external `backtesting.py` library has a Timedelta/float comparison bug.
- Monkey Patch required in `services/backtest_service.py` via `_patch_backtesting_stats()`
- **Must** apply patch before `bt = Backtest(...)` instantiation
- Fallback: returns default statistics if patch fails

### API Response Serialization
JSON serialization requirements for pandas/numpy types:
```python
# pandas Timestamp → string
timestamp.isoformat()
timestamp.strftime('%Y-%m-%d')

# numpy types → Python native
numpy_value.item()
float(numpy_value)

# Decimal → float
float(decimal_value)
```
- Helper functions in `utils/serializers.py`
- **Always** convert before returning from API endpoints

### Frontend Proxy Configuration
- `vite.config.ts` proxy is **development-only**
- Docker internal: use service name `http://backtest-be-fast:8000`
- Local development: use `http://localhost:8000`
- Environment variable `FASTAPI_PROXY_TARGET` controls target

### Import Patterns
Backend absolute imports (no relative paths):
```python
from app.services.backtest_service import backtest_service  # Singleton
from app.repositories import data_repository
from app.core.config import settings
```
Frontend path alias `@/` → `src/` directory

## Testing Philosophy

Test structure follows pytest markers defined in `pytest.ini`:
- **Unit tests** (`tests/unit/`): Fast, isolated, no external API calls, mocked dependencies
- **Integration tests** (`tests/integration/`): DB/API dependencies included
- **E2E tests** (`tests/e2e/`): Full workflow validation, end-to-end scenarios
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`, `@pytest.mark.db`, `@pytest.mark.external`
- Fixtures: `tests/fixtures/` - backtest, portfolio sample data
- Shared setup: `tests/conftest.py` - pytest fixtures and configuration

## Database (MySQL)

- **Schema**: `database/schema.sql`
- **Tables**: `stocks`, `daily_prices`, `stock_news`
- Purpose: Cache yfinance data to minimize API calls
- **No ORM**: Direct pymysql or pandas SQL operations via `services/yfinance_db.py`
- **No migrations**: Manual SQL execution required for schema changes

## Environment Variables

Loaded via `.env` file in project root, referenced in `compose.dev.yaml`:
- **Backend**: `DEBUG`, `LOG_LEVEL`, `DATABASE_URL`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_NAME`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `BACKEND_CORS_ORIGINS`
- **Frontend**: `VITE_API_BASE_URL`, `API_PROXY_TARGET`, `FASTAPI_PROXY_TARGET`
- `settings` object in `app/core/config.py` centralizes access
- CORS origins: JSON array or comma-separated string

## Adding New Features

### Adding a New Trading Strategy
1. Create `app/strategies/new_strategy.py` inheriting from `backtesting.Strategy`
2. Implement `init()` (indicator setup) and `next()` (trading logic) methods
3. Add strategy to factory in `app/services/strategy_service.py`
4. Update `StrategyType` enum in `app/schemas/requests.py`
5. Update frontend `constants/strategies.ts` for UI dropdown
6. Write unit tests in `tests/unit/test_new_strategy.py`

### Adding a New API Endpoint
1. Create endpoint function in `app/api/v1/endpoints/` (e.g., `new_endpoint.py`)
2. Register router in `app/api/v1/api.py` via `api_router.include_router()`
3. Define request/response Pydantic models in `app/schemas/`
4. Add API client function in `backtest_fe/src/features/*/api/`
5. Apply error decorator `@handle_portfolio_errors` for consistent error handling

### Database Schema Changes
1. Update `database/schema.sql` manually
2. Execute SQL against MySQL database
3. Modify data access logic in `services/yfinance_db.py`
4. Update repository layer if data structure changes
5. **No migration system** - changes are manual

## Performance Considerations

- **Caching**: 3-tier caching reduces yfinance API calls (memory → MySQL → API)
- **Chunking**: Frontend uses code splitting via `manualChunks` in `vite.config.ts`
- **Lazy Loading**: Components use React.lazy for code splitting
- **Polling**: Vite dev server uses polling for file watching in Docker (WSL compatibility)

## Documentation Style

All modules include docstrings with:
- **역할** (Role): Purpose of the module
- **주요 기능** (Key Features): Main functionality
- **의존성** (Dependencies): External dependencies
- **연관 컴포넌트** (Related Components): Cross-references
- Functions: Google-style docstrings (Args, Returns, Raises)
- Language: Korean for technical documentation
