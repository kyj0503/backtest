# Repository Guidelines

## Project Structure & Module Organization
- `backend/` — FastAPI app (`app/main.py`), domain modules, services, and `tests/`.
- `frontend/` — React + Vite + TypeScript (`src/`), Vitest tests, Tailwind.
- `compose/` — Docker Compose files (`compose.dev.yml`, `compose.prod.yml`).
- `scripts/` — Local CI helpers (`verify-before-commit.sh`).
- `docs/` — Architecture, testing, and commit conventions.
- `database/` — SQL schema and fixtures.

## Build, Test, and Development Commands
- Run dev stack (hot reload):
  - `docker compose -f compose.yml -f compose/compose.dev.yml up --build`
  - Backend: http://localhost:8001, Frontend: http://localhost:5174
- Backend local (alt): `cd backend && python run_server.py`
- Backend tests: `cd backend && pytest -q` (coverage: `pytest --cov=app --cov-report=term-missing`)
- Frontend dev: `cd frontend && npm ci && npm run dev`
- Frontend tests: `cd frontend && npm run test:run` (coverage: `npm run test:coverage`)
- Lint/format:
  - Python: `cd backend && black . && isort . && flake8 && mypy app/`
  - Frontend: `cd frontend && npm run lint && npm run type-check`

## Coding Style & Naming Conventions
- Python: Black (PEP8, practical 88/100-char), isort (stdlib/third-party/local), type hints required in `app/`.
- TypeScript/React: ESLint defaults, functional components, hooks prefix `use*`, filenames `PascalCase.tsx` for components, `camelCase.ts` for utils.
- Tests live next to code (frontend) or under `backend/tests/` with clear, descriptive names.

## Testing Guidelines
- Backend: pytest with markers (`unit`, `integration`, `e2e`). Async tests use `pytest-asyncio`.
- Frontend: Vitest + Testing Library; file pattern `*.test.ts(x)`.
- Aim for meaningful coverage of core services, strategies, and API endpoints.

## Commit & Pull Request Guidelines
- Use Conventional Commits (see `docs/COMMIT_CONVENTION.md`). Example: `feat(api): add portfolio optimization endpoint`.
- Enable hooks: `git config core.hooksPath .githooks` (runs `scripts/verify-before-commit.sh`).
- PRs: concise description, linked issues, test evidence (logs/screenshots for UI), pass CI, update docs when behavior changes.

## Security & Configuration
- Never commit secrets. Copy `.env.example` to `.env` in `backend/` and `frontend/`.
- Default ports: backend 8001, frontend 5174 (dev) / 8082 (prod). Redis at `redis://redis:6379/0`.

## Agent-Specific Instructions
- Follow this guide’s scope when editing files. Prefer minimal, focused diffs that keep existing structure and tooling intact.
