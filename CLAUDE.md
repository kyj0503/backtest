# CLAUDE.md

## Project Overview

**라고할때살걸** — Korean trading strategy backtesting platform (SMA, RSI, MACD, Bollinger, EMA, Buy&Hold). Supports portfolios, DCA, rebalancing.

## Commands

```bash
# Docker (full stack)
docker compose -f compose.dev.yaml up -d --build
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit -v
docker compose -f compose.dev.yaml exec backtest-fe npm test

# FE quality checks (all four run in CI)
docker compose -f compose.dev.yaml exec backtest-fe npm run lint
docker compose -f compose.dev.yaml exec backtest-fe npm run type-check       # prod code
docker compose -f compose.dev.yaml exec backtest-fe npm run type-check:test  # test code
docker compose -f compose.dev.yaml exec backtest-fe npm run test:run

# Reproduce the CI gate exactly (same as Jenkins 'Quality Gate' stage)
docker build --target test ./backtest_fe
docker build --target test ./backtest_be_fast
```

## Architecture

**BE flow:** `FastAPI Endpoint → PortfolioManagerService → BacktestEngine / StrategyService / StockRepository → UnifiedDataService`

**FE (Feature-Sliced Design):** `shared` ← `features` ← `pages` (no reverse imports). State: Zustand (global) + `useReducer` (forms). UI: shadcn/ui + Tailwind + Recharts.

**DB schema:** see `database/schema.sql`

**API:** POST `/api/v1/backtest` — main endpoint. Errors: `@handle_portfolio_errors` decorator.

## Critical Constraints

1. **Async/Sync boundary:** Always `await asyncio.to_thread(sync_fn, ...)` for sync I/O in async endpoints. Violating this causes race conditions (first run fails, second succeeds).

2. **backtesting.py pinned to 0.3.3:** No `finalize_trades`, no `spread` param, commission on entry only, no Kelly Criterion.

3. **Strategy enum values:** `sma_strategy`, `rsi_strategy`, `bollinger_strategy`, `macd_strategy`, `buy_hold_strategy` (NOT "buy_and_hold"), `ema_strategy`

4. **Currency:** Stored in original currency, converted to USD via `BacktestEngine._convert_to_usd()` for calculations.

5. **CORS:** Handled by Nginx in production, not FastAPI.

6. **`cachetools>=5.3.0`** required in BE (TTLCache for data_repository).

7. **`VITE_API_BASE_URL` must be empty.** The service layer passes full paths (`/api/v1/...`) to axios, so a `/api` base yields `/api/api/v1/backtest` and 404s. `client.ts` has a defensive interceptor that strips the duplicate, but that is a safety net — do not rely on it by setting a base.

8. **Tailwind 4, CSS-first config.** There is no `tailwind.config.js`; config lives in `src/index.css`. Do NOT move theme color literals into `@theme` — `useTheme` injects them at runtime via `root.style.setProperty()`, and baking them in kills theme switching. Dark mode is `@custom-variant dark (&:is(.dark *))`. Use `.app-container`, not `.container` (v4 emits its own with different max-widths).

9. **Never set `isolate: false` in `vitest.config.ts`.** All test files would share one happy-dom environment, and vitest reorders files by cached durations, so the suite becomes flaky — the same commit alternated between `113 passed` and `3 failed`.

10. **FE build must pin `NODE_ENV=production`.** `Dockerfile.dev` sets `NODE_ENV=development`, which leaks into `docker compose exec ... npm run build` and makes vite bundle the React dev build. The `build` scripts set it explicitly; keep it when editing them.

## Sub-Agent Usage

- **`Explore`** for broad codebase research (where does X live, how is Y wired)
- **`Plan`** for designing multi-step changes before writing code
- **`general-purpose`** for multi-step research/edit tasks that need their own context

Always verify changes in Docker containers (`docker compose exec`) before declaring work complete.

## Testing

- **BE markers:** `@pytest.mark.unit` (no DB), `@pytest.mark.integration` (DB), `@pytest.mark.external` (real API)
- **FE:** Vitest + React Testing Library; Playwright for E2E
- **Current baseline:** BE 141 unit tests, FE 113 tests — both fully green. Any failure is a regression, not pre-existing noise.
- **Test files are type-checked** via `tsconfig.test.json` / `npm run type-check:test`. `tsconfig.build.json` deliberately excludes them.

## CI

`Jenkinsfile` runs a `Quality Gate` stage (FE and BE in parallel) before building images. Each Dockerfile has a `test` stage that CI invokes with `--target test`; those stages are outside the final image's dependency chain, so a plain `docker build` does not run them and produces the same artifacts as before.

The gate blocks **deployment**, not merging — the pipeline checks out `*/main` and the repo uses no branch protection or GitHub checks.

## Commit Convention

`tag(scope): subject` — Scopes: `be`, `fe`, `common`, `infra` — Tags: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Documentation

Detailed improvement history and architectural decisions in `docs/`:
- `docs/CHANGELOG-improvement-2026-02-06.md` — Full changelog (Phases 1-5 + follow-up fixes)
- `docs/VERIFICATION-REPORT-2026-02-06.md` — Independent verification & regression analysis
- `docs/improvement_analysis.md` — Initial codebase analysis
