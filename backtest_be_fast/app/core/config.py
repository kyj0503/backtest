"""
API 서버 설정 관리

**역할**:
- 환경 변수를 통한 애플리케이션 설정 관리
- pydantic-settings를 사용한 타입 안전 설정
- 데이터베이스, CORS, API 경로 등 모든 설정 중앙화

**주요 설정**:
1. API 설정: 버전, 경로 prefix (/api/v1)
2. 서버 설정: 호스트, 포트
3. 데이터베이스: MySQL 연결 정보
4. CORS: 프론트엔드 허용 도메인
5. 로그: 로그 레벨 설정

**환경 변수**:
- 프로젝트 루트의 .env 파일에서 로드
- CORS_ORIGINS: JSON 배열 또는 쉼표로 구분된 문자열

**연관 컴포넌트**:
- Backend: app/main.py (설정 사용)
- Docker: compose.dev.yaml (환경 변수 주입)
- Database: database/schema.sql (스키마 정의)

**싱글톤 패턴**:
- `settings` 객체는 모듈 로드 시 한 번만 생성됨
"""
import json
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic import field_validator


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 설정
    api_v1_str: str = "/api/v1"
    project_name: str = "라고할때살걸"
    version: str = "1.7.10"
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
    max_backtest_duration_years: int = 10  # 포트폴리오 백테스트 최대 기간
    default_commission: float = 0.002  # 0.2%
    
    # 포트폴리오 설정
    max_portfolio_items: int = 20  # 포트폴리오 최대 종목 수

    # 백테스트 요청 한도 (P2-16)
    # 포트폴리오 크기는 max_portfolio_items로 제한되지만 "동시 요청 수 x 기간 x
    # 종목 수"로 늘어나는 총 작업량에는 상한이 없다. 시뮬레이션은 워커 스레드로
    # 위임돼 이벤트 루프를 막지는 않으나, 동시 요청이 많으면 공유 스레드풀을
    # 점유해 다른 요청까지 밀린다.
    min_backtest_period_days: int = 30  # 이보다 짧으면 연환산 지표가 무의미하다

    # --- 동시 실행 상한 / 대기열 / 취소 (A-04 · A-05 · A-06) ---
    # 자세한 동작은 app/services/backtest_runner.py 모듈 docstring 참고.
    #
    # max_concurrent_backtests는 **컨테이너 전체** 상한이다(A-04). uvicorn
    # 워커 프로세스들이 backtest_slot_dir 아래 N개 락 파일(fcntl.flock)을 슬롯으로
    # 공유하므로 워커 수와 무관하다. 과거(P2-16)에는 프로세스 로컬
    # asyncio.Semaphore라서 실제 상한이 워커 수 x 8이었다.
    # 슬롯 디렉터리는 같은 상한을 공유할 프로세스끼리만 같아야 한다 — 컨테이너의
    # /tmp는 컨테이너마다 따로이므로 기본값이 곧 "컨테이너 단위"다.
    # 기본값 8의 근거(2026-09-27 로컬 부하 측정, 17 workers / cpus 4, 캐시 워밍 후,
    # 10년 5종목 SMA): 상한 4/8/12/16에서 처리량 0.63/0.91/0.95/0.64 rps.
    # 8~12에서 포화하고 16에서는 CPU 경합으로 실행 시간 p95가 45초까지 늘어 60초
    # 타임아웃에 근접했다. 대략 "CPU 수 x 2"로 잡고, CPU 한도를 바꾸면 함께 조정한다.
    max_concurrent_backtests: int = 8
    # 슬롯을 얻은 뒤의 실행 시간 상한(초). 넘으면 504를 반환하고 작업에 취소
    # 신호를 보낸다. 슬롯은 작업 스레드가 실제로 끝날 때 반환된다(A-05).
    # P2-16 시절에는 "대기 + 실행" 합계였으나 대기 시간은 아래
    # backtest_queue_timeout_seconds로 분리했다.
    backtest_timeout_seconds: float = 60.0
    # 슬롯 대기 상한(초). 넘으면 503 + Retry-After (작업은 시작도 하지 않음).
    # 대기 + 실행 최대 합계(30 + 60 = 90초)는 nginx proxy_read_timeout(180초)과
    # FE axios 타임아웃(185초)보다 짧아야 한다.
    backtest_queue_timeout_seconds: float = 30.0
    # 취소 신호 후 이 시간 안에 작업이 멈추지 않으면 ERROR 로그를 남긴다(감시용).
    # 슬롯은 이 시간이 지나도 강제 반환하지 않는다 — 실제로 도는 작업이 있는 동안
    # 슬롯을 내주면 상한이 다시 무력화되기 때문이다.
    backtest_cancel_grace_seconds: float = 15.0
    # 클라이언트(IP)별 동시 실행 상한(A-06). 대기 중인 요청도 포함해 센다.
    # 초과 요청은 대기열에 넣지 않고 즉시 429. 0 이하이면 비활성화.
    max_concurrent_backtests_per_client: int = 2
    # 락 파일 디렉터리. 같은 컨테이너의 워커들이 공유해야 한다.
    backtest_slot_dir: str = "/tmp/backtest-slots"
    # X-Forwarded-For를 덧붙일 수 있는 "신뢰하는 프록시" 대역(쉼표 구분 CIDR).
    # 클라이언트 IP는 XFF를 오른쪽부터 읽으며 이 대역이 아닌 첫 주소로 정한다
    # (app/core/client_ip.py). 기본값은 루프백 + 사설망(도커 네트워크 포함).
    trusted_proxy_cidrs: str = (
        "127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fc00::/7"
    )
    max_symbol_length: int = 10  # 심볼 최대 길이
    default_dca_periods: int = 12  # DCA 기본 기간 (개월)
    max_dca_periods: int = 60  # DCA 최대 기간 (개월)
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

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
