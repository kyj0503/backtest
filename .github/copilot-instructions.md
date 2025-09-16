# AI Coding Agent Instructions

Project: Backtesting System (FastAPI + React + DDD-in-progress + CQRS/Event patterns)

## 1. Big Picture
- Monorepo: `backend/` (FastAPI, evolving DDD, CQRS, events) + `frontend/` (React/Vite/Tailwind) + infra (`compose/`, `scripts/`, `database/`, `docs/`).
- Backend layering (current reality, not aspiration): service-centric; `domains/` gradually absorbing business concepts. CQRS + EventBus selectively wrap higher-level operations (backtest execution, portfolio ops, optimization, metrics/alerts).
- Data flow (backtest): HTTP request -> Pydantic request model (`app/models/requests.py`) -> service / CQRS command -> domain services (if enhanced) -> repository (fetch/DB/yfinance) -> result aggregation -> optional domain analysis -> response model.
- Portfolio & optimization follow analogous command/query flow. Event handlers augment logging/metrics/alerts without coupling core logic.

## 2. Key Directories
- `backend/app/services/` primary business logic (`backtest_service.py`, `enhanced_backtest_service.py`, `enhanced_portfolio_service.py`).
- `backend/app/cqrs/` command/query abstractions, handlers, `service_manager.py` orchestrator.
- `backend/app/events/` event bus + handlers (logging, metrics, alerts) (`event_system.py`).
- `backend/app/models/` Pydantic request/response/schemas; strict validation + examples.
- `backend/app/core/config.py` central settings (env via pydantic-settings) exposing computed CORS list.
- `backend/app/repositories/` data access (`backtest_repository.py`, `data_repository.py`) with DB cache + external fetch logic.
- `backend/app/domains/` emerging DDD entities/value objects/services; treat as enhancement layer, never break service contracts.
- `frontend/src/` React app: components, hooks, context, reducers; Vitest setup in `src/test/`.
- `scripts/verify-before-commit.sh` pre-commit CI mimic (Docker build + health probe).

## 3. Conventions & Patterns
- Python: Async where IO-bound (CQRS handlers/services). Type hints required; add validators via Pydantic `field_validator`. Keep domain additions additive (do not remove existing service method signatures).
- Commands/Queries: Always implement `validate()` and `_get_data()`. Weight totals: portfolio assets sum to 100 (percent) or 1.0 (weights) depending on context—mirror existing checks when extending.
- Enhanced services: subclass base service; extend via helper/private methods (`_enhance_*`) returning dict fragments; never mutate input arguments.
- Events: Subscribe new handlers by instantiation + `event_bus.subscribe(handler)` inside an initializer similar to `EventSystemManager.initialize()`. Handlers expose data retrieval helpers (`get_metrics_summary`, etc.).
- Testing markers aligned with `pytest.ini` (`unit`, `integration`, `e2e`, `slow`). New tests must choose one marker; avoid unmarked slow tests.
- Frontend components: functional components, hooks named `use*`. Co-locate tests as `*.test.tsx` or inside `src/test/` utilities.

## 4. Critical Workflows
- Dev stack: `docker compose -f compose.yml -f compose/compose.dev.yml up --build` (backend 8001->8000, frontend 5174, Redis 6379).
- Backend local (quick): `python run_server.py` (uses `settings.*`).
- Tests (backend): `pytest -q` (CI uses Dockerfile with `RUN_TESTS` arg). Coverage: `pytest --cov=app --cov-report=term-missing`.
- Tests (frontend): `npm run test:run`; coverage via `npm run test:coverage`.
- Pre-commit simulation: run `scripts/verify-before-commit.sh` (expects Docker daemon).
- Health endpoint: `/health` on backend container (used by script & Docker HEALTHCHECK).

## 5. Safe Extension Guidelines
- Add new strategy: update enum in `models/requests.py` (StrategyType) + implement logic in strategy/ or service layer; ensure parameter names match request schema.
- Add command/query: create class with validation, implement handler, register in `CQRSServiceManager._register_handlers()` (keep idempotence guard), expose public wrapper method if needed.
- Domain expansion: place new value objects/entities under appropriate `domains/<bounded_context>/`; keep them pure (no DB/HTTP); integrate by optional enrichment methods (`_analyze_*`).
- Events: Add handler under `events/handlers/`; register through `EventSystemManager` to avoid ad-hoc subscription scatter.

## 6. Error & Validation Nuances
- Dates must be `YYYY-MM-DD`; end_date strictly after start_date (see validators). Commission capped (<=0.1). Portfolio weights validated with tolerance (abs(total-100) <= 0.01) for percent form; separate commands may expect sum == 1.0 (rebalance) with 0.01 tolerance.
- Quality/analysis steps swallow exceptions and attach error fields while preserving base result (pattern: return dict with `analysis_error` / `..._available` flags). Follow this fail-soft model for new enrichment.

## 7. Performance & History
- CQRS bus limits history to 1000 entries; when adding heavy queries, keep result payload lean or paginate.
- Avoid synchronous blocking inside handlers; prefer async repository/service calls.

## 8. Do / Avoid
- Do: minimal diffs, preserve public service signatures, add tests with proper markers, reuse existing logging style (`logger.info/warning/error`).
- Avoid: introducing breaking enum changes, altering validation semantics silently, embedding secrets, bypassing central config or event registration patterns.

## 9. Quick Reference Files
`backend/app/services/enhanced_backtest_service.py` - enrichment pattern
`backend/app/cqrs/service_manager.py` - handler registration contract
`backend/app/models/requests.py` - canonical input validation
`backend/app/core/config.py` - environment & CORS parsing
`backend/app/events/event_system.py` - handler lifecycle & status API

## 10. When Unsure
Search adjacent service or handler for precedent; mirror structure & naming. Prefer additive over destructive edits.

(End)
