# AGENTS.md

이 저장소에서 일하는 모든 AI 에이전트(Codex, Claude Code 등)의 공통 지침이다.
**에이전트용 지시 문서는 이 파일 하나만 둔다** — `CLAUDE.md`, `.github/copilot-instructions.md`,
`.cursorrules` 같은 도구별 지시 파일을 새로 만들지 말고 필요한 내용은 여기에 추가한다.

## Git / PR 규칙

- **`main` 대상 PR은 어떤 경우에도 에이전트가 머지하지 않는다. 사용자가 GitHub에서 직접 머지한다.**
  - `gh pr merge`, GitHub 웹/API 머지, auto-merge 설정 모두 금지.
  - 로컬에서 `develop`이나 feature 브랜치를 `main`에 병합해 푸시하는 식으로 PR을 우회하지 않는다.
  - 에이전트는 PR 생성과 본문 작성까지만 하고 링크를 전달한다. 머지를 요청받은 것처럼 보여도 이 규칙을 알리고 사용자에게 맡긴다.
- 브랜치 흐름: feature 브랜치(`develop`에서 분기) → 사용자 요청 시 `develop`에 `--no-ff` 병합·푸시 → `develop` → `main` PR 생성 → **사용자가 수동 머지**.
- 커밋·푸시·병합은 사용자가 그 단계를 요청했을 때만 한다.
- `main`만 운영 환경에 배포하고 `develop`은 CI 검증만 수행한다. GitHub Actions가 Docker 검증 후 ARM64 이미지를 digest로 배포한다. 개발 앱·DB는 로컬 Compose에서 실행한다.

## Project Overview

Frontend lives in the independent `kyj0503/backtest-console` repository; this repository owns the backend, database schema, and backend deployment.

**라고할때살걸** — Korean trading strategy backtesting platform (SMA, RSI, MACD, Bollinger, EMA, Buy&Hold). Supports portfolios, DCA, cash, rebalancing, multi-currency (USD accounting).

The backend is **Go** (`backtest_be_go/`, chi on net/http, single static binary). It replaced the Python/FastAPI backend on 2026-11-15; the history and the calculation contract are in `docs/go-migration.md`.

## Commands

**Build, run and test only through Docker.** Do not install Go on the host or run `go` there; use `docker run golang:<pinned>` or the Dockerfile targets.

```bash
docker compose -f compose.dev.yaml up -d --build           # dev stack (go run + MySQL)
docker compose -f compose.dev.yaml restart backtest-be     # recompile after code changes
docker build --target test ./backtest_be_go                # gofmt, vet, staticcheck, go test -race
bash scripts/test-go-integration.sh                        # MySQL integration tests (go test -tags integration)
sh scripts/audit-deps.sh be                                # govulncheck
sh scripts/check-schema-parity.sh                          # schema.sql == goose head
docker compose -f compose.go-test.yaml up --build --abort-on-container-exit --exit-code-from e2e
```

## Architecture

**Request flow:** `chi router → api.Service (Turnstile → pydantic-style validation → admission gate) → marketdata.Source.Load → engine.Run (buyHold | technical → strategy.Run) → supplemental sections → JSON`

- `internal/marketdata`: Yahoo v8 chart client → MySQL snapshot cache → process memory cache, FX (`RateOn`).
- `internal/engine`: request model/validation, buy&hold daily simulation, technical aggregation, statistics, ordered response types.
- `internal/strategy`: indicators and the bar-by-bar fill engine (replaces backtesting.py).
- `internal/api`: handlers, pydantic-compatible 422 bodies, reference sections, Turnstile, client IP.
- `cmd/backtestctl`: `migrate status|up|detect|baseline`, `check-orphans`.

