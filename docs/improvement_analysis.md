# Deep Dive Analysis & Improvement Report

**Project:** 라고할때살걸 — Trading Strategy Backtesting Platform
**Date:** 2026-02-06
**Scope:** Frontend, Backend, Architecture, Database, Infrastructure

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Frontend](#2-frontend)
3. [Backend](#3-backend)
4. [System Architecture](#4-system-architecture)
5. [Database](#5-database)
6. [Infrastructure](#6-infrastructure)
7. [Priority Matrix](#7-priority-matrix)
8. [Recommended Roadmap](#8-recommended-roadmap)

---

## 1. Executive Summary

### Critical Issues (Fix Immediately)

| # | Area | Issue | Location |
|---|------|-------|----------|
| 1 | Backend | Sync I/O blocks async event loop | `backtest.py:82`, `unified_data_service.py` |
| 2 | Backend | No unit tests for core business logic | `PortfolioManagerService`, `BacktestEngine` |
| 3 | Backend | Sequential per-stock backtest execution | `portfolio_manager_service.py:231` |
| 4 | Database | Unbounded in-memory cache (OOM risk) | `data_repository.py:45` |
| 5 | Infra | Secrets exposed in Git (.env committed) | `.env` |
| 6 | Infra | No test stage in CI/CD pipeline | `Jenkinsfile` |
| 7 | Frontend | Missing test coverage for core utilities | `dataSampling.ts`, `useChartData.ts` |

### Statistics

| Area | Findings | Critical | High | Medium | Low |
|------|----------|----------|------|--------|-----|
| Frontend | 25 | 1 | 10 | 9 | 5 |
| Backend | 29 | 3 | 11 | 9 | 6 |
| Architecture | 22 | 1 | 4 | 11 | 6 |
| Database | 22 | 5 | 0 | 8 | 9 |
| Infrastructure | 20+ | 5 | 6 | 5 | 4 |

---

## 2. Frontend

### 2.1 Performance

#### [HIGH] No Route-Level Code Splitting
- **Location:** `App.tsx`
- **Problem:** All pages are eagerly imported. `PortfolioPage` (largest) loads even when the user is on the landing page.
- **Fix:** Use `React.lazy()` + `Suspense` for route-level splitting:
  ```tsx
  const PortfolioPage = React.lazy(() => import('@/pages/PortfolioPage'));
  ```

#### [HIGH] Unused npm Dependencies Bloating Bundle
- **Location:** `package.json`
- **Problem:** `react-hook-form`, `zod`, `@hookform/resolvers`, `next-themes`, `cmdk`, `react-day-picker`, `react-resizable-panels`, `vaul` are declared but never imported.
- **Fix:** `npm uninstall` all unused packages.

#### [HIGH] Hero Image Not Optimized
- **Location:** `src/pages/landing/HeroSection.tsx:42`
- **Problem:** PNG with no `loading`, `width/height`, `srcset`, or modern format (WebP). Hurts LCP and CLS.
- **Fix:** Convert to WebP, add `srcSet`, set explicit dimensions.

#### [MEDIUM] `window.innerWidth` in useMemo with Missing Dependency
- **Location:** `EquityChart.tsx:50-58`
- **Problem:** `window.innerWidth` captured once; never updates on resize.
- **Fix:** Use a `useWindowWidth` hook and include in dependency array.

#### [MEDIUM] PerformanceMonitor Runs in Production
- **Location:** `PerformanceMonitor.tsx`
- **Problem:** `performance.mark()` and `console.log` execute regardless of environment.
- **Fix:** Guard with `if (import.meta.env.DEV)`.

### 2.2 State Management

#### [HIGH] useTheme Duplicates State Across Components
- **Location:** `shared/hooks/useTheme.ts`
- **Problem:** Each `useTheme()` call creates independent `useState`. `Header` and `App` can desync.
- **Fix:** Convert to Zustand store for single-source-of-truth.

#### [HIGH] Data Fetching Hooks Lack Cancellation
- **Location:** `useStockData.ts`, `useExchangeRate.ts`, `useVolatilityNews.ts`
- **Problem:** No `AbortController` — rapid parameter changes cause race conditions.
- **Fix:** Add `AbortController` in `useEffect`. Consider TanStack Query.

#### [MEDIUM] BacktestContext Defined But Never Used
- **Location:** `model/BacktestContext.tsx`
- **Problem:** Dead code. `useBacktestForm()` hook is used instead.
- **Fix:** Delete `BacktestContext.tsx`.

#### [MEDIUM] Duplicate Validation Logic (3 locations)
- **Locations:** `useFormValidation.ts`, `useBacktestForm.ts:121-145`, `backtestFormReducer.ts:366-419`
- **Fix:** Consolidate into a single validation function.

### 2.3 Component Structure (FSD)

#### [HIGH] Shared Hook Imports Feature Types (FSD Violation)
- **Location:** `shared/hooks/useFormValidation.ts:2` imports from `features/backtest/`
- **Fix:** Move to `features/backtest/hooks/` or make generic.

#### [HIGH] Duplicate API Client Architecture
- **Locations:** `shared/api/client.ts` (Axios) vs `features/backtest/api/backtestApi.ts` (fetch)
- **Problem:** Inconsistent error handling, headers, base URL resolution.
- **Fix:** Consolidate all API calls on `apiClient` (Axios).

### 2.4 Code Quality

#### [HIGH] Excessive `any` Types in Chart Pipeline
- **Location:** `useChartData.ts`, `chartDataTransform.ts`
- **Problem:** Undermines strict TypeScript. Runtime errors in chart transforms go uncaught.
- **Fix:** Replace `any` with types from `backtest-result-types.ts`.

#### [HIGH] Duplicate Type Definitions
- **Problem:** `EquityPoint`, `TradeMarker`, `NewsItem` defined 2-3 times with different shapes.
- **Fix:** Single canonical types per file, explicit naming for API vs frontend variants.

#### [MEDIUM] Hardcoded Dates in Initial Form State
- **Locations:** `backtest-form-types.ts:56` (`2025-01-01`) vs `backtestFormReducer.ts:302` (`2023-01-01`)
- **Fix:** Compute dynamically (1 year ago → today). Reuse `initialBacktestFormState` in RESET_FORM.

### 2.5 Testing

#### [CRITICAL] Core Utilities and Hooks Untested
- **Missing:** `dataSampling.ts` (736 lines), `useChartData.ts` (490 lines), `reportGenerator.ts` (357 lines), `backtestApi.ts`, `BacktestResults.tsx`
- **Fix:** Prioritize pure-function tests for `dataSampling`, `reportGenerator`, then hook tests.

### 2.6 Accessibility

#### [HIGH] Only One Global Error Boundary
- **Location:** `App.tsx:27`
- **Problem:** Chart error crashes entire app. User loses form state.
- **Fix:** Add granular error boundaries around chart sections.

#### [HIGH] Charts Lack ARIA Labels
- **Problem:** All Recharts SVG charts have no `role="img"`, no `aria-label`. WCAG 2.1 violation.
- **Fix:** Add `role="img"` and descriptive `aria-label` to chart containers.

#### [HIGH] Form Inputs Missing Label Associations
- **Location:** `PortfolioTable.tsx`, `PortfolioMobileCard.tsx`
- **Fix:** Add `<Label htmlFor="...">` with matching `id` on inputs.

---

## 3. Backend

### 3.1 Async/Sync Safety

#### [CRITICAL] UnifiedDataService Blocks Event Loop
- **Location:** `backtest.py:82` → `unified_data_service.collect_all_unified_data()`
- **Problem:** Synchronous method called from async endpoint. Makes sequential blocking I/O calls for stock data, exchange rates, benchmarks, and news. This is the exact race condition documented in `CLAUDE.md`.
- **Fix:** Wrap in `asyncio.to_thread()` or refactor to async with `asyncio.gather()`.

#### [HIGH] News Service Uses Blocking urllib
- **Location:** `news_service.py:84-140`
- **Problem:** `urllib.request.urlopen()` blocks event loop. With retries, can block 7+ seconds.
- **Fix:** Use `aiohttp` or ensure caller uses `asyncio.to_thread()`.

### 3.2 Performance

#### [CRITICAL] Sequential Per-Symbol Strategy Backtest
- **Location:** `portfolio_manager_service.py:231`
- **Problem:** `for idx, item in enumerate(request.portfolio)` runs 20 backtests sequentially.
- **Fix:** Use `asyncio.gather()` like `PortfolioDataLoader.load_stock_data_parallel()`.

#### [HIGH] Unbounded Memory Cache
- **Location:** `data_repository.py:45`
- **Problem:** `_memory_cache: Dict` grows without limit. Each entry is a full DataFrame. Missing `_calculate_hit_rate()` method would raise `AttributeError`.
- **Fix:** Use `cachetools.TTLCache(maxsize=500, ttl=3600)`.

#### [HIGH] Row-by-Row Currency Conversion
- **Location:** `currency_converter.py:199-217`
- **Problem:** Python `for` loop with per-row `DatetimeIndex` creation. The vectorized approach already exists in `portfolio_simulation_engine.py:192-208`.
- **Fix:** Vectorize with pandas: remove timezone once, reindex, multiply column.

#### [MEDIUM] Connection Pool Oversized
- **Location:** `pool_config.py:22-23` — `pool_size=40`, `max_overflow=80` = 120 connections
- **Problem:** MySQL default `max_connections=151`. With 17 workers = 2,040 potential connections.
- **Fix:** Reduce to `pool_size=5`, `max_overflow=15` (dev) / `pool_size=10`, `max_overflow=30` (prod).

### 3.3 Code Quality

#### [HIGH] 400+ Line Methods in PortfolioManagerService
- **Locations:** `run_strategy_portfolio_backtest()` (273 lines), `run_buy_and_hold_portfolio_backtest()` (424 lines)
- **Fix:** Extract statistics into `PortfolioMetrics`, trade logs into `TradeLogBuilder`, formatting into `BacktestResultFormatter`.

#### [HIGH] Conflicting Exception Hierarchies
- **Locations:** `core/exceptions.py` (HTTPException subclasses) vs `data_fetcher.py:12-21` (plain Exception subclasses)
- **Problem:** Same names (`DataNotFoundError`, `InvalidSymbolError`), different base classes.
- **Fix:** Single domain exception hierarchy. Map to HTTP in decorators only.

#### [HIGH] Swallowed Exceptions Drop Portfolio Symbols
- **Location:** `portfolio_manager_service.py:321-323`
- **Problem:** Failed symbols silently skipped. User sees "success" with fewer symbols than requested.
- **Fix:** Collect failures, return as `warnings` field in response.

#### [HIGH] BacktestEngine Fallback Masks Real Errors
- **Location:** `backtest_engine.py:79-105`
- **Problem:** Any error → fallback Buy & Hold result. Bugs never surface.
- **Fix:** Only fallback for known errors (insufficient data). Re-raise unexpected exceptions.

#### [HIGH] Global Singleton Proliferation / DI Container Unused
- **Problem:** 10+ module-level singletons. `ServiceContainer` exists but bypassed entirely.
- **Fix:** Choose one approach: either adopt `Depends()` or remove unused DI container.

### 3.4 Testing

#### [CRITICAL] No Tests for Core Business Logic
- **Missing:** `PortfolioManagerService`, `BacktestEngine`, `CurrencyConverter`, `PortfolioSimulationEngine`, `DataFetcher`, `UnifiedDataService`, `PortfolioDataLoader`
- **Existing:** ~1,800 lines across 13 files (strategies, schemas only)
- **Fix:** Prioritize `PortfolioManagerService`, `BacktestEngine`, `CurrencyConverter`.

#### [HIGH] No Async Test Coverage
- **Problem:** `asyncio_mode = strict` set but zero async tests exist.
- **Fix:** Add `@pytest.mark.asyncio` tests verifying `asyncio.to_thread()` usage.

### 3.5 Security

#### [MEDIUM] Hardcoded Default Secret Key
- **Location:** `config.py:90` — `secret_key = "your-secret-key-here"`
- **Fix:** Raise startup error if default is used in non-debug mode.

#### [MEDIUM] Debug Info Leak in Error Responses
- **Location:** `portfolio_manager_service.py:190-194` — `'error': str(e)`
- **Fix:** In production, return only error ID + generic message. Log full exception server-side.

---

## 4. System Architecture

### 4.1 Data Flow

#### [CRITICAL] Sequential Strategy Backtest (Same as 3.2)
The single most impactful performance bottleneck. 20-stock portfolio = 20 serial API + backtest calls.

#### [HIGH] Duplicate Data Loading (Backtest + Supplementary)
- **Location:** `backtest.py` endpoint flow
- **Problem:** Step 3 loads stock data for backtesting, then Step 6 re-fetches the same data via `unified_data_service.collect_stock_data()`.
- **Fix:** Share loaded data between backtest execution and supplementary data collection.

#### [HIGH] No Circuit Breaker for yfinance
- **Problem:** During Yahoo Finance outage, every request attempts 18 retries per symbol (3 retries x 3 range expansions x 2 methods). 20-stock portfolio = minutes of blocking.
- **Fix:** Implement simple state machine (closed/open/half-open) with configurable cooldown.

### 4.2 API Design

#### [MEDIUM] No Response Model on Main Endpoint
- **Location:** `backtest.py:28-35`
- **Problem:** No `response_model` → no OpenAPI docs, no validation, no client contract.
- **Fix:** Define `PortfolioBacktestResponse` Pydantic model. Eliminates `recursive_serialize()`.

#### [HIGH] Frontend-Backend Type Contract Drift
- **Problem:** Backend returns raw dicts, frontend defines TypeScript interfaces manually. No automated sync.
- **Examples:** Frontend `stats` vs backend `portfolio_statistics` key mismatch.
- **Fix:** Add `response_model` → generate TypeScript types from OpenAPI spec.

### 4.3 Resilience

#### [MEDIUM] Health Check Doesn't Verify Database
- **Location:** `main.py:99-120`
- **Problem:** Reports "healthy" even with dead database.
- **Fix:** Add DB connectivity check to `/health`.

#### [MEDIUM] No Distributed Tracing
- **Problem:** No request/correlation ID through service chain. Cannot trace slow requests.
- **Fix:** Add OpenTelemetry or simple request-scoped correlation ID.

---

## 5. Database

### 5.1 Schema

#### [MODERATE] `stock_news.ticker` Not a Foreign Key
- **Location:** `schema.sql`
- **Problem:** No referential integrity between `stock_news` and `stocks`.
- **Fix:** Add `FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE`.

#### [MINOR] Redundant Indexes
- `stocks.idx_ticker` — redundant with UNIQUE constraint
- `daily_prices.idx_stock_date_desc` — PK backward scan covers this
- `stock_news.idx_ticker` — subsumed by `idx_ticker_date`

### 5.2 Query Efficiency

#### [CRITICAL] Manual Connection Management (Leak Risk)
- **Location:** `yfinance_repository.py:249` — `conn = engine.connect()` without context manager
- **Fix:** Use `with engine.connect() as conn:` consistently.

#### [CRITICAL] `time.sleep(0.1)` in Data Load Path
- **Locations:** `yfinance_repository.py:456, 531, 554`
- **Problem:** 100-300ms per ticker of pure wait. 20-ticker portfolio = 2-6 seconds wasted.
- **Fix:** Remove sleeps. Restructure to read after commit without reconnection delay.

#### [MODERATE] Sequential Queries in UnifiedDataService
- **Location:** `unified_data_service.py:78-89`
- **Problem:** `for symbol in symbols:` loops sequentially.
- **Fix:** Parallelize like `PortfolioDataLoader.load_stock_data_parallel()`.

#### [MODERATE] Write Inside Read Method
- **Location:** `yfinance_repository.py:270-276` — UPDATE in `get_ticker_info_from_db()`
- **Fix:** Move mutation to separate `update_ticker_info()` method.

### 5.3 Connection Management

#### [CRITICAL] Pool Oversized (120 max connections)
- **Location:** `pool_config.py:22-23`
- **Fix:** Reduce to 5+15 (dev) / 10+30 (prod). Add MySQL server tuning config.

### 5.4 Migration Strategy

#### [P1] No Migration Tooling
- **Current:** Single `schema.sql` with `DROP TABLE IF EXISTS` (destructive).
- **Fix:** Adopt Alembic. Add `alembic upgrade head` to Docker startup.

### 5.5 Caching

#### [CRITICAL] Unbounded Memory Cache (Same as 3.2)

#### [MODERATE] Exchange Rates Not Cached in DB
- **Problem:** Fetched from yfinance on every non-USD portfolio backtest.
- **Fix:** Cache in `daily_prices` table or dedicated `exchange_rates` table.

---

## 6. Infrastructure

### 6.1 Security

#### [CRITICAL] Secrets Exposed in Git
- **Location:** `.env` is committed with real Naver API keys, DB passwords.
- **Immediate:** Revoke credentials, `git filter-branch` to remove from history, add `.env` to `.gitignore`.

### 6.2 CI/CD

#### [CRITICAL] No Test Stage in Pipeline
- **Location:** `Jenkinsfile` goes from checkout → build → deploy. No `pytest` or `npm test`.
- **Fix:** Add test stages before build. Fail pipeline on test failure.

#### [CRITICAL] Health Check Doesn't Fail Pipeline
- **Location:** `Jenkinsfile:98` — exits 0 on timeout, deployment stays.
- **Fix:** `exit 1` on health check failure. Add rollback mechanism.

### 6.3 Docker

#### [HIGH] No Multi-Stage Builds
- **Location:** Backend `Dockerfile` — single stage, ~830MB image.
- **Fix:** Multi-stage build → ~250MB. Separate test dependencies.

#### [HIGH] Containers Run as Root
- **Fix:** Add `USER` directive in Dockerfiles.

#### [HIGH] No Resource Limits
- **Location:** `compose.dev.yaml` — no `deploy.resources`
- **Fix:** Add CPU/memory limits to all services.

### 6.4 Nginx

#### [MEDIUM] Missing Security Headers
- **Location:** `nginx.prod.conf`
- **Fix:** Add `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `HSTS`, rate limiting.

### 6.5 Monitoring

#### [HIGH] No Observability
- **Problem:** Prometheus is in `requirements.txt` but metrics endpoint not fully configured. No log aggregation, no alerting.
- **Fix:** Configure Prometheus + Grafana + Loki stack. Add custom business metrics.

---

## 7. Priority Matrix

### Critical (Fix This Week)

| # | Issue | Area | Impact |
|---|-------|------|--------|
| 1 | Sync I/O blocks event loop | BE | Race conditions, frozen requests |
| 2 | No unit tests for core logic | BE | Regressions ship to production |
| 3 | Sequential backtest execution | BE/Arch | 5-20x slower multi-stock backtests |
| 4 | Unbounded memory cache | DB/BE | OOM crash under load |
| 5 | Secrets in Git | Infra | Credential theft |
| 6 | No CI test stage | Infra | Broken code reaches production |
| 7 | Manual connection management | DB | Connection pool drain |
| 8 | `time.sleep()` in data path | DB | 2-6s wasted per portfolio |

### High (Fix Within 2 Weeks)

| # | Issue | Area |
|---|-------|------|
| 9 | Missing FE test coverage | FE |
| 10 | Route code splitting | FE |
| 11 | useTheme state sync bug | FE |
| 12 | Duplicate API clients | FE |
| 13 | FSD violation in shared hook | FE |
| 14 | `any` types in chart pipeline | FE |
| 15 | Duplicate type definitions | FE |
| 16 | Chart accessibility (WCAG) | FE |
| 17 | Global error boundary only | FE |
| 18 | 400+ line methods | BE |
| 19 | Conflicting exception hierarchies | BE |
| 20 | Swallowed exceptions (silent failures) | BE |
| 21 | Fallback masks real errors | BE |
| 22 | Global singleton / unused DI | BE |
| 23 | No circuit breaker for yfinance | Arch |
| 24 | FE-BE type contract drift | Arch |
| 25 | No multi-stage Docker build | Infra |
| 26 | No monitoring/alerting | Infra |
| 27 | Health check doesn't fail pipeline | Infra |

### Medium (Fix Within 1 Month)

| # | Issue | Area |
|---|-------|------|
| 28 | Unused npm dependencies | FE |
| 29 | Hero image optimization | FE |
| 30 | Duplicate validation logic | FE |
| 31 | Dead BacktestContext code | FE |
| 32 | No response model on endpoint | BE |
| 33 | Connection pool oversized | BE/DB |
| 34 | Hardcoded default secret key | BE |
| 35 | Debug info leak in errors | BE |
| 36 | No migration tooling (Alembic) | DB |
| 37 | Exchange rates not cached | DB |
| 38 | Health check ignores DB | Arch |
| 39 | No distributed tracing | Arch |
| 40 | Nginx security headers | Infra |
| 41 | No resource limits | Infra |

---

## 8. Recommended Roadmap

### Phase 1: Critical Fixes (Week 1)

**Security:**
- [ ] Remove `.env` from Git history, add to `.gitignore`
- [ ] Revoke exposed Naver API credentials
- [ ] Rotate all passwords

**Backend Stability:**
- [ ] Wrap `collect_all_unified_data()` in `asyncio.to_thread()`
- [ ] Add LRU eviction to memory cache (`cachetools.TTLCache`)
- [ ] Remove `time.sleep(0.1)` calls in `yfinance_repository.py`
- [ ] Use `with engine.connect() as conn:` everywhere

**CI/CD:**
- [ ] Add `pytest tests/unit` stage to Jenkinsfile
- [ ] Add `npm test` stage to Jenkinsfile
- [ ] Fix health check failure logic (`exit 1` on timeout)

### Phase 2: Performance & Quality (Weeks 2-3)

**Backend Performance:**
- [ ] Parallelize strategy portfolio backtests with `asyncio.gather()`
- [ ] Vectorize currency conversion (remove Python for-loop)
- [ ] Reduce connection pool to `pool_size=10, max_overflow=30`
- [ ] Add circuit breaker for yfinance

**Backend Refactoring:**
- [ ] Consolidate exception hierarchies
- [ ] Break down 400+ line methods
- [ ] Add warnings for skipped symbols in response

**Frontend:**
- [ ] Add `React.lazy()` route-level code splitting
- [ ] Remove unused npm dependencies
- [ ] Fix `useTheme` → Zustand store
- [ ] Consolidate API clients (remove raw fetch)
- [ ] Add `AbortController` to data fetching hooks

**Testing:**
- [ ] Unit tests for `PortfolioManagerService`, `BacktestEngine`
- [ ] Tests for `dataSampling.ts`, `reportGenerator.ts`
- [ ] Async tests for key service methods

### Phase 3: Architecture & Infrastructure (Weeks 3-4)

**Architecture:**
- [ ] Add `response_model` to endpoint → generate FE types from OpenAPI
- [ ] Share loaded data between backtest and supplementary collection
- [ ] Add correlation ID for request tracing
- [ ] Enhance health check with DB connectivity

**Database:**
- [ ] Adopt Alembic for migrations
- [ ] Add MySQL custom config (`innodb_buffer_pool_size`, `max_connections`)
- [ ] Cache exchange rates in DB
- [ ] Remove redundant indexes

**Infrastructure:**
- [ ] Multi-stage Docker builds (830MB → 250MB)
- [ ] Add resource limits to `compose.dev.yaml`
- [ ] Set up Prometheus + Grafana monitoring
- [ ] Add Nginx security headers
- [ ] Add automated rollback on deploy failure

**Frontend Polish:**
- [ ] Add granular error boundaries around charts
- [ ] Add ARIA labels to all charts
- [ ] Add form label associations
- [ ] Delete dead code (`BacktestContext`, unused config)
- [ ] Fix duplicate type definitions

---

*Analysis conducted by 5 specialized agents examining all source files across the full stack.*
