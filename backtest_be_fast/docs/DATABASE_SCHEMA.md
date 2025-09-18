# Database Schema — FastAPI backtesting service

Two primary schemas are used by the FastAPI backtesting service:

1) Community / Users / Backtest history (MySQL)
- `users` (id, username, email, password_hash, investment_type, ...)
- `user_sessions` (id, user_id, session_token, expires_at, ...)
- `posts`, `post_comments`, `post_likes`
- `backtest_history` (id, user_id, backtest_type, parameters, results, ...)

2) Stock data cache (yfinance cache)
- `stocks`, `daily_prices`, `dividends`, `stock_splits`, `exchange_rates`, `cache_metadata`

Refer to `backtest_be_fast/database/yfinance.sql` for the canonical schema used for stock data caching.
