# Exact Locations of 6 Duplicate Data Loading Functions

## Quick Index

| # | Function | File | Lines | Hash |
|---|----------|------|-------|------|
| 1 | DataService.get_ticker_data() | app/services/data_service.py | 57-100 | Async DB-first |
| 2 | DataService.get_ticker_data_sync() | app/services/data_service.py | 102-135 | Sync DB-first |
| 3 | BacktestEngine._get_price_data() | app/services/backtest_engine.py | 169-187 | Async Repo |
| 4 | ChartDataService._get_price_data() | app/services/chart_data_service.py | 200-214 | Async Repo 🐛 BUG |
| 5 | YFinanceDataRepository.get_stock_data() | app/repositories/data_repository.py | 106-151 | Async 3-Layer |
| 6 | yfinance_db._load_ticker_data_internal() | app/services/yfinance_db.py | 767-813 | Sync Core |

---

## Function 1: DataService.get_ticker_data() [ASYNC]

**Location**: `/home/user/backtest/backtest_be_fast/app/services/data_service.py:57-100`

**Absolute Path**: `/home/user/backtest/backtest_be_fast/app/services/data_service.py`

**Function Signature**:
```python
async def get_ticker_data(
    self,
    ticker: str,
    start_date: Union[date, str],
    end_date: Union[date, str],
    use_db_first: bool = True
) -> pd.DataFrame:
```

**Purpose**: DB-first strategy with yfinance fallback (async version)

**Key Code Section** (lines 79-94):
```python
try:
    if use_db_first:
        # 1. DB 캐시에서 조회 시도 (asyncio.to_thread로 async/sync 경계 준수)
        df = await asyncio.to_thread(load_ticker_data, ticker, start_date, end_date)
        if df is not None and not df.empty:
            logger.debug(f"DB 캐시에서 데이터 반환: {ticker}")
            return df

    # 2. yfinance에서 실시간 조회 (asyncio.to_thread로 async/sync 경계 준수)
    logger.info(f"yfinance에서 데이터 조회: {ticker}")
    df = await asyncio.to_thread(self.data_fetcher.get_stock_data, ticker, start_date, end_date)

    if df is None or df.empty:
        raise DataNotFoundError(ticker, str(start_date), str(end_date))

    return df
```

**LOC**: 43 lines

---

## Function 2: DataService.get_ticker_data_sync() [SYNC - DUPLICATE]

**Location**: `/home/user/backtest/backtest_be_fast/app/services/data_service.py:102-135`

**Absolute Path**: `/home/user/backtest/backtest_be_fast/app/services/data_service.py`

**Function Signature**:
```python
def get_ticker_data_sync(
    self,
    ticker: str,
    start_date: Union[date, str],
    end_date: Union[date, str],
    use_db_first: bool = True
) -> pd.DataFrame:
```

**Purpose**: Synchronous version of Function 1 (for backward compatibility)

**Key Code Section** (lines 114-129):
```python
try:
    if use_db_first:
        # 1. DB 캐시에서 조회 시도
        df = load_ticker_data(ticker, start_date, end_date)
        if df is not None and not df.empty:
            logger.debug(f"DB 캐시에서 데이터 반환: {ticker}")
            return df
    
    # 2. yfinance에서 실시간 조회
    logger.info(f"yfinance에서 데이터 조회: {ticker}")
    df = self.data_fetcher.get_stock_data(ticker, start_date, end_date)
    
    if df is None or df.empty:
        raise DataNotFoundError(ticker, str(start_date), str(end_date))
    
    return df
```

**LOC**: 33 lines

**⚠️ ISSUE**: 95% duplicate of Function 1, just without async/await. Both functions should be consolidated.

---

## Function 3: BacktestEngine._get_price_data() [ASYNC]

**Location**: `/home/user/backtest/backtest_be_fast/app/services/backtest_engine.py:169-187`

**Absolute Path**: `/home/user/backtest/backtest_be_fast/app/services/backtest_engine.py`

**Function Signature**:
```python
async def _get_price_data(
    self, ticker: str, start_date, end_date
) -> pd.DataFrame:
```

