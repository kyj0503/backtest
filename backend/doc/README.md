# 백엔드 개발 가이드

FastAPI 기반의 백테스팅 시스템 백엔드 개발 가이드입니다.

## 기술 스택

- **Framework**: FastAPI + uvicorn
- **Database**: MySQL (캐시 저장소)
- **Data Source**: yfinance API
- **Testing**: pytest + asyncio
- **Container**: Docker
- **Validation**: Pydantic V2

**상세한 기술 선택 이유**: [`TECH_STACK_BACKEND.md`](TECH_STACK_BACKEND.md) 참조

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                    # FastAPI 애플리케이션 진입점
│   ├── api/                       # API 라우터
│   │   ├── api.py                # 메인 라우터
│   │   └── v1/endpoints/         # API 엔드포인트
│   ├── core/                     # 핵심 설정
│   │   ├── config.py            # 환경 설정
│   │   └── exceptions.py        # 예외 처리
│   ├── models/                   # 데이터 모델
│   │   ├── requests.py          # 요청 모델
│   │   ├── responses.py         # 응답 모델
│   │   └── schemas.py           # 데이터베이스 스키마
│   ├── services/                # 비즈니스 로직
│   │   ├── backtest_service.py  # 백테스트 서비스
│   │   ├── strategy_service.py  # 전략 관리
│   │   └── portfolio_service.py # 포트폴리오 서비스
│   └── utils/                   # 유틸리티
│       ├── data_fetcher.py      # 데이터 수집
│       └── portfolio_utils.py   # 포트폴리오 유틸리티
├── strategies/                  # 투자 전략
│   ├── sma_cross.py            # 이동평균 전략
│   └── rsi_strategy.py         # RSI 전략
├── tests/                      # 테스트 코드
│   ├── unit/                   # 단위 테스트
│   ├── integration/            # 통합 테스트
│   └── e2e/                    # 종단 간 테스트
└── doc/                        # 문서
```

## 핵심 서비스

### BacktestService
백테스트 실행을 담당하는 핵심 서비스입니다.

```python
# 백테스트 실행
async def run_backtest(
    request: UnifiedBacktestRequest
) -> UnifiedBacktestResponse:
    # 데이터 수집
    data = await fetch_stock_data(request.portfolio)
    
    # 전략 적용
    strategy = get_strategy(request.strategy)
    
    # 백테스트 실행
    bt = Backtest(data, strategy, **strategy_params)
    result = bt.run()
    
    return format_response(result)
```

### StrategyService
투자 전략 관리를 담당합니다.

```python
# 전략 등록
_strategies = {
    'sma_cross': SMAStrategy,
    'rsi': RSIStrategy,
    'buy_and_hold': BuyAndHoldStrategy
}

def get_strategy(strategy_name: str) -> Strategy:
    """전략 인스턴스 반환"""
    if strategy_name not in _strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    return _strategies[strategy_name]
