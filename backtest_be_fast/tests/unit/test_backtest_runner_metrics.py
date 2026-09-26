"""백테스트 동시 실행 관측 지표 회귀 테스트

A-04/A-05의 실행기(app/services/backtest_runner.py)는 실행 중·대기 중 작업 수를
로그로만 남겼다. /metrics에서 보려면 uvicorn 워커 여러 개(PROMETHEUS_MULTIPROC_DIR)의
값을 합쳐야 하므로 multiprocess_mode='livesum' Gauge로 노출한다.

- backtest_jobs_running: 전체 슬롯을 쥐고 아직 끝나지 않은 작업 스레드 수.
  504 뒤 취소 신호를 받고 정리 중인 작업도 슬롯을 쥐고 있으므로 포함한다.
- backtest_jobs_waiting: 전체 슬롯을 기다리는 요청 수.

livesum은 mark_process_dead가 불리기 전까지 죽은 워커의 값도 더한다. uvicorn은 그
훅을 부르지 않으므로, 작업 도중 OOM 등으로 죽은 워커의 +1이 컨테이너 재시작까지
남는다. 새 워커가 메트릭 모듈을 임포트할 때 살아 있지 않은 pid의 live 파일을 지운다.
"""
import asyncio
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from prometheus_client import REGISTRY, CollectorRegistry, multiprocess

from app.services.backtest_runner import BacktestJobRunner, ExecutionTimeout

pytestmark = pytest.mark.unit


def _gauge(name: str) -> float:
    return REGISTRY.get_sample_value(name) or 0.0


def _runner(tmp_path, **overrides) -> BacktestJobRunner:
    params = dict(
        slot_dir=str(tmp_path / "slots"),
        max_concurrent=1,
        per_client=0,
        queue_timeout=5.0,
        exec_timeout=5.0,
        cancel_grace=2.0,
        poll_interval=0.01,
    )
    params.update(overrides)
    return BacktestJobRunner(**params)


async def _until(predicate, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.01)
    return predicate()


class TestInProcessGauges:
    def test_running_and_waiting_follow_the_slot(self, tmp_path):
        runner = _runner(tmp_path)
        base_running = _gauge("backtest_jobs_running")
        base_waiting = _gauge("backtest_jobs_waiting")
        release = threading.Event()

        async def blocking_job():
            await asyncio.to_thread(release.wait, 5.0)
            return "ok"

        async def main():
            first = asyncio.create_task(runner.run(blocking_job))
            assert await _until(lambda: runner.active_jobs() == 1)
            second = asyncio.create_task(runner.run(blocking_job))

            # 상한 1: 첫 작업은 실행 중, 두 번째는 슬롯 대기 중
            assert await _until(lambda: _gauge("backtest_jobs_waiting") == base_waiting + 1)
            assert _gauge("backtest_jobs_running") == base_running + 1

            release.set()
            assert await asyncio.gather(first, second) == ["ok", "ok"]

        try:
            asyncio.run(main())
        finally:
            runner.shutdown()

        assert _gauge("backtest_jobs_running") == base_running
        assert _gauge("backtest_jobs_waiting") == base_waiting

    def test_timed_out_job_counts_as_running_until_its_thread_ends(self, tmp_path):
        """504를 돌려준 뒤에도 취소 지점이 없는 작업은 슬롯을 쥐고 돈다(A-05).
        실행 중 지표도 그 작업이 실제로 끝날 때 내려가야 한다."""
        runner = _runner(tmp_path, exec_timeout=0.1, cancel_grace=5.0)
        base_running = _gauge("backtest_jobs_running")

        async def uncooperative():
            await asyncio.to_thread(time.sleep, 0.6)
            return "late"

        async def main():
            with pytest.raises(ExecutionTimeout):
                await runner.run(uncooperative)
            assert _gauge("backtest_jobs_running") == base_running + 1
            assert await _until(lambda: runner.active_jobs() == 0, 3.0)

        try:
            asyncio.run(main())
        finally:
            runner.shutdown()

        assert _gauge("backtest_jobs_running") == base_running

    def test_queue_timeout_does_not_leave_a_waiting_count(self, tmp_path):
        runner = _runner(tmp_path, queue_timeout=0.1)
        base_waiting = _gauge("backtest_jobs_waiting")
        holder = runner.global_pool.try_acquire()  # 다른 워커가 슬롯을 쥔 상황

        async def job():
            return "never"

        try:
            with pytest.raises(Exception):
                asyncio.run(runner.run(job))
        finally:
            holder.release()
            runner.shutdown()

        assert _gauge("backtest_jobs_waiting") == base_waiting