**Purpose**: Fetch price data for backtest execution (used in line 89 of run_backtest())

**Full Implementation** (lines 169-187):
```python
async def _get_price_data(
    self, ticker: str, start_date, end_date
) -> pd.DataFrame:
    """캐시-우선 가격 데이터 조회"""
    if self.data_repository:
        data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
    else:
        # 동기 data_fetcher를 안전하게 async로 실행
        data = await asyncio.to_thread(
            self.data_fetcher.get_stock_data,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

    if data is None or data.empty:
        raise HTTPException(status_code=404, detail="가격 데이터를 찾을 수 없습니다.")

    return data
```

**LOC**: 19 lines

**Key Point**: Uses repository pattern with fallback to data_fetcher. ✓ Correctly wraps fallback with `asyncio.to_thread()`

---

## Function 4: ChartDataService._get_price_data() [ASYNC - HAS BUG]

**Location**: `/home/user/backtest/backtest_be_fast/app/services/chart_data_service.py:200-214`

**Absolute Path**: `/home/user/backtest/backtest_be_fast/app/services/chart_data_service.py`

**Function Signature**:
```python
async def _get_price_data(self, ticker, start_date, end_date) -> pd.DataFrame:
```

**Purpose**: Fetch price data for chart generation (called from line 113)

**Full Implementation** (lines 200-214):
```python
async def _get_price_data(self, ticker, start_date, end_date) -> pd.DataFrame:
    """캐시 우선 가격 데이터 조회"""
    if self.data_repository:
        data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
    else:
        data = self.data_fetcher.get_stock_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

    if data is None or data.empty:
        raise ValidationError(f"'{ticker}' 종목의 가격 데이터를 찾을 수 없습니다.")

    return data
```

**LOC**: 14 lines

**🔴 CRITICAL BUG** (Line 205):
```python
# WRONG - Missing asyncio.to_thread() wrapper!
data = self.data_fetcher.get_stock_data(...)
```

**Should be** (Fix):
```python
# CORRECT - Wrap synchronous call with asyncio.to_thread()
data = await asyncio.to_thread(
    self.data_fetcher.get_stock_data,
    ticker=ticker,
    start_date=start_date,
    end_date=end_date
)
```

**Impact**: Can cause race conditions on first execution due to blocking I/O in async context

---

## Function 5: YFinanceDataRepository.get_stock_data() [ASYNC - 3-LAYER CACHE]

**Location**: `/home/user/backtest/backtest_be_fast/app/repositories/data_repository.py:106-151`

**Absolute Path**: `/home/user/backtest/backtest_be_fast/app/repositories/data_repository.py`

**Function Signature**:
```python
async def get_stock_data(self, ticker: str, start_date: Union[date, str],
                       end_date: Union[date, str]) -> pd.DataFrame:
```

**Purpose**: 3-layer caching: Memory → MySQL → yfinance API

**Full Implementation** (lines 106-151):
```python
async def get_stock_data(self, ticker: str, start_date: Union[date, str],
                       end_date: Union[date, str]) -> pd.DataFrame:
    """주식 데이터 조회 (캐시 우선)"""
    try:
        # 캐시 키 생성
        cache_key = f"{ticker}_{start_date}_{end_date}"
        
        # 1. 메모리 캐시 확인
        if self._is_cache_valid(cache_key, end_date):
            self.logger.debug(f"메모리 캐시에서 데이터 반환: {cache_key}")
            return self._memory_cache[cache_key]['data']

        # 2. MySQL 캐시 확인
        try:
            cached_data = await asyncio.to_thread(
                yfinance_db.load_ticker_data, ticker, start_date, end_date
            )
            if cached_data is not None and not cached_data.empty:
                self.logger.debug(f"MySQL 캐시에서 데이터 반환: {ticker}")
                # 메모리 캐시에도 저장
                self._memory_cache[cache_key] = {
                    'data': cached_data,
                    'timestamp': datetime.now(),
                    'end_date': end_date
                }
                return cached_data
        except Exception as e:
            self.logger.warning(f"MySQL 캐시 조회 실패: {str(e)}")

        # 3. 실시간 데이터 페칭
        self.logger.info(f"실시간 데이터 페칭: {ticker}")
        fresh_data = await asyncio.to_thread(
            self.data_fetcher.get_stock_data, ticker, start_date, end_date
        )

        # 4. 캐시에 저장
        await self.cache_stock_data(ticker, fresh_data)

        # 5. 메모리 캐시에 저장
        self._memory_cache[cache_key] = {
            'data': fresh_data,
            'timestamp': datetime.now(),
            'end_date': end_date
        }
        
        return fresh_data
        
    except Exception as e:
        self.logger.error(f"주식 데이터 조회 실패: {ticker}, {str(e)}")
        raise
```