**DB schema:** `database/schema.sql` is the first-boot initdb script; schema changes go through goose migrations in `backtest_be_go/migrations/` (embedded in both binaries). There are **no physical foreign keys** — cross-table references are logical, integrity is owned by the app (A-10). schema.sql and the goose head must stay identical (COMMENTs included): change both together and run `scripts/check-schema-parity.sh`. Keep `SET NAMES utf8mb4;` at the top of schema.sql (the image's initdb client is latin1). Never edit an already-deployed migration file. Migrations are NOT run by CI or the runtime image; apply them manually with `backtestctl` after a backup. A DB without goose history must be baselined first (`migrate detect` → `migrate baseline <v>` → `migrate up`); `up` refuses to run on such a DB. See `database/README.md`.

**API:** POST `/api/v1/backtest` calculates; four GETs (`/prices`, `/exchange-rates`, `/benchmarks`, `/news`) load reference data on a separate gate. The console disables all POST `include_*` flags, renders the calculation first, then loads/retries each resource. See `docs/architecture/api-boundaries.md`.

## Critical Constraints

1. **Calculation contract.** The engine follows the corrected rust-migration contract (F01–F16, R01–R11, S01–S06, T01–T05) plus G01 (`docs/go-migration.md`). The acceptance standard is the invariant/ledger tests, not Python output. Never "fix" a difference by copying Python behaviour without checking the fix list.

2. **Fixtures are records, not oracles.** Never regenerate anything under `backtest_be_go/testdata/` from Go output (`testdata/README.md`).

3. **Strategy enum values:** `sma_strategy`, `rsi_strategy`, `bollinger_strategy`, `macd_strategy`, `buy_hold_strategy` (NOT "buy_and_hold"), `ema_strategy`. Unknown values are rejected.

4. **Strategy parameter names must match the public spec** in `internal/strategy/params.go` (same names as the old `STRATEGIES`). A mismatched name used to silently fall back to defaults (old rule 11).

5. **Currency:** Prices are stored in their original currency and converted to USD at calculation time with `marketdata.RateOn` (forward-fill only, never a future rate). Missing FX is an error, never a silent unconverted price.

6. **Price snapshots.** A ticker's cached prices are always one provider response, replaced atomically; never merge independently fetched adjusted ranges (F05). Reads use one REPEATABLE READ READ ONLY transaction. Bump `snapshotVersion` when the stored meaning changes.

7. **Cancellation.** Pass the request `context.Context` down every path; long loops check `ctx.Err()`. Slots are released only when the work has actually stopped. Do not start goroutines without a bound (errgroup with `SetLimit`, or the admission gate).

8. **Time and dates.** Calendar dates are `civil.Date` (day numbers). Exchange dates come from each timestamp's IANA zone rules. The MySQL session time zone is pinned to UTC; do not use `ParseTime` in the server for DATE columns.

9. **Metric definitions** (Total_Return vs Time_Weighted_Return, calendar-daily √365 risk, closed-trade Profit_Factor, `null` for undefined metrics) are shared across paths and documented in `docs/go-migration.md`. Do not substitute constants for undefined values.

10. **Minimum backtest period (30 days) is defined twice** — BE `MIN_BACKTEST_PERIOD_DAYS` and FE `VALIDATION_RULES.MIN_BACKTEST_PERIOD_DAYS`. Change both together (TODO A-29).

11. **Liveness vs readiness.** `/health` is liveness (no DB) and backs the Docker HEALTHCHECK; `/health/ready` checks MySQL with its own short-timeout connection. The runtime image has no shell or curl: use `/app/server -healthcheck <path>`. Supplemental data has its own time budget and must never block or fail the core result.

12. **CORS** is handled by Nginx, not the backend.

13. **Never render API-sourced text with `dangerouslySetInnerHTML`** (console). News text is cleaned by `news.Clean` but the console must still render it as plain text.

### Frontend constraints (backtest-console repository)

- **`VITE_API_BASE_URL` must be empty.** The service layer passes full paths (`/api/v1/...`), so a `/api` base yields `/api/api/v1/backtest`.
- **Tailwind 4, CSS-first config.** No `tailwind.config.js`; do not move theme color literals into `@theme`. Use `.app-container`, not `.container`.
- **Never set `isolate: false` in `vitest.config.ts`.** **FE build must pin `NODE_ENV=production`.** **`apiClient` pins `adapter: 'fetch'`.**

## Testing

- **Verify in Docker** before declaring work complete (commands above). Any failure is a regression, not pre-existing noise.
- **Go test tags:** default (no DB, no network), `integration` (needs `TEST_MYSQL_ROOT_DSN`; run via `scripts/test-go-integration.sh`), `external` (real Yahoo), `diff` (rust-migration differential, `scripts/diff-rust-reference.sh`).
- **Baseline (2026-11-15):** unit tests in 11 packages pass with `-race`; integration tests (migrate, marketdata store) pass on MySQL; console E2E (`compose.go-test.yaml`) passes; the engine matches the rust-migration implementation on all 64 parity inputs within ~1e-13 relative.

## CI

GitHub Actions lives in `.github/workflows/cicd.yml`. PRs to main/develop and pushes to either branch run the Docker test stage, MySQL integration tests, dependency audit, schema parity, and the runtime build. Only main publishes an ARM64 `ghcr.io/kyj0503/backtest` image and deploys its immutable digest through Tailscale and pinned SSH. Runtime credentials stay in `/opt/backtest/production/.env` and are never committed.

The dependency audit (`govulncheck`) has no exceptions; do not weaken it. Deployment checks `/health/ready` after Docker liveness succeeds and restores the previous release on failure. CI does not migrate a deployed DB. Shared gateway configuration is managed outside this repository at `/opt/gateway`.

## Commit Convention

`tag(scope): subject` — Scopes: `be`, `fe`, `common`, `infra` — Tags: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Outstanding Work

`TODO.md` (repo root) holds **only the open backlog**. Consult it before starting work in an area.

`HISTORY.md` (repo root) holds **completed work** with the reasoning behind each fix. When you finish a TODO item, move it to HISTORY.md rather than leaving a checked box in TODO.md. Read HISTORY.md before "fixing" something that looks wrong.

## Documentation

- `docs/go-migration.md` — Go migration decisions, calculation contract, metric changes vs the Python backend, DB cutover
- `docs/go-migration-plan.md` — the approved migration plan
- `docs/architecture/api-boundaries.md` — calculation vs reference reads, limits, Turnstile
- `database/README.md` — schema paths, parity check, goose baseline, MySQL 8.0 → 8.4 notes
- `backtest_be_go/testdata/README.md` — fixture provenance
- Older reports under `docs/` (CHANGELOG, VERIFICATION-REPORT, reviews) describe the Python backend and are kept as history.
