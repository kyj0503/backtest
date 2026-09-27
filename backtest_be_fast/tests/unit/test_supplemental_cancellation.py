"""부가 데이터 시간 예산(A-08)과 작업 취소(A-05)의 결합 테스트

두 변경은 따로 만들어졌다. A-08은 시간 예산을 넘긴 부가 수집을 기다리지 않고
반환하고, A-05는 작업이 만든 스레드가 계속 돌지 않게 취소 토큰으로 멈춘다.
합친 뒤에는 다음 두 가지가 성립해야 한다.

- 예산을 넘긴 수집 스레드는 하위 토큰 취소로 다음 확인 지점에서 곧바로 멈춘다
  (기다리지 않고 반환하되, 남은 스레드가 계속 돌지 않는다).
- 작업 자체가 취소되면 부가 수집도 멈추고 BacktestCancelled가 전파된다.
"""
import threading
import time

import pytest

from app.core.cancellation import BacktestCancelled, CancelToken, bind_token, cancellable_sleep
from app.services.unified_data_service import UnifiedDataService

pytestmark = pytest.mark.unit


def _service_with_slow_news(stopped: threading.Event, started: threading.Event) -> UnifiedDataService:
    """뉴스 수집만 오래 걸리고(취소 확인 지점 포함) 나머지는 즉시 빈 값인 서비스."""
    service = UnifiedDataService()

    def slow_news(symbols, display_count):
        started.set()
        try:
            for _ in range(200):  # 최대 10초
                cancellable_sleep(0.05)
            return {s: [] for s in symbols}
        except BacktestCancelled:
            stopped.set()
            raise

    service.collect_latest_news = slow_news
    service.collect_ticker_info = lambda symbols: {}
    service.collect_exchange_data = lambda start, end: ([], {})
    service.collect_benchmark_data = lambda start, end: ([], [])
    return service


def _collect(service: UnifiedDataService, timeout_seconds: float):
    return service.collect_all_unified_data(
        ['AAPL'], '2024-01-01', '2024-06-30',
        include_stock_data=False, include_volatility_events=False,
        timeout_seconds=timeout_seconds,
    )


def test_budget_timeout_returns_without_waiting_and_stops_leftover_thread():
    stopped, started = threading.Event(), threading.Event()
    service = _service_with_slow_news(stopped, started)

    t0 = time.monotonic()
    result = _collect(service, timeout_seconds=0.3)
    elapsed = time.monotonic() - t0

    assert result['supplemental_status']['news'] == 'timeout'
    assert elapsed < 2.0, f"예산 초과 섹션을 기다렸다: {elapsed:.2f}s"
    # 남은 스레드가 10초를 다 채우지 않고 다음 확인 지점에서 멈춰야 한다
    assert stopped.wait(2.0), "예산을 넘긴 수집 스레드가 계속 돌았다"


def test_job_cancellation_stops_supplemental_collection_and_propagates():
    stopped, started = threading.Event(), threading.Event()
    service = _service_with_slow_news(stopped, started)
    job_token = CancelToken()

    def cancel_soon():
        started.wait(2.0)
        job_token.cancel("timeout")

    canceller = threading.Thread(target=cancel_soon)
    canceller.start()
    t0 = time.monotonic()
    with bind_token(job_token), pytest.raises(BacktestCancelled):
        _collect(service, timeout_seconds=30)
    canceller.join()

    assert time.monotonic() - t0 < 3.0, "작업 취소 후에도 예산(30초)까지 기다렸다"
    assert stopped.wait(2.0), "작업 취소가 부가 수집 스레드로 전파되지 않았다"


def test_without_job_token_budget_still_works():
    """토큰이 없는 호출(스크립트·단위 테스트)에서도 예산과 하위 토큰이 동작한다."""
    stopped, started = threading.Event(), threading.Event()
    service = _service_with_slow_news(stopped, started)

    result = _collect(service, timeout_seconds=0.3)

    assert result['supplemental_status']['news'] == 'timeout'
    assert stopped.wait(2.0)
