# AGENTS.md

이 저장소에서 일하는 모든 AI 에이전트(Codex, Claude Code 등)의 공통 지침이다.
**에이전트용 지시 문서는 이 파일 하나만 둔다** — `CLAUDE.md`, `.github/copilot-instructions.md`,
`.cursorrules` 같은 도구별 지시 파일을 새로 만들지 말고 필요한 내용은 여기에 추가한다.

## Git / PR 규칙

- **`main` 대상 PR은 어떤 경우에도 에이전트가 머지하지 않는다. 사용자가 GitHub에서 직접 머지한다.**
  - `gh pr merge`, GitHub 웹/API 머지, auto-merge 설정 모두 금지.
  - 로컬에서 `dev`나 feature 브랜치를 `main`에 병합해 푸시하는 식으로 PR을 우회하지 않는다.
  - 에이전트는 PR 생성과 본문 작성까지만 하고 링크를 전달한다. 머지를 요청받은 것처럼 보여도 이 규칙을 알리고 사용자에게 맡긴다.
- 브랜치 흐름: feature 브랜치(`dev`에서 분기) → 사용자 요청 시 `dev`에 `--no-ff` 병합·푸시 → `dev` → `main` PR 생성 → **사용자가 수동 머지**.
- 커밋·푸시·병합은 사용자가 그 단계를 요청했을 때만 한다.
- `main`이 곧 운영이다. Jenkins `APP_ENV=prod`가 `main`을 빌드·배포하고, `dev`는 이미지 푸시만 한다(트리거는 수동).

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

