"""POST /api/v1/backtest 동시 실행 상한 · 타임아웃 · 취소 · IP별 제한 회귀 테스트

**이력**:
- P2-16(2026-08-03): 프로세스 로컬 `asyncio.Semaphore(8)` + `asyncio.wait_for(60)`.
- A-04: 세마포어가 프로세스 로컬이라 uvicorn 워커 17개면 실제 상한이 17 x 8 = 136건.
  → 락 파일 슬롯(fcntl.flock)으로 컨테이너 전체 상한.
- A-05: `wait_for`는 코루틴 대기만 끊는다. to_thread로 넘긴 스레드는 504 이후에도
  계속 돌았고, 세마포어는 코루틴 취소와 함께 먼저 반환돼 그 슬롯으로 새 요청이
  추가로 실행됐다. → 슬롯은 작업 스레드가 실제로 끝날 때 반환, 타임아웃 시 협력적
  취소 신호 전달.
- A-06: 인증 없는 공개 서비스 유지 결정. → 클라이언트(IP)별 동시 실행 상한(429).

타임아웃 테스트는 "504가 빨리 오는가"만이 아니라 **실제로 돌고 있는 작업 수가
줄어드는가**와 **작업이 끝나기 전에는 슬롯이 재사용되지 않는가**를 확인한다.
"""
import asyncio
import json
import multiprocessing
import threading
import time
from typing import Callable, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

import app.services.backtest_runner as runner_module
from app.core.cancellation import check_cancelled
from app.main import app
from app.services.backtest_runner import (
    BacktestJobRunner,
    ClientDisconnected,
    ExecutionTimeout,
)

pytestmark = pytest.mark.unit

PAYLOAD = {
    "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
    "start_date": "2023-01-01",
    "end_date": "2023-06-30",
    "strategy": "buy_hold_strategy",
}

UNIFIED_DATA = {
    "sp500_benchmark": [],
    "nasdaq_benchmark": [],
    "exchange_rates": {},
    "latest_news": [],
}

SUCCESS = {"status": "success", "data": {"portfolio_statistics": {}, "individual_returns": {}}}


def _mock_stock_repository() -> MagicMock:
    repo = MagicMock()
    repo.get_tickers_info_batch.return_value = {}
    return repo


