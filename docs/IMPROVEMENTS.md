# Project Improvements Plan

This document captures issues observed in the current codebase, suggested improvements, and a concrete TODO plan. It focuses on backtesting features, indicators, APIs, and the deployment setup.

## Problems & Deficiencies

- Missing indicator overlays in chart responses
  - RSI, Bollinger Bands, and MACD overlays are declared as supported strategies but their indicator arrays in `ChartDataResponse` are empty. See: backtest_be_fast/app/services/backtest/chart_data_service.py:292
  - Only SMA overlays are generated for SMA strategy.

- Trade markers not produced for algorithmic strategies
  - `trade_markers` are returned for Buy & Hold only; other strategies return an empty array. See: backtest_be_fast/app/services/backtest/chart_data_service.py:212
  - Per-trade data from Backtesting (`stats._trades`) is not surfaced.

- Benchmark analytics incomplete
  - `BacktestRequest` permits `benchmark_ticker`, and `BacktestResult` contains `alpha_pct` and `beta`, but alpha/beta are not computed in the backtest pipeline.

- Strategy catalog duplication in FE
  - The FE maintains a hardcoded strategy config while the BE exposes `/api/v1/strategies`. Divergence risks mismatch and additional maintenance.

- Compose path structure changed
  - Compose files moved to repo root, but `compose.dev.yaml` still referenced `../` paths. README and scripts referenced `compose/compose.dev.yaml`.

- Documentation drift
  - Several docs reference `compose/compose.dev.yaml` and `compose/compose.server.yaml` paths, and mention `compose.prod.yaml` which is being replaced by `compose.server.yaml`.

## Recommended Improvements

- Implement indicator overlays for all supported strategies
  - RSI line with overbought/oversold reference levels.
  - Bollinger upper/lower bands with mid SMA.
  - MACD line and Signal line (optionally histogram later).

- Extract trade markers
  - Map Backtesting results’ trade log to `TradeMarker` items (entry/exit, price, size, pnl%).

- Compute benchmark alpha/beta (optional in v1)
  - If `benchmark_ticker` provided, calculate daily returns regression to derive `alpha_pct` and `beta` and populate `BacktestResult`.

- FE strategy catalog integration
  - Fetch `/api/v1/strategies` to render parameter UIs dynamically; deprecate static config or keep as fallback.

- Compose & docs alignment
  - Keep `compose.dev.yaml` in repo root with `./` paths.
  - Use `compose.server.yaml` for production runtime; deprecate `compose.prod.yaml` in docs.

## TODOs (Prioritized)

1) Compose/dev ergonomics (done in this change)
   - Fix `compose.dev.yaml` relative paths to match new root placement.
   - Update README commands from `compose/compose.dev.yaml` to `compose.dev.yaml`.
   - Note `compose.prod.yaml` deprecation in README.

2) ChartData indicators (started)
   - Implement RSI, Bollinger, MACD indicator generation in ChartDataService.
   - Validate names, colors, and data shape with FE charts.

3) Trade markers (next)
   - Surface trade logs from Backtesting results; extend ChartDataService to include entry/exit markers.

4) Benchmark metrics (next)
   - Add optional alpha/beta computation when `benchmark_ticker` is provided.

5) FE strategy catalog (next)
   - Add a client service to fetch `/api/v1/strategies`; render controls dynamically.

6) Docs cleanup (follow-up)
   - Sweep docs for `compose/compose.dev.yaml` references and replace with `compose.dev.yaml`.
   - Replace `compose.prod.yaml` mentions with `compose.server.yaml` where appropriate.

## Work Started in This Commit

- Fixed compose paths and README to work with root-level compose files.
- Implemented RSI, Bollinger, and MACD overlays in ChartDataService so indicator lines appear on FE charts for those strategies.

