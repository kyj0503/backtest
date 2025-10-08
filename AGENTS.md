# Repository Guidelines

This monorepo contains a FastAPI back end, a React front end, shared Compose files, and SQL assets. Use the guidance below to contribute consistently.

## Project Structure & Modules
- `backtest_be_fast/` FastAPI service (app code under `app/`, tests under `tests/`).
- `backtest_fe/` React + TypeScript app (`src/`, tests in `__tests__` or `*.test.tsx`).
- Docker Compose files (`compose.dev.yaml`, `compose.server.yaml`).
- `database/` SQL init scripts. Root `.env.local` (dev) and `.env` (prod) load into services.

## Build, Test, and Run
- Dev stack: `docker compose -f compose.dev.yaml up -d --build`
- FastAPI (local): `cd backtest_be_fast && python run_server.py`
  - Tests: `pip install -r requirements.txt -r requirements-test.txt && PYTHONPATH=. pytest -v`
- Frontend: `cd backtest_fe && npm ci && npm run dev`
  - Tests: `npm run test:run`; Lint: `npm run lint`; Build: `npm run build`

## Coding Style & Naming
- Python: 4-space indent, type hints preferred. Format with Black and isort (`requirements.txt`). Modules `snake_case`, classes `PascalCase`, tests `test_*.py`.
- TypeScript/React: ESLint + TS strict. Components `PascalCase` in `.tsx`, hooks `use*`. Prefer named exports; co-locate tests as `*.test.ts[x]`.

## Testing Guidelines
- FastAPI: pytest markers available (`unit`, `integration`, `e2e`). Target coverage for `app`, see `pytest.ini`. Example: `pytest -m unit --cov=app`.
- Frontend: Vitest + Testing Library; run `npm run test:coverage` for reports. No hard threshold, but add/maintain tests for changed code.

## Commit & Pull Requests
- Prefer Conventional Commits with scope: `feat(frontend): ...`, `fix(fastapi): ...`. Short imperative subject; body explains what/why.
- PRs include: clear description, linked issues, screenshots for UI changes, test evidence, and notes on env/DB changes. Ensure CI passes and docs updated (`README.md`, `docs/`).

## Security & Configuration
- Do not commit secrets. Use root `.env.local` for dev and `.env` for prod. In Compose, service hosts are `mysql`, `redis`, `backtest_be_fast`.
