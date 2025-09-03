# 백엔드 개발 가이드

FastAPI 기반 백테스팅 시스템의 백엔드 개발 가이드입니다.

## 기술 스택

### 핵심 프레임워크
- **FastAPI** 0.104+ - 고성능 웹 API 프레임워크
- **Pydantic V2** - 데이터 검증 및 직렬화
- **Python** 3.11+ - 메인 개발 언어

### 백테스팅 엔진
- **backtesting.py** - 핵심 백테스트 엔진
- **yfinance** - 주가 데이터 수집 (Yahoo Finance API)
- **pandas** - 데이터 처리 및 분석
- **numpy** - 수치 계산

### 데이터 저장소
- **MySQL** - 주가 데이터 캐시 저장소
- **SQLAlchemy** - ORM (Object-Relational Mapping)

### 외부 API
- **네이버 검색 API** - 뉴스 검색 서비스
- **Yahoo Finance API** - 실시간 주가 데이터

### 개발 및 테스트
- **pytest** - 단위 테스트 및 통합 테스트
- **uvicorn** - ASGI 서버
- **Docker** - 컨테이너 환경

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                 # FastAPI 애플리케이션 진입점
│   ├── api/                    # API 라우터 및 엔드포인트
│   │   └── v1/
│   │       ├── endpoints/      # 각 도메인별 엔드포인트
│   │       │   ├── backtest.py      # 백테스트 API
│   │       │   ├── naver_news.py    # 네이버 뉴스 API
│   │       │   ├── strategies.py    # 전략 관리 API
│   │       │   └── optimize.py      # 최적화 API
│   │       └── api.py          # API 라우터 통합
│   ├── core/                   # 핵심 설정 및 예외 처리
│   │   ├── config.py           # 애플리케이션 설정
│   │   ├── exceptions.py       # 공통 예외 정의
│   │   └── custom_exceptions.py # 커스텀 예외 처리
│   ├── models/                 # 데이터 모델 정의
│   │   ├── requests.py         # API 요청 모델 (Pydantic)
│   │   ├── responses.py        # API 응답 모델 (Pydantic)
│   │   └── schemas.py          # 공통 스키마 정의
│   ├── services/               # 비즈니스 로직 서비스
│   │   ├── backtest_service.py      # 백테스트 핵심 로직
│   │   ├── portfolio_service.py     # 포트폴리오 관리
│   │   ├── strategy_service.py      # 전략 관리
│   │   └── yfinance_db.py          # 데이터베이스 캐시 관리
│   └── utils/                  # 유틸리티 함수
│       ├── data_fetcher.py     # 데이터 수집 유틸리티
│       ├── portfolio_utils.py  # 포트폴리오 계산 유틸리티
│       ├── serializers.py      # 데이터 직렬화
│       └── user_messages.py    # 사용자 친화적 메시지
├── strategies/                 # 투자 전략 구현
│   ├── sma_cross.py           # 단순이동평균 교차 전략
│   └── rsi_strategy.py        # RSI 기반 전략
├── tests/                     # 테스트 코드
│   ├── unit/                  # 단위 테스트
│   ├── integration/           # 통합 테스트
│   ├── e2e/                   # End-to-End 테스트
│   └── fixtures/              # 테스트 데이터 및 모킹
├── doc/                       # 백엔드 문서
├── requirements.txt           # 운영 의존성
├── requirements-test.txt      # 테스트 의존성
└── pytest.ini               # pytest 설정
```

## 개발 환경 설정

### 1. Docker 개발 환경 (권장)
```bash
# 백엔드 컨테이너만 실행
docker-compose up backend

# 전체 개발 환경 실행
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### 2. 로컬 개발 환경
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-test.txt

# 환경변수 설정
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=yfinance_cache
export NAVER_CLIENT_ID=your_client_id
export NAVER_CLIENT_SECRET=your_client_secret

# 서버 실행
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 환경변수 설정
```bash
# MySQL 데이터베이스 (캐시)
MYSQL_HOST=host.docker.internal  # Windows Docker
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=yfinance_cache

# 네이버 검색 API (선택사항)
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# 개발 환경 설정
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## API 개발

### 1. 새로운 엔드포인트 추가

#### Step 1: 요청/응답 모델 정의
```python
# app/models/requests.py
class NewFeatureRequest(BaseModel):
    """새로운 기능 요청 모델"""
    parameter1: str = Field(..., description="필수 파라미터")
    parameter2: Optional[int] = Field(default=10, description="선택 파라미터")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parameter1": "example_value",
                "parameter2": 10
            }
        }
    )

