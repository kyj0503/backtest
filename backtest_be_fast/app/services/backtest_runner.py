"""백테스트 작업 실행기: 컨테이너 전체 동시 실행 상한 · IP별 상한 · 타임아웃 · 취소

A-04 / A-05 / A-06을 한곳에서 처리한다. 엔드포인트
(app/api/v1/endpoints/backtest.py)는 작업 코루틴을 만들어 `run()`에 넘기기만 한다.

요청 한 건의 흐름
=================

1. **IP별 슬롯** (A-06, `max_concurrent_backtests_per_client`, 기본 2):
   즉시 시도하고, 없으면 대기 없이 **429** + Retry-After. 대기 중인 요청도 한 건으로
   센다(한 IP가 대기열을 채우지 못하게). 클라이언트를 식별할 수 없으면 건너뛴다
   (app/core/client_ip.py).
2. **전체 슬롯** (A-04, `max_concurrent_backtests`, 기본 8): 락 파일 슬롯
   (app/core/file_slots.py)이라 uvicorn 워커 수와 무관한 컨테이너 전체 상한이다.
   비어 있지 않으면 `backtest_queue_timeout_seconds`(기본 30초)까지 짧은 간격으로
   재시도하며 기다리고, 넘으면 **503** + Retry-After(작업은 시작하지 않음).
   대기 순서는 FIFO가 아니다(프로세스 간 폴링).
3. **실행**: 작업 전용 스레드에서 **작업 전용 이벤트 루프**(`asyncio.run`)로 작업
   코루틴을 돌린다. `backtest_timeout_seconds`(기본 60초)를 넘으면 **504**를 즉시
   반환하고 취소 신호를 보낸다. 클라이언트가 연결을 끊어도 같은 취소 신호를 보낸다.
4. **슬롯 반환**: 작업 스레드의 finally에서만 반환한다. 즉 504를 돌려준 뒤에도
   작업이 실제로 멈출 때까지 두 슬롯 모두 계속 점유된다(A-05). 과거에는
   `wait_for`의 코루틴 취소와 함께 세마포어가 먼저 풀려, 아직 도는 스레드 위에 새
   요청이 추가로 실행됐다.

왜 작업 전용 이벤트 루프인가 (A-05)
=====================================

파이썬 스레드는 밖에서 멈출 수 없다. 대신 멈출 수 있는 지점을 최대한 늘렸다.

- **await 지점**: 작업 코루틴을 전용 루프의 태스크로 돌리므로, 취소 신호가 오면
  `loop.call_soon_threadsafe(task.cancel)`로 그 태스크를 취소한다. 종목별 처리 사이,
  외부 수집 사이 등 **모든 await가 취소 지점**이 된다. 메인 루프에서 코루틴을 취소하는
  것과 달리, 전용 루프는 `asyncio.run`이 끝나기 전에 자신의 기본 스레드풀을 종료하며
  **아직 도는 to_thread 스레드를 끝까지 기다린다** — 그래서 작업 스레드가 끝났다는
  것은 그 작업이 만든 스레드가 모두 끝났다는 뜻이고, 슬롯 반환 시점이 정확해진다.
- **스레드 안의 긴 구간**: `app.core.cancellation.check_cancelled()` /
  `cancellable_sleep()`을 시뮬레이션 일별 루프, Yahoo 다운로드 재시도, DB 로드 재시도
  대기, 뉴스 재시도 대기에 넣었다. 부가 데이터 병렬 수집 스레드에는
  `submit_with_context()`로 토큰을 넘긴다.

**끊을 수 없는 구간과 최대 지연** (취소 신호 → 작업 종료):
- backtesting.py 0.3.3 `Backtest.run()` 한 번: 10년 일봉 기준 약 0.03~0.04초
  (로컬 측정, 전략 5종). 종목 사이는 await 지점이라 한 종목만 더 돈다.
- 외부 HTTP 호출 한 번(yfinance, 네이버 뉴스): 라이브러리 타임아웃까지(수 초~30초).
  재시도·백오프는 취소 지점이므로 "한 번"을 넘지 않는다.
- DB 쿼리 한 번: 커넥션 풀·MySQL 타임아웃까지.
- 판다스 벡터 연산(가격 정렬, 지표 계산): 수십 ms 단위.
이 상한을 넘으면(`backtest_cancel_grace_seconds`, 기본 15초) ERROR 로그를 남긴다.
슬롯은 그래도 강제로 반환하지 않는다.

관측
====

작업마다 `backtest job start`/`backtest job end` INFO 로그(벽시계 시각, 대기·실행
시간, 결과)를 남긴다. 멀티 프로세스 부하 측정에서 실제 동시 실행 수는 이 로그의
구간 겹침으로 계산한다.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import itertools
import logging
import os
import random
import threading
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from ..core.cancellation import BacktestCancelled, CancelToken, bind_token
from ..core.config import settings
from ..core.file_slots import FileSlot, FileSlotPool

logger = logging.getLogger(__name__)

# IP별 슬롯 파일 묶음 수. IP마다 파일을 만들면 IPv6 주소를 바꿔 가며 파일을 무한히
# 만들 수 있으므로 해시 버킷으로 상한을 둔다(파일 수 = 버킷 x IP별 상한).
# 서로 다른 IP가 같은 버킷에 걸리면 한도를 나눠 쓰게 되지만, 동시에 활성인 IP
# 수(전체 상한 8 + 대기열)에 비해 버킷이 충분히 많아 드물다.
CLIENT_BUCKETS = 4096

JobFactory = Callable[[], Awaitable[Any]]
DisconnectProbe = Callable[[], Awaitable[bool]]


class BacktestRejected(Exception):
    """작업이 결과 없이 끝났음을 알리는 예외. 엔드포인트가 HTTP 응답으로 바꾼다."""

    status_code = 500

    def __init__(self, detail: str, retry_after: Optional[int] = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.retry_after = retry_after


class ClientLimitExceeded(BacktestRejected):
    status_code = 429


class QueueTimeout(BacktestRejected):
    status_code = 503


class ExecutionTimeout(BacktestRejected):
    status_code = 504


class ClientDisconnected(BacktestRejected):
    # nginx가 "클라이언트가 먼저 끊음"에 쓰는 비표준 코드. 응답은 아무도 받지 않는다.
    status_code = 499


class BacktestJobRunner:
    def __init__(
        self,
        *,
        slot_dir: str,
        max_concurrent: int,
        per_client: int,
        queue_timeout: float,
        exec_timeout: float,
        cancel_grace: float,
        poll_interval: float = 0.05,
        disconnect_poll_interval: float = 1.0,
    ) -> None:
        self.max_concurrent = max(1, int(max_concurrent))
        self.per_client = int(per_client)
        self.queue_timeout = float(queue_timeout)
        self.exec_timeout = float(exec_timeout)
        self.cancel_grace = float(cancel_grace)
        self.poll_interval = float(poll_interval)
        self.disconnect_poll_interval = float(disconnect_poll_interval)
        self.slot_dir = slot_dir
        self.global_pool = FileSlotPool(slot_dir, "global", self.max_concurrent)
        self._client_pools: Dict[int, FileSlotPool] = {}
        self._client_pools_lock = threading.Lock()
        # 이 프로세스의 작업 스레드. 슬롯 없이 작업이 시작될 수 없으므로 프로세스당
        # 동시 작업 수는 전체 상한을 넘지 않는다.
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_concurrent, thread_name_prefix="backtest-job"
        )
        self._active = 0
        self._active_lock = threading.Lock()
        self._ids = itertools.count(1)
        self._background: Set[asyncio.Task] = set()

    # -- 진단 ---------------------------------------------------------------

    def active_jobs(self) -> int:
        """이 프로세스에서 아직 끝나지 않은 작업 스레드 수(504 이후 정리 중인 것 포함)."""
        with self._active_lock:
            return self._active

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)

    # -- 슬롯 ---------------------------------------------------------------

    def _client_pool(self, client_key: str) -> FileSlotPool:
        digest = hashlib.sha256(client_key.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % CLIENT_BUCKETS
        with self._client_pools_lock:
            pool = self._client_pools.get(bucket)
            if pool is None:
                pool = FileSlotPool(self.slot_dir, f"client-{bucket:04d}", self.per_client)
                self._client_pools[bucket] = pool
            return pool

    async def _wait_for_global_slot(
        self, is_disconnected: Optional[DisconnectProbe]
    ) -> FileSlot:
        # try_acquire는 로컬 락 파일 open + 논블로킹 flock뿐이라 이벤트 루프에서
        # 직접 호출해도 막히지 않는다(to_thread 왕복이 오히려 더 비싸다).
        loop_time = time.monotonic
        deadline = loop_time() + self.queue_timeout
        next_probe = loop_time() + self.disconnect_poll_interval
        while True:
            slot = self.global_pool.try_acquire()
            if slot is not None:
                return slot
            now = loop_time()
            if now >= deadline:
                raise QueueTimeout(
                    f"요청이 몰려 {self.queue_timeout:.0f}초 동안 기다렸지만 백테스트를 "
                    f"시작하지 못했습니다(동시 실행 {self.max_concurrent}건 사용 중). "
                    "잠시 후 다시 시도해주세요.",
                    retry_after=max(1, int(self.exec_timeout // 2)),
                )
            if is_disconnected is not None and now >= next_probe:
                next_probe = now + self.disconnect_poll_interval
                if await is_disconnected():
                    raise ClientDisconnected("클라이언트가 대기 중 연결을 끊었습니다.")
            jitter = random.uniform(0.5, 1.5)
            await asyncio.sleep(min(self.poll_interval * jitter, max(0.0, deadline - now)))

    # -- 실행 ---------------------------------------------------------------

    async def run(
        self,
        job_factory: JobFactory,
        *,
        client_key: Optional[str] = None,
        is_disconnected: Optional[DisconnectProbe] = None,
        label: str = "",
    ) -> Any:
        """슬롯을 얻어 작업을 실행하고 결과를 돌려준다.

        작업 안에서 난 예외는 그대로 전파된다(엔드포인트의 에러 매핑이 처리).
        상한·시간 초과·연결 끊김은 BacktestRejected 하위 예외로 알린다.
        """
        client_slot: Optional[FileSlot] = None
        if client_key and self.per_client > 0:
            client_slot = self._client_pool(client_key).try_acquire()
            if client_slot is None:
                logger.warning("백테스트 IP별 동시 실행 상한 초과: client=%s", client_key)
                raise ClientLimitExceeded(
                    f"같은 클라이언트에서 이미 {self.per_client}건의 백테스트가 실행 중입니다. "
                    "이전 요청이 끝난 뒤 다시 시도해주세요.",
                    retry_after=10,
                )

        wait_started = time.monotonic()
        try:
            global_slot = await self._wait_for_global_slot(is_disconnected)
        except BaseException:
            if client_slot is not None:
                client_slot.release()
            raise
        waited = time.monotonic() - wait_started

        token = CancelToken()
        job_id = f"{os.getpid()}-{next(self._ids)}"
        with self._active_lock:
            self._active += 1
        try:
            cf = self._executor.submit(
                self._run_job_thread, job_factory, token, global_slot, client_slot, job_id, label, waited
            )
        except BaseException:
            global_slot.release()
            if client_slot is not None:
                client_slot.release()
            with self._active_lock:
                self._active -= 1
            raise
        fut = asyncio.wrap_future(cf)
        fut.add_done_callback(_consume_result)

        try:
            await self._wait_for_job(fut, token, is_disconnected, job_id)
        except asyncio.CancelledError:
            # 요청 코루틴 자체가 취소됨(서버 종료 등). 작업도 멈추게 한다.
            self._cancel(token, "request cancelled", fut, job_id)
            raise
        return fut.result()

    async def _wait_for_job(
        self,
        fut: asyncio.Future,
        token: CancelToken,
        is_disconnected: Optional[DisconnectProbe],
        job_id: str,
    ) -> None:
        deadline = time.monotonic() + self.exec_timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._cancel(token, "timeout", fut, job_id)
                raise ExecutionTimeout(
                    f"백테스트 처리 시간이 {self.exec_timeout:.0f}초를 초과하여 중단되었습니다. "
                    "기간을 줄이거나 잠시 후 다시 시도해주세요.",
                    retry_after=30,
                )
            wait_for = remaining
            if is_disconnected is not None:
                wait_for = min(wait_for, self.disconnect_poll_interval)
            # asyncio.wait는 시간이 다 돼도 fut를 취소하지 않는다(작업은 계속 돈다).
            done, _ = await asyncio.wait({fut}, timeout=wait_for)
            if done:
                return
            if is_disconnected is not None and await is_disconnected():
                self._cancel(token, "client disconnected", fut, job_id)
                raise ClientDisconnected("클라이언트가 연결을 끊어 백테스트를 중단했습니다.")

    def _cancel(self, token: CancelToken, reason: str, fut: asyncio.Future, job_id: str) -> None:
        if fut.done():
            return
        logger.warning("backtest job cancel id=%s reason=%s", job_id, reason)
        token.cancel(reason)
        task = asyncio.get_running_loop().create_task(self._watch_cancelled(fut, job_id, reason))
        self._background.add(task)
        task.add_done_callback(self._background.discard)

    async def _watch_cancelled(self, fut: asyncio.Future, job_id: str, reason: str) -> None:
        started = time.monotonic()
        done, _ = await asyncio.wait({fut}, timeout=self.cancel_grace)
        if not done:
            logger.error(
                "backtest job did not stop within %.0fs after cancel id=%s reason=%s "
                "(슬롯은 작업이 실제로 끝날 때까지 계속 점유된다)",
                self.cancel_grace, job_id, reason,
            )
            await asyncio.wait({fut})
        logger.info(
            "backtest job stopped after cancel id=%s reason=%s delay=%.3fs",
            job_id, reason, time.monotonic() - started,
        )

    def _run_job_thread(
        self,
        job_factory: JobFactory,
        token: CancelToken,
        global_slot: FileSlot,
        client_slot: Optional[FileSlot],
        job_id: str,
        label: str,
        waited: float,
    ) -> Any:
        started = time.monotonic()
        logger.info(
            "backtest job start id=%s t=%.3f wait=%.3fs label=%s", job_id, time.time(), waited, label
        )
        outcome = "ok"
        try:
            with bind_token(token):
                return asyncio.run(_guarded(job_factory, token))
        except BacktestCancelled as exc:
            outcome = f"cancelled({exc.reason})"
            raise
        except BaseException as exc:
            outcome = f"error({type(exc).__name__})"
            raise
        finally:
            # 작업 전용 루프가 기본 스레드풀까지 닫은 뒤에야 여기에 도달한다 —
            # 이 작업이 만든 스레드가 모두 끝났다는 뜻이다.
            # 종료 시각은 슬롯 반환 "전"에 잰다. start(획득 후)~end(반환 전) 구간이
            # 슬롯 점유 구간 안에 들어가야 로그 기반 동시 실행 수 계산이 정확하다.
            ended_wall = time.time()
            elapsed = time.monotonic() - started
            global_slot.release()
            if client_slot is not None:
                client_slot.release()
            with self._active_lock:
                self._active -= 1
            logger.info(
                "backtest job end id=%s t=%.3f elapsed=%.3fs outcome=%s",
                job_id, ended_wall, elapsed, outcome,
            )


async def _guarded(job_factory: JobFactory, token: CancelToken) -> Any:
    """작업 전용 루프의 메인 태스크. 취소 신호를 태스크 취소로 연결한다."""
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()

    def _cancel_task() -> None:
        try:
            loop.call_soon_threadsafe(task.cancel)
        except RuntimeError:  # 루프가 이미 닫힘 — 작업이 끝났다
            pass

    token.add_callback(_cancel_task)
    try:
        return await job_factory()
    except asyncio.CancelledError:
        if token.cancelled:
            raise BacktestCancelled(token.reason or "cancelled") from None
        raise


def _consume_result(fut: asyncio.Future) -> None:
    # 504 등으로 아무도 결과를 기다리지 않는 작업의 예외가
    # "Future exception was never retrieved" 경고로 새지 않게 한다.
    if not fut.cancelled():
        fut.exception()


# -- 프로세스 전역 인스턴스 ----------------------------------------------------

_runner: Optional[BacktestJobRunner] = None
_runner_lock = threading.Lock()


def get_backtest_runner() -> BacktestJobRunner:
    """설정값으로 만든 프로세스 전역 실행기(지연 생성)."""
    global _runner
    if _runner is None:
        with _runner_lock:
            if _runner is None:
                _runner = BacktestJobRunner(
                    slot_dir=settings.backtest_slot_dir,
                    max_concurrent=settings.max_concurrent_backtests,
                    per_client=settings.max_concurrent_backtests_per_client,
                    queue_timeout=settings.backtest_queue_timeout_seconds,
                    exec_timeout=settings.backtest_timeout_seconds,
                    cancel_grace=settings.backtest_cancel_grace_seconds,
                )
    return _runner


def reset_backtest_runner() -> None:
    """테스트용: 다음 호출에서 설정값으로 다시 만든다."""
    global _runner
    with _runner_lock:
        old, _runner = _runner, None
    if old is not None:
        old.shutdown(wait=False)
