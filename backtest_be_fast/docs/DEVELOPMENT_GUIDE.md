# Development Guide — FastAPI backtesting service

Prerequisites:
- Python 3.11+
- Docker (for compose-based development)
- MySQL and Redis are required when running full stack locally via Docker Compose

Quick start (compose):
```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Quick start (local, backend only):
```bash
cd backtest_be_fast
python run_server.py
```

Run tests:
```bash
cd backtest_be_fast
pytest -q
```

Notes:
- Configuration values are read from environment variables and `app/core/config.py`.
- Service wiring and factories live under `app/factories/` and `app/cqrs/service_manager.py`.
