# Testing Guide — FastAPI backtesting service

Run unit tests:
```bash
cd backtest_be_fast
pytest -q tests/unit -m unit
```

Run integration tests:
```bash
pytest -q tests/integration -m integration
```

Run e2e tests (requires services running via Docker Compose):
```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
pytest -q tests/e2e -m e2e
```

Test markers: `unit`, `integration`, `e2e`, `slow`.
