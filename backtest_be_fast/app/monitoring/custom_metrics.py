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

# 백테스트 요청의 단계별 소요 시간 (A-08 계측)
# stage 라벨은 코드가 정하는 고정 집합(BACKTEST_STAGES)이다 — 사용자 입력이 아니므로
# 카디널리티 걱정이 없다. simulation은 BACKTEST_PROCESSING_SECONDS와 같은 구간을
# 재지만, 부가 데이터 단계와 한 메트릭에서 나란히 비교하려고 여기에도 기록한다.
# 부가 데이터 단계는 병렬로 돌므로 단계별 합이 supplemental_total보다 클 수 있다.
BACKTEST_STAGES = (
    "simulation",          # 시뮬레이션(전략/Buy&Hold 계산, 입력 주가 로드 포함)
    "ticker_info",         # 종목 메타데이터(DB 일괄 조회)
    "price_history",       # 원본 주가 히스토리 조회(심볼별 병렬)
    "exchange_rates",      # 환율 조회 + 통계
    "benchmarks",          # S&P 500 / NASDAQ 지수 조회
    "news",                # 뉴스(DB 캐시 우선, 없으면 네이버 API)
    "stock_data",          # 원본 주가를 응답 형식으로 변환
    "volatility_events",   # 급등락 이벤트 계산
    "supplemental_total",  # 부가 데이터 수집 전체(병렬 구간 + 후처리)
)
BACKTEST_STAGE_SECONDS = Histogram(
    "backtest_stage_duration_seconds",
    "Time spent in each stage of a single backtest request",
    ["stage"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)


def observe_stage(stage: str, seconds: float) -> None:
    """단계 소요 시간을 기록한다. 알 수 없는 stage는 무시한다(라벨 폭증 방지)."""
    if stage in BACKTEST_STAGES:
        BACKTEST_STAGE_SECONDS.labels(stage=stage).observe(seconds)


# 부가 데이터 섹션별 수집 결과 (A-08). 외부 Yahoo/Naver 장애를 readiness에 넣지 않는
# 대신(A-07) 여기서 관측한다 — 수집기는 외부 오류를 삼키고 빈 값을 돌려주므로
# "empty" 비율이 급증하면 외부 API 장애를 의심할 수 있다.
#   ok: 데이터 있음 / empty: 끝났지만 비어 있음 / skipped: 요청에서 끔 /
#   timeout: 시간 예산 초과 / error: 예상 못 한 예외
SUPPLEMENTAL_SECTIONS = (
    "ticker_info", "stock_data", "volatility_events", "exchange_rates", "benchmarks", "news",
)
SUPPLEMENTAL_OUTCOMES = ("ok", "empty", "skipped", "timeout", "error")
BACKTEST_SUPPLEMENTAL_OUTCOME_TOTAL = Counter(
    "backtest_supplemental_outcome_total",
    "Outcome of each supplemental data section attached to a backtest response",
    ["section", "outcome"],
)


def record_supplemental_outcome(section: str, outcome: str) -> None:
    """부가 데이터 섹션 결과를 센다. 고정 집합 밖의 값은 무시한다."""
    if section in SUPPLEMENTAL_SECTIONS and outcome in SUPPLEMENTAL_OUTCOMES:
        BACKTEST_SUPPLEMENTAL_OUTCOME_TOTAL.labels(section=section, outcome=outcome).inc()


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
