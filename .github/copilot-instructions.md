# Copilot instructions for the backtest repo

This file gives focused, actionable guidance so an AI coding assistant can be immediately productive in this repository.

Key points (read before editing code)
- Project layout: `backtest_be_fast/` (FastAPI backend), `backtest_fe/` (React frontend). The FastAPI service is the primary target for AI changes.
- Architecture: DDD-inspired layered structure with CQRS and an EventBus. Main folders:
  - `app/api/` — request/response layer; endpoints are under `api/v1/endpoints`.
  - `app/services/` — business logic and backtest engine wrappers.
  - `app/domains/` — domain entities and models.
  - `app/repositories/` — persistence layer; prefer repository interfaces (`BacktestRepository`, `DataRepository`).
  - `app/cqrs/` — command/query definitions and base bus.
  - `app/events/` — EventBus and handlers for async side-effects.
  - `app/factories/` — `ServiceFactory` provides DI-style creation and singletons.

Run / debug (FastAPI)
- Local dev (no docker): `python run_server.py` from `backtest_be_fast/` — uses `uvicorn` and `app.core.config.settings`.
- With Docker Compose (recommended for full stack):
  - Start: `docker compose -f compose.dev.yaml up -d --build` (root `README.md` shows this).
  - Stop: `docker compose -f compose.dev.yaml down`.
- Entrypoint: `backtest_be_fast/entrypoint.sh` creates a virtualenv in container and installs `/requirements.txt` if missing.

Important conventions and patterns
- CQRS & handlers: Command and Query handlers are registered centrally in `app/cqrs/service_manager.py`. Add new handlers by registering them there (or call existing registration helper patterns).
- Service creation: Use `app/factories/service_factory.py` to construct services so tests and runtime share the same singletons (e.g., `service_factory.create_backtest_service()`). Avoid directly instantiating deep service classes unless necessary for tests.
- Repositories: Use repository interfaces and exported global instances (e.g., `backtest_repository`) from `app/repositories/__init__.py`. When writing code that needs DB access, depend on the repository abstraction.
- Settings: Configuration values come from `app/core/config.py` (`settings` global). Environment overrides are expected; `.env`/`.env.local` is used by Compose. Prefer reading `settings` instead of os.environ directly.
- API surface: Main router is mounted at `settings.api_v1_str` (default `/api/v1`). Endpoints are grouped under `api/v1/endpoints` (e.g., `backtest`, `strategies`).

Testing & dev notes
- There is a `TestServiceFactory` for unit tests that creates in-memory/mock repositories. Prefer it for unit-level service tests.
- Styles/tools: `black` and `isort` are in `requirements.txt` — follow the code formatting used in the repository.

Files to consult for context when editing
- `backtest_be_fast/app/main.py` — app lifespan, logging, health endpoint, and how server is launched.
- `backtest_be_fast/app/core/config.py` — env loading and defaults.
- `backtest_be_fast/app/cqrs/service_manager.py` — where handlers are registered and how the CQRS bus is used.
- `backtest_be_fast/app/factories/service_factory.py` — DI patterns and singleton caching.
- `backtest_be_fast/docs/04-Architecture.md` — high level architecture notes used by maintainers.

When making changes
- Preserve public function/class signatures unless you update all call sites (search for usages first).
- If adding a new API route: register it under `app/api/v1/endpoints`, add it to `api/router` in `app/api/v1/api.py`, and add docs/README note.
- If adding a new command/query: put definitions in `app/cqrs/commands.py` or `queries.py`, implement handlers in `app/cqrs/command_handlers.py` or `query_handlers.py`, and register in `cqrs/service_manager.py`.
- If the change affects configuration, update `app/core/config.py` and add a note in the root `README.md` and `backtest_be_fast/README.md` if it changes runtime behavior.

Examples
- Create a new backtest API endpoint:
  - add `backtest_be_fast/app/api/v1/endpoints/my_endpoint.py` with an APIRouter and route functions.
  - import and include it from `app/api/v1/api.py`.

- Register a new CQRS command:
  - add a dataclass to `app/cqrs/commands.py`.
  - implement `MyCommandHandler` in `app/cqrs/command_handlers.py` accepting required services.
  - register the handler in `app/cqrs/service_manager.py` using `cqrs_bus.register_command_handler(...)`.

Avoid these common mistakes
- Do not bypass `service_factory` to instantiate services in production code; it breaks the singleton and test swap assumptions.
- Do not hardcode credentials or secrets into code — `app/core/config.py` expects env vars and `.env` files.

If unclear or incomplete
- Ask for the specific runtime you want to target (local python, Docker Compose, or production container). I will update examples accordingly.

Please review and tell me which parts need more detail (examples, more file references, or additional run/debug commands).