**LOC**: 45 lines

**Key Features**:
- ✓ Correct async implementation with `asyncio.to_thread()` wrappers
- ✓ 3-layer caching strategy
- ✓ Dynamic TTL (24h for historical, 1h for recent data)
- ✓ Most sophisticated implementation

---

## Function 6: yfinance_db._load_ticker_data_internal() [SYNC - CORE]

**Location**: `/home/user/backtest/backtest_be_fast/app/services/yfinance_db.py:767-813`

**Absolute Path**: `/home/user/backtest/backtest_be_fast/app/services/yfinance_db.py`

**Function Signature**:
```python
def _load_ticker_data_internal(ticker: str, start_date=None, end_date=None) -> pd.DataFrame:
```

**Purpose**: Core internal implementation for DB-first strategy with intelligent gap filling

**Main Function** (lines 767-813):
```python
def _load_ticker_data_internal(ticker: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    실제 데이터 로드 로직 (내부용)

    DB 우선 조회 전략:
    1. 날짜 매개변수 정규화
    2. stock_id 확보 (없으면 yfinance에서 가져와 저장)
    3. DB 데이터 범위 조회
    4. 누락 구간 수집 (통합 fetch → fallback: 개별 fetch)
    5. 최종 데이터 조회 및 DataFrame 반환
    ...
    """
    engine = _get_engine()
    conn = engine.connect()
    try:
        # 1. 날짜 정규화 및 기본값 설정
        start_date, end_date = _normalize_date_params(start_date, end_date)

        # 2. stock_id 확보 (DB에 없으면 yfinance에서 수집)
        stock_id, conn = _ensure_stock_exists(conn, engine, ticker, start_date, end_date)

        # 3. DB에 저장된 데이터 범위 조회
        db_min, db_max = _get_date_coverage(conn, stock_id)

        # 4. 누락된 구간 수집 (통합 fetch 시도 → fallback: 개별 fetch)
        conn = _fetch_and_save_missing_data(conn, engine, ticker, start_date, end_date, db_min, db_max)

        # 5. 최종 데이터 조회 및 DataFrame 반환
        df = _query_and_format_dataframe(conn, stock_id, ticker, start_date, end_date)

        return df
    finally:
        conn.close()
```

**LOC**: 46 lines (main function) + ~250 lines in 5 helper functions

**Helper Functions**:
1. `_normalize_date_params()` (lines 491-532) - 42 lines
2. `_ensure_stock_exists()` (lines 535-579) - 45 lines
3. `_get_date_coverage()` (lines 582-604) - 23 lines
4. `_fetch_and_save_missing_data()` (lines 607-695) - 89 lines
5. `_query_and_format_dataframe()` (lines 698-764) - 67 lines

**Key Characteristics**:
- ✓ Most complex implementation
- ✓ Intelligent gap filling with fallback strategies
- ✓ Connection pooling and transaction management
- ✓ Called by Function 7 (load_ticker_data wrapper)

---

## Wrapper Function: yfinance_db.load_ticker_data() [SYNC - WRAPPER]

**Location**: `/home/user/backtest/backtest_be_fast/app/services/yfinance_db.py:252-302`

**Absolute Path**: `/home/user/backtest/backtest_be_fast/app/services/yfinance_db.py`

**Function Signature**:
```python
def load_ticker_data(ticker: str, start_date=None, end_date=None, 
                     max_retries: int = 3, retry_delay: float = 2.0) -> pd.DataFrame:
```