class RunningCounter:
    """작업 스레드 안에서 '지금 실제로 도는 계산 수'를 센다."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.current = 0
        self.peak = 0
        self.stopped_by_cancel = 0

    def enter(self) -> None:
        with self._lock:
            self.current += 1
            self.peak = max(self.peak, self.current)

    def leave(self) -> None:
        with self._lock:
            self.current -= 1


def _wait_until(predicate: Callable[[], bool], timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


@pytest.fixture
def install_runner(tmp_path, monkeypatch):
    """엔드포인트가 쓸 BacktestJobRunner를 테스트용 값으로 교체한다."""
    created: List[BacktestJobRunner] = []

    def _install(**overrides) -> BacktestJobRunner:
        params = dict(
            slot_dir=str(tmp_path / "slots"),
            max_concurrent=4,
            per_client=0,
            queue_timeout=5.0,
            exec_timeout=5.0,
            cancel_grace=2.0,
            poll_interval=0.01,
            disconnect_poll_interval=0.05,
        )
        params.update(overrides)
        runner = BacktestJobRunner(**params)
        created.append(runner)
        monkeypatch.setattr(runner_module, "_runner", runner)
        return runner

    yield _install
    for runner in created:
        runner.shutdown(wait=True)


def _patch_backtest(side_effect):
    """엔드포인트의 외부 의존(상장일 조회, 시뮬레이션, 부가 데이터)을 대체한다."""
    return (
        patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=_mock_stock_repository(),
        ),
        patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(side_effect=side_effect),
        ),
        patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            return_value=UNIFIED_DATA,
        ),
    )


class _Patched:
    def __init__(self, side_effect):
        self._patches = _patch_backtest(side_effect)

    def __enter__(self):
        for p in self._patches:
            p.__enter__()
        return self

    def __exit__(self, *exc):
        for p in reversed(self._patches):
            p.__exit__(*exc)


def _async_client(peer: str = "203.0.113.10") -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, client=(peer, 40000))
    return httpx.AsyncClient(transport=transport, base_url="http://test")


# ---------------------------------------------------------------------------
# A-04: 컨테이너(=슬롯 디렉터리) 전체 상한
# ---------------------------------------------------------------------------


class TestCapIsSharedAcrossWorkerProcesses:
    def test_three_processes_never_exceed_the_shared_cap(self, tmp_path):
        """uvicorn 워커 3개를 흉내 낸 프로세스 3개가 각자 작업 3건을 동시에 던져도
        (프로세스 로컬 세마포어라면 최대 9건) 실제 동시 계산 수는 상한 2를 넘지 않는다."""
        cap, procs, jobs_per_proc, job_seconds = 2, 3, 3, 0.25
        slot_dir = str(tmp_path / "slots")
        log_path = str(tmp_path / "jobs.log")

        ctx = multiprocessing.get_context("spawn")
        from tests.unit.backtest_runner_mp_helper import run_jobs_in_process

        workers = [
            ctx.Process(
                target=run_jobs_in_process,
                args=(slot_dir, cap, jobs_per_proc, job_seconds, log_path),
            )
            for _ in range(procs)
        ]
        for w in workers:
            w.start()
        for w in workers:
            w.join(timeout=60)
        assert all(w.exitcode == 0 for w in workers), [w.exitcode for w in workers]

        with open(log_path) as fh:
            records = [json.loads(line) for line in fh if line.strip()]
        assert len(records) == procs * jobs_per_proc

        events = []
        for r in records:
            events.append((r["start"], 1))
            events.append((r["end"], -1))
        events.sort(key=lambda e: (e[0], e[1]))  # 같은 시각이면 종료를 먼저
        current = peak = 0
        for _, delta in events:
            current += delta
            peak = max(peak, current)

        assert peak <= cap, f"프로세스 {procs}개 합계 동시 실행 {peak}건 > 상한 {cap}"
        assert peak == cap, f"상한만큼은 동시에 돌아야 한다: peak={peak}"
        assert len({r["pid"] for r in records}) == procs


class TestQueueing:
    @pytest.mark.asyncio
    async def test_excess_requests_wait_in_queue_and_all_complete(self, install_runner):
        """상한을 넘는 요청은 거부되지 않고 대기했다가 실행된다(P2-16 동작 유지)."""
        install_runner(max_concurrent=2, queue_timeout=5.0)
        counter = RunningCounter()

        def work():
            counter.enter()
            try:
                time.sleep(0.1)
            finally:
                counter.leave()

        async def backtest(*args, **kwargs):
            await asyncio.to_thread(work)
            return SUCCESS

        with _Patched(backtest):
            async with _async_client() as ac:
                responses = await asyncio.gather(
                    *[ac.post("/api/v1/backtest", json=PAYLOAD) for _ in range(5)]
                )

        assert [r.status_code for r in responses] == [200] * 5
        assert counter.peak == 2

    def test_queue_wait_over_limit_returns_503_without_starting_work(self, install_runner):
        runner = install_runner(max_concurrent=1, queue_timeout=0.2)
        holder = runner.global_pool.try_acquire()  # 다른 워커가 슬롯을 쥔 상황
        assert holder is not None
        calls = []

        async def backtest(*args, **kwargs):
            calls.append(1)
            return SUCCESS

        try:
            with _Patched(backtest):
                start = time.monotonic()
                response = TestClient(app).post("/api/v1/backtest", json=PAYLOAD)
                elapsed = time.monotonic() - start
        finally:
            holder.release()

        assert response.status_code == 503, response.text
        assert response.headers.get("Retry-After")
        assert response.json()["detail"]
        assert calls == [], "대기 초과 요청은 작업을 시작하지 않아야 한다"
        assert 0.15 <= elapsed < 2.0


# ---------------------------------------------------------------------------
# A-05: 타임아웃 후 실제 작업 종료 + 슬롯 재사용 금지
# ---------------------------------------------------------------------------


class TestTimeoutStopsRealWork:
    def test_timeout_returns_504_and_running_work_actually_stops(self, install_runner):
        runner = install_runner(max_concurrent=2, exec_timeout=0.2, cancel_grace=2.0)
        counter = RunningCounter()

        def long_cooperative_work():
            counter.enter()
            try:
                for _ in range(500):  # 취소가 없으면 5초
                    check_cancelled()
                    time.sleep(0.01)
            except BaseException:
                counter.stopped_by_cancel += 1
                raise
            finally:
                counter.leave()

        async def backtest(*args, **kwargs):
            await asyncio.to_thread(long_cooperative_work)
            return SUCCESS

        with _Patched(backtest):
            start = time.monotonic()
            response = TestClient(app).post("/api/v1/backtest", json=PAYLOAD)
            elapsed = time.monotonic() - start

            assert response.status_code == 504, response.text
            assert response.json().get("detail")
            assert elapsed < 1.5, f"504가 늦게 왔다: {elapsed:.2f}s"

            # 핵심: 응답 이후 실제로 돌던 계산이 멈춘다.
            assert _wait_until(lambda: counter.current == 0, 1.0), (
                "504 이후에도 계산 스레드가 계속 돈다"
            )
            assert counter.stopped_by_cancel == 1
            assert _wait_until(lambda: runner.active_jobs() == 0, 1.0)
            assert runner.global_pool.held_count() == 0

    def test_slot_is_not_reused_until_uncooperative_work_finishes(self, install_runner):
        """취소 지점이 없는 구간(예: backtesting.py 내부)은 끝날 때까지 기다려야 한다.
        그동안 슬롯은 반환되지 않아 새 요청이 추가로 실행되지 않는다."""
        runner = install_runner(
            max_concurrent=1, exec_timeout=0.2, queue_timeout=0.3, cancel_grace=5.0
        )
        counter = RunningCounter()
        call_count = {"n": 0}

        def uncooperative(seconds: float):
            counter.enter()
            try:
                time.sleep(seconds)
            finally:
                counter.leave()

        async def backtest(*args, **kwargs):
            call_count["n"] += 1
            seconds = 1.2 if call_count["n"] == 1 else 0.01
            await asyncio.to_thread(uncooperative, seconds)
            return SUCCESS

        client = TestClient(app)
        with _Patched(backtest):
            first = client.post("/api/v1/backtest", json=PAYLOAD)
            assert first.status_code == 504
            assert counter.current == 1, "첫 작업 스레드는 아직 돌고 있어야 한다(전제)"

            # 첫 작업이 아직 도는 동안: 슬롯이 반환되지 않았으므로 대기 → 503
            second = client.post("/api/v1/backtest", json=PAYLOAD)
            assert second.status_code == 503, (
                f"작업이 끝나기 전에 슬롯이 재사용됨: {second.status_code}"
            )
            assert counter.peak == 1, f"상한 1인데 동시에 {counter.peak}건이 돌았다"
            assert call_count["n"] == 1

            # 첫 작업이 실제로 끝나면 슬롯이 돌아온다
            assert _wait_until(lambda: runner.active_jobs() == 0, 3.0)
            third = client.post("/api/v1/backtest", json=PAYLOAD)
            assert third.status_code == 200, third.text
            assert counter.peak == 1


class TestClientDisconnectCancelsWork:
    @pytest.mark.asyncio
    async def test_disconnect_cancels_running_work(self, tmp_path):
        runner = BacktestJobRunner(
            slot_dir=str(tmp_path / "slots"),
            max_concurrent=2,
            per_client=0,
            queue_timeout=5.0,
            exec_timeout=10.0,
            cancel_grace=2.0,
            poll_interval=0.01,
            disconnect_poll_interval=0.02,
        )
        counter = RunningCounter()

        def work():
            counter.enter()
            try:
                for _ in range(500):
                    check_cancelled()
                    time.sleep(0.01)
            finally:
                counter.leave()

        async def job():
            await asyncio.to_thread(work)

        started = time.monotonic()

        async def is_disconnected() -> bool:
            return time.monotonic() - started > 0.2

        try:
            with pytest.raises(ClientDisconnected):
                await runner.run(job, is_disconnected=is_disconnected)
            assert time.monotonic() - started < 1.5
            for _ in range(100):
                if counter.current == 0 and runner.active_jobs() == 0:
                    break
                await asyncio.sleep(0.01)
            assert counter.current == 0
            assert runner.active_jobs() == 0
            assert runner.global_pool.held_count() == 0
        finally:
            runner.shutdown()

    @pytest.mark.asyncio
    async def test_await_points_are_cancellation_points(self, tmp_path):
        """스레드 밖(비동기 코드)에서는 별도 확인 없이도 다음 await에서 멈춘다 —
        종목별 처리 사이, 외부 수집 사이 등."""
        runner = BacktestJobRunner(
            slot_dir=str(tmp_path / "slots"),
            max_concurrent=1,
            per_client=0,
            queue_timeout=5.0,
            exec_timeout=0.2,
            cancel_grace=2.0,
            poll_interval=0.01,
        )
        steps = []

        async def job():
            for i in range(100):
                steps.append(i)
                await asyncio.sleep(0.05)

        try:
            with pytest.raises(ExecutionTimeout):
                await runner.run(job)
            for _ in range(100):
                if runner.active_jobs() == 0:
                    break
                await asyncio.sleep(0.01)
            assert runner.active_jobs() == 0
            done = len(steps)
            await asyncio.sleep(0.2)
            assert len(steps) == done, "타임아웃 후에도 비동기 단계가 계속 진행됨"
            assert done < 10
        finally:
            runner.shutdown()


# ---------------------------------------------------------------------------
# A-06: 클라이언트(IP)별 동시 실행 상한
# ---------------------------------------------------------------------------


class TestPerClientLimit:
    @pytest.mark.asyncio
    async def test_third_concurrent_request_from_same_ip_gets_429(self, install_runner):
        install_runner(max_concurrent=8, per_client=2)
        release = threading.Event()
        started = threading.Semaphore(0)

        def work():
            started.release()
            release.wait(5)

        async def backtest(*args, **kwargs):
            await asyncio.to_thread(work)
            return SUCCESS

        with _Patched(backtest):
            async with _async_client("203.0.113.10") as same, _async_client("198.51.100.20") as other:
                first = asyncio.create_task(same.post("/api/v1/backtest", json=PAYLOAD))
                second = asyncio.create_task(same.post("/api/v1/backtest", json=PAYLOAD))
                for _ in range(2):
                    assert await asyncio.to_thread(started.acquire, True, 5)

                t0 = time.monotonic()
                third = await same.post("/api/v1/backtest", json=PAYLOAD)
                assert third.status_code == 429, third.text
                assert third.headers.get("Retry-After")
                assert third.json()["detail"]
                assert time.monotonic() - t0 < 1.0, "429는 대기 없이 즉시 와야 한다"

                other_task = asyncio.create_task(other.post("/api/v1/backtest", json=PAYLOAD))
                assert await asyncio.to_thread(started.acquire, True, 5), (
                    "다른 IP는 제한받지 않아야 한다"
                )
                release.set()
                results = await asyncio.gather(first, second, other_task)

        assert [r.status_code for r in results] == [200, 200, 200]

    @pytest.mark.asyncio
    async def test_forged_forwarded_for_from_untrusted_peer_is_ignored(self, install_runner):
        """프록시를 거치지 않은(공인 IP) 피어가 요청마다 다른 X-Forwarded-For를 넣어도
        같은 클라이언트로 센다."""
        install_runner(max_concurrent=8, per_client=1)
        release = threading.Event()
        started = threading.Semaphore(0)

        def work():
            started.release()
            release.wait(5)

        async def backtest(*args, **kwargs):
            await asyncio.to_thread(work)
            return SUCCESS

        with _Patched(backtest):
            async with _async_client("203.0.113.10") as ac:
                first = asyncio.create_task(
                    ac.post("/api/v1/backtest", json=PAYLOAD, headers={"X-Forwarded-For": "1.1.1.1"})
                )
                assert await asyncio.to_thread(started.acquire, True, 5)
                second = await ac.post(
                    "/api/v1/backtest", json=PAYLOAD, headers={"X-Forwarded-For": "2.2.2.2"}
                )
                release.set()
                first_response = await first

        assert second.status_code == 429
        assert first_response.status_code == 200

    @pytest.mark.asyncio
    async def test_clients_behind_trusted_proxy_are_told_apart_and_spoofing_is_ignored(
        self, install_runner
    ):
        """nginx(사설망 피어) 뒤: XFF 오른쪽부터 첫 공인 주소가 클라이언트다.
        클라이언트가 왼쪽에 끼워 넣은 값은 무시된다."""
        install_runner(max_concurrent=8, per_client=1)
        release = threading.Event()
        started = threading.Semaphore(0)

        def work():
            started.release()
            release.wait(5)

        async def backtest(*args, **kwargs):
            await asyncio.to_thread(work)
            return SUCCESS

        def xff(*hops: str) -> dict:
            return {"X-Forwarded-For": ", ".join(hops)}

        with _Patched(backtest):
            async with _async_client("172.18.0.5") as nginx:
                a1 = asyncio.create_task(
                    nginx.post("/api/v1/backtest", json=PAYLOAD,
                               headers=xff("9.9.9.9", "198.51.100.7", "172.18.0.2"))
                )
                assert await asyncio.to_thread(started.acquire, True, 5)
                # 같은 실제 클라이언트가 왼쪽 값을 바꿔 사칭 → 여전히 같은 클라이언트
                a2 = await nginx.post("/api/v1/backtest", json=PAYLOAD,
                                      headers=xff("8.8.8.8", "198.51.100.7", "172.18.0.2"))
                assert a2.status_code == 429, a2.text
                # 다른 실제 클라이언트는 통과
                b1 = asyncio.create_task(
                    nginx.post("/api/v1/backtest", json=PAYLOAD,
                               headers=xff("198.51.100.8", "172.18.0.2"))
                )
                assert await asyncio.to_thread(started.acquire, True, 5)
                release.set()
                results = await asyncio.gather(a1, b1)

        assert [r.status_code for r in results] == [200, 200]

    @pytest.mark.asyncio
    async def test_unidentifiable_client_is_not_limited_per_ip(self, install_runner):
        """프록시가 XFF를 넘기지 않아 클라이언트를 식별할 수 없으면 IP별 제한을
        적용하지 않는다(모든 사용자가 프록시 주소 하나로 묶여 서비스 전체가 막히는
        것을 막는다). 전체 상한은 그대로 적용된다."""
        install_runner(max_concurrent=8, per_client=1)
        release = threading.Event()
        started = threading.Semaphore(0)

        def work():
            started.release()
            release.wait(5)

        async def backtest(*args, **kwargs):
            await asyncio.to_thread(work)
            return SUCCESS

        with _Patched(backtest):
            async with _async_client("172.18.0.5") as nginx:
                tasks = [
                    asyncio.create_task(nginx.post("/api/v1/backtest", json=PAYLOAD))
                    for _ in range(3)
                ]
                for _ in range(3):
                    assert await asyncio.to_thread(started.acquire, True, 5)
                release.set()
                results = await asyncio.gather(*tasks)

        assert [r.status_code for r in results] == [200, 200, 200]

    def test_client_slot_is_held_until_timed_out_work_really_ends(self, install_runner):
        """504 직후 같은 IP가 곧바로 다시 요청해도, 이전 작업 스레드가 아직 돌고 있으면
        그 IP의 몫으로 계속 센다."""
        runner = install_runner(max_concurrent=4, per_client=1, exec_timeout=0.2)
        call_count = {"n": 0}

        def uncooperative(seconds):
            time.sleep(seconds)

        async def backtest(*args, **kwargs):
            call_count["n"] += 1
            await asyncio.to_thread(uncooperative, 1.0 if call_count["n"] == 1 else 0.01)
            return SUCCESS

        client = TestClient(app, client=("203.0.113.10", 50000))
        with _Patched(backtest):
            assert client.post("/api/v1/backtest", json=PAYLOAD).status_code == 504
            assert client.post("/api/v1/backtest", json=PAYLOAD).status_code == 429
            assert _wait_until(lambda: runner.active_jobs() == 0, 3.0)
            assert client.post("/api/v1/backtest", json=PAYLOAD).status_code == 200
