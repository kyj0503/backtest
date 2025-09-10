# 아키텍처 가이드

이 문서는 백테스팅 시스템의 전체적인 아키텍처와 설계 원칙을 설명합니다.

## 목차

1. [시스템 개요](#시스템-개요)
2. [아키텍처 패턴](#아키텍처-패턴)
3. [도메인 모델](#도메인-모델)
4. [데이터베이스 설계](#데이터베이스-설계)
5. [컴포넌트 구조](#컴포넌트-구조)
6. [상태 관리](#상태-관리)

## 시스템 개요

### 전체 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│    Backend      │◄──►│   Database      │
│   React + TS    │    │   FastAPI       │    │    MySQL        │
│   Vite          │    │   Python        │    │    Redis        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  UI Components  │    │ Business Logic  │    │  Data Storage   │
│  Charts         │    │ Backtest Engine │    │  Cache Layer    │
│  Forms          │    │ API Endpoints   │    │  External APIs  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 주요 특징
- **마이크로서비스 지향**: 프론트엔드와 백엔드 분리
- **이벤트 기반**: 비동기 이벤트 처리 시스템
- **캐시 우선**: 데이터베이스 캐시를 통한 성능 최적화
- **확장 가능**: 새로운 전략과 기능 추가 용이

## 아키텍처 패턴

### Domain-Driven Design (DDD)
현재 부분적으로 적용 중이며, 점진적으로 확장하고 있습니다.

#### 현재 구조
```
app/
├── api/                 # Presentation Layer
├── services/            # Application Layer (주요 비즈니스 로직)
├── domains/             # Domain Layer (점진 도입)
├── repositories/        # Infrastructure Layer
└── events/              # Event System
```

#### 도메인 경계
- **Backtest Domain**: 백테스트 실행, 결과 분석, 성과 지표
- **Portfolio Domain**: 포트폴리오 구성, 리밸런싱, 자산 배분
- **Data Domain**: 데이터 수집, 캐싱, 품질 관리

### CQRS (Command Query Responsibility Segregation)
명령과 쿼리를 분리하여 처리합니다.

```python
# Command 예시 - 백테스트 실행
class RunBacktestCommand:
    def __init__(self, ticker: str, strategy: str, ...):
        self.ticker = ticker
        self.strategy = strategy

# Query 예시 - 백테스트 결과 조회
class GetBacktestResultQuery:
    def __init__(self, backtest_id: str):
        self.backtest_id = backtest_id
```

### 이벤트 시스템
도메인 이벤트를 통한 느슨한 결합을 구현합니다.

```python
# 이벤트 정의
class BacktestCompletedEvent:
    def __init__(self, backtest_id: str, result: dict):
        self.backtest_id = backtest_id
        self.result = result

# 이벤트 핸들러
class BacktestMetricsHandler:
    def handle(self, event: BacktestCompletedEvent):
        # 성과 지표 계산 및 저장
        pass
```

## 도메인 모델

### 백테스트 도메인

#### 엔티티
```python
class Backtest:
    def __init__(self, id: BacktestId, strategy: Strategy, period: DatePeriod):
        self.id = id
        self.strategy = strategy
        self.period = period
        self.status = BacktestStatus.PENDING
    
    def execute(self) -> BacktestResult:
        # 백테스트 실행 로직
        pass
```

#### 값 객체
```python
class BacktestResult:
    def __init__(self, total_return: Decimal, sharpe_ratio: Decimal, ...):
        self.total_return = total_return
        self.sharpe_ratio = sharpe_ratio
        self.max_drawdown = max_drawdown
    
    def is_profitable(self) -> bool:
        return self.total_return > Decimal('0')
```

### 포트폴리오 도메인

#### 집합체
```python
class Portfolio:
    def __init__(self, assets: List[Asset], rebalance_frequency: RebalanceFrequency):
        self.assets = assets
        self.rebalance_frequency = rebalance_frequency
    
    def add_asset(self, asset: Asset):
        # 가중치 합계 검증
        if self.total_weight + asset.weight > 1.0:
            raise ValueError("Total weight cannot exceed 100%")
        self.assets.append(asset)
    
    def rebalance(self, current_values: Dict[str, Decimal]):
        # 리밸런싱 로직
        pass
```

### 현금 자산 처리
현금 자산은 특별한 자산 타입으로 처리됩니다.

```python
class CashAsset(Asset):
    def __init__(self, amount: Decimal):
        super().__init__(symbol="CASH", amount=amount)
        self.volatility = Decimal('0')
        self.expected_return = Decimal('0')
    
    def get_price_data(self, period: DatePeriod) -> List[PriceData]:
        # 현금은 가격 변동 없음
        return []
```

## 데이터베이스 설계

### 데이터베이스 분리
시스템은 두 개의 분리된 데이터베이스를 사용합니다:

#### 1. Community Database
```sql
-- 사용자 관리
users (id, username, email, password_hash, investment_type, ...)
user_sessions (id, user_id, session_token, expires_at, ...)

-- 커뮤니티
posts (id, user_id, title, content, view_count, like_count, ...)
post_comments (id, post_id, user_id, content, ...)
post_likes (id, post_id, user_id, ...)

-- 백테스트 히스토리
backtest_history (id, user_id, backtest_type, parameters, results, ...)
```

#### 2. Stock Data Cache Database
```sql
-- 주식 정보
stocks (id, ticker, name, exchange, sector, ...)
daily_prices (stock_id, date, open, high, low, close, volume, ...)

-- 부가 정보
dividends (id, stock_id, date, dividend, ...)
stock_splits (id, stock_id, date, split_ratio, ...)
exchange_rates (id, currency_pair, date, rate, ...)

-- 캐시 관리
cache_metadata (id, ticker, data_type, last_fetch, next_update, ...)
```

### 데이터 흐름
```
API Request → Cache Check → Data Fetch → Business Logic → Response
     ↓             ↓            ↓              ↓            ↓
  Validation   MySQL DB    yfinance API   Backtest     JSON Result
```

### 캐시 전략
- **우선순위**: DB 캐시 → 외부 API
- **자동 보강**: 누락된 데이터 구간 자동 채움
- **품질 관리**: 데이터 품질 등급 및 메타데이터 관리

## 컴포넌트 구조

### 프론트엔드 아키텍처

#### 계층 구조
```
Pages (라우트)
  ↓
Containers (비즈니스 로직)
  ↓
Components (UI 컴포넌트)
  ↓
Hooks (상태 관리)
  ↓
Services (API 통신)
```

#### 주요 컴포넌트
```typescript
// 페이지 컴포넌트
const BacktestPage = () => {
  const { result, loading, error, runBacktest } = useBacktest();
  
  return (
    <div>
      <UnifiedBacktestForm onSubmit={runBacktest} />
      <UnifiedBacktestResults result={result} loading={loading} />
    </div>
  );
};

// 폼 컴포넌트
const UnifiedBacktestForm = ({ onSubmit }) => {
  const formState = useBacktestForm();
  
  return (
    <form onSubmit={handleSubmit}>
      <PortfolioForm {...formState.portfolio} />
      <DateRangeForm {...formState.dateRange} />
      <StrategyForm {...formState.strategy} />
    </form>
  );
};
```

#### 차트 컴포넌트
```typescript
// 차트 컴포넌트 계층
<ChartsSection>
  <OHLCChart data={ohlcData} indicators={indicators} />
  <EquityChart data={equityData} />
  <TradesChart data={trades} />
</ChartsSection>

// 지연 로딩
const LazyOHLCChart = lazy(() => import('./components/charts/OHLCChart'));
```

### 백엔드 아키텍처

#### 레이어 구조
```python
# API Layer - 요청/응답 처리
@router.post("/backtest/run")
async def run_backtest(request: BacktestRequest) -> BacktestResult:
    command = CreateBacktestCommand.from_request(request)
    result = await command_bus.execute(command)
    return BacktestResponse.from_result(result)

# Application Layer - 비즈니스 로직 조율
class BacktestService:
    def __init__(self, repo: BacktestRepository, event_bus: EventBus):
        self.repo = repo
        self.event_bus = event_bus
    
    async def run_backtest(self, command: CreateBacktestCommand):
        # 비즈니스 로직 실행
        result = self.backtest_engine.execute(...)
        
        # 이벤트 발행
        event = BacktestCompletedEvent(result)
        await self.event_bus.publish(event)
        
        return result

# Domain Layer - 핵심 비즈니스 규칙
class BacktestEngine:
    def execute(self, strategy: Strategy, data: MarketData) -> BacktestResult:
        # 백테스트 실행 로직
        pass
```

#### 의존성 주입
```python
# 의존성 컨테이너
class Container:
    def __init__(self):
        self.backtest_repo = BacktestRepository()
        self.event_bus = EventBus()
        self.backtest_service = BacktestService(
            self.backtest_repo, 
            self.event_bus
        )
```

## 상태 관리

### 프론트엔드 상태 관리

#### 로컬 상태 우선
```typescript
// 컴포넌트 레벨 상태
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

// 커스텀 훅으로 로직 분리
const useBacktest = () => {
  const [state, setState] = useState(initialState);
  
  const runBacktest = useCallback(async (request) => {
    setState(prev => ({ ...prev, loading: true }));
    try {
      const result = await api.runBacktest(request);
      setState(prev => ({ ...prev, result, loading: false }));
    } catch (error) {
      setState(prev => ({ ...prev, error, loading: false }));
    }
  }, []);
  
  return { ...state, runBacktest };
};
```

#### 상태 구조
```typescript
interface BacktestState {
  // 폼 상태
  portfolio: PortfolioAsset[];
  dateRange: DateRange;
  strategy: StrategyConfig;
  
  // 실행 상태
  loading: boolean;
  error: string | null;
  
  // 결과 상태
  result: BacktestResult | null;
  chartData: ChartData | null;
}
```

#### 리듀서 패턴
```typescript
const backtestReducer = (state: BacktestState, action: BacktestAction) => {
  switch (action.type) {
    case 'SET_PORTFOLIO':
      return { ...state, portfolio: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_RESULT':
      return { ...state, result: action.payload, loading: false };
    default:
      return state;
  }
};
```

### 백엔드 상태 관리

#### 무상태 서비스
```python
# 서비스는 상태를 가지지 않음
class BacktestService:
    def __init__(self, repository: BacktestRepository):
        self.repository = repository  # 의존성만 주입
    
    async def run_backtest(self, request: BacktestRequest):
        # 매번 새로운 실행, 상태 저장 없음
        return await self.execute_backtest(request)
```

#### 캐시 상태
```python
# 캐시는 별도 계층에서 관리
class DataCache:
    def __init__(self):
        self.memory_cache = {}
        self.db_cache = DatabaseCache()
    
    async def get_stock_data(self, ticker: str, period: DatePeriod):
        # 메모리 → DB → 외부 API 순서로 조회
        if ticker in self.memory_cache:
            return self.memory_cache[ticker]
        
        db_data = await self.db_cache.get(ticker, period)
        if db_data:
            self.memory_cache[ticker] = db_data
            return db_data
        
        # 외부 API 호출 및 캐시 저장
        external_data = await self.fetch_from_yfinance(ticker, period)
        await self.db_cache.save(ticker, external_data)
        self.memory_cache[ticker] = external_data
        
        return external_data
```

### 데이터 동기화
```typescript
// 프론트엔드와 백엔드 간 타입 동기화
interface BacktestRequest {
  ticker: string;
  start_date: string;  // YYYY-MM-DD
  end_date: string;
  strategy: StrategyType;
  // ...
}

// 백엔드 Pydantic 모델과 일치
class BacktestRequest(BaseModel):
    ticker: str
    start_date: date
    end_date: date
    strategy: StrategyType
```

이 아키텍처는 확장성, 유지보수성, 테스트 가능성을 고려하여 설계되었으며, 점진적으로 DDD 패턴을 도입하고 있습니다.
