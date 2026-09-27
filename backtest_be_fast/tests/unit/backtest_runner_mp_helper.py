"""멀티 프로세스 테스트용 헬퍼 (test_backtest_concurrency_and_timeout.py에서 spawn으로 실행).

파일 이름이 test_*.py가 아니므로 pytest가 수집하지 않는다. spawn 자식은 이 모듈만
임포트하므로 app.main(FastAPI 앱 전체)을 끌어오지 않는다.
"""
import asyncio
import json
import os
import time


def run_jobs_in_process(slot_dir: str, cap: int, jobs: int, job_seconds: float, log_path: str) -> None:
    """이 프로세스 안에서 BacktestJobRunner로 작업 `jobs`개를 동시에 실행하고
    각 작업의 [시작, 끝] 벽시계 시각을 log_path에 한 줄씩 남긴다."""
    from app.services.backtest_runner import BacktestJobRunner

    runner = BacktestJobRunner(
        slot_dir=slot_dir,
        max_concurrent=cap,
        per_client=0,
        queue_timeout=30.0,
        exec_timeout=30.0,
        cancel_grace=5.0,
        poll_interval=0.01,
    )

    def blocking_work() -> None:
        start = time.time()
        time.sleep(job_seconds)
        end = time.time()
        line = json.dumps({"pid": os.getpid(), "start": start, "end": end}) + "\n"
        fd = os.open(log_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(fd, line.encode())
        finally:
            os.close(fd)
        return None

    async def job():
        await asyncio.to_thread(blocking_work)
        return "ok"

    async def main():
        return await asyncio.gather(*[runner.run(job) for _ in range(jobs)])

    try:
        results = asyncio.run(main())
        assert results == ["ok"] * jobs, results
    finally:
        runner.shutdown()


def hold_slot_until_killed(slot_dir: str, name: str, size: int, ready_path: str) -> None:
    """슬롯 하나를 쥔 채 무한 대기한다(부모가 SIGKILL로 죽인다)."""
    from app.core.file_slots import FileSlotPool

    slot = FileSlotPool(slot_dir, name, size).try_acquire()
    assert slot is not None
    with open(ready_path, "w") as fh:
        fh.write("ready")
    while True:
        time.sleep(1)
