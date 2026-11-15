"""Prometheus 커스텀 메트릭 정의

**티커 라벨 카디널리티 상한 (P2-15 → A-18)**:
TICKER_POPULARITY_TOTAL은 사용자가 자유 입력으로 채우는 symbol 값을 label로
쓴다. 형식 검증(정규식)을 통과했더라도 실재하지 않는 티커거나, asset_type='cash'
항목의 임의 커스텀 이름일 수 있다. Prometheus Counter는 한 번 생성된 라벨
조합을 프로세스 생명주기 동안 절대 GC하지 않으므로, 공격자가 매 요청마다 다른
문자열을 보내면 시계열이 무한정 늘어나 메모리를 고갈시킬 수 있다(카디널리티
폭발). record_ticker_popularity()가 이 파일 밖에서 TICKER_POPULARITY_TOTAL에
라벨을 붙이는 유일한 진입점이고, 라벨 결정은 TickerLabelPolicy가 한다.

P2-15의 첫 구현은 "처음 본 티커 200개 + other"(first-N-seen)였다. 프로세스
초반에 무작위 티커가 슬롯을 채우면 그 뒤의 실제 인기 티커가 전부 other로
묶였다(A-18). 지금 정책은 TickerLabelPolicy docstring 참고.
"""
import logging
import os
import re
from threading import Lock
from typing import Dict, FrozenSet, Iterable, Optional, Set

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import multiprocess

from app.constants.ticker_mapping import TICKER_TO_COMPANY_NAME

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


# --- 동시 실행 관측 (A-04/A-05 후속) ---
# 실행기(app/services/backtest_runner.py)의 실행 중·대기 중 작업 수. uvicorn 워커마다
# 따로 세고 /metrics(MultiProcessCollector)가 살아 있는 워커 값을 더한다(livesum).
# 전체 슬롯이 컨테이너 전체 상한이므로 running 합계는 max_concurrent_backtests를
# 넘지 않는다. 비멀티프로세스(개발·테스트)에서는 multiprocess_mode가 무시된다.
#
# livesum은 mark_process_dead(pid)가 불리기 전까지 죽은 워커의 파일도 더한다.
# uvicorn은 gunicorn의 child_exit 같은 훅이 없어, 작업 도중 죽은 워커(OOM kill 등)의
# +1이 컨테이너 재시작(entrypoint가 디렉터리를 비움)까지 남는다. 그래서 게이지를
# 만들기 전에 _purge_stale_live_gauge_files()로 정리한다. uvicorn이 죽은 워커를 새로
# 띄우면 그 워커가 이 모듈을 임포트하며 정리하므로, 죽은 워커의 값은 교체 워커가
# 뜰 때 사라진다.
_LIVE_GAUGE_FILE = re.compile(r"^gauge_live[a-z]+_(\d+)\.db$")

logger = logging.getLogger(__name__)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:  # 다른 사용자 프로세스 — 살아 있다
        return True
    except OSError:
        return False
    return True


def _purge_stale_live_gauge_files(path: Optional[str] = None) -> None:
    """죽은 pid와 자기 pid의 live 게이지 파일을 지운다.

    자기 pid도 지우는 이유: prometheus_client는 pid로 파일 이름을 정하고, 파일이 이미
    있으면 그 값을 이어받는다. 죽은 워커와 같은 pid를 새 워커가 받으면 이전 값이
    그대로 이어진다. 이 함수는 이 프로세스가 live 게이지를 만들기 전에(이 모듈 임포트
    시점) 불리므로 자기 pid 파일은 이전 프로세스의 것이다.
    """
    path = path or os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not path or not os.path.isdir(path):
        return
    own_pid = os.getpid()
    pids = set()
    for name in os.listdir(path):
        match = _LIVE_GAUGE_FILE.match(name)
        if match:
            pids.add(int(match.group(1)))
    for pid in pids:
        if pid == own_pid or not _pid_alive(pid):
            try:
                multiprocess.mark_process_dead(pid, path)
            except OSError as exc:  # 다른 워커가 먼저 지운 경우 등
                logger.debug("live 게이지 파일 정리 실패 pid=%s: %s", pid, exc)


_purge_stale_live_gauge_files()

