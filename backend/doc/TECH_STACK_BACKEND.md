# 백엔드 기술 스택 가이드

FastAPI 기반 백테스팅 시스템 백엔드의 기술 선택과 구현 상세를 설명합니다.

## 목차
- [FastAPI 프레임워크 심화](#fastapi-프레임워크-심화)
- [Pydantic V2 데이터 모델링](#pydantic-v2-데이터-모델링)
- [백테스팅 엔진 아키텍처](#백테스팅-엔진-아키텍처)
- [데이터 레이어 설계](#데이터-레이어-설계)
- [외부 API 통합](#외부-api-통합)
- [테스팅 전략](#테스팅-전략)
- [성능 최적화](#성능-최적화)

## FastAPI 프레임워크 심화

### 아키텍처 패턴 선택

#### 레이어드 아키텍처 채택
```
API Layer (endpoints/) → Service Layer (services/) → Data Layer (utils/)
```

**선택 이유**:
1. **관심사 분리**: 각 레이어의 책임 명확화
2. **테스트 용이성**: 레이어별 독립적 테스트 가능
3. **확장성**: 새로운 기능 추가 시 영향 범위 최소화
4. **유지보수성**: 코드 위치 예측 가능성 향상

#### 의존성 주입 패턴
```python
@app.get("/api/v1/backtest/chart-data")
async def get_chart_data(
    request: ChartDataRequest,
    backtest_service: BacktestService = Depends(get_backtest_service)
):
```

**FastAPI Depends 활용 이유**:
- **타입 안전성**: 컴파일 타임 의존성 체크
- **자동 주입**: 보일러플레이트 코드 제거
- **테스트 친화적**: Mock 객체 주입 용이

### 비동기 프로그래밍 전략

#### async/await 적극 활용
```python
async def get_stock_data(ticker: str, start_date: str, end_date: str) -> StockData:
    # 네트워크 I/O 비동기 처리
    async with aiohttp.ClientSession() as session:
        data = await fetch_from_api(session, ticker, start_date, end_date)
    return process_data(data)
```

**비동기 채택 배경**:
1. **I/O 바운드 작업 최적화**: yfinance API 호출, 뉴스 API 호출
2. **동시성 향상**: 여러 종목 데이터 병렬 처리
3. **사용자 경험**: 블로킹 없는 응답 시간
4. **서버 리소스 효율성**: 스레드 풀 대비 메모리 사용량 절약

#### 동기/비동기 혼용 전략
```python
# CPU 집약적 작업은 동기로 처리
def run_backtest_sync(data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
    bt = Backtest(data, strategy)
    return bt.run()

# I/O 작업은 비동기로 처리
async def fetch_multiple_stocks(tickers: List[str]) -> List[StockData]:
    tasks = [fetch_stock_data(ticker) for ticker in tickers]
    return await asyncio.gather(*tasks)
```

### API 설계 원칙

#### RESTful API 구조
```
GET  /api/v1/backtest/chart-data     # 단일 종목 백테스트
POST /api/v1/backtest/portfolio      # 포트폴리오 백테스트
GET  /api/v1/naver-news/ticker/{ticker}  # 뉴스 조회
```

**엔드포인트 설계 원칙**:
1. **직관적 URL**: 리소스 중심의 명사형 URL
2. **HTTP 메서드 의미론**: GET(조회), POST(생성/복잡한 쿼리)
3. **버전 관리**: /v1/ 접두사로 API 버전 관리
4. **일관된 응답 구조**: 모든 API 동일한 응답 포맷

#### 응답 표준화
```python
class APIResponse(BaseModel):
    status: str = "success"
    message: str = ""
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
```

**표준화 이유**:
- **클라이언트 예측 가능성**: 일관된 응답 구조
- **에러 처리 통일**: 프론트엔드 에러 핸들링 단순화
- **API 문서 일관성**: OpenAPI 스펙 자동 생성 품질 향상

## Pydantic V2 데이터 모델링

### 모델 설계 철학

#### 도메인 중심 모델링
```python
class PortfolioStock(BaseModel):
    symbol: str = Field(..., description="종목 코드")
    amount: Decimal = Field(..., gt=0, description="투자 금액")
    investment_type: InvestmentType = Field(default="lump_sum")
    dca_periods: Optional[int] = Field(default=12, ge=1, le=60)
    asset_type: AssetType = Field(default="stock")
```

**설계 원칙**:
1. **비즈니스 로직 반영**: 금융 도메인 규칙을 타입으로 표현
2. **검증 내장**: Field 제약조건으로 비즈니스 규칙 강제
3. **문서화 자동화**: description으로 API 문서 자동 생성
4. **타입 안전성**: Enum으로 허용값 제한

#### V2 마이그레이션 전략
```python
# V1에서 V2로 마이그레이션
class ConfigDict:
    # V2 방식
    str_strip_whitespace = True
    validate_assignment = True
    use_enum_values = True
    
    # V1 deprecated 제거
    # allow_population_by_field_name = True  # 제거됨
    # json_encoders = {...}  # 제거됨
```

**V2 채택 이유**:
- **성능 향상**: Rust 기반 코어로 5-50배 빠른 검증
- **메모리 효율성**: 더 적은 메모리 사용량
- **타입 추론 개선**: 더 정확한 타입 체크
- **미래 지향성**: 장기 지원 보장

### 검증 전략

#### 다층 검증 시스템
```python
class BacktestRequest(BaseModel):
    start_date: date = Field(..., description="백테스트 시작일")
    end_date: date = Field(..., description="백테스트 종료일")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, end_date: date, info: ValidationInfo) -> date:
        start_date = info.data.get('start_date')
        if start_date and end_date <= start_date:
            raise ValueError("종료일은 시작일보다 늦어야 합니다")
        return end_date
```

**검증 레벨**:
1. **타입 검증**: 기본 타입 및 제약조건
2. **필드 검증**: @field_validator로 개별 필드 로직
3. **모델 검증**: @model_validator로 필드 간 관계 검증
4. **비즈니스 검증**: 서비스 레이어에서 도메인 규칙

## 백테스팅 엔진 아키텍처

### backtesting.py 라이브러리 통합

#### 전략 팩토리 패턴
```python
class StrategyService:
    _strategies = {
        "buy_and_hold": BuyAndHoldStrategy,
        "sma_crossover": SMAStrategy,
        "rsi_strategy": RSIStrategy,
        # ... 추가 전략들
    }
    
    def get_strategy_class(self, name: str) -> Type[Strategy]:
        if name not in self._strategies:
            raise StrategyNotFoundError(f"전략 '{name}'을 찾을 수 없습니다")
        return self._strategies[name]
```

**팩토리 패턴 채택 이유**:
1. **확장성**: 새 전략 추가가 설정 변경만으로 가능
2. **타입 안전성**: 컴파일 타임 전략 존재 확인
3. **플러그인 아키텍처**: 전략을 독립 모듈로 개발 가능
4. **테스트 용이성**: Mock 전략 주입 간편

#### 사용자 정의 전략 지원
```python
class CustomStrategy(Strategy):
    def init(self):
        # 지표 초기화
        self.sma_short = self.I(SMA, self.data.Close, self.short_window)
        self.sma_long = self.I(SMA, self.data.Close, self.long_window)
    
    def next(self):
        # 매매 로직
        if crossover(self.sma_short, self.sma_long):
            self.buy()
        elif crossover(self.sma_long, self.sma_short):
            self.sell()
```

**전략 개발 지원**:
- **템플릿 제공**: 기본 전략 구조 템플릿
- **지표 라이브러리**: 공통 기술적 지표 제공
- **백테스트 헬퍼**: 공통 백테스트 로직 추상화
- **성과 분석**: 표준화된 성과 지표 계산

### 현금 자산 처리 시스템

#### 혼합 자산 백테스트
```python
def process_portfolio_assets(portfolio: List[PortfolioStock]) -> BacktestResult:
    stock_assets = [asset for asset in portfolio if asset.asset_type == "stock"]
    cash_assets = [asset for asset in portfolio if asset.asset_type == "cash"]
    
    # 주식 자산 백테스트
    stock_result = run_stock_backtest(stock_assets) if stock_assets else None
    
    # 현금 자산 처리 (무위험 자산)
    cash_value = sum(asset.amount for asset in cash_assets)
    
    # 결합된 포트폴리오 결과 생성
    return combine_portfolio_results(stock_result, cash_value)
```

**현금 자산 설계 원칙**:
1. **무위험 가정**: 0% 수익률, 0% 변동성
2. **포트폴리오 통합**: 주식과 현금의 가중평균 수익률
3. **리밸런싱 지원**: 현금 비중 조정 가능
4. **실제성 반영**: 실제 투자에서 현금 보유 시나리오

## 데이터 레이어 설계

### MySQL 캐시 시스템

#### 캐시 전략
```python
class DataFetcher:
    async def get_stock_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        # 1. 캐시 확인
        cached_data = await self.get_cached_data(ticker, start_date, end_date)
        if cached_data is not None and self.is_cache_valid(cached_data):
            return cached_data
        
        # 2. API 호출
        fresh_data = await self.fetch_from_yfinance(ticker, start_date, end_date)
        
        # 3. 캐시 저장
        await self.save_to_cache(ticker, fresh_data)
        
        return fresh_data
```

**캐시 정책**:
- **TTL**: 당일 데이터는 1시간, 과거 데이터는 24시간
- **무효화**: 새로운 거래일 시작 시 자동 무효화
- **압축**: OHLCV 데이터 JSON 압축 저장
- **인덱싱**: (ticker, date) 복합 인덱스로 빠른 조회

#### 데이터 정합성 보장
```python
class StockDataValidator:
    def validate_ohlcv_data(self, data: pd.DataFrame) -> bool:
        # 1. 필수 컬럼 존재 확인
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_columns):
            return False
        
        # 2. OHLC 관계 검증
        invalid_ohlc = (
            (data['High'] < data['Open']) | 
            (data['High'] < data['Close']) |
            (data['Low'] > data['Open']) | 
            (data['Low'] > data['Close'])
        )
        if invalid_ohlc.any():
            return False
        
        return True
```

### yfinance API 통합

#### 에러 처리 전략
```python
class YFinanceError(Exception):
    pass

class DataFetcher:
    async def fetch_with_retry(self, ticker: str, retries: int = 3) -> pd.DataFrame:
        for attempt in range(retries):
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
                if data.empty:
                    raise YFinanceError(f"No data available for {ticker}")
                return data
            except Exception as e:
                if attempt == retries - 1:
                    raise YFinanceError(f"Failed to fetch data after {retries} attempts")
                await asyncio.sleep(2 ** attempt)  # 지수 백오프
```

**API 제한 대응**:
- **Rate Limiting**: 요청 간격 제어
- **Circuit Breaker**: 연속 실패 시 일시 차단
- **Fallback**: 캐시된 데이터로 대체
- **Monitoring**: API 응답 시간 및 실패율 모니터링

## 외부 API 통합

### 네이버 뉴스 API

#### 티커 매핑 시스템
```python
TICKER_MAPPING = {
    # 미국 주식
    'AAPL': '애플',
    'MSFT': '마이크로소프트',
    'GOOGL': '구글',
    # 한국 주식
    '005930.KS': '삼성전자',
    '000660.KS': 'SK하이닉스',
    # ... 70+ 매핑
}

def get_company_name(ticker: str) -> str:
    return TICKER_MAPPING.get(ticker.upper(), ticker)
```

**매핑 전략**:
1. **다국가 지원**: 미국/한국 주식 동시 지원
2. **검색 최적화**: 한국어 회사명으로 뉴스 검색 정확도 향상
3. **확장성**: 새 종목 추가 시 설정만 변경
4. **유지보수**: 중앙집중식 매핑 관리

#### 뉴스 컨텐츠 정제
```python
def clean_news_content(html_content: str) -> str:
    # HTML 태그 제거
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    # 특수 문자 정제
    clean_text = html.unescape(clean_text)
    # 중복 공백 제거
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text
```

**컨텐츠 품질 개선**:
- **HTML 태그 제거**: 순수 텍스트 추출
- **인코딩 정규화**: 유니코드 이스케이프 처리
- **관련성 필터링**: 키워드 기반 관련도 점수
- **중복 제거**: 동일 뉴스 중복 노출 방지

## 테스팅 전략

### 계층별 테스트 구조

#### 단위 테스트 (Unit Tests)
```python
class TestBacktestService:
    def test_buy_and_hold_strategy(self, mock_data):
        service = BacktestService()
        result = service.run_backtest(
            ticker="AAPL",
            strategy="buy_and_hold",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        assert result.total_return > 0
        assert result.max_drawdown < 0
```

#### 통합 테스트 (Integration Tests)
```python
class TestAPIEndpoints:
    async def test_portfolio_backtest_endpoint(self, test_client):
        response = await test_client.post("/api/v1/backtest/portfolio", json={
            "portfolio": [{"symbol": "AAPL", "amount": 10000, "asset_type": "stock"}],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

#### E2E 테스트 (End-to-End Tests)
```python
class TestCompleteWorkflow:
    async def test_complete_backtest_flow(self):
        # 1. 데이터 조회
        # 2. 백테스트 실행
        # 3. 결과 검증
        # 4. 뉴스 연동 확인
```

### Mock 시스템 구축

#### 오프라인 테스트 환경
```python
class MockYFinance:
    def download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        # 사전 정의된 테스트 데이터 반환
        return load_test_data(ticker, start, end)

@pytest.fixture
def mock_yfinance(monkeypatch):
    monkeypatch.setattr("yfinance.download", MockYFinance().download)
```

**Mock 전략**:
1. **외부 의존성 제거**: API 호출 없는 테스트
2. **일관된 결과**: 동일한 입력에 동일한 출력 보장
3. **엣지 케이스 테스트**: 극단적 시나리오 시뮬레이션
4. **빠른 실행**: 네트워크 I/O 제거로 테스트 속도 향상

## 성능 최적화

### 데이터 처리 최적화

#### Pandas 벡터화 활용
```python
def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    # 벡터화된 계산으로 성능 최적화
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['RSI'] = calculate_rsi_vectorized(data['Close'])
    return data

def calculate_rsi_vectorized(prices: pd.Series, window: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
```

**성능 개선 기법**:
- **벡터화**: 루프 대신 NumPy 연산 활용
- **메모리 효율성**: 불필요한 데이터 복사 방지
- **지연 연산**: 필요한 시점에만 계산 수행
- **캐시 활용**: 동일 계산 결과 재사용

### 응답 시간 최적화

#### 비동기 병렬 처리
```python
async def fetch_portfolio_data(symbols: List[str]) -> Dict[str, pd.DataFrame]:
    tasks = []
    for symbol in symbols:
        if symbol not in ['CASH', '현금']:  # 현금 자산 제외
            task = asyncio.create_task(fetch_stock_data(symbol))
            tasks.append((symbol, task))
    
    results = {}
    for symbol, task in tasks:
        try:
            results[symbol] = await task
        except Exception as e:
            logger.warning(f"Failed to fetch data for {symbol}: {e}")
            results[symbol] = pd.DataFrame()  # 빈 데이터프레임으로 대체
    
    return results
```

**병렬 처리 효과**:
- **다중 API 호출**: 순차 처리 대비 70-90% 시간 단축
- **에러 격리**: 일부 종목 실패가 전체에 영향 없음
- **리소스 활용**: CPU/네트워크 자원 효율적 사용

이러한 기술적 선택과 구현을 통해 안정적이고 성능이 우수한 백테스팅 시스템을 구축했습니다.