# app/models/responses.py  
class NewFeatureResponse(BaseModel):
    """새로운 기능 응답 모델"""
    result: str
    data: Dict[str, Any]
```

#### Step 2: 서비스 로직 구현
```python
# app/services/new_feature_service.py
class NewFeatureService:
    """새로운 기능 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process_request(self, request: NewFeatureRequest) -> NewFeatureResponse:
        """요청 처리 메인 로직"""
        try:
            # 비즈니스 로직 구현
            result_data = self._perform_calculation(request)
            
            return NewFeatureResponse(
                result="success",
                data=result_data
            )
        except Exception as e:
            self.logger.error(f"처리 중 오류: {str(e)}")
            raise
    
    def _perform_calculation(self, request: NewFeatureRequest) -> Dict[str, Any]:
        """실제 계산 로직"""
        # 구현 내용
        pass
```

#### Step 3: API 엔드포인트 생성
```python
# app/api/v1/endpoints/new_feature.py
from fastapi import APIRouter, HTTPException, status
from ....models.requests import NewFeatureRequest
from ....models.responses import NewFeatureResponse
from ....services.new_feature_service import NewFeatureService

router = APIRouter()
service = NewFeatureService()

@router.post(
    "/process",
    response_model=NewFeatureResponse,
    status_code=status.HTTP_200_OK,
    summary="새로운 기능 처리",
    description="새로운 기능을 처리합니다."
)
async def process_new_feature(request: NewFeatureRequest):
    """
    새로운 기능 처리 API
    
    - **parameter1**: 필수 파라미터 설명
    - **parameter2**: 선택 파라미터 설명
    """
    try:
        result = await service.process_request(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"처리 중 오류가 발생했습니다: {str(e)}"
        )
```

#### Step 4: 라우터 등록
```python
# app/api/v1/api.py
from .endpoints import new_feature

api_router.include_router(
    new_feature.router,
    prefix="/new-feature",
    tags=["new-feature"]
)
```

### 2. 데이터베이스 캐시 활용

#### 데이터 저장
```python
from app.services.yfinance_db import save_ticker_data, load_ticker_data

# 주가 데이터 저장
df = yfinance_client.download("AAPL", start="2023-01-01", end="2023-12-31")
save_ticker_data("AAPL", df)

# 주가 데이터 로드
cached_data = load_ticker_data("AAPL", "2023-01-01", "2023-12-31")
if cached_data is not None:
    # 캐시된 데이터 사용
    pass
else:
    # 새로운 데이터 가져오기
    pass
```

### 3. 전략 개발

#### 새로운 전략 추가
```python
# strategies/my_strategy.py
from backtesting import Strategy
import pandas as pd

class MyCustomStrategy(Strategy):
    """커스텀 투자 전략"""
    
    # 전략 파라미터 정의
    fast_period = 10
    slow_period = 30
    
    def init(self):
        """전략 초기화"""
        # 기술 지표 계산
        self.fast_ma = self.I(self._sma, self.data.Close, self.fast_period)
        self.slow_ma = self.I(self._sma, self.data.Close, self.slow_period)
    
    def next(self):
        """매 시점마다 실행되는 전략 로직"""
        # 매수 신호
        if self.fast_ma[-1] > self.slow_ma[-1] and self.fast_ma[-2] <= self.slow_ma[-2]:
            self.buy()
        
        # 매도 신호
        elif self.fast_ma[-1] < self.slow_ma[-1] and self.fast_ma[-2] >= self.slow_ma[-2]:
            self.sell()
    
    def _sma(self, series, period):
        """단순 이동평균 계산"""
        return pd.Series(series).rolling(period).mean()

# app/services/strategy_service.py에 전략 등록
_strategies = {
    # 기존 전략들...
    "my_custom_strategy": MyCustomStrategy,
}
```

## 테스트

### 1. 테스트 실행
```bash
# 전체 테스트 실행
docker-compose exec backend pytest tests/ -v

# 특정 테스트 파일 실행
docker-compose exec backend pytest tests/unit/test_backtest_service.py -v

# 커버리지 리포트 생성
docker-compose exec backend pytest tests/ --cov=app --cov-report=html
```

### 2. 테스트 구조

#### 단위 테스트 (Unit Tests)
```python
# tests/unit/test_backtest_service.py
import pytest
from app.services.backtest_service import BacktestService
from app.models.requests import BacktestRequest

class TestBacktestService:
    """백테스트 서비스 단위 테스트"""
    
    @pytest.fixture
    def service(self):
        return BacktestService()
    
    @pytest.fixture
    def sample_request(self):
        return BacktestRequest(
            ticker="AAPL",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_cash=10000,
            strategy="buy_and_hold"
        )
    
    def test_validate_request(self, service, sample_request):
        """요청 검증 테스트"""
        # 유효한 요청은 예외가 발생하지 않아야 함
        service.validate_backtest_request(sample_request)
    
    def test_invalid_ticker(self, service):
        """유효하지 않은 티커 테스트"""
        invalid_request = BacktestRequest(
            ticker="INVALID",
            start_date="2023-01-01", 
            end_date="2023-12-31",
            initial_cash=10000,
            strategy="buy_and_hold"
        )
        
        with pytest.raises(ValueError):
            service.validate_backtest_request(invalid_request)
```

#### 통합 테스트 (Integration Tests)
```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestBacktestAPI:
    """백테스트 API 통합 테스트"""
    
    def test_portfolio_backtest_success(self):
        """포트폴리오 백테스트 성공 케이스"""
        request_data = {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 5000,
                    "investment_type": "lump_sum",
                    "asset_type": "stock"
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "commission": 0.002,
            "strategy": "buy_and_hold"
        }
        
        response = client.post("/api/v1/backtest/portfolio", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "portfolio_performance" in data["data"]
```

### 3. 모킹 및 픽스처

#### 데이터 모킹
```python
# tests/fixtures/mock_data.py
import pandas as pd
from datetime import datetime, timedelta

def create_mock_stock_data(start_date: str, end_date: str, ticker: str = "AAPL") -> pd.DataFrame:
    """모의 주가 데이터 생성"""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 간단한 랜덤 워크로 주가 생성
    prices = []
    current_price = 100.0
    
    for _ in dates:
        change = np.random.normal(0, 0.02)  # 2% 변동성
        current_price *= (1 + change)
        prices.append(current_price)
    
    return pd.DataFrame({
        'Open': prices,
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Close': prices,
        'Volume': [1000000] * len(prices)
    }, index=dates)

# tests/conftest.py
@pytest.fixture
def mock_yfinance_data():
    """yfinance 데이터 모킹"""
    def _mock_download(ticker, start, end):
        return create_mock_stock_data(start, end, ticker)
    
    with patch('yfinance.download', side_effect=_mock_download):
        yield
```

## 현금 자산 처리

현금 자산은 무위험 자산으로 특별한 처리가 필요합니다.

### 현금 자산 특징
- **0% 수익률**: 시간에 관계없이 변동 없음
- **asset_type**: 'cash'로 구분
- **변동성 없음**: 안전 자산으로 포트폴리오 리스크 감소

### 구현 예시
```python
# app/services/portfolio_service.py
def handle_cash_asset(self, portfolio_item: PortfolioStock) -> Dict[str, Any]:
    """현금 자산 처리"""
    if portfolio_item.asset_type == 'cash':
        return {
            'symbol': portfolio_item.symbol,
            'amount': portfolio_item.amount,
            'final_value': portfolio_item.amount,  # 변동 없음
            'return': 0.0,  # 0% 수익률
            'volatility': 0.0,  # 변동성 없음
            'asset_type': 'cash'
        }
    else:
        # 일반 주식 자산 처리
        return self.process_stock_asset(portfolio_item)
```

상세한 현금 자산 처리 방법은 [`CASH_ASSETS.md`](CASH_ASSETS.md)를 참조하세요.

## 성능 최적화

### 1. 데이터베이스 캐시 활용
```python
# 캐시 우선 데이터 로딩
def get_stock_data_optimized(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """캐시 우선 주가 데이터 로딩"""
    # 1. DB 캐시에서 데이터 확인
    cached_data = load_ticker_data(ticker, start_date, end_date)
    
    if cached_data is not None and not cached_data.empty:
        logger.info(f"캐시에서 데이터 로드: {ticker}")
        return cached_data
    
    # 2. 캐시에 없으면 yfinance에서 가져오기
    logger.info(f"yfinance에서 데이터 가져오기: {ticker}")
    fresh_data = yfinance.download(ticker, start=start_date, end=end_date)
    
    # 3. 가져온 데이터를 캐시에 저장
    save_ticker_data(ticker, fresh_data)
    
    return fresh_data
```

### 2. 비동기 처리
```python
# app/services/backtest_service.py
import asyncio

async def run_multiple_backtests(requests: List[BacktestRequest]) -> List[BacktestResult]:
    """여러 백테스트 동시 실행"""
    tasks = []
    
    for request in requests:
        task = asyncio.create_task(self.run_backtest(request))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### 3. 메모리 최적화
```python
# 대용량 데이터 처리 시 청크 단위 처리
def process_large_dataset(data: pd.DataFrame, chunk_size: int = 1000) -> pd.DataFrame:
    """대용량 데이터 청크 단위 처리"""
    results = []
    
    for i in range(0, len(data), chunk_size):
        chunk = data.iloc[i:i+chunk_size]
        processed_chunk = process_chunk(chunk)
        results.append(processed_chunk)
    
    return pd.concat(results, ignore_index=True)
```

## 모니터링 및 로깅

### 로깅 설정
```python
# app/core/config.py
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)

# 서비스별 로거
logger = logging.getLogger(__name__)
```

### 에러 모니터링
```python
# app/utils/user_messages.py
import uuid
import logging

def log_error_for_debugging(error: Exception, context: str, additional_info: dict = None) -> str:
    """디버깅을 위한 에러 로깅"""
    error_id = str(uuid.uuid4())[:8]
    
    error_info = {
        'error_id': error_id,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'additional_info': additional_info or {}
    }
    
    logging.error(f"[{error_id}] {context}: {error_info}")
    
    return error_id
```

## 배포

### 1. Docker 빌드
```bash
# 백엔드 이미지 빌드
docker build -t backtest-backend ./backend

# 멀티 플랫폼 빌드 (ARM64, AMD64)
docker buildx build --platform linux/amd64,linux/arm64 -t backtest-backend ./backend
```

### 2. 환경별 설정
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 설정"""
    environment: str = "development"
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "yfinance_cache"
    
    # 네이버 API (선택사항)
    naver_client_id: Optional[str] = None
    naver_client_secret: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3. 헬스체크
