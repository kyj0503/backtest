# Architecture Guide — FastAPI backtesting service

High level:
- The FastAPI app implements a layered architecture inspired by DDD: `api/` (presentation), `services/` (application), `domains/` (domain), `repositories/` (infrastructure), and `events/` (integration/async hooks).

Key patterns:
- Commands/Queries (CQRS) implemented in `app/cqrs/` with handlers wired by `service_manager.py`.
- Event bus and handlers under `app/events/` for metrics, notifications, and async jobs.
- Pydantic models (v2) are the canonical request/response schemas in `app/models/`.

Databases and cache:
- Uses MySQL for persistent storage (community, history) and a cache for yfinance data. See `backtest_be_fast/database/yfinance.sql`.

Where to add new code:
- Application-level features belong in `services/` and should be implemented as async when IO-bound.
- New domain entities go to `domains/` and must avoid IO.