_WORKER_SCRIPT = r"""
import json, os, sys
from app.monitoring.custom_metrics import BACKTEST_JOBS_RUNNING, BACKTEST_JOBS_WAITING
action = sys.argv[1]
if action == "crash_while_running":
    BACKTEST_JOBS_RUNNING.inc()
    BACKTEST_JOBS_WAITING.inc()
    sys.stdout.write(json.dumps({"pid": os.getpid()}) + "\n")
    sys.stdout.flush()
    os._exit(0)  # 감소 없이 죽는다 (OOM kill 흉내)
elif action == "hold_running":
    BACKTEST_JOBS_RUNNING.inc()
    sys.stdout.write(json.dumps({"pid": os.getpid()}) + "\n")
    sys.stdout.flush()
    sys.stdin.readline()  # 부모가 값을 읽을 때까지 살아 있는다
"""


def _collect(mp_dir: Path) -> dict:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry, path=str(mp_dir))
    return {
        s.name: s.value
        for metric in registry.collect()
        for s in metric.samples
        if s.name in ("backtest_jobs_running", "backtest_jobs_waiting")
    }


class TestMultiprocessMode:
    def _env(self, mp_dir: Path) -> dict:
        return dict(os.environ, PROMETHEUS_MULTIPROC_DIR=str(mp_dir))

    def test_live_workers_are_summed(self, tmp_path):
        mp_dir = tmp_path / "prom"
        mp_dir.mkdir()
        be_root = Path(__file__).resolve().parents[2]
        procs = [
            subprocess.Popen(
                [sys.executable, "-c", _WORKER_SCRIPT, "hold_running"],
                cwd=be_root, env=self._env(mp_dir), text=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            for _ in range(2)
        ]
        try:
            for p in procs:
                assert p.stdout.readline(), p.stderr.read()[-2000:]
            assert _collect(mp_dir)["backtest_jobs_running"] == 2
        finally:
            for p in procs:
                p.communicate(input="\n", timeout=60)

    def test_dead_worker_values_are_dropped_when_a_new_worker_starts(self, tmp_path):
        mp_dir = tmp_path / "prom"
        mp_dir.mkdir()
        be_root = Path(__file__).resolve().parents[2]

        crashed = subprocess.run(
            [sys.executable, "-c", _WORKER_SCRIPT, "crash_while_running"],
            cwd=be_root, env=self._env(mp_dir), capture_output=True, text=True, timeout=120,
        )
        assert crashed.returncode == 0, crashed.stderr[-2000:]
        # 전제: 정리 전에는 죽은 워커의 +1이 그대로 합산된다
        assert _collect(mp_dir) == {"backtest_jobs_running": 1, "backtest_jobs_waiting": 1}

        # uvicorn이 새 워커를 띄우면 그 워커가 메트릭 모듈을 임포트한다
        replacement = subprocess.Popen(
            [sys.executable, "-c", _WORKER_SCRIPT, "hold_running"],
            cwd=be_root, env=self._env(mp_dir), text=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            assert replacement.stdout.readline(), replacement.stderr.read()[-2000:]
            assert _collect(mp_dir) == {"backtest_jobs_running": 1, "backtest_jobs_waiting": 0}
        finally:
            replacement.communicate(input="\n", timeout=60)

    def test_stale_file_of_a_reused_pid_is_not_inherited(self, tmp_path):
        """죽은 워커와 같은 pid를 새 워커가 받으면, prometheus_client는 pid로 파일을
        열어 이전 값을 이어받는다. 자기 pid의 live 파일도 게이지를 만들기 전에 지운다."""
        mp_dir = tmp_path / "prom"
        mp_dir.mkdir()
        be_root = Path(__file__).resolve().parents[2]

        crashed = subprocess.run(
            [sys.executable, "-c", _WORKER_SCRIPT, "crash_while_running"],
            cwd=be_root, env=self._env(mp_dir), capture_output=True, text=True, timeout=120,
        )
        assert crashed.returncode == 0, crashed.stderr[-2000:]
        dead_pid = json.loads(crashed.stdout.strip().splitlines()[-1])["pid"]
        stale = mp_dir / f"gauge_livesum_{dead_pid}.db"
        assert stale.exists()

        # 같은 pid를 받은 새 프로세스를 흉내: 죽은 워커의 파일을 자기 pid 이름으로
        # 옮긴 뒤 메트릭 모듈을 임포트한다(자기 pid는 살아 있으므로 "죽은 pid" 정리로는
        # 지워지지 않는다).
        script = (
            "import os, sys\n"
            "d = os.environ['PROMETHEUS_MULTIPROC_DIR']\n"
            "os.replace(sys.argv[1], os.path.join(d, f'gauge_livesum_{os.getpid()}.db'))\n"
            "from app.monitoring.custom_metrics import BACKTEST_JOBS_RUNNING\n"
        )
        reused = subprocess.run(
            [sys.executable, "-c", script, str(stale)],
            cwd=be_root, env=self._env(mp_dir), capture_output=True, text=True, timeout=120,
        )
        assert reused.returncode == 0, reused.stderr[-2000:]
        assert _collect(mp_dir) == {"backtest_jobs_running": 0, "backtest_jobs_waiting": 0}
