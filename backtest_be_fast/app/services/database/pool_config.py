"""
데이터베이스 연결 풀 설정 관리

**역할**:
- SQLAlchemy 연결 풀 설정 관리
- 동시성 및 성능 최적화 설정 제공
- 연결 재사용 및 검증 설정

**의존성**:
- None
"""

import logging

logger = logging.getLogger(__name__)


class PoolConfig:
    """데이터베이스 연결 풀 설정 클래스"""

    # 기본값 상수
    DEFAULT_POOL_SIZE = 40  # 기본 풀 크기 (기본값 5에서 증가)
    DEFAULT_MAX_OVERFLOW = 80  # 추가 연결 허용 수 (기본값 10에서 증가)
    DEFAULT_POOL_TIMEOUT = 30  # 연결 대기 시간 (초)
    DEFAULT_POOL_RECYCLE = 3600  # 1시간마다 연결 재생성
    DEFAULT_POOL_PRE_PING = True  # 사용 전 연결 유효성 검사
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
            pool_size: 기본 풀 크기 (기본값: 40)
                - 동시에 유지할 연결 수
                - 높을수록 더 많은 동시 연결 지원
            max_overflow: 추가 연결 허용 수 (기본값: 80)
                - 기본 풀이 가득 찰 때 추가로 허용할 연결 수
                - pool_size + max_overflow = 최대 연결 수
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
