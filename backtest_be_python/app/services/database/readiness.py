"""
readiness 프로브: MySQL에 제한 시간 안에 `SELECT 1` (A-07)

**liveness와 readiness를 나누는 이유**:
    /health(liveness)는 "프로세스가 살아 있는가"만 본다. 재시작으로 고쳐지는
    상태만 여기에 걸어야 한다 — DB 장애를 liveness에 넣으면 DB가 내려갔을 때
    멀쩡한 앱 컨테이너까지 재시작 대상이 되어 복구는커녕 재시작 폭주만 부른다.
    /health/ready(readiness)는 "지금 요청을 처리할 수 있는가"를 본다. 백테스트
    요청은 종목 메타데이터·주가 캐시를 MySQL에서 읽으므로 DB 연결이 조건이다.
    외부 Yahoo/Naver API는 조건에 넣지 않는다 — 외부 장애가 배포 실패로 번지면
    안 되고, 그쪽은 backtest_supplemental_outcome_total 같은 별도 지표로 본다.

**운영 연결 풀을 쓰지 않는 이유**:
    1. 풀이 요청으로 가득 차 있으면 pool_timeout(기본 30초)까지 대기한다 —
       "바쁨"과 "DB에 닿을 수 없음"이 구분되지 않는다.
    2. 풀의 연결에는 read_timeout이 없어 반쯤 끊긴 연결에서 `SELECT 1`이 무기한
       멈출 수 있다.
    그래서 같은 URL로 NullPool + 드라이버 타임아웃을 건 전용 엔진을 쓴다. 매
    프로브가 새 TCP 연결·인증까지 실제로 확인한다는 장점도 있다.

**single-flight**:
    프로브는 전용 스레드 1개에서만 돈다. 이전 프로브가 아직 끝나지 않았으면 새로
    띄우지 않고 그 결과를 함께 기다린다. DB가 멈춘 상태에서 readiness를 반복
    호출해도 멈춘 스레드와 DB 연결은 최대 1개다. 드라이버 타임아웃이 걸려 있으므로
    멈춘 프로브도 결국 끝나고, 다음 호출은 새 프로브를 띄운다.
"""

import asyncio
import concurrent.futures
import logging
import math
import threading
from typing import Callable, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)


def _timeout_seconds() -> float:
    """readiness 제한 시간 (테스트에서 교체할 수 있도록 함수로 둔다)."""
    return settings.readiness_db_timeout_seconds


def _default_engine_factory() -> Engine:
    """운영 엔진과 같은 URL로, 풀 없이 드라이버 타임아웃을 건 프로브 전용 엔진."""
    # 순환 임포트를 피하려고 지연 임포트한다.
    from app.services.database.connection_manager import DatabaseConnectionManager

    url = DatabaseConnectionManager.get_engine().url
    connect_args = {}
    if url.get_driver_name() == "pymysql":
        # PyMySQL의 connect_timeout은 1초 이상 정수여야 한다.
        driver_timeout = max(1, math.ceil(_timeout_seconds()))
        connect_args = {
            "connect_timeout": driver_timeout,
            "read_timeout": driver_timeout,
            "write_timeout": driver_timeout,
        }
    return create_engine(url, poolclass=NullPool, connect_args=connect_args)


class DatabaseReadinessProbe:
    """MySQL `SELECT 1` 프로브. check()는 (준비 여부, 사유) 튜플을 돌려준다.

    사유는 "ok" / "timeout" / "unavailable" 중 하나다. 드라이버 오류 문자열
    (호스트명·사용자명이 들어 있을 수 있다)은 응답에 싣지 않고 로그로만 남긴다.
    """

    def __init__(self, engine_factory: Optional[Callable[[], Engine]] = None):
        self._engine_factory = engine_factory or _default_engine_factory
        self._engine: Optional[Engine] = None
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="readiness-probe"
        )
        self._lock = threading.Lock()
        self._in_flight: Optional[concurrent.futures.Future] = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = self._engine_factory()
        return self._engine

    def _run_check(self) -> None:
        """동기 프로브 본체. 실패하면 예외를 던진다 (전용 스레드에서 실행)."""
        with self._get_engine().connect() as conn:
            conn.execute(text("SELECT 1")).scalar()

    def _submit(self) -> concurrent.futures.Future:
        with self._lock:
            if self._in_flight is None or self._in_flight.done():
                # 테스트가 인스턴스 속성으로 _run_check를 교체할 수 있도록
                # 호출 시점에 속성을 읽는다.
                self._in_flight = self._executor.submit(lambda: self._run_check())
            return self._in_flight

    async def check(self, timeout_seconds: Optional[float] = None) -> Tuple[bool, str]:
        timeout = _timeout_seconds() if timeout_seconds is None else timeout_seconds
        future = self._submit()
        try:
            # shield: 이 호출자가 시간 초과로 빠져도 공유 중인 프로브는 취소하지
            # 않는다 (다른 호출자가 같은 결과를 기다리고 있을 수 있다).
            wrapped = asyncio.wrap_future(future)
            # 시간 초과로 버려진 뒤 프로브가 실패해도 "exception was never
            # retrieved" 경고가 남지 않도록 결과를 소비해 둔다.
            wrapped.add_done_callback(lambda f: f.cancelled() or f.exception())
            await asyncio.wait_for(asyncio.shield(wrapped), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("readiness: DB 프로브가 %.1f초 안에 끝나지 않음", timeout)
            return False, "timeout"
        except Exception as exc:  # 드라이버마다 예외 타입이 달라 넓게 잡는다
            logger.warning("readiness: DB 프로브 실패: %s: %s", type(exc).__name__, exc)
            return False, "unavailable"
        return True, "ok"

    def shutdown(self) -> None:
        """전용 스레드를 정리한다 (테스트용). 멈춘 프로브는 기다리지 않는다."""
        self._executor.shutdown(wait=False, cancel_futures=True)
        if self._engine is not None:
            self._engine.dispose()


# 프로세스(워커)당 하나. main.py의 /health/ready가 사용한다.
database_readiness_probe = DatabaseReadinessProbe()
