"""
데이터베이스 연결 풀 설정 관리

**역할**:
- SQLAlchemy 연결 풀 설정 관리
- 동시성 및 성능 최적화 설정 제공
- 연결 재사용 및 검증 설정

**의존성**:
- None (환경 변수는 os.environ을 직접 읽는다 — app.core.config.Settings에는
  의도적으로 의존하지 않아 이 모듈의 "의존성 없음" 성격을 유지한다)

**P2-27 — 풀 크기와 워커 수의 관계 (중요)**:
    프로세스당 최대 연결 수 = pool_size + max_overflow
    전체 최대 연결 수      = workers x (pool_size + max_overflow)

    이 값은 반드시 MySQL의 max_connections보다 작아야 한다:
        workers x (pool_size + max_overflow) <= MySQL max_connections

    MySQL 기본 max_connections는 151이다. compose.dev-prod.yaml은
    uvicorn --workers 17로 기동한다(문서화된 워커 수). 기존 기본값
    (pool_size=40, max_overflow=80 => 프로세스당 120)은 17 workers에서
    최대 2,040 연결을 시도할 수 있어 MySQL 기본 한도를 훨씬 초과했다.
    아래 기본값은 17 workers를 가정해도 안전하도록 낮췄다:
        17 x (DEFAULT_POOL_SIZE + DEFAULT_MAX_OVERFLOW) = 17 x 6 = 102 <= 151
    (mysqld 자체 관리자 연결, 헬스체크, 다른 워커 수로 배포되는 경우 등을 위한
    여유를 남겨 둔다.) DATABASE_POOL_SIZE / DATABASE_MAX_OVERFLOW 환경 변수로
    배포 환경별(워커 수, MySQL max_connections)로 재정의할 수 있다.
"""

import logging
import os

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    """환경 변수를 정수로 읽는다. 미설정이거나 정수로 해석할 수 없으면 기본값을 쓴다."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "Invalid integer for env var %s=%r; falling back to default %d",
            name,
            raw,
            default,
        )
        return default


def _env_bool(name: str, default: bool) -> bool:
    """환경 변수를 불리언으로 읽는다. 미설정이면 기본값을 쓴다."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class PoolConfig:
    """데이터베이스 연결 풀 설정 클래스"""

    # 기본값 상수 — DATABASE_* 환경 변수로 재정의 가능 (app/core/config.py의
    # DATABASE_HOST/PORT/USER/... 명명 규칙을 따름). 클래스 속성 평가 시점
    # (모듈 임포트 시)에 한 번 읽으므로, 컨테이너 기동 전에 환경 변수가
    # 설정돼 있어야 한다 (compose의 environment/env_file이면 충분하다).
    DEFAULT_POOL_SIZE = _env_int("DATABASE_POOL_SIZE", 4)  # 기본 풀 크기 (프로세스당)
    DEFAULT_MAX_OVERFLOW = _env_int("DATABASE_MAX_OVERFLOW", 2)  # 추가 연결 허용 수 (프로세스당)
    DEFAULT_POOL_TIMEOUT = _env_int("DATABASE_POOL_TIMEOUT", 30)  # 연결 대기 시간 (초)
    DEFAULT_POOL_RECYCLE = _env_int("DATABASE_POOL_RECYCLE", 3600)  # 1시간마다 연결 재생성
    DEFAULT_POOL_PRE_PING = _env_bool("DATABASE_POOL_PRE_PING", True)  # 사용 전 연결 유효성 검사
    DEFAULT_FUTURE = True  # SQLAlchemy 2.0 스타일 API 사용

    def __init__(
        self,
        pool_size: int = DEFAULT_POOL_SIZE,
        max_overflow: int = DEFAULT_MAX_OVERFLOW,
        pool_timeout: int = DEFAULT_POOL_TIMEOUT,
        pool_recycle: int = DEFAULT_POOL_RECYCLE,
        pool_pre_ping: bool = DEFAULT_POOL_PRE_PING,
        future: bool = DEFAULT_FUTURE,
    ):
        """
        데이터베이스 연결 풀 설정을 초기화합니다.

        Args:
            pool_size: 기본 풀 크기 (기본값: DATABASE_POOL_SIZE 환경 변수, 없으면 4)
                - 동시에 유지할 연결 수
                - 높을수록 더 많은 동시 연결 지원하지만, 워커(프로세스) 수만큼
                  곱해져 MySQL max_connections에 영향을 준다 (클래스
                  docstring의 P2-27 설명 참고)
            max_overflow: 추가 연결 허용 수 (기본값: DATABASE_MAX_OVERFLOW 환경 변수, 없으면 2)
                - 기본 풀이 가득 찰 때 추가로 허용할 연결 수
                - pool_size + max_overflow = 프로세스당 최대 연결 수
            pool_timeout: 연결 대기 시간 (기본값: 30초)
                - 사용 가능한 연결을 기다리는 최대 시간
            pool_recycle: 연결 재생성 주기 (기본값: 3600초 = 1시간)
                - 이 시간이 지난 연결은 자동으로 재생성
                - DB 타임아웃 방지에 유용
            pool_pre_ping: 사용 전 연결 유효성 검사 (기본값: True)
                - 연결을 사용하기 전에 PING 실행
                - 끊긴 연결 자동 감지
            future: SQLAlchemy 2.0 스타일 API 사용 (기본값: True)
        """
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.future = future

        self._validate()
        self._log_config()

    def _validate(self) -> None:
        """설정 값의 유효성을 검사합니다."""
        if self.pool_size <= 0:
            raise ValueError(f"pool_size must be positive, got {self.pool_size}")
        if self.max_overflow < 0:
            raise ValueError(f"max_overflow must be non-negative, got {self.max_overflow}")
        if self.pool_timeout <= 0:
            raise ValueError(f"pool_timeout must be positive, got {self.pool_timeout}")
        if self.pool_recycle <= 0:
            raise ValueError(f"pool_recycle must be positive, got {self.pool_recycle}")

    def _log_config(self) -> None:
        """설정 정보를 로깅합니다."""
        logger.debug(
            "Pool configuration: pool_size=%d max_overflow=%d timeout=%ds recycle=%ds",
            self.pool_size,
            self.max_overflow,
            self.pool_timeout,
            self.pool_recycle,
        )

    def get_kwargs(self) -> dict:
        """SQLAlchemy create_engine()에 전달할 kwargs를 반환합니다."""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "future": self.future,
        }

    def get_info(self) -> dict:
        """설정 정보를 딕셔너리로 반환합니다."""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "future": self.future,
            "max_total_connections": self.pool_size + self.max_overflow,
        }
