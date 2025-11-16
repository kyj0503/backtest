"""
데이터베이스 설정 관리

**역할**:
- 환경 변수 및 settings에서 DB 설정 로드
- DATABASE_URL 또는 개별 설정 우선순위 처리
- DB 연결 정보 검증 및 제공
- 마스킹된 URL 생성 (로깅용)

**의존성**:
- app.core.config: 애플리케이션 설정
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """데이터베이스 설정 정보 클래스"""

    def __init__(
        self,
        database_url: Optional[str] = None,
        database_host: Optional[str] = None,
        database_port: Optional[str] = None,
        database_user: Optional[str] = None,
        database_password: Optional[str] = None,
        database_name: Optional[str] = None,
    ):
        """
        데이터베이스 설정을 초기화합니다.

        Args:
            database_url: 전체 DATABASE_URL (이 값이 있으면 우선 사용)
            database_host: 호스트명 (기본값: 127.0.0.1)
            database_port: 포트 번호 (기본값: 3306)
            database_user: 사용자명 (기본값: root)
            database_password: 비밀번호 (기본값: password)
            database_name: 데이터베이스명 (기본값: stock_data_cache)

        Note:
            - database_url이 제공되면 이를 우선 사용합니다
            - 개별 설정이 제공되면 DATABASE_URL을 생성합니다
            - 모두 없으면 환경 변수 또는 기본값을 사용합니다
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")

        # DATABASE_URL에서 설정 파싱 시도
        if self.database_url:
            self._parse_url_components()
        else:
            # 개별 설정 사용
            self._load_from_components(
                database_host=database_host,
                database_port=database_port,
                database_user=database_user,
                database_password=database_password,
                database_name=database_name,
            )

    def _parse_url_components(self) -> None:
        """DATABASE_URL에서 설정 요소 파싱합니다."""
        try:
            # SQLAlchemy >=1.4 URL 파싱
            try:
                from sqlalchemy.engine import make_url
            except ImportError:
                from sqlalchemy.engine.url import make_url

            parsed = make_url(self.database_url)
            self.database_host = parsed.host
            self.database_port = str(parsed.port) if parsed.port is not None else "3306"
            self.database_user = parsed.username
            self.database_password = parsed.password
            self.database_name = parsed.database

            logger.debug(f"DATABASE_URL 파싱 성공: {parsed.host}:{parsed.port}/{parsed.database}")
        except Exception as e:
            logger.warning(f"DATABASE_URL 파싱 실패: {e}, 개별 환경 변수로 폴백합니다")
            self._load_from_components()

    def _load_from_components(
        self,
        database_host: Optional[str] = None,
        database_port: Optional[str] = None,
        database_user: Optional[str] = None,
        database_password: Optional[str] = None,
        database_name: Optional[str] = None,
    ) -> None:
        """개별 설정 요소에서 설정을 로드합니다."""
        try:
            from app.core.config import settings

            self.database_host = database_host or settings.database_host or os.getenv("DATABASE_HOST", "127.0.0.1")
            self.database_port = database_port or settings.database_port or os.getenv("DATABASE_PORT", "3306")
            self.database_user = database_user or settings.database_user or os.getenv("DATABASE_USER", "root")
            self.database_password = database_password or settings.database_password or os.getenv("DATABASE_PASSWORD", "password")
            self.database_name = database_name or settings.database_name or os.getenv("DATABASE_NAME", "stock_data_cache")
        except Exception:
            # settings를 로드할 수 없으면 환경 변수만 사용
            self.database_host = database_host or os.getenv("DATABASE_HOST", "127.0.0.1")
            self.database_port = database_port or os.getenv("DATABASE_PORT", "3306")
            self.database_user = database_user or os.getenv("DATABASE_USER", "root")
            self.database_password = database_password or os.getenv("DATABASE_PASSWORD", "password")
            self.database_name = database_name or os.getenv("DATABASE_NAME", "stock_data_cache")

        # DATABASE_URL이 없으면 생성
        if not self.database_url:
            self._build_url()

    def _build_url(self) -> None:
        """개별 설정 요소로부터 DATABASE_URL을 생성합니다."""
        self.database_url = (
            f"mysql+pymysql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}?charset=utf8mb4"
        )

    def get_url(self) -> str:
        """데이터베이스 연결 URL을 반환합니다."""
        return self.database_url

    def get_masked_url(self) -> str:
        """로깅용 마스킹된 URL을 반환합니다 (비밀번호 숨김)."""
        try:
            if self.database_password and isinstance(self.database_url, str):
                return self.database_url.replace(self.database_password, "***")
        except Exception:
            pass
        return self.database_url

    def get_components(self) -> dict:
        """연결 설정 요소를 딕셔너리로 반환합니다."""
        return {
            "host": self.database_host,
            "port": self.database_port,
            "user": self.database_user,
            "password": self.database_password,
            "name": self.database_name,
            "url_provided": bool(os.getenv("DATABASE_URL")),
        }

    def log_info(self) -> None:
        """연결 정보를 로깅합니다."""
        logger.info(
            "Database configuration loaded: host=%s port=%s user=%s db=%s DATABASE_URL_set=%s",
            self.database_host or "<unknown>",
            self.database_port or "<unknown>",
            self.database_user or "<unknown>",
            self.database_name or "<unknown>",
            "yes" if os.getenv("DATABASE_URL") else "no",
        )
        logger.debug(f"SQLAlchemy URL (masked): {self.get_masked_url()}")
        print(
            f"[database_config] Loaded: host={self.database_host} port={self.database_port} "
            f"user={self.database_user} db={self.database_name} masked_url={self.get_masked_url()}"
        )
