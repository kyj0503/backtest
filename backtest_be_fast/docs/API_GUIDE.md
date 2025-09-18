# API Guide — FastAPI backtesting service

This document describes the REST and WebSocket endpoints provided by the FastAPI backtesting service (`backtest_be_fast`). Routes are mounted under `/api/v1` when running the service.

Base URL (development): `http://localhost:8000` (service run by `run_server.py`)

Authentication:
- Uses `Authorization: Bearer <token>` for endpoints that require authentication (community, history, portfolio operations).

Key endpoints (examples):
- `POST /api/v1/auth/register` — register user
- `POST /api/v1/auth/login` — login
- `POST /api/v1/backtest/run` — run a single backtest (returns `BacktestResult`)
- `POST /api/v1/backtest/portfolio` — run portfolio backtest
- `POST /api/v1/backtest/execute` — unified execution endpoint
- `POST /api/v1/backtest/chart-data` — returns chart-ready data for frontend
- `GET /api/v1/backtest/metrics` — aggregated metrics
- `GET /api/v1/backtest/history` — user backtest history (requires auth)
- `GET /api/v1/strategies` — available strategies

WebSocket:
- `/api/v1/chat/ws/{room}` — WebSocket endpoint for chat (if enabled)

Documentation endpoints (Swagger / Redoc):
- `/api/v1/docs` and `/api/v1/redoc` when server is started with docs enabled.

Notes:
- Refer to `backtest_be_fast/app/models/requests.py` and `responses.py` for precise request/response schema definitions.
- Backtest payloads and responses are Pydantic models; validate requests using examples in `tests/fixtures`.
