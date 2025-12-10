from prometheus_client import Counter, Histogram

# 백테스트 실행 횟수 (성공/실패, 전략 타입별)
BACKTEST_EXECUTION_TOTAL = Counter(
    "backtest_execution_total",
    "Total number of executed backtests",
    ["strategy_type", "status"]
)

# 티커 인기 순위 (사용자들이 백테스트에 포함시킨 티커)
TICKER_POPULARITY_TOTAL = Counter(
    "ticker_popularity_total",
    "Total count of tickers included in backtests",
    ["ticker"]
)

# 백테스트 소요 시간 (순수 계산 시간)
BACKTEST_PROCESSING_SECONDS = Histogram(
    "backtest_processing_seconds",
    "Time spent processing backtest logic",
    ["strategy_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)
