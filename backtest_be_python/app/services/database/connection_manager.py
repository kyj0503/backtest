"""
데이터베이스 연결 관리

**역할**:
- SQLAlchemy Engine 생성 및 캐싱
- DatabaseConfig와 PoolConfig를 활용한 통합 관리
- 싱글톤 패턴으로 중복 생성 방지

**의존성**:
- app.services.database.database_config: DB 설정
- app.services.database.pool_config: 연결 풀 설정
"""

import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from app.services.database.database_config import DatabaseConfig
from app.services.database.pool_config import PoolConfig

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """데이터베이스 연결 관리 클래스 (싱글톤)"""

    _instance: Optional["DatabaseConnectionManager"] = None
    _engine_cache: Optional[Engine] = None

    def __new__(cls) -> "DatabaseConnectionManager":
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        database_config: Optional[DatabaseConfig] = None,
        pool_config: Optional[PoolConfig] = None,
    ):
        """
        데이터베이스 연결 관리자를 초기화합니다.

        Args:
            database_config: 데이터베이스 설정 (None이면 새로 생성)
            pool_config: 연결 풀 설정 (None이면 기본값 사용)

        Note:
            - 싱글톤 패턴이므로 첫 초기화만 사용됨
            - 이후 호출은 기존 설정을 재사용
        """
        # 이미 초기화된 경우 스킵
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.config = database_config or DatabaseConfig()
        self.pool_config = pool_config or PoolConfig()
        self._initialized = True

        self.config.log_info()

    @classmethod
    def get_engine(cls) -> Engine:
        """
        캐시된 SQLAlchemy Engine을 반환합니다.

        캐시가 없으면 생성합니다.

        Returns:
            SQLAlchemy Engine 인스턴스
        """
        if cls._engine_cache is not None:
            return cls._engine_cache

        # 싱글톤 인스턴스 생성 및 초기화
        manager = cls()
        cls._engine_cache = manager._create_engine()
        return cls._engine_cache

    def _create_engine(self) -> Engine:
        """
        DatabaseConfig와 PoolConfig를 사용하여 Engine을 생성합니다.

        Returns:
            SQLAlchemy Engine 인스턴스
        """
        db_url = self.config.get_url()
        pool_kwargs = self.pool_config.get_kwargs()

        logger.info(
            "Creating SQLAlchemy engine: %s (pool_size=%d, max_overflow=%d)",
            self.config.get_masked_url(),
            pool_kwargs["pool_size"],
            pool_kwargs["max_overflow"],
        )

        engine = create_engine(db_url, **pool_kwargs)

        logger.info("SQLAlchemy engine created successfully")
        return engine

    @classmethod
    def reset_cache(cls) -> None:
        """엔진 캐시를 초기화합니다 (테스트용)."""
        cls._engine_cache = None
        logger.info("Database engine cache cleared")

    @classmethod
    def get_info(cls) -> dict:
        """현재 연결 설정 정보를 반환합니다."""
        manager = cls()
        return {
            "database": manager.config.get_components(),
            "pool": manager.pool_config.get_info(),
        }