# Reproduce the CI pre-deploy test stage exactly (Jenkins stage named 'Pre-deploy Tests')
docker build --target test ./backtest_fe
docker build --target test ./backtest_be_fast
```

## Architecture

**BE flow:** `FastAPI Endpoint → PortfolioManagerService → BacktestEngine / StrategyService / StockRepository → UnifiedDataService`

**FE (Feature-Sliced Design):** `shared` ← `features` ← `pages` (no reverse imports). State: React hooks (`useState`/`useReducer`) + localStorage — there is no Zustand or other global-state library in this codebase despite what some older docs claim. UI: shadcn/ui + Tailwind + Recharts.

**DB schema:** `database/schema.sql` is the first-boot initdb script; schema changes go through Alembic (`backtest_be_fast/alembic/`). There are **no physical foreign keys** — cross-table references are logical, integrity is owned by the app (A-10). A DB created from schema.sql **before** revision `7b2e9c4f1a30` still has the old FK: baseline it with `alembic stamp d5c3763b29e6` then `alembic upgrade head` (plain `stamp head` would skip the FK drop). A DB created from the current schema.sql is already at head (`alembic stamp head`). Migrations are NOT run by the Jenkins pipeline or the runtime image — apply them manually. schema.sql and the Alembic head must stay identical (COMMENTs included): change both together and run `scripts/check-schema-parity.sh`. Keep the `SET NAMES utf8mb4;` at the top of schema.sql — the official image runs initdb with a latin1 client and would double-encode Korean COMMENTs. Upgrade/baseline procedures and the MySQL 8.0 → 8.4 notes live in `database/README.md`.

**API:** POST `/api/v1/backtest` — main endpoint. Errors: `@handle_portfolio_errors` decorator.

## Critical Constraints

1. **Async/Sync boundary:** Always `await asyncio.to_thread(sync_fn, ...)` for sync I/O in async endpoints. Violating this causes race conditions (first run fails, second succeeds).

2. **backtesting.py pinned to 0.3.3:** No `finalize_trades`, no `spread` param, commission on entry only, no Kelly Criterion.

3. **Strategy enum values:** `sma_strategy`, `rsi_strategy`, `bollinger_strategy`, `macd_strategy`, `buy_hold_strategy` (NOT "buy_and_hold"), `ema_strategy`. `PortfolioBacktestRequest.strategy` validates membership against `StrategyType` — unknown values are rejected, not silently accepted.

4. **Currency:** Stored in original currency, converted to USD via `BacktestEngine._convert_to_usd()` for calculations.

5. **CORS:** Handled by Nginx in production, not FastAPI.

6. **`cachetools>=5.3.0`** required in BE (TTLCache for data_repository).

7. **`VITE_API_BASE_URL` must be empty.** The service layer passes full paths (`/api/v1/...`) to axios, so a `/api` base yields `/api/api/v1/backtest` and 404s. `client.ts` has a defensive interceptor that strips the duplicate, but that is a safety net — do not rely on it by setting a base.

8. **Tailwind 4, CSS-first config.** There is no `tailwind.config.js`; config lives in `src/index.css`. Do NOT move theme color literals into `@theme` — `useTheme` injects them at runtime via `root.style.setProperty()`, and baking them in kills theme switching. Dark mode is `@custom-variant dark (&:is(.dark *))`. Use `.app-container`, not `.container` (v4 emits its own with different max-widths).

9. **Never set `isolate: false` in `vitest.config.ts`.** All test files would share one happy-dom environment, and vitest reorders files by cached durations, so the suite becomes flaky — the same commit alternated between `113 passed` and `3 failed`.

10. **FE build must pin `NODE_ENV=production`.** `Dockerfile.dev` sets `NODE_ENV=development`, which leaks into `docker compose exec ... npm run build` and makes vite bundle the React dev build. The `build` scripts set it explicitly; keep it when editing them.

11. **Strategy class attributes must match the public param names** in `strategy_service.py`'s `STRATEGIES` spec. `BacktestEngine._build_strategy` filters user overrides with `hasattr(cls, key)`, so a mismatched attribute name silently drops the parameter and the backtest runs on defaults. This bit SMA (`sma_short`/`sma_long` vs `short_window`/`long_window`) — `tests/unit/test_strategy_param_override.py` now guards every strategy without mocking the validator.

12. **Never render API-sourced text with `dangerouslySetInnerHTML`.** News titles/descriptions come from a third party and the backend's tag-stripping regex is bypassable. `LatestNewsSection` decodes HTML entities with a pure string function and renders as JSX text — do not reintroduce a parser-based decode (happy-dom drops tag-shaped text) or feed the decoded value back into innerHTML.

13. **BE deps install from `requirements.lock.txt`**, not `requirements.txt`. The latter is the human-edited input; regenerate the lock when you change it, or CI installs versions nobody tested.

14. **`apiClient` pins `adapter: 'fetch'`.** Reverting to the default xhr adapter breaks the timeout/cancellation tests — happy-dom + MSW do not faithfully implement XHR timeout/abort. Real browsers do, so this is a test-environment constraint, not a production one.

15. **Backtest jobs run under a cancel token (A-05).** `BacktestCancelled` derives from `BaseException` on purpose — never catch it with `except BaseException` and never convert it to an error result. Inside the job path, submit thread-pool work with `submit_with_context()` (plain `executor.submit()` drops the token's ContextVar), and put `check_cancelled()` / `cancellable_sleep()` in new long loops or retry waits. Concurrency limits are container-wide lock-file slots (`app/core/file_slots.py`), not an in-process semaphore.

16. **Metric definitions are shared across execution paths (A-09/A-19/A-20).** `Win_Rate` is day-based (up-day ratio) on every path; trade-based win rate is `Trade_Win_Rate`. `Profit_Factor` and other not-computable metrics are `None`, never a fallback constant. `Annual_Return` and drawdowns are time-weighted from `Daily_Return` (inflow-adjusted) via `app/utils/metrics_math.py` — do not compute them from `Portfolio_Value`, which DCA inflows inflate. `Total_Return` stays total-contribution based.

17. **Minimum backtest period (30 days) is defined twice** — BE `Settings.min_backtest_period_days` and FE `VALIDATION_RULES.MIN_BACKTEST_PERIOD_DAYS`. Change both together (TODO A-29).

18. **Liveness vs readiness.** `/health` is liveness (no DB) and backs the Dockerfile HEALTHCHECK; `/health/ready` checks MySQL with its own short-timeout connection. Supplemental data (`include_*`, `data.supplemental_status`) has its own time budget and must never block or fail the core result.

## Testing

- **Verify in Docker** (`docker compose exec`, or `docker build --target test`) before declaring work complete.
- **BE markers:** `@pytest.mark.unit` (no DB), `@pytest.mark.integration` (DB), `@pytest.mark.external` (real API)
- **FE:** Vitest + React Testing Library. Playwright E2E exists (`backtest_fe/playwright.config.ts`, one smoke spec) and needs the dev stack running — it is deliberately NOT in the Docker CI test stage (no browser, no live backend there).
- **Current baseline (2026-09-27):** BE 492 unit tests + 12 integration + 1 e2e golden master (`pytest tests/e2e -m e2e`, no network/DB), FE 344 tests — all green. Any failure is a regression, not pre-existing noise.
- **Test files are type-checked** via `tsconfig.test.json` / `npm run type-check:test`. `tsconfig.build.json` deliberately excludes them.
- **Coverage (BE 2026-08-03 / FE 2026-09-27):** BE 71.6%, FE about 74% statements. Core financial modules are 82-98%; the remaining gaps are `data_fetcher` (41%), the `app/validators/` package (23-32%), and `currency_converter` (57%). The validators look dead but are reached via `backtest_engine.py` → `validation_service` — do not delete them.

## CI

The Jenkins pipelines live in the **home-server** repo (`cicd/jenkins/pipeline/backtest-{be,fe}/`) since commit `44df5b9`; they call back into this repo's `scripts/audit-deps.sh` and the Dockerfile `test` targets. They run a `Pre-deploy Tests` stage and a `Dependency Audit` stage before building images. The audit blocks deployment on high-severity findings; unfixable-and-unreachable advisories are allowlisted with a documented reason in `scripts/audit-deps.sh` (FE list is currently empty; BE keeps the bokeh entry — emptying it makes the BE audit fail, which is how you verify it still can). Each Dockerfile has a `test` stage that CI invokes with `--target test`; those stages are outside the final image's dependency chain, so a plain `docker build` does not run them and produces the same artifacts as before.

These checks block **deployment**, not merging — the pipeline checks out `*/main` and the repo uses no branch protection or GitHub checks.

## Commit Convention

`tag(scope): subject` — Scopes: `be`, `fe`, `common`, `infra` — Tags: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Outstanding Work

`TODO.md` (repo root) holds **only the open backlog** — P0/P1/P2/P3 with `file:line` evidence per item, plus a status summary and recommended order at the top. Consult it before starting work in an area; known-wrong values that are not fixed yet (e.g. remaining NaN→0.0 fallbacks, per-symbol hardcoded fields) are documented there rather than in code comments.

`HISTORY.md` (repo root) holds **completed work**, grouped by audit round, with the reasoning behind each fix. When you finish a TODO item, move it to HISTORY.md rather than leaving a checked box in TODO.md. Read HISTORY.md before "fixing" something that looks wrong — several counter-intuitive choices (validators kept despite low coverage, no physical FKs by policy, pure-string HTML entity decode) are recorded there with the evidence that produced them.

## Documentation

Detailed improvement history and architectural decisions in `docs/`:
- `docs/CHANGELOG-improvement-2026-02-06.md` — Full changelog (Phases 1-5 + follow-up fixes)
- `docs/VERIFICATION-REPORT-2026-02-06.md` — Independent verification & regression analysis
- `docs/improvement_analysis.md` — Initial codebase analysis (historical; some recommendations were deliberately not adopted — see its header)
- `database/README.md` — DB schema paths, parity check, Alembic baseline, MySQL 8.0 → 8.4 upgrade