BACKTEST_JOBS_RUNNING = Gauge(
    "backtest_jobs_running",
    "Backtest jobs holding a global concurrency slot (includes jobs still stopping after a 504)",
    multiprocess_mode="livesum",
)
BACKTEST_JOBS_WAITING = Gauge(
    "backtest_jobs_waiting",
    "Backtest requests waiting for a global concurrency slot",
    multiprocess_mode="livesum",
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


# --- 티커 라벨 정책 (P2-15 → A-18) ---
_OTHER_TICKER_LABEL = "other"

# 사전 허용 목록: 이 앱이 이미 알고 있는 종목(뉴스 검색어 매핑과 같은 목록) + 주요
# ETF. 항상 자기 라벨을 쓴다. 모든 워커가 같은 목록을 쓰므로 멀티프로세스 모드에서
# 워커별 값이 한 시계열로 합쳐진다.
_POPULAR_ETF_TICKERS = (
    "SPY", "QQQ", "VOO", "VTI", "IVV", "DIA", "IWM", "SCHD", "JEPI", "TQQQ", "SQQQ",
    "SOXL", "SOXX", "SMH", "ARKK", "GLD", "SLV", "TLT", "IEF", "SHY", "BND", "AGG",
    "VNQ", "VEA", "VWO", "EFA", "EEM", "XLK", "XLF", "XLE", "XLV", "BRK-B",
)
_STATIC_TICKER_ALLOWLIST: FrozenSet[str] = frozenset(
    t.strip().upper() for t in (*TICKER_TO_COMPANY_NAME.keys(), *_POPULAR_ETF_TICKERS)
)

_MAX_DYNAMIC_TICKERS = 30       # 워커(프로세스)당 동적 슬롯 수
_PROMOTION_MIN_COUNT = 3        # 보장 횟수가 이 이상이어야 동적 슬롯에 올린다
_CANDIDATE_CAPACITY = 500       # Space-Saving 후보 표 크기(메모리 상한)


def _normalize_ticker(ticker: Optional[str]) -> str:
    return (ticker or "").strip().upper()


class TickerLabelPolicy:
    """티커를 Prometheus 라벨 값으로 바꾸는 정책 (A-18).

    1. 허용 목록에 있으면 항상 자기 라벨.
    2. 목록 밖이면 Space-Saving(Metwally et al.) 후보 표로 빈도를 센다. 표가 가득
       차면 최소 count 항목을 내보내고, 새 항목은 그 count를 오차(error)로
       물려받는다. count - error는 실제 등장 횟수의 하한이므로, 이 "보장 횟수"가
       min_count 이상일 때만 동적 슬롯에 올린다. 한 번씩만 나오는 무작위 티커는
       보장 횟수가 1을 넘지 못해 슬롯을 차지할 수 없다 — first-N-seen과 달리
       초반 잡음이 인기 티커의 자리를 빼앗지 못한다.
    3. 동적 슬롯은 max_dynamic개까지이고 강등하지 않는다. prometheus_client는
       멀티프로세스 모드에서 라벨 삭제를 지원하지 않는다(remove()는 경고만 내고
       mmap 파일의 값은 남는다). 강등해도 노출 시계열은 줄지 않고 상한만 깨진다.
       재평가는 재배포 때 일어난다(entrypoint가 멀티프로세스 디렉터리를 비움).

    라벨 수 상한: 프로세스당 len(allowlist) + max_dynamic + 1(other).
    멀티프로세스(uvicorn --workers N): 워커마다 이 상태를 따로 가지므로
    /metrics 전체 상한은 len(allowlist) + N x max_dynamic + 1이다(죽었다 다시 뜬
    워커의 파일도 컨테이너 재시작 전까지 합산되므로 N은 "기동된 워커 프로세스 수").
    한 워커에서 승격되기 전 다른 워커의 같은 티커 요청은 other로 들어가므로, 동적
    라벨 값은 전체 요청 수의 하한이다. 허용 목록 티커는 이 문제가 없다.
    """

    def __init__(
        self,
        allowlist: Iterable[str] = _STATIC_TICKER_ALLOWLIST,
        max_dynamic: int = _MAX_DYNAMIC_TICKERS,
        min_count: int = _PROMOTION_MIN_COUNT,
        candidate_capacity: int = _CANDIDATE_CAPACITY,
    ):
        self.allowlist: FrozenSet[str] = frozenset(_normalize_ticker(t) for t in allowlist)
        self.max_dynamic = max_dynamic
        self.min_count = min_count
        self.candidate_capacity = candidate_capacity
        self._promoted: Set[str] = set()
        self._counts: Dict[str, int] = {}
        self._errors: Dict[str, int] = {}
        self._lock = Lock()

    @property
    def max_labels(self) -> int:
        """이 정책(프로세스 하나)이 만들 수 있는 라벨 종류 수의 상한."""
        return len(self.allowlist) + self.max_dynamic + 1

    def _observe(self, ticker: str) -> int:
        """Space-Saving 갱신 후 ticker의 보장 횟수(count - error)를 돌려준다."""
        if ticker in self._counts:
            self._counts[ticker] += 1
        elif len(self._counts) < self.candidate_capacity:
            self._counts[ticker] = 1
            self._errors[ticker] = 0
        else:
            victim = min(self._counts, key=self._counts.__getitem__)
            floor = self._counts.pop(victim)
            self._errors.pop(victim, None)
            self._counts[ticker] = floor + 1
            self._errors[ticker] = floor
        return self._counts[ticker] - self._errors[ticker]

    def label_for(self, ticker: Optional[str]) -> str:
        normalized = _normalize_ticker(ticker)
        if not normalized:
            return _OTHER_TICKER_LABEL
        if normalized in self.allowlist:
            return normalized
        with self._lock:
            if normalized in self._promoted:
                return normalized
            if len(self._promoted) >= self.max_dynamic:
                return _OTHER_TICKER_LABEL
            if self._observe(normalized) >= self.min_count:
                self._promoted.add(normalized)
                self._counts.pop(normalized, None)
                self._errors.pop(normalized, None)
                return normalized
        return _OTHER_TICKER_LABEL


_ticker_label_policy = TickerLabelPolicy()


def record_ticker_popularity(ticker: str) -> None:
    """검증되지 않았을 수 있는 사용자 입력을 라벨로 직접 쓰지 않고, 카디널리티를
    제한해서 티커 인기도를 기록한다 (라벨 결정은 TickerLabelPolicy).

    Args:
        ticker: 사용자가 입력한 심볼 문자열 (빈 값/공백도 안전하게 처리됨)
    """
    label = _ticker_label_policy.label_for(ticker)
    TICKER_POPULARITY_TOTAL.labels(ticker=label).inc()
