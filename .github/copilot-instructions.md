# AI Coding Agent Instructions for Backtesting Platform

## Project Overview
**라고할때살걸** is a Korean trading strategy backtesting platform ("I should have bought it then") that helps users test "what if" investment scenarios using historical data. It supports single stocks, multi-asset portfolios, DCA (dollar-cost averaging), and rebalancing strategies.

**Tech Stack:**
- Backend: Python/FastAPI, backtesting.py, SQLAlchemy, pandas, yfinance
- Frontend: TypeScript/React/Vite, Zustand, Recharts, shadcn/ui, Tailwind CSS
- Database: MySQL (dev/prod), SQLite (tests)
- Infrastructure: Docker Compose, Nginx

## Architecture Overview

### Backend Flow
```
API Request → FastAPI → PortfolioService → BacktestEngine → backtesting.py
                                      ↓
Data Sources: MySQL Cache → yfinance API → External APIs
```

**Key Components:**
- `app/services/portfolio_service.py`: Main orchestration for multi-asset backtesting
- `app/services/backtest_engine.py`: Wraps backtesting.py with currency conversion
- `app/services/unified_data_service.py`: Collects prices, news, exchange rates
- `app/repositories/`: Data access layer (stock prices, news)

### Frontend Architecture (Feature-Sliced Design)
```
pages/ → features/ → shared/
```
**Dependency Rule:** `shared` ← `features` ← `pages` (no circular imports)

**State Management:**
- Global: Zustand stores (theme, shared data)
- Local: `useState` (simple), `useReducer` (complex forms like portfolio weights)

## Critical Patterns & Pitfalls

### ASYNC/SYNC BOUNDARY (CRITICAL)
**Problem:** Race conditions occur when synchronous I/O (DB queries, yfinance API) runs directly in async context without `asyncio.to_thread()`.

**Symptoms:** First backtest with new data fails, second run succeeds.

**Solution:** ALL synchronous I/O in async functions MUST be wrapped:
```python
# WRONG - causes race conditions
async def some_function():
    data = load_ticker_data(symbol, start, end)  # Sync I/O in async context

# CORRECT
async def some_function():
    data = await asyncio.to_thread(load_ticker_data, symbol, start, end)
```

**Check these files:** `portfolio_service.py`, `backtest_engine.py`, any async function calling DB/API operations.

### Currency Conversion Policy
- **Individual prices:** Stored in original currency (KRW, JPY, EUR, etc.)
- **Backtesting calculations:** ALL assets converted to USD via exchange rates
- **Frontend display:** Stock data in original currency, backtest results in USD

**Implementation:** `app/services/backtest_engine.py:_convert_to_usd()`

### Database Transaction Isolation
**Problem:** Save data then query immediately fails due to snapshot isolation.

**Solution:** Explicit commit + refresh, or query within same transaction.

### Testing Strategy
**Backend (pytest):**
- `@pytest.mark.unit`: Fast, isolated (no DB/external)
- `@pytest.mark.integration`: With database
- `@pytest.mark.external`: Calls yfinance/external APIs
- `@pytest.mark.asyncio`: All async tests

**Frontend (Vitest + RTL + Playwright):**
- Unit: Pure functions, utilities, reducers
- Component: React behavior, user interactions
- E2E: Full user workflows

## Development Workflow

### Local Development
```bash
# Start all services
docker compose -f compose.dev.yaml up -d --build

# Access points
# Frontend: http://localhost:5173
# Backend API docs: http://localhost:8000/api/v1/docs

# Run tests
docker compose -f compose.dev.yaml exec backtest-be-fast pytest
docker compose -f compose.dev.yaml exec backtest-fe npm test
```

### Key Files to Understand
- `backtest_be_fast/app/main.py`: FastAPI app setup, CORS, routing
- `backtest_be_fast/app/core/config.py`: Settings, environment variables
- `backtest_be_fast/app/services/portfolio_service.py`: Main backtest orchestration
- `backtest_be_fast/app/services/backtest_engine.py`: Currency conversion, strategy execution
- `backtest_fe/src/App.tsx`: React app structure, routing
- `database/schema.sql`: MySQL schema for stock data caching

### Common Tasks
- **Add new strategy:** Modify `app/strategies/`, update `backtest_engine.py:_build_strategy()`
- **Add API endpoint:** Create in `app/api/v1/endpoints/`, register in `api.py`
- **Add frontend feature:** Create in `src/features/`, follow Feature-Sliced Design
- **Database changes:** Update `database/schema.sql`, create migration script

### Performance Optimizations
- N+1 query elimination (10x speedup)
- Parallel data loading for portfolios
- Chart memoization: `memo`, `useMemo`, `useCallback`
- Smart data sampling for long-term backtests

## Code Quality Standards
- **Backend:** Type hints, pydantic models, comprehensive error handling
- **Frontend:** TypeScript strict mode, ESLint, component composition over inheritance
- **Testing:** Behavior over implementation, mock external dependencies
- **Architecture:** Repository pattern, dependency injection, single responsibility

## Deployment
- **Dev:** Docker Compose with hot reload
- **Prod:** Nginx reverse proxy, separate containers
- **Database:** MySQL in prod, SQLite for tests

Reference: `CLAUDE.md` for detailed architecture docs in each service's `docs/` directory.