```

### DataFetcher
yfinance를 통한 주식 데이터 수집을 담당합니다.

```python
async def fetch_stock_data(
    symbols: List[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """주식 데이터 수집 및 캐싱"""
    # MySQL 캐시 확인
    cached_data = await get_cached_data(symbols, start_date, end_date)
    if cached_data:
        return cached_data
    
    # yfinance에서 데이터 수집
    data = yf.download(symbols, start=start_date, end=end_date)
    
    # MySQL에 캐싱
    await cache_data(data, symbols, start_date, end_date)
    
    return data
```

## 현금 자산 처리

### 무위험 자산 구현
현금 자산은 `asset_type='cash'`로 식별되며, 무위험 자산으로 처리됩니다.

```python
def process_cash_assets(portfolio: List[PortfolioStock]) -> pd.DataFrame:
    """현금 자산을 무위험 자산으로 처리"""
    cash_assets = [asset for asset in portfolio if asset.asset_type == 'cash']
    
    for cash_asset in cash_assets:
        # 현금은 0% 수익률, 변동성 없음
        cash_data = create_cash_data(
            amount=cash_asset.amount,
            start_date=start_date,
            end_date=end_date
        )
        portfolio_data[f"CASH_{cash_asset.symbol}"] = cash_data
    
    return portfolio_data
```

### 현금 데이터 생성
```python
def create_cash_data(amount: float, start_date: str, end_date: str) -> pd.Series:
    """현금 자산 데이터 생성 (일정한 가치 유지)"""
    date_range = pd.date_range(start=start_date, end=end_date)
    return pd.Series(
        data=[amount] * len(date_range),
        index=date_range,
        name='Cash'
    )
```

## API 엔드포인트

### 통합 백테스트 API
```python
@router.post("/backtest", response_model=UnifiedBacktestResponse)
async def run_unified_backtest(
    request: UnifiedBacktestRequest
) -> UnifiedBacktestResponse:
    """단일 종목 및 포트폴리오 백테스트 통합 API"""
    try:
        result = await backtest_service.run_backtest(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 네이버 뉴스 API
```python
@router.get("/naver-news/{ticker}")
async def get_news_for_ticker(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[NewsItem]:
    """종목별 네이버 뉴스 검색"""
    return await naver_news_service.search_news(ticker, start_date, end_date)
```

## 데이터 모델 (Pydantic V2)

### 요청 모델
```python
class PortfolioStock(BaseModel):
    symbol: str = Field(..., description="종목 심볼")
    amount: float = Field(..., gt=0, description="투자 금액")
    investment_type: Optional[Literal['lump_sum', 'dca']] = 'lump_sum'
    dca_periods: Optional[int] = Field(None, gt=0)
    asset_type: Optional[Literal['stock', 'cash']] = 'stock'

class UnifiedBacktestRequest(BaseModel):
    portfolio: List[PortfolioStock]
    start_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    strategy: str
    strategy_params: Optional[Dict[str, Any]] = {}
    commission: Optional[float] = Field(0.001, ge=0, le=1)
    rebalance_frequency: Optional[str] = 'quarterly'
```

### 응답 모델
```python
class BacktestMetrics(BaseModel):
    total_return: float = Field(..., description="총 수익률")
    sharpe_ratio: float = Field(..., description="샤프 비율")
    max_drawdown: float = Field(..., description="최대 손실폭")
    volatility: float = Field(..., description="변동성")
    
class UnifiedBacktestResponse(BaseModel):
    success: bool
    metrics: BacktestMetrics
    chart_data: List[Dict[str, Any]]
    portfolio_composition: List[PortfolioStock]
```

## 투자 전략 개발

### 새 전략 추가
1. `strategies/` 디렉터리에 전략 클래스 생성
2. `strategy_service.py`의 `_strategies` 딕셔너리에 등록

```python
# strategies/ma_strategy.py
from backtesting import Strategy
import talib

class MovingAverageStrategy(Strategy):
    short_period = 10
    long_period = 30
    
    def init(self):
        self.short_ma = self.I(talib.SMA, self.data.Close, self.short_period)
        self.long_ma = self.I(talib.SMA, self.data.Close, self.long_period)
    
    def next(self):
        if self.short_ma[-1] > self.long_ma[-1]:
            if not self.position:
                self.buy()
        elif self.short_ma[-1] < self.long_ma[-1]:
            if self.position:
                self.sell()

# strategy_service.py에 등록
_strategies = {
    'sma_cross': SMAStrategy,
    'rsi': RSIStrategy,
    'ma_strategy': MovingAverageStrategy,  # 새 전략 추가
}
```

## 테스트 아키텍처

### 완전 오프라인 모킹
CI/CD 안정성을 위해 모든 외부 의존성을 모킹합니다.

```python
# conftest.py
@pytest.fixture
def mock_yfinance_data():
    """yfinance 데이터 모킹"""
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = create_mock_stock_data()
        yield mock_download

@pytest.fixture
def mock_mysql_connection():
    """MySQL 연결 모킹"""
    with patch('app.services.yfinance_db.get_connection') as mock_conn:
        mock_conn.return_value = create_mock_connection()
        yield mock_conn
```

### 테스트 실행
```bash
# 전체 테스트
docker-compose exec backend pytest tests/ -v

# 단위 테스트만
pytest tests/unit/ -v

# 통합 테스트만
pytest tests/integration/ -v

# 커버리지 리포트
pytest tests/ --cov=app --cov-report=html
```

## 데이터베이스 설계

### MySQL 캐시 테이블
```sql
CREATE TABLE stock_data_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date)
);
```

### 캐시 전략
- **TTL**: 데이터는 1일 후 만료
- **Upsert**: 중복 데이터 자동 업데이트
- **Batch Insert**: 대량 데이터 효율적 삽입

## 성능 최적화

### 데이터 수집 최적화
```python
async def fetch_multiple_stocks(symbols: List[str]) -> Dict[str, pd.DataFrame]:
    """멀티 심볼 병렬 데이터 수집"""
    tasks = [fetch_single_stock(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)
    return dict(zip(symbols, results))
```

### 백테스트 캐싱
```python
@lru_cache(maxsize=128)
def run_cached_backtest(
    strategy_name: str,
    params_hash: str,
    data_hash: str
) -> BacktestResult:
    """백테스트 결과 캐싱"""
    # 동일한 조건의 백테스트 결과 재사용
    pass
```

## 환경 설정

### config.py
```python
class Settings(BaseSettings):
    # 데이터베이스
    MYSQL_HOST: str = "host.docker.internal"  # 윈도우 Docker
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "yfinance_cache"
    
    # API 설정
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    
    # 백테스트 설정
    DEFAULT_COMMISSION: float = 0.001
    MAX_PORTFOLIO_SIZE: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 에러 처리

### 커스텀 예외
```python
class BacktestError(Exception):
    """백테스트 관련 예외"""
    pass

class DataFetchError(Exception):
    """데이터 수집 관련 예외"""
    pass

class StrategyError(Exception):
    """전략 관련 예외"""
    pass
```

### 글로벌 에러 핸들러
```python
@app.exception_handler(BacktestError)
async def backtest_error_handler(request: Request, exc: BacktestError):
    return JSONResponse(
        status_code=400,
        content={"detail": f"백테스트 오류: {str(exc)}"}
    )
```

## 모니터링 및 로깅

### 구조화된 로깅
```python
import logging
import structlog

logger = structlog.get_logger(__name__)

async def run_backtest(request: UnifiedBacktestRequest):
    logger.info(
        "백테스트 시작",
        portfolio_size=len(request.portfolio),
        strategy=request.strategy,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    try:
        result = await execute_backtest(request)
        logger.info("백테스트 완료", duration=result.duration)
        return result
    except Exception as e:
        logger.error("백테스트 실패", error=str(e))
        raise
```

## 보안 고려사항

### 입력 검증
- **Pydantic 검증**: 모든 입력 데이터 검증
- **SQL 인젝션 방지**: 파라미터화된 쿼리 사용
- **레이트 리미팅**: API 호출 횟수 제한

### 환경 변수 관리
- **민감 정보**: .env 파일로 관리
- **API 키**: 환경 변수로 분리
- **Docker Secrets**: 프로덕션 환경에서 사용

## 배포 및 운영

### Docker 이미지
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 헬스 체크
```python
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

## 향후 개선 계획

### 단기 (성능 개선)
- **Redis 캐싱**: 메모리 캐시 추가
- **비동기 최적화**: 더 많은 비동기 처리
- **배치 처리**: 대량 데이터 처리 최적화

### 중기 (기능 확장)
- **실시간 데이터**: WebSocket을 통한 실시간 가격 업데이트
- **알림 시스템**: 백테스트 완료 알림
- **사용자 관리**: 인증 및 권한 시스템

### 장기 (확장성)
- **마이크로서비스**: 서비스별 분리
- **클라우드 배포**: AWS/GCP 배포
- **머신러닝**: AI 기반 전략 추천

## 참고 링크

- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **Pydantic 문서**: https://docs.pydantic.dev/
- **backtesting.py**: https://kernc.github.io/backtesting.py/
- **yfinance**: https://pypi.org/project/yfinance/
