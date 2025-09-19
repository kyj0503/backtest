# Repository Guidelines

## Project Structure & Module Organization
- `backtest_be_fast/`: FastAPI microservice; domain logic under `app/`.
- `backtest_be_spring/`: Spring Boot API; primary code lives in `src/main/java`.
- `backtest_fe/`: Vite + React client; feature modules in `src/features`, shared UI and utilities under `src/shared`.
- `database/`: SQL snapshots (`schema.sql`, `yfinance.sql`) used for schema updates.
- `compose/`: Central Docker Compose files for dev and production parity.

## Build and Development Commands
- Full stack: `docker compose -f compose/compose.dev.yaml up -d --build`; stop with `docker compose down`.
- FastAPI: `pip install -r requirements.txt`, then `uvicorn app.main:app --reload` or `python run_server.py`.
- Frontend: In `backtest_fe`, run `npm install`, `npm run dev` for Vite, `npm run build` for optimized assets, and `npm run lint` for ESLint.
- Spring: `./gradlew bootRun` for local API and `./gradlew build` for production artifacts. Devtools is enabled; in IntelliJ turn on `Build project automatically` and `compiler.automake.allow.when.app.running` to restart on save.

### API Documentation
- Spring Boot exposes Swagger UI at `http://localhost:8080/swagger-ui.html` once running. OpenAPI endpoints are under `/v3/api-docs/**` and are publicly accessible by default.

## Coding Style & Naming Conventions
- Python: PEP 8 via `black` (line length 88) and `isort`; snake_case modules, PascalCase classes, prefer typed interfaces.
- TypeScript/React: ESLint defaults, 2-space indentation, PascalCase components, camelCase hooks/services.
- Java: Use Java 17 features sparingly, keep Spring packages layered (`controller`, `service`, `config`).

## Testing Guidelines
- Automated unit test suites for FastAPI and frontend are not maintained; rely on manual QA and integration smoke checks when required.
- Spring Boot retains its Gradle test configuration; execute `./gradlew test` if Java tests are reintroduced.

## Commit & Pull Request Guidelines
- Write concise, imperative commit titles (e.g., `HMR 비활성화`, `compose 수정`) with optional bilingual context in the body.
- PRs should link issues, summarize risk/rollback, call out affected services, and attach UI screenshots or coverage diffs when applicable.
- Verify lint and a targeted `docker compose` smoke run before requesting review.

## Configuration & Ops Notes
- Provide `.env` files in `backtest_fe` and `backtest_be_fast`; for `backtest_be_spring` use `application.properties` plus an optional `.env` (copy from `.env.example`) to override sensitive values locally. Never commit secrets.
- Spring Boot pulls `.env` from its project root (same directory where you run `./gradlew bootRun`). Docker Compose uses the root `.env` for prod overrides.
- `database/schema.sql` defines the canonical MySQL schema; keep it in sync with JPA mappings (e.g., `users.investment_type` now uses `VARCHAR(20)` with a CHECK constraint). Document new environment keys in the relevant README when they’re introduced.
