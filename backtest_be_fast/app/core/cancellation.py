"""백테스트 작업의 협력적 취소 (A-05)

**왜 필요한가**:
파이썬은 실행 중인 스레드를 밖에서 강제로 멈출 수 없다. 과거에는
`asyncio.wait_for(..., timeout=60)`이 코루틴 대기만 끊고 `asyncio.to_thread()`로
넘긴 시뮬레이션·DB·외부 API 스레드는 계속 돌았다(사용자는 504를 받는데 작업은
계속되고, 세마포어는 먼저 반환됐다).

**구조**:
- `CancelToken`: 작업 하나당 하나. 내부는 `threading.Event`라 어느 스레드에서든
  확인·대기할 수 있다.
- 토큰은 `ContextVar`로 전달한다. 작업 실행기(app/services/backtest_runner.py)가
  작업 스레드에서 토큰을 바인딩하면, 그 스레드의 이벤트 루프가 만든 태스크와
  `asyncio.to_thread()` 호출이 컨텍스트를 복사하므로 호출 경로 전체에 인자를
  추가하지 않아도 된다. 단 `concurrent.futures.ThreadPoolExecutor.submit()`은
  컨텍스트를 복사하지 않으므로 `submit_with_context()`를 써야 한다.
- 동기 코드의 긴 루프·재시도 대기·외부 호출 직전에 `check_cancelled()` /
  `cancellable_sleep()`을 둔다. 토큰이 바인딩되지 않은 호출(단위 테스트, 스크립트)
  에서는 둘 다 아무 일도 하지 않는다(`cancellable_sleep`은 그냥 sleep).

**`BacktestCancelled`가 `BaseException`인 이유**:
실행 경로 곳곳에 `except Exception:`이 있다(종목별 백테스트 루프는 실패 종목을
건너뛰고 계속하고, `load_ticker_data`는 예외를 재시도한다). `Exception`
하위였다면 취소가 "한 종목 실패" 또는 "재시도할 일시 오류"로 삼켜져 작업이 계속
돈다. `asyncio.CancelledError`가 `BaseException`인 것과 같은 이유다.
"""
from __future__ import annotations

import concurrent.futures
import contextvars
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, List, Optional


class BacktestCancelled(BaseException):
    """취소 신호를 받은 작업이 협력적으로 중단될 때 발생한다."""

    def __init__(self, reason: str = "cancelled"):
        self.reason = reason
        super().__init__(reason)


class CancelToken:
    """스레드 안전한 취소 토큰."""

    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[], None]] = []
        self.reason: Optional[str] = None

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self, reason: str = "cancelled") -> None:
        """취소를 요청한다. 여러 번 호출해도 첫 사유만 남는다."""
        with self._lock:
            if self._event.is_set():
                return
            self.reason = reason
            self._event.set()
            callbacks, self._callbacks = self._callbacks, []
        for cb in callbacks:
            try:
                cb()
            except Exception:  # 콜백 실패가 취소 전파를 막지 않게 한다
                pass

    def add_callback(self, cb: Callable[[], None]) -> None:
        """취소 시 호출할 콜백 등록. 이미 취소됐다면 즉시 호출한다."""
        with self._lock:
            if not self._event.is_set():
                self._callbacks.append(cb)
                return
        cb()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise BacktestCancelled(self.reason or "cancelled")

    def wait(self, timeout: float) -> bool:
        """최대 timeout초 기다린다. 취소되면 True를 즉시 반환한다."""
        return self._event.wait(timeout)


_current_token: contextvars.ContextVar[Optional[CancelToken]] = contextvars.ContextVar(
    "backtest_cancel_token", default=None
)


def current_token() -> Optional[CancelToken]:
    return _current_token.get()


@contextmanager
def bind_token(token: CancelToken) -> Iterator[CancelToken]:
    """현재 컨텍스트에 토큰을 바인딩한다."""
    reset = _current_token.set(token)
    try:
        yield token
    finally:
        _current_token.reset(reset)


def check_cancelled() -> None:
    """현재 작업이 취소됐으면 BacktestCancelled를 던진다(토큰이 없으면 no-op)."""
    token = _current_token.get()
    if token is not None:
        token.raise_if_cancelled()


def cancellable_sleep(seconds: float) -> None:
    """time.sleep 대체. 취소되면 대기를 끊고 BacktestCancelled를 던진다."""
    token = _current_token.get()
    if token is None:
        time.sleep(seconds)
        return
    if token.wait(seconds):
        token.raise_if_cancelled()


def submit_with_context(
    executor: concurrent.futures.Executor, fn: Callable[..., Any], *args: Any, **kwargs: Any
) -> concurrent.futures.Future:
    """executor.submit과 같되 호출 시점의 컨텍스트(취소 토큰 포함)를 넘긴다.

    같은 Context 객체는 여러 스레드에서 동시에 run()할 수 없으므로 제출마다
    새로 복사한다.
    """
    ctx = contextvars.copy_context()
    return executor.submit(ctx.run, fn, *args, **kwargs)
