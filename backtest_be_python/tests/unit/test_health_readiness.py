"""
liveness(/health)와 readiness(/health/ready) 분리 회귀 테스트 (A-07)

**문제**: /health는 `len(app.routes) > 0`만 검사한다. MySQL이 내려가도 항상
`healthy`를 반환하므로, 배포 후 헬스 체크가 통과해도 실제로 요청을 처리할 수
있는지는 보장되지 않는다.

**수정**:
- /health(liveness)는 지금처럼 가볍게 유지한다 — 외부 의존성을 보지 않고,
  응답 형식(status/timestamp/version)도 그대로다.
- /health/ready(readiness)를 추가해 MySQL에 제한 시간 안에 `SELECT 1`을
  수행한다. 실패하거나 시간을 넘기면 503을 반환한다. 외부 Yahoo/Naver API는
  조건에 넣지 않는다(외부 장애가 배포 실패로 번지지 않도록).
- 프로브는 전용 단일 스레드에서 single-flight로 실행한다 — DB가 멈춘 상태에서
  readiness를 반복 호출해도 멈춘 프로브 스레드와 DB 연결이 요청 수만큼
  늘어나지 않는다.

이 테스트는 MySQL을 쓰지 않는다. 프로브 대상 엔진을 SQLite 인메모리로 바꾸거나
프로브 함수를 목으로 대체한다.
"""
import asyncio
import threading
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app.main import app
from app.services.database import readiness

pytestmark = pytest.mark.unit

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_probe(monkeypatch):
    """모듈 전역 single-flight 상태가 테스트 사이에 새지 않도록 새 프로브로 교체한다."""
    probe = readiness.DatabaseReadinessProbe()
    monkeypatch.setattr(readiness, "database_readiness_probe", probe)
    yield probe
    probe.shutdown()


class TestLivenessStaysLightweight:
    def test_health_keeps_existing_response_shape(self):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"status", "timestamp", "version"}
        assert body["status"] == "healthy"

    def test_health_does_not_touch_the_database(self, fresh_probe, monkeypatch):
        """DB 프로브가 실패해도 liveness는 200이다 — DB 장애로 프로세스를
        재시작시키면 복구에 도움이 안 되고 재시작 폭주만 부른다."""
        def exploding_check():
            raise AssertionError("liveness가 DB 프로브를 호출했다")

        monkeypatch.setattr(fresh_probe, "_run_check", exploding_check)
        response = client.get("/health")
        assert response.status_code == 200


class TestReadinessReflectsDatabase:
    def test_ready_returns_200_when_select_1_succeeds(self, fresh_probe, monkeypatch):
        """RED(수정 전): /health/ready 라우트가 없어 404."""
        monkeypatch.setattr(
            fresh_probe,
            "_engine_factory",
            lambda: create_engine("sqlite://", poolclass=NullPool),
        )
        response = client.get("/health/ready")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"] == {"database": "ok"}
        assert "version" in body and "timestamp" in body

    def test_ready_returns_503_when_database_is_unreachable(self, fresh_probe, monkeypatch):
        def failing_check():
            raise ConnectionRefusedError("Can't connect to MySQL server on 'db' (secret detail)")

        monkeypatch.setattr(fresh_probe, "_run_check", failing_check)
        response = client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "not_ready"
        assert body["checks"] == {"database": "unavailable"}
        # 드라이버 오류 문자열(호스트명 등)은 응답에 싣지 않고 로그로만 남긴다
        assert "secret detail" not in response.text

    def test_ready_returns_503_quickly_when_database_hangs(self, fresh_probe, monkeypatch):
        release = threading.Event()

        def hanging_check():
            release.wait(5)

        monkeypatch.setattr(fresh_probe, "_run_check", hanging_check)
        monkeypatch.setattr(readiness, "_timeout_seconds", lambda: 0.1)
        try:
            started = time.monotonic()
            response = client.get("/health/ready")
            elapsed = time.monotonic() - started
        finally:
            release.set()

        assert response.status_code == 503
        assert response.json()["checks"] == {"database": "timeout"}
        assert elapsed < 1.0, f"제한 시간(0.1s)을 넘겨 {elapsed:.2f}s 동안 응답이 막혔다"


class TestProbeIsSingleFlight:
    @pytest.mark.asyncio
    async def test_concurrent_checks_share_one_in_flight_probe(self, fresh_probe, monkeypatch):
        """DB가 멈췄을 때 readiness를 여러 번 호출해도 프로브는 하나만 돈다."""
        calls = []
        release = threading.Event()

        def hanging_check():
            calls.append(1)
            release.wait(5)

        monkeypatch.setattr(fresh_probe, "_run_check", hanging_check)
        try:
            results = await asyncio.gather(
                *[fresh_probe.check(timeout_seconds=0.1) for _ in range(10)]
            )
            # 앞선 프로브가 아직 멈춰 있는 동안 다시 호출해도 새 프로브를 띄우지 않는다
            again = await fresh_probe.check(timeout_seconds=0.1)
        finally:
            release.set()

        assert all(r == (False, "timeout") for r in results + [again])
        assert len(calls) == 1, f"프로브가 {len(calls)}번 실행됐다 (1번이어야 함)"

    @pytest.mark.asyncio
    async def test_new_probe_runs_after_previous_one_finished(self, fresh_probe, monkeypatch):
        calls = []

        def ok_check():
            calls.append(1)

        monkeypatch.setattr(fresh_probe, "_run_check", ok_check)
        assert await fresh_probe.check(timeout_seconds=1.0) == (True, "ok")
        assert await fresh_probe.check(timeout_seconds=1.0) == (True, "ok")
        assert len(calls) == 2, "끝난 프로브의 결과를 재사용하면 안 된다(매번 새로 확인)"
