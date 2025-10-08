# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack backtesting platform for financial trading strategies with a FastAPI backend and React/TypeScript frontend. The backend uses the `backtesting.py` library for strategy simulation and `yfinance` for market data.

## Development Commands

### Docker Compose (Recommended)

All development happens in Docker containers with hot-reload enabled:

```bash
# Start development environment
docker compose -f compose.dev.yaml up -d --build

# Stop services
docker compose -f compose.dev.yaml down

# View logs
docker compose -f compose.dev.yaml logs -f [backtest-be-fast|backtest-fe]

# Restart specific service
docker compose -f compose.dev.yaml restart backtest-be-fast

# Complete teardown (removes containers, images, volumes)
docker compose -f compose.dev.yaml down --rmi all --volumes --remove-orphans
```

**Service URLs (Development)**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

### Backend (`backtest_be_fast/`)

```bash
# Inside container or with local venv
cd backtest_be_fast

# Run server directly (development)
python run_server.py

# Code formatting
black app/
isort app/

# Run tests
pytest
pytest tests/test_specific.py  # Single test file
pytest -v  # Verbose output
```

### Frontend (`backtest_fe/`)

```bash
cd backtest_fe

# Development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix

# Testing
npm run test        # Watch mode
npm run test:run    # Run once
npm run test:ui     # UI mode
npm run test:coverage

# Clean build artifacts
npm run clean
```

## Architecture

### Backend Structure

The backend follows a **layered domain-driven architecture**:

```
backtest_be_fast/app/
├── api/v1/endpoints/       # FastAPI route handlers
├── domains/                # Domain layer (business logic organized by domain)
│   ├── backtest/          # Backtest domain logic
│   ├── data/              # Market data domain
│   └── portfolio/         # Portfolio domain
├── services/              # Application services (orchestration)
│   ├── backtest_service.py
│   └── portfolio_service.py
├── repositories/          # Data access layer (Repository pattern)
├── factories/             # Object creation (Factory pattern)
├── models/                # Pydantic models (requests/responses)
├── core/                  # Configuration and shared utilities
│   └── config.py         # Settings management via pydantic-settings
└── utils/                 # Shared utilities
```

**Key Patterns**:
- **Repository Pattern**: All data access goes through repositories (`app/repositories/`)
- **Factory Pattern**: Strategy and service creation via factories (`app/factories/`)
- **Monkey Patching**: `backtest_service.py` patches `backtesting.py` to fix Timedelta compatibility issues

**Critical Components**:
- `app/services/backtest_service.py`: Main backtesting orchestration (includes monkey patch for pandas Timedelta)
- `app/services/portfolio_service.py`: Multi-asset portfolio backtesting
- `app/core/config.py`: Centralized configuration with environment variables

### Frontend Structure

The frontend uses a **feature-based architecture** with shared resources:

```
backtest_fe/src/
├── features/backtest/      # Backtest feature (self-contained)
│   ├── components/        # Feature-specific UI components
│   ├── hooks/             # Feature-specific hooks (useBacktest, useMarketData, etc.)
│   ├── api/               # API client for backtest endpoints
│   ├── model/             # Type definitions and schemas
│   └── services/          # Business logic layer
├── shared/                # Shared resources across features
│   ├── ui/               # Reusable UI components (shadcn/ui)
│   ├── api/              # Shared API clients
│   ├── hooks/            # Shared hooks (useTheme)
│   ├── types/            # Shared TypeScript types
│   ├── utils/            # Utilities
│   └── config/           # Configuration
├── components/            # Global components (Header, ErrorBoundary)
├── pages/                 # Page components (routing)
└── themes/                # Theme definitions
```

**Key Patterns**:
- **Feature Isolation**: Each feature in `features/` is self-contained with its own components, hooks, and API clients
- **Custom Hooks Pattern**: Business logic encapsulated in hooks (e.g., `useBacktest`, `useMarketData`, `useOptimization`)
- **UI Library**: Uses shadcn/ui components built on Radix UI primitives

**Critical Components**:
- `features/backtest/hooks/useBacktest.ts`: Main backtest execution hook
- `pages/BacktestPage.tsx`: Main backtest UI orchestration
- `shared/api/`: API client with error handling

## Configuration & Environment

**All environment variables are managed in a single `.env` file at the project root** (not tracked in git).

Key backend settings (`backtest_be_fast/app/core/config.py`):
- `BACKEND_CORS_ORIGINS`: Comma-separated or JSON array of allowed origins
- `DATABASE_URL` or individual `DATABASE_*` variables
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`: For Naver News API
- `DEBUG`, `LOG_LEVEL`, `HOST`, `PORT`

Frontend environment variables are prefixed with `VITE_`:
- `VITE_API_BASE_URL`: API endpoint base URL
- `API_PROXY_TARGET`: Backend proxy target in Docker

## Testing

### Backend Testing
- Framework: `pytest`
- Test files: `backtest_be_fast/tests/`
- Configuration: `conftest.py` for fixtures

### Frontend Testing
- Framework: `vitest` with React Testing Library
- Test files: Co-located with components or in `src/test/`
- Mocks: MSW (Mock Service Worker) in `src/test/mocks/`
- Configuration: `vitest.config.ts`

## Key Integrations

- **Market Data**: `yfinance` for fetching historical stock data
- **Backtesting Engine**: `backtesting.py` library (with custom patches)
- **Database**: SQLAlchemy with MySQL/MariaDB
- **News API**: Naver Search API for Korean market news

## Common Gotchas

1. **Timedelta Compatibility**: The `backtesting.py` library has compatibility issues with newer pandas versions. The monkey patch in `backtest_service.py` must be preserved.

2. **CORS Configuration**: Backend CORS settings support both JSON array and comma-separated string formats for flexibility across environments.

3. **Docker Volumes**: Frontend uses `node_modules` volume mount, backend uses `venv` volume to avoid reinstalling dependencies on container restart.

4. **Route Structure**: Frontend routes are defined in `App.tsx`. The app currently has two main pages: HomePage (`/`) and BacktestPage (`/backtest`).

5. **API Versioning**: All backend routes are prefixed with `/api/v1` (configured in `core/config.py`).
