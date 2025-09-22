# AI Coding Agent Instructions

Project: Backtesting System (FastAPI + Spring Boot + React + DDD-in-progress + CQRS/Event patterns)

## 1. Big Picture
- Monorepo with three main top-level apps: `backtest_be_fast/` (FastAPI for backtesting), `backtest_be_spring/` (Spring Boot for community, chat, auth, and member features), and `backtest_fe/` (React/Vite/Tailwind + shadcn/ui) plus infra (`compose/`, `scripts/`, `database/`, `docs/`).
- Backend layering (current reality, not aspiration): service-centric; `domains/` gradually absorbing business concepts. CQRS + EventBus selectively wrap higher-level operations (backtest execution, portfolio ops, optimization, metrics/alerts).
- Data flow (backtest): HTTP request -> Pydantic request model (`app/models/requests.py`) -> service / CQRS command -> domain services (if enhanced) -> repository (fetch/DB/yfinance) -> result aggregation -> optional domain analysis -> response model.
- Portfolio & optimization follow analogous command/query flow. Event handlers augment logging/metrics/alerts without coupling core logic.

- ## 2. Key Directories
- Top-level apps and important files:
- `backtest_be_fast/` - FastAPI app dedicated to backtesting.
- `backtest_be_fast/run_server.py` - quick local run script for the FastAPI service.
- `backtest_be_fast/app/` - FastAPI application code (services, cqrs, events, models, repositories, domains).
- `backtest_be_fast/requirements.txt` - Python deps for the backtesting service; `requirements-test.txt` for tests.
- `backtest_be_spring/` - Spring Boot app for community, chat, member and authentication features.
- `backtest_be_spring/build.gradle` - Gradle build for Spring Boot service; `src/main` and `src/test` contain Java/Kotlin sources and tests.
- `backtest_fe/` - Frontend React app using Vite, Tailwind and `shadcn/ui`.
- `backtest_fe/src/` - React source including `App.tsx`, `main.tsx`, `components/`, `features/`, and `test/` utilities.
- `compose/`, `scripts/`, `database/`, `docs/` - infra, helper scripts, DB fixtures, and documentation.

- In-repo FastAPI layout (inside `backtest_be_fast/app/`):
- `services/` - primary business logic (e.g., `backtest_service_old.py`, `enhanced_backtest_service.py`).
- `cqrs/` - command/query abstractions and handlers.
- `events/` - event bus and handlers.
- `models/` - Pydantic request/response/schemas and validators.
- `repositories/` - data access (DB cache + external fetches like yfinance).
- `domains/` - DDD entities/value objects and domain services (additive only).
- `scripts/verify-before-commit.sh` pre-commit CI mimic (Docker build + health probe).

## 3. Conventions & Patterns
- Python: Async where IO-bound (CQRS handlers/services). Type hints required; add validators via Pydantic `field_validator`. Keep domain additions additive (do not remove existing service method signatures).
- Commands/Queries: Always implement `validate()` and `_get_data()`. Weight totals: portfolio assets sum to 100 (percent) or 1.0 (weights) depending on context—mirror existing checks when extending.
- Enhanced services: subclass base service; extend via helper/private methods (`_enhance_*`) returning dict fragments; never mutate input arguments.
- Events: Subscribe new handlers by instantiation + `event_bus.subscribe(handler)` inside an initializer similar to `EventSystemManager.initialize()`. Handlers expose data retrieval helpers (`get_metrics_summary`, etc.).
- Testing markers aligned with `pytest.ini` (`unit`, `integration`, `e2e`, `slow`). New tests must choose one marker; avoid unmarked slow tests.
- Frontend components: functional components, hooks named `use*`. Uses `React`, `Vite`, `Tailwind CSS`, and `shadcn/ui` (component primitives). Co-locate tests as `*.test.tsx` or inside `src/test/` utilities.

- ## 4. Critical Workflows
- Dev stack: `docker compose -f compose.yml -f compose/compose.dev.yml up --build` (FastAPI backend 8001->8000, Spring Boot backend default 8080, frontend 5174, Redis 6379).
- FastAPI local (quick): `python run_server.py` from `backtest_be_fast/` (uses `settings.*`). Health endpoint: `http://localhost:8000/health`.
- Spring Boot local: from `backtest_be_spring/` run `./gradlew bootRun` or build with `./gradlew bootJar` then run the jar. Health endpoint: `http://localhost:8080/actuator/health` (if Spring Actuator is enabled).
- Frontend local: `npm install` then `npm run dev` from `backtest_fe/` (Vite dev server usually on `http://localhost:5174`).
- Tests (FastAPI): `pytest -q` from `backtest_be_fast/`. Coverage: `pytest --cov=app --cov-report=term-missing`.
- Tests (Spring Boot): use Gradle test tasks: `./gradlew test` from `backtest_be_spring/`.
- Tests (frontend): `npm run test:run` from `backtest_fe/`; coverage via `npm run test:coverage`.
- Pre-commit simulation: run `scripts/verify-before-commit.sh` (expects Docker daemon).

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
`backtest_be_fast/app/services/enhanced_backtest_service.py` - enrichment pattern
`backtest_be_fast/app/cqrs/service_manager.py` - handler registration contract
`backtest_be_fast/app/models/requests.py` - canonical input validation
`backtest_be_fast/app/core/config.py` - environment & CORS parsing
`backtest_be_fast/app/events/event_system.py` - handler lifecycle & status API

Spring Boot quick refs:
- `backtest_be_spring/build.gradle` - Gradle build; `src/main` contains application entrypoints and controllers.
- `backtest_be_spring/src/main/resources/application.yml` - environment profiles and actuator settings (if present).

Frontend quick refs:
- `backtest_fe/src/main.tsx` / `backtest_fe/src/App.tsx` - app entry points.
- `backtest_fe/package.json` - scripts: `dev`, `build`, `preview`, `test`.

## 10. When Unsure
Search adjacent service or handler for precedent; mirror structure & naming. Prefer additive over destructive edits.
이모티콘과 이모지를 절대 사용하지 마.


(End)
