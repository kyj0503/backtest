# Frontend Testing Overview

## Test Locations

- `src/components/__tests__`: user-facing components (`ThemeSelector`, `ErrorBoundary`)
- `src/shared/**/__tests__`: shared hooks/utilities (`useForm`, `useAsync`, number/date helpers, `debounce`)
- `src/features/backtest/hooks/__tests__`: core domain hooks (`useBacktest`, `useBacktestForm`)
- `src/features/backtest/model/__tests__`: backtest form reducer/helpers
- `src/features/backtest/services/__tests__/backtestService.integration.test.ts`: MSW-backed API calls

Tests live alongside the code they cover, making maintenance straightforward.

## What’s Covered

| Area | Files | Purpose |
|------|-------|---------|
| Hooks | `useBacktest`, `useBacktestForm`, shared hooks | Success/error handling, state transitions (AAA pattern) |
| Reducer | `backtestFormReducer`, helpers | Amount/weight conversions, validation messages |
| Services | `BacktestService` integration | Validates axios requests/responses through MSW |
| Components | `ThemeSelector`, `ErrorBoundary` | User interactions and accessibility hints |
| Utilities | `shared/utils` | Pure function behaviour, fake timers for `debounce` |

E2E tests are not yet implemented; start with Playwright/Cypress if a full flow check becomes necessary.

## How to Run

```bash
# Local one-off run
npm run test:run

# Specific file
npx vitest run src/features/backtest/hooks/__tests__/useBacktest.test.ts

# Docker workflow (keeps parity with compose setup)
export REDIS_PASSWORD=change-me-dev-redis-pass
cd /home/kyj/backtest
docker compose -f compose/compose.dev.yaml up -d backtest_fe
docker compose -f compose/compose.dev.yaml exec backtest_fe npm run test:run
docker compose -f compose/compose.dev.yaml down
```

Vitest uses `src/test/setup.ts` to attach Testing Library matchers, start/stop the MSW server, and mock required browser APIs. Coverage can be generated with `npm run test:coverage` (reports saved under `coverage/`).
