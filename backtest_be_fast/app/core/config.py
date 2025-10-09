"""
API 서버 설정 관리
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic import field_validator


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 설정
    api_v1_str: str = "/api/v1"
    project_name: str = "라고할때살걸"
    version: str = "1.0.0"
    description: str = "FastAPI server for backtesting.py library"
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # CORS 설정
    # CORS 설정: read raw env as string and expose a parsed property to avoid
    # pydantic attempting to json-decode complex env values.
    backend_cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:5174,http://localhost:8001,http://localhost:8082,https://backtest.yeonjae.kr,https://backtest-be.yeonjae.kr",
        env="BACKEND_CORS_ORIGINS",
    )

    @property
    def backend_cors_origins(self) -> list[str]:
        """Return CORS origins as a list. Accepts JSON array or comma-separated string."""
        v = getattr(self, "backend_cors_origins_str", "")
        if not v:
            return []
        v = v.strip()
        # try JSON first
        try:
            import json

            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
        # fallback: comma-separated
        return [s.strip() for s in v.split(",") if s.strip()]
    
    # 백테스팅 설정
    default_initial_cash: float = 10000.0
    max_backtest_duration_days: int = 3650  # 10년
    max_backtest_duration_years: int = 5  # 포트폴리오 백테스트 최대 기간
    default_commission: float = 0.002  # 0.2%
    
    # 포트폴리오 설정
    max_portfolio_items: int = 10  # 포트폴리오 최대 종목 수
    max_symbol_length: int = 10  # 심볼 최대 길이
    max_dca_periods: int = 60  # DCA 최대 기간 (개월)
    
    # 최적화 설정
    max_optimization_iterations: int = Field(default=1000, env="MAX_OPTIMIZATION_ITERATIONS")
    optimization_timeout_seconds: int = Field(default=300, env="OPTIMIZATION_TIMEOUT_SECONDS")  # 5분
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 보안 설정
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    
    # 외부 API 설정
    yahoo_finance_timeout: int = 30
    exchange_rate_ticker: str = "KRW=X"  # 원달러 환율 티커
    volatility_threshold_pct: float = 5.0  # 주가 변동성 기본 임계값 (%)
    
    # 네이버 API 키 (환경변수 또는 .env에서 로드)
    naver_client_id: Optional[str] = Field(default=None, env="NAVER_CLIENT_ID")
    naver_client_secret: Optional[str] = Field(default=None, env="NAVER_CLIENT_SECRET")
    # Database configuration (support both DATABASE_URL and individual parts)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_host: Optional[str] = Field(default=None, env="DATABASE_HOST")
    database_port: Optional[str] = Field(default=None, env="DATABASE_PORT")
    database_user: Optional[str] = Field(default=None, env="DATABASE_USER")
    database_password: Optional[str] = Field(default=None, env="DATABASE_PASSWORD")
    database_name: Optional[str] = Field(default=None, env="DATABASE_NAME")
    
    # pydantic v2 configuration
    model_config = {
        "env_file": ".env",
        # allow different env var casing and ignore extra env variables that
        # may be provided by the container environment
        "case_sensitive": False,
        "extra": "ignore",
    }


# 글로벌 설정 인스턴스
settings = Settings() 