```python
# app/api/v1/endpoints/health.py
@router.get("/health")
async def health_check():
    """서비스 상태 확인"""
    checks = {
        "database": check_database_connection(),
        "yfinance": check_yfinance_connection(),
        "naver_api": check_naver_api_connection()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 문제 해결

### 일반적인 이슈

1. **yfinance 연결 실패**
   - 인터넷 연결 확인
   - Yahoo Finance 서비스 상태 확인
   - 요청 빈도 조절 (Rate Limiting)

2. **MySQL 연결 실패**
   - 데이터베이스 서버 상태 확인
   - 네트워크 연결 확인
   - 인증 정보 확인

3. **메모리 부족**
   - 데이터 처리 청크 크기 조절
   - 불필요한 데이터 정리
   - 가비지 컬렉션 최적화

### 디버깅 도구
```bash
# 로그 확인
docker-compose logs backend

# 컨테이너 접속
docker-compose exec backend bash

# 프로세스 모니터링
docker-compose exec backend top

# 메모리 사용량 확인
docker-compose exec backend free -h
```

## 기여 가이드

### 코드 스타일
- **PEP 8** 준수
- **Type Hints** 사용
- **Docstring** 작성 (Google Style)

### 커밋 메시지
- `feat: 새로운 기능 추가`
- `fix: 버그 수정`
- `docs: 문서 업데이트`
- `test: 테스트 추가`
- `refactor: 코드 리팩토링`

### Pull Request
1. Feature 브랜치 생성
2. 개발 및 테스트
3. 문서 업데이트
4. PR 생성 및 리뷰 요청