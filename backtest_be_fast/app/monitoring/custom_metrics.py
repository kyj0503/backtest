"""Prometheus 커스텀 메트릭 정의

**티커 라벨 카디널리티 상한 (P2-15)**:
TICKER_POPULARITY_TOTAL은 사용자가 자유 입력으로 채우는 symbol 값을 label로
쓴다. 형식 검증(정규식)을 통과했더라도 실재하지 않는 티커거나, asset_type='cash'
항목의 임의 커스텀 이름일 수 있다. Prometheus Counter는 한 번 생성된 라벨
조합을 프로세스 생명주기 동안 절대 GC하지 않으므로, 공격자가 매 요청마다 다른
문자열을 보내면 시계열이 무한정 늘어나 메모리를 고갈시킬 수 있다(카디널리티
폭발). record_ticker_popularity()가 이 파일 밖에서 TICKER_POPULARITY_TOTAL에
라벨을 붙이는 유일한 진입점이 되도록 하고, 그 안에서 카디널리티를
_MAX_TRACKED_TICKERS로 제한한다 -- 상한을 넘는 새로운(=처음 보는) 티커는
'other' 라벨로 합쳐진다. 이미 추적 중인 티커는 계속 자기 라벨로 집계되므로
(실제로 인기 있는 티커일수록 초반에 캡을 채울 가능성이 높다) "어떤 티커가
인기있는지"라는 메트릭의 목적은 유지된다.
"""
from threading import Lock
from prometheus_client import Counter, Histogram

# 백테스트 실행 횟수 (성공/실패, 전략 타입별)
BACKTEST_EXECUTION_TOTAL = Counter(
    "backtest_execution_total",
    "Total number of executed backtests",
    ["strategy_type", "status"]
)

# 티커 인기 순위 (사용자들이 백테스트에 포함시킨 티커)
# 주의: 이 Counter에 직접 .labels(ticker=...)를 호출하지 말 것 -- 카디널리티가
# 무제한으로 늘어난다. 대신 아래 record_ticker_popularity()를 사용한다 (P2-15).
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

# --- 카디널리티 상한 설정 (P2-15) ---
_MAX_TRACKED_TICKERS = 200
_OTHER_TICKER_LABEL = "other"
_ticker_cardinality_lock = Lock()
_seen_tickers: set = set()


def record_ticker_popularity(ticker: str) -> None:
    """검증되지 않았을 수 있는 사용자 입력을 라벨로 직접 쓰지 않고, 카디널리티를
    제한해서 티커 인기도를 기록한다.

    최초로 등장하는 티커는 최대 _MAX_TRACKED_TICKERS개까지 고유 라벨로 추적한다.
    이미 추적 중인 티커는 계속 자신의 라벨로 집계되고, 캡을 넘어서 처음 보는
    티커는 전부 _OTHER_TICKER_LABEL로 합쳐진다 -- 이 Counter가 만들어내는 라벨
    종류의 총 개수는 절대 _MAX_TRACKED_TICKERS + 1(자기 자신 + other)을 넘지
    않는다.

    Args:
        ticker: 사용자가 입력한 심볼 문자열 (빈 값/공백도 안전하게 처리됨)
    """
    normalized = (ticker or "").strip().upper()
    if not normalized:
        label = _OTHER_TICKER_LABEL
    else:
        with _ticker_cardinality_lock:
            if normalized in _seen_tickers:
                label = normalized
            elif len(_seen_tickers) < _MAX_TRACKED_TICKERS:
                _seen_tickers.add(normalized)
                label = normalized
            else:
                label = _OTHER_TICKER_LABEL
    TICKER_POPULARITY_TOTAL.labels(ticker=label).inc()