**Purpose**: Wrapper around `_load_ticker_data_internal()` with retry logic

**Key Code Section** (lines 273-302):
```python
last_exception = None

for attempt in range(1, max_retries + 1):
    try:
        logger.info(f"[시도 {attempt}/{max_retries}] {ticker} 데이터 로드 중... ({start_date} ~ {end_date})")
        
        # 실제 데이터 로드 로직
        df = _load_ticker_data_internal(ticker, start_date, end_date)
        
        if df is not None and not df.empty:
            logger.info(f"[성공] {ticker} 데이터 로드 완료: {len(df)}행 (시도 {attempt}회)")
            return df
        else:
            logger.warning(f"[시도 {attempt}/{max_retries}] {ticker} 데이터가 비어있음")
            last_exception = ValueError(f"{ticker} 데이터가 비어있습니다")
            
    except Exception as e:
        logger.warning(f"[시도 {attempt}/{max_retries}] {ticker} 데이터 로드 실패: {str(e)}")
        last_exception = e
    
    # 마지막 시도가 아니면 대기 후 재시도
    if attempt < max_retries:
        wait_time = retry_delay * attempt  # 점진적 증가 (2초, 4초, 6초...)
        logger.info(f"[재시도 대기] {wait_time}초 후 {ticker} 데이터 재시도...")
        time.sleep(wait_time)

# 모든 재시도 실패
error_msg = f"[실패] {ticker} 데이터 로드 실패 (총 {max_retries}회 시도)"
if last_exception:
    error_msg += f": {str(last_exception)}"
logger.error(error_msg)
raise ValueError(error_msg)
```

**LOC**: 50 lines

**Key Feature**: Exponential backoff retry (2s, 4s, 6s for 3 attempts)

---

## Summary of Call Graph

```
DataService.get_ticker_data() [#1]
├─ load_ticker_data() [wrapper]
│   └─ _load_ticker_data_internal() [#6 - core]
│       ├─ _normalize_date_params()
│       ├─ _ensure_stock_exists()
│       │   └─ data_fetcher.get_stock_data() [yfinance fallback]
│       ├─ _get_date_coverage()
│       ├─ _fetch_and_save_missing_data()
│       │   └─ data_fetcher.get_stock_data()
│       └─ _query_and_format_dataframe()
└─ Fallback: data_fetcher.get_stock_data()

BacktestEngine._get_price_data() [#3]
├─ data_repository.get_stock_data() [#5 - 3-layer cache]
│   ├─ Memory cache check
│   ├─ load_ticker_data() [MySQL cache layer]
│   └─ data_fetcher.get_stock_data() [yfinance fallback]
└─ Fallback: data_fetcher.get_stock_data() ✓ (Correctly wrapped)

ChartDataService._get_price_data() [#4]
├─ data_repository.get_stock_data() [#5 - 3-layer cache]
│   └─ (same as above)
└─ Fallback: data_fetcher.get_stock_data() ✗ (MISSING asyncio.to_thread() - BUG!)

YFinanceDataRepository.get_stock_data() [#5]
├─ Memory cache
├─ load_ticker_data() [MySQL cache]
└─ data_fetcher.get_stock_data() [API fallback]
```

---

## Files Modified by Duplicates

| File | Functions | Issue |
|------|-----------|-------|
| `app/services/data_service.py` | #1, #2 | Duplicate async/sync versions (76 LOC) |
| `app/services/backtest_engine.py` | Uses #3 | Calls _get_price_data for backtest |
| `app/services/chart_data_service.py` | Uses #4 | Calls _get_price_data for charts; 🐛 Has critical bug |
| `app/repositories/data_repository.py` | #5 | Alternative 3-layer implementation |
| `app/services/yfinance_db.py` | #6, wrapper | Core DB logic (296 LOC total) |
| `app/services/unified_data_service.py` | Caller | Uses data_service.get_ticker_data_sync() |

---

## Total Code Affected

- **Total Data Loading Code**: ~360 lines
- **Duplicated Code**: ~189 lines (52%)
- **Unique Code**: ~171 lines (48%)
- **Potential Reduction**: 40-50% with consolidation

