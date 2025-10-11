# AI Coding Agent Instructions for Backtest Platform

## Project Overview
Full-stack financial backtesting platform with FastAPI backend using `backtesting.py` library and React/TypeScript frontend. All development occurs in Docker containers with hot-reload enabled.

## Architecture Patterns

### Backend (Domain-Driven Design)
```
backtest_be_fast/app/
├── api/v1/endpoints/          # FastAPI route handlers
├── domains/                   # Business logic by domain (backtest, data, portfolio)
├── services/                  # Application services (orchestration layer)
├── repositories/              # Data access (Repository pattern)
├── factories/                 # Object creation (Factory pattern)
├── models/                    # Pydantic request/response models
├── core/config.py             # Centralized settings via pydantic-settings
└── utils/                     # Shared utilities
```

**Critical Patterns:**
- **Repository Pattern**: All data access through `app/repositories/` (e.g., `backtest_repository`, `data_repository`)
- **Factory Pattern**: Strategy/service creation via `app/factories/` (e.g., `strategy_factory`, `service_factory`)
- **Monkey Patch Required**: `backtest_service.py` patches `backtesting.py` for pandas Timedelta compatibility

### Frontend (Feature-Based Architecture)
```
backtest_fe/src/
├── features/backtest/         # Self-contained feature modules
│   ├── components/           # Feature-specific UI components
│   ├── hooks/               # Business logic in custom hooks (e.g., useBacktestForm, useStockData)
│   ├── api/                 # Feature-specific API clients
│   ├── model/               # TypeScript types and schemas
│   └── services/            # Business logic layer
├── shared/                   # Cross-feature resources (ui/, api/, hooks/, types/)
├── pages/                    # Route components
└── themes/                   # Theme definitions
```

**Critical Patterns:**
- **Custom Hooks Pattern**: Business logic encapsulated in hooks (e.g., `useBacktestForm`, `useStockData`, `useStrategies`)
- **Feature Isolation**: Each feature in `features/` is self-contained with own components, hooks, and API clients
- **UI Library**: shadcn/ui components on Radix UI primitives

## Development Workflow

### Docker Development Environment (Required)
```bash
# Start all services with hot-reload
docker compose -f compose.dev.yaml up -d --build

# View logs
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# Access services
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/v1/docs
```

### Environment Configuration
- **Single .env file at project root** contains ALL environment variables
- Backend: `app/core/config.py` loads via pydantic-settings
- Frontend: Vite loads `VITE_*` prefixed variables
- CORS origins support both JSON arrays and comma-separated strings

### Backend Development
```bash
# Code formatting (inside container)
black app/
isort app/

# Testing with pytest
pytest tests/unit/           # Fast unit tests
pytest tests/integration/    # External dependencies
pytest -k "backtest"         # Filter by keyword
```

### Frontend Development
```bash
# TypeScript checking
npm run type-check

# Linting
npm run lint:fix

# Testing with vitest
npm run test:run            # Run once
npm run test:ui             # Interactive UI
```

## Key Integration Points

### Data Sources
- **Market Data**: `yfinance` for historical prices (cached in MySQL)
- **Backtesting Engine**: `backtesting.py` with custom Timedelta compatibility patch
- **News API**: Naver Search API for Korean market news
- **Database**: MySQL/MariaDB with SQLAlchemy async support

### External Dependencies
- `backtesting.py` library requires monkey patch in `app/services/backtest_service.py`
- CORS configuration in `app/core/config.py` supports flexible origin formats
- Docker volumes preserve `node_modules` and Python virtual environment

## Testing Strategy

### Backend Testing (`pytest`)
- **Unit tests**: `tests/unit/` - isolated, fast tests
- **Integration tests**: `tests/integration/` - external APIs, database
- **E2E tests**: `tests/e2e/` - full workflow tests
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

### Frontend Testing (`vitest`)
- **Co-located tests**: Components and hooks tested alongside implementation
- **Mock Service Worker**: API mocking in `src/test/mocks/`
- **Coverage**: `npm run test:coverage`

## Common Patterns & Conventions

### Backend Patterns
- **Service Layer**: Business logic in services, data access through repositories
- **Factory Creation**: Use `strategy_factory` and `service_factory` for object instantiation
- **Configuration**: All settings through `app/core/config.py` singleton
- **Error Handling**: Custom exceptions in `app/core/exceptions.py`

### Frontend Patterns
- **Hook Composition**: Complex features built from multiple focused hooks
- **Type Safety**: Strict TypeScript with interfaces in `model/` directories
- **API Layer**: Feature-specific API clients in `features/*/api/`
- **State Management**: useReducer for complex form state (see `useBacktestForm`)

## Critical Gotchas

1. **Timedelta Compatibility**: `backtesting.py` fails with newer pandas - monkey patch in `backtest_service.py` is mandatory
2. **CORS Flexibility**: Backend accepts both `["origin1", "origin2"]` and `"origin1,origin2"` formats
3. **Docker Volumes**: Frontend uses `node_modules` volume, backend uses `venv` volume for dependency persistence
4. **Environment Variables**: Never create `.env` files in subdirectories - single file at project root
5. **API Versioning**: All routes prefixed with `/api/v1` (configured in `core/config.py`)
6. **Database Schema**: MySQL with utf8mb4 charset, composite primary keys in `daily_prices`

## File Structure Examples

### Adding New Strategy (Backend)
1. Create strategy class in `app/strategies/implementations/`
2. Register in `app/factories/strategy_factory.py`
3. Add to `app/models/requests.py` and `app/models/responses.py`

### Adding New Feature (Frontend)
1. Create `src/features/new-feature/` with `components/`, `hooks/`, `api/`, `model/`
2. Add route in `src/App.tsx`
3. Create custom hooks following `useBacktestForm` pattern

### Database Changes
1. Update `database/schema.sql`
2. Create migration scripts if needed
3. Update repository classes in `app/repositories/`

Remember: This codebase emphasizes clean architecture, comprehensive testing, and containerized development. Always run tests after changes and verify Docker environment functionality.