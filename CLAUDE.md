# CLAUDE.md

## Project Overview

**라고할때살걸** — Korean trading strategy backtesting platform (SMA, RSI, MACD, Bollinger, EMA, Buy&Hold). Supports portfolios, DCA, rebalancing.

**Stack:** Python 3.11 / FastAPI | TypeScript / React / Vite | MySQL 8.0 (prod) / SQLite (tests) | Docker Compose | Jenkins CI/CD

## Commands

```bash
# BE tests (no DB)
pytest backtest_be_fast/tests/unit -v

# FE
cd backtest_fe && npm run dev | npm run build | npm test

# Docker (full stack)
docker compose -f compose.dev.yaml up -d --build
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit -v
docker compose -f compose.dev.yaml exec backtest-fe npm test
```

**URLs:** FE http://localhost:5173 | BE Docs http://localhost:8000/docs

## Architecture

**BE flow:** `FastAPI Endpoint → PortfolioManagerService → BacktestEngine / StrategyService / StockRepository → UnifiedDataService`

**FE (Feature-Sliced Design):** `shared` ← `features` ← `pages` (no reverse imports). State: Zustand (global) + `useReducer` (forms). UI: shadcn/ui + Tailwind + Recharts.

**DB:** `stocks`, `daily_prices`, `stock_news` (see `database/schema.sql`)

**API:** POST `/api/v1/backtest` — main endpoint. Errors: `@handle_portfolio_errors` decorator.

## Critical Constraints

1. **Async/Sync boundary:** Always `await asyncio.to_thread(sync_fn, ...)` for sync I/O in async endpoints. Violating this causes race conditions (first run fails, second succeeds).

2. **backtesting.py pinned to 0.3.3:** No `finalize_trades`, no `spread` param, commission on entry only, no Kelly Criterion.

3. **Strategy enum values:** `sma_strategy`, `rsi_strategy`, `bollinger_strategy`, `macd_strategy`, `buy_hold_strategy` (NOT "buy_and_hold"), `ema_strategy`

4. **Currency:** Stored in original currency, converted to USD via `BacktestEngine._convert_to_usd()` for calculations.

5. **CORS:** Handled by Nginx in production, not FastAPI.

6. **`cachetools>=5.3.0`** required in BE (TTLCache for data_repository).

## Sub-Agent Usage

When working on this codebase, **actively use specialized sub-agents** for better quality:
- **`frontend-developer`** for React/TypeScript component changes
- **`python-pro` / `fastapi-pro`** for BE service/API changes
- **`test-automator`** for writing tests
- **`code-reviewer` / `architect-review`** for reviewing changes before finalizing
- **`debugger`** when encountering errors
- **`Explore`** agent for broad codebase research

Always verify changes in Docker containers (`docker compose exec`) before declaring work complete.

## Testing

- **BE markers:** `@pytest.mark.unit` (no DB), `@pytest.mark.integration` (DB), `@pytest.mark.external` (real API)
- **FE:** Vitest + React Testing Library; Playwright for E2E
- 141 BE unit tests, 94+ FE tests

## Commit Convention

`tag(scope): subject` — Scopes: `be`, `fe`, `common`, `infra` — Tags: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Documentation

Detailed improvement history and architectural decisions in `docs/`:
- `docs/CHANGELOG-improvement-2026-02-06.md` — Full changelog (Phases 1-5 + follow-up fixes)
- `docs/VERIFICATION-REPORT-2026-02-06.md` — Independent verification & regression analysis
- `docs/improvement_analysis.md` — Initial codebase analysis
