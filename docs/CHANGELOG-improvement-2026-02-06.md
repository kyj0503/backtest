# 코드베이스 개선 변경 로그 (2026-02-06)

> 35개 파일 변경 | +645줄 / -984줄 (순 339줄 감소)
> 신규 파일 5개 (테스트 4 + 검증 유틸 1) | 삭제 파일 2개 (죽은 코드)

---

## 목차

1. [Phase 1: BE 안정성 — 이벤트 루프 블로킹 · 커넥션 누수 · 에러 마스킹](#phase-1-be-안정성)
2. [Phase 2: BE 코드 품질 — 중복 제거 · 벡터화 · 메서드 분리](#phase-2-be-코드-품질)
3. [Phase 3: 단위 테스트 추가 (BE 59개)](#phase-3-단위-테스트)
4. [Phase 4: FE 개선 — 번들·타입·아키텍처](#phase-4-fe-개선)
5. [Phase 5: 접근성·UX](#phase-5-접근성ux)
6. [검증 결과](#검증-결과)
7. [변경 파일 전체 목록](#변경-파일-전체-목록)

---

## Phase 1: BE 안정성

### 1-1. Async/Sync 경계 수정 — 이벤트 루프 블로킹 방지

| 파일 | 변경 |
|------|------|
| `app/api/v1/endpoints/backtest.py` | `unified_data_service.collect_all_unified_data()` 호출을 `await asyncio.to_thread(...)` 로 래핑 |
| `app/services/unified_data_service.py` | `import asyncio` 추가 (to_thread 사용 준비) |

**문제:** `collect_all_unified_data()`는 내부에서 `urllib.request.urlopen()` (뉴스), DB 조회 등 동기 I/O를 실행합니다. async 엔드포인트에서 직접 호출하면 이벤트 루프가 블로킹되어 동시 요청 처리가 불가능합니다.

**수정 전:**
```python
unified_data = unified_data_service.collect_all_unified_data(symbols=symbols, ...)
```

**수정 후:**
```python
unified_data = await asyncio.to_thread(
    unified_data_service.collect_all_unified_data,
    symbols=symbols, ...
)
```

### 1-2. `time.sleep()` 제거

| 파일 | 변경 |
|------|------|
| `app/repositories/yfinance_repository.py` (3곳) | `time.sleep(0.1)` 제거 |

**문제:** DB에 데이터 저장 후 `time.sleep(0.1)`로 "커밋 완료 보장"을 시도했으나, SQLAlchemy의 `conn.close()` → 재연결 패턴으로 이미 트랜잭션 격리가 보장됩니다. 20종목 포트폴리오에서 2~6초 불필요한 지연이 발생했습니다.

**제거한 위치:**
- L447: `_load_ticker_data_internal` 내부 — 신규 티커 저장 후
- L521: `_fetch_and_save_missing_data` 내부 — 갱신 데이터 저장 후
- L543: `_fetch_and_save_missing_data` 내부 — 누락 기간 수집 후

### 1-3. 커넥션 컨텍스트 매니저 적용

| 파일 | 변경 |
|------|------|
| `app/repositories/yfinance_repository.py` | `get_ticker_info_from_db()`, `get_ticker_info_batch_from_db()`, `get_news_from_db()`, `save_news_to_db()` |

**문제:** `conn = engine.connect()` + `finally: conn.close()` 패턴은 예외 발생 시 `close()` 호출이 보장되지 않는 경우가 있고, 트랜잭션이 롤백되지 않을 수 있습니다.

**수정 전:**
```python
conn = engine.connect()
try:
    ...
finally:
    conn.close()
```

**수정 후:**
```python
with engine.connect() as conn:
    ...
```

`save_news_to_db()`는 `engine.begin()`으로 변경하여 자동 커밋/롤백을 보장합니다.

> **참고:** `_load_ticker_data_internal()`은 내부에서 `_ensure_stock_exists`와 `_fetch_and_save_missing_data`가 커넥션을 닫고 재연결하는 패턴을 사용하므로 수동 관리를 유지합니다. 이 결정을 설명하는 주석을 추가했습니다.

### 1-4. 읽기 메서드에서 쓰기 분리

| 파일 | 변경 |
|------|------|
| `app/repositories/yfinance_repository.py` | `_update_ticker_info()` 메서드 신규 추출 |

**문제:** `get_ticker_info_from_db()` (읽기 메서드) 내에서 상장일이 없으면 Yahoo Finance에서 조회 후 UPDATE를 실행했습니다. 읽기/쓰기가 혼재되어 예상치 못한 부수효과가 발생합니다.

**수정:** UPDATE 로직을 `_update_ticker_info(ticker, stock_id, info)` 별도 메서드로 분리했습니다.

### 1-5. 무제한 메모리 캐시 → TTLCache

| 파일 | 변경 |
|------|------|
| `app/repositories/data_repository.py` | `Dict` → `TTLCache(maxsize=500, ttl=3600)` |
| `requirements.txt` | `cachetools>=5.3.0` 추가 |

**문제:** `_memory_cache: Dict[str, Dict[str, Any]]`에 크기/시간 제한이 없어 장시간 운영 시 OOM 위험이 있었습니다. 또한 TTL 검증을 위한 `_is_cache_valid()`, `_get_cache_ttl()` 같은 커스텀 로직이 별도로 존재했습니다.

**수정 후:**
```python
from cachetools import TTLCache
self._memory_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)
```

`TTLCache`가 자동으로 만료 항목을 제거하므로 `_is_cache_valid()`, `_get_cache_ttl()` 메서드를 삭제하고, 캐시 저장도 `{'data': ..., 'timestamp': ..., 'end_date': ...}` 래퍼 없이 DataFrame을 직접 저장합니다. `get_cache_stats()`도 `maxsize`, `ttl` 속성을 활용하도록 간소화했습니다.

### 1-6. BacktestEngine 에러 마스킹 수정

| 파일 | 변경 |
|------|------|
| `app/services/backtest_engine.py` | `run_backtest()` 의 try/except 구조 변경 |

**문제:** 모든 예외를 catch하여 fallback Buy&Hold 결과를 반환했습니다. 잘못된 전략 파라미터, 코드 버그 등 실제 오류도 조용히 무시되어 디버깅이 불가능했습니다.

**수정 전:**
```python
try:
    result = await asyncio.to_thread(self._execute_backtest, bt, run_kwargs)
    if result is not None and '# Trades' in result:
        return self._convert_result_to_response(result, request)
    else:
        raise Exception("유효하지 않은 결과")
except Exception as e:
    return self._create_fallback_result(data, request)  # 모든 에러 무시
```

**수정 후:**
```python
result = await asyncio.to_thread(self._execute_backtest, bt, run_kwargs)
if result is not None and '# Trades' in result:
    return self._convert_result_to_response(result, request)
else:
    # 결과가 유효하지 않은 경우만 fallback
    return self._create_fallback_result(data, request)
```

바깥 try/except에서 `InvalidSymbolError`(HTTPException)는 그대로 재발생시키고, 그 외 에러는 500으로 처리합니다. `data_fetcher.py`의 중복 예외 클래스도 제거하고 `core/exceptions.py`를 임포트합니다.

### 1-7. 실패 종목 추적 (`failed_symbols`)

| 파일 | 변경 |
|------|------|
| `app/services/portfolio_manager_service.py` | `run_strategy_portfolio_backtest()` 내 `failed_symbols` 추가 |

**문제:** 포트폴리오 내 개별 종목 백테스트가 실패하면 `continue`로 건너뛰고 "성공" 응답을 반환했습니다. 사용자는 결과에 누락된 종목이 있다는 사실을 인지할 수 없었습니다.

**수정:**
```python
failed_symbols = []
for idx, item in enumerate(request.portfolio):
    try:
        ...
    except Exception as e:
        failed_symbols.append({'symbol': symbol, 'error': str(e)})
        continue

# 응답에 warnings 필드 추가
warnings = []
if failed_symbols:
    for fs in failed_symbols:
        warnings.append(f"종목 {fs['symbol']} 백테스트 실패: {fs['error']}")
result['data']['warnings'] = warnings
```

---

## Phase 2: BE 코드 품질

### 2-1. 중복 예외 클래스 통합

| 파일 | 변경 |
|------|------|
| `app/utils/data_fetcher.py` | `DataNotFoundError`, `InvalidSymbolError`, `YfinanceRateLimitError` 3개 클래스 삭제 → `core/exceptions.py`에서 임포트 |
| `app/core/exceptions.py` | 생성자를 유연하게 변경 (문자열 직접 전달 지원) |
| `scripts/daily_price_update.py` | 임포트 경로 변경 |

**문제:** 동일한 이름의 예외 클래스가 `core/exceptions.py`(HTTPException 기반)와 `utils/data_fetcher.py`(plain Exception 기반) 양쪽에 존재했습니다. 어디서 발생한 예외인지에 따라 에러 핸들링이 달라지는 미묘한 버그가 가능했습니다.

### 2-2. 통화 변환 벡터화

| 파일 | 변경 |
|------|------|
| `app/utils/currency_converter.py` | `convert_dataframe_to_usd()` 내 for-loop → pandas 벡터 연산 |

**문제:** Python for-loop으로 각 행의 환율을 조회하고 곱셈을 수행했습니다. 1000일 데이터 × 4 컬럼(OHLC) = 4000번의 개별 연산.

**수정 후:**
```python
# 1. 타임존 제거
price_index_no_tz = self._remove_timezone(converted_data.index)

# 2. 환율 데이터를 가격 인덱스에 맞게 정렬
exchange_rates_aligned = exchange_data['Close'].reindex(price_index_no_tz)

# 3. 통화별 변환 비율 계산 (벡터)
if currency in ['EUR', 'GBP', 'AUD', 'CAD', 'CHF']:
    multipliers = exchange_rates_aligned
else:
    multipliers = 1.0 / exchange_rates_aligned.where(exchange_rates_aligned > 0, 1.0)

# 4. NaN이 아닌 행만 변환
valid_mask = multipliers.notna()
multipliers.index = converted_data.index
for col in ['Open', 'High', 'Low', 'Close']:
    converted_data.loc[valid_mask.values, col] *= multipliers[valid_mask].values
```

### 2-3. 400줄+ 메서드 분리 (PortfolioManagerService)

| 파일 | 변경 |
|------|------|
| `app/services/portfolio_manager_service.py` | 3개 `@staticmethod` 헬퍼 추출 |

**추출된 메서드:**

| 메서드 | 용도 |
|--------|------|
| `_calculate_weighted_stats(portfolio_results)` | 가중 평균 거래 수, 승률, 최대 드로우다운, 샤프 비율 계산 |
| `_calculate_daily_return_stats(daily_returns)` | 연간 변동성, 프로핏 팩터, positive/negative days 계산 |
| `_format_individual_results_list(individual_returns, ...)` | individual_returns 딕셔너리를 프론트엔드 호환 리스트로 변환 (strategy/buy_hold 2가지 모드) |

`run_strategy_portfolio_backtest()`와 `run_buy_and_hold_portfolio_backtest()` 양쪽에서 중복되던 통계 계산 · 결과 포맷팅 로직이 공유됩니다.

---

## Phase 3: 단위 테스트

| 테스트 파일 | 테스트 수 | 대상 모듈 |
|-------------|-----------|-----------|
| `tests/unit/test_backtest_engine.py` | 10 | `BacktestEngine` — run_backtest, fallback, 전략 빌드, 결과 변환 |
| `tests/unit/test_currency_converter.py` | 18 | `CurrencyConverter` — 13개 통화, 벡터 변환, 엣지 케이스 |
| `tests/unit/test_data_repository.py` | 17 | `YfinanceDataRepository` — TTLCache 동작, 3-tier 캐시, 캐시 무효화 |
| `tests/unit/test_portfolio_manager_helpers.py` | 14 | `PortfolioManagerService` 정적 헬퍼 — 가중 통계, 일별 수익률, 결과 포맷팅 |

**총 59개 테스트 추가** → 기존 82개 + 59개 = **141개 (0.8s)**

모든 테스트는 외부 I/O를 모킹하고 `@pytest.mark.unit`을 사용합니다.

---

## Phase 4: FE 개선

### 4-1. Route-level 코드 스플리팅

| 파일 | 변경 |
|------|------|
| `src/App.tsx` | `import HomePage` → `React.lazy(() => import(...))` + `Suspense` 래핑 |

**수정 전:** `HomePage`, `PortfolioPage`가 메인 번들에 직접 포함 (초기 로드 시 전체 코드 다운로드).

**수정 후:**
```tsx
const HomePage = lazy(() => import('./pages/HomePage'));
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'));

// Routes를 Suspense로 래핑
<Suspense fallback={<div className="flex items-center justify-center min-h-[60vh]" />}>
  <Routes>...</Routes>
</Suspense>
```

빌드 결과에서 `HomePage-DhHv2ohA.js` (23.78KB), `PortfolioPage-UBHPKlMZ.js` (223.76KB)로 분리된 것을 확인할 수 있습니다.

### 4-2. 미사용 npm 패키지 제거 (7개)

| 파일 | 변경 |
|------|------|
| `package.json` | 7개 의존성 제거 |

**제거 목록:**
| 패키지 | 용도 (사용되지 않음) |
|--------|---------------------|
| `@hookform/resolvers` | react-hook-form 유효성 검증 |
| `react-hook-form` | 폼 관리 (useReducer로 대체됨) |
| `zod` | 스키마 유효성 검증 |
| `cmdk` | 커맨드 팔레트 UI |
| `react-day-picker` | 날짜 선택기 |
| `react-resizable-panels` | 리사이저블 패널 |
| `vaul` | 드로어 컴포넌트 |

> `next-themes`는 sonner 컴포넌트가 내부 의존하므로 유지합니다.

### 4-3. useTheme 이중화 수정

| 파일 | 변경 |
|------|------|
| `src/App.tsx` | `useEffect`로 DOM 조작하던 로직 제거, `useTheme()` 호출만 유지 |

**문제:** `App.tsx`의 `useEffect`와 `useTheme` 훅 양쪽에서 독립적으로 `document.documentElement`의 `data-theme`, `dark` 클래스를 조작 → 상태 불일치 가능.

**수정:** `useTheme()` 훅이 이미 모든 DOM 업데이트를 처리하므로 App.tsx의 중복 로직 삭제.

### 4-4. API 클라이언트 통합 (fetch → axios)

| 파일 | 변경 |
|------|------|
| `src/features/backtest/api/backtestApi.ts` | 전면 리라이트 (223줄 → 135줄, -88줄) |

**문제:** `shared/api/client.ts`에 axios 인스턴스가 있는데, `backtestApi.ts`는 별도로 `fetch`를 사용. 에러 처리, 타임아웃, 인터셉터 등이 불일치.

**수정:** 모든 API 함수를 `apiClient.get()`으로 변경하고, `toApiError()` 함수로 axios 에러를 `ApiError` 타입으로 통합 변환.

**수정 전:**
```typescript
const response = await fetch(`/api/v1/backtest/stock-data/${ticker}?start_date=...`);
if (!response.ok) throw await parseErrorResponse(response);
return response.json();
```

**수정 후:**
```typescript
const { data } = await apiClient.get(
  `/api/v1/backtest/stock-data/${ticker}`,
  { params: { start_date: startDate, end_date: endDate } },
);
return data;
```

### 4-5. AbortController 추가 (레이스 컨디션 방지)

| 파일 | 변경 |
|------|------|
| `src/features/backtest/hooks/useStockData.ts` | AbortController + cleanup |
| `src/features/backtest/hooks/useExchangeRate.ts` | AbortController + cleanup |
| `src/features/backtest/hooks/useVolatilityNews.ts` | AbortController + cleanup |

**문제:** 사용자가 파라미터를 빠르게 변경하면 이전 요청의 응답이 나중에 도착하여 최신 상태를 덮어쓸 수 있습니다 (레이스 컨디션). 컴포넌트 언마운트 시 메모리 누수도 가능했습니다.

**수정 패턴 (3개 훅 공통):**
```typescript
const abortControllerRef = useRef<AbortController | null>(null);

const fetchData = useCallback(async () => {
  abortControllerRef.current?.abort();          // 이전 요청 취소
  const controller = new AbortController();
  abortControllerRef.current = controller;

  try {
    const response = await getStockData(ticker, startDate, endDate);
    if (controller.signal.aborted) return;       // 취소된 요청 무시
    setData(response);
  } catch (err) {
    if (controller.signal.aborted) return;       // 취소 에러 무시
    setError('...');
  } finally {
    if (!controller.signal.aborted) setLoading(false);
  }
}, [deps]);

useEffect(() => {
  fetchData();
  return () => { abortControllerRef.current?.abort(); };  // cleanup
}, [fetchData]);
```

### 4-6. FSD 위반 수정

| 파일 | 변경 |
|------|------|
| `src/shared/hooks/useFormValidation.ts` | **삭제** |
| `src/features/backtest/hooks/useFormValidation.ts` | **신규** (이동 + 리팩터링) |
| `src/features/backtest/components/PortfolioBacktestForm.tsx` | 임포트 경로 변경 |

**문제:** `shared/` 레이어가 `features/backtest/` 타입을 임포트 → Feature-Sliced Design의 의존성 방향 위반 (`shared` ← `features` ← `pages`).

**수정:** `useFormValidation`을 `features/backtest/hooks/`로 이동하고, 내부 임포트를 상대 경로로 변경.

### 4-7. 차트 파이프라인 `any` 타입 제거

| 파일 | `any` 제거 수 |
|------|--------------|
| `src/features/backtest/utils/chartDataTransform.ts` | 12개 → 0개 |
| `src/features/backtest/hooks/charts/useChartData.ts` | 24개 → 0개 |

**교체 규칙:**

| 원래 타입 | 교체 타입 | 위치 |
|-----------|-----------|------|
| `any[]` (equity) | `EquityPoint[]` | transformSingleEquityData, etc. |
| `any[]` (trades) | `TradeMarker[]` | transformTradeMarkers |
| `any[]` (ohlc) | `OhlcPoint[]` | transformOhlcData |
| `any[]` (benchmark) | `BenchmarkPoint[]` / `(BenchmarkPoint & { return_pct?: number })[]` | withBenchmarkReturn, sp500/nasdaq |
| `Record<string, any>` (ticker) | `Record<string, TickerInfo>` | tickerInfo |
| `Record<string, any[]>` (trades) | `Record<string, TradeLog[]>` | tradeLogs |
| `any[]` (exchange) | `ExchangeRatePoint[]` | exchangeRates |
| `any` (exchangeStats) | `unknown` | exchangeStats |
| `Record<string, any[]>` (volatility) | `Record<string, VolatilityEvent[]>` | volatilityEvents |
| `Record<string, any[]>` (news) | `Record<string, NewsItem[]>` | latestNews |
| `any[]` (rebalance) | `RebalanceEvent[]` | rebalanceHistory |
| `any[]` (weight) | `WeightHistoryPoint[]` | weightHistory |
| `null as any` | `undefined` / `0` | fallback equity values |

`(data as any).property` 패턴은 `'property' in data ? (data as PortfolioData).property : undefined` 타입 가드로 교체했습니다.

### 4-8. 중복 NewsItem 타입 통합

| 파일 | 변경 |
|------|------|
| `model/types/backtest-result-types.ts` | `company?: string` 필드 추가 (canonical 타입) |
| `model/types/volatility-news-types.ts` | 로컬 `NewsItem` 삭제, re-export from `backtest-result-types` |
| `model/types/api-types.ts` | 로컬 `NewsItem` 삭제, re-export from `backtest-result-types` |
| `components/results/LatestNewsSection.tsx` | 인라인 `NewsItem` 삭제, 임포트로 교체 |
| `components/results/UnifiedInfoSection.tsx` | 인라인 `NewsItem`, `VolatilityEvent` 삭제, 임포트로 교체 |

**문제:** `NewsItem`이 5곳에 독립적으로 정의되어 있었고, 필드 구조가 미묘하게 달랐습니다 (예: `company` 필드 유무, `originallink` 유무).

### 4-9. 하드코딩 날짜 → 동적 계산

| 파일 | 변경 |
|------|------|
| `model/types/backtest-form-types.ts` | `getDefaultDates()` 함수 추가, `initialBacktestFormState` 적용 |
| `model/backtestFormReducer.ts` | `RESET_FORM` 케이스에서 `{ ...initialBacktestFormState }` 사용 |

**문제:** `startDate: '2025-01-01'`, `endDate: '2025-10-31'` (초기값)과 `startDate: '2023-01-01'`, `endDate: '2024-12-31'` (리셋)이 하드코딩. 시간이 지나면 의미 없는 기간이 됩니다.

**수정:**
```typescript
const getDefaultDates = () => {
  const today = new Date();
  const oneYearAgo = new Date(today);
  oneYearAgo.setFullYear(today.getFullYear() - 1);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { startDate: fmt(oneYearAgo), endDate: fmt(today) };
};
```

`RESET_FORM`도 `{ ...initialBacktestFormState }`를 재사용하여 하드코딩된 26줄 중복을 제거했습니다.

### 4-10. 죽은 코드 삭제

| 파일 | 변경 |
|------|------|
| `model/BacktestContext.tsx` | **삭제** (138줄) |

**확인:** `useBacktestForm` 훅이 완전히 대체하여 어디서도 임포트되지 않습니다.

### 4-11. 검증 로직 통합

| 파일 | 변경 |
|------|------|
| `hooks/useFormValidation.ts` (신규) | `validateBacktestForm()` 순수 함수 추출 |
| `hooks/useBacktestForm.ts` | 인라인 검증 25줄 → `validateBacktestForm(state)` 1줄 |

**문제:** 동일한 폼 검증 로직이 `useFormValidation.ts`, `useBacktestForm.ts`, `backtestFormReducer.ts` 3곳에 중복.

**수정:** `validateBacktestForm(formState)`을 `useFormValidation.ts`에 순수 함수로 정의하고, `backtestFormHelpers.validatePortfolio()`에 위임합니다. `useBacktestForm`과 `useFormValidation` 훅 양쪽에서 이 함수를 호출합니다.

---

## Phase 5: 접근성/UX

### 5-1. 차트 섹션별 ErrorBoundary

| 파일 | 변경 |
|------|------|
| `components/results/ChartsSection/index.tsx` | `ErrorBoundary` 3개 추가 |

**문제:** `App.tsx`에 글로벌 ErrorBoundary만 존재 → 차트 1개에서 에러 발생 시 전체 앱 크래시.

**수정:** 3개 차트 섹션 (포트폴리오/종목, 벤치마크, 부가 정보)을 개별 `ErrorBoundary`로 래핑. 에러 발생 시 해당 섹션만 에러 메시지를 표시하고 나머지 차트는 정상 작동합니다.

```tsx
const ChartErrorFallback = ({ section }: { section: string }) => (
  <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-center">
    <p className="text-sm text-destructive">{section} 차트를 렌더링하는 중 오류가 발생했습니다.</p>
    <p className="text-xs text-muted-foreground mt-1">다른 차트는 정상 표시됩니다.</p>
  </div>
);
```

### 5-2. 차트 ARIA 라벨

| 파일 | 변경 |
|------|------|
| `components/shared/ResultBlock.tsx` | `role="img"` + `aria-label` 추가 |

모든 차트 카드가 `ResultBlock`을 사용하므로 한 곳의 수정으로 모든 차트에 접근성 라벨이 적용됩니다.

```tsx
<div className="mt-4" role="img" aria-label={`${title} 차트`}>{children}</div>
```

### 5-3. 폼 입력 aria-label

| 파일 | 변경 |
|------|------|
| `components/portfolio-form/PortfolioTable.tsx` | 4개 `aria-label` 추가 |

**추가 위치:**
- 현금 자산 이름 입력: `${index + 1}번째 현금 자산 이름`
- 종목 심볼 입력: `${index + 1}번째 종목 심볼`
- 투자 금액 입력: `${index + 1}번째 종목 투자 금액`
- 비중 입력: `${index + 1}번째 종목 비중`

### 5-4. Hero 이미지 최적화

| 파일 | 변경 |
|------|------|
| `src/pages/landing/HeroSection.tsx` | `loading`, `width`, `height`, `alt` 추가 |

```tsx
<img
  src="/images/landing/backtest-main.png"
  alt="백테스트 플랫폼 메인 화면 — 포트폴리오 수익률 차트와 전략 설정 화면"
  loading="lazy"
  width={1200}
  height={675}
/>
```

- `loading="lazy"`: 뷰포트에 진입할 때만 로드
- `width/height`: CLS(Cumulative Layout Shift) 방지
- 상세한 `alt`: 스크린 리더 접근성

---

## 검증 결과

| 항목 | 결과 |
|------|------|
| BE 단위 테스트 (Docker) | **141 passed** (0.80s) |
| BE API 호출 | `POST /api/v1/backtest` → 200 OK, 정상 응답 |
| FE TypeScript (소스) | **0 에러** (`tsc --noEmit`, 테스트 파일 기존 에러 제외) |
| FE 빌드 | **성공** (`tsc + vite build`, 9.84s) |
| FE 단위 테스트 | **94 passed, 4 failed** (변경 전과 동일한 기존 실패) |

**기존 FE 테스트 실패 (변경과 무관):**
- `portfolioCalculations.test.ts`: `"weekly_4"` 미정의 타입 참조 (3개)
- `ThemeSelector.test.tsx`: "라이트" 버튼 쿼리 실패 — 컴포넌트 리팩터링 후 테스트 미갱신 (1개)

---

## 변경 파일 전체 목록

### Backend (11 files, +311/-348)

| 파일 | 변경 유형 |
|------|-----------|
| `app/api/v1/endpoints/backtest.py` | asyncio.to_thread 래핑 |
| `app/core/exceptions.py` | 생성자 유연화 |
| `app/repositories/data_repository.py` | TTLCache, 코드 간소화 |
| `app/repositories/yfinance_repository.py` | 컨텍스트 매니저, sleep 제거, 쓰기 분리 |
| `app/services/backtest_engine.py` | 에러 마스킹 수정, 예외 통합 |
| `app/services/portfolio_manager_service.py` | 헬퍼 추출, failed_symbols |
| `app/services/unified_data_service.py` | asyncio import 추가 |
| `app/utils/currency_converter.py` | 벡터화 |
| `app/utils/data_fetcher.py` | 중복 예외 제거 |
| `requirements.txt` | cachetools 추가 |
| `scripts/daily_price_update.py` | 임포트 경로 변경 |

### Backend 테스트 (4 new files, +1489)

| 파일 | 테스트 수 |
|------|-----------|
| `tests/unit/test_backtest_engine.py` | 10 |
| `tests/unit/test_currency_converter.py` | 18 |
| `tests/unit/test_data_repository.py` | 17 |
| `tests/unit/test_portfolio_manager_helpers.py` | 14 |

### Frontend (23 files, +307/-635)

| 파일 | 변경 유형 |
|------|-----------|
| `package.json` | 7개 패키지 제거 |
| `src/App.tsx` | lazy loading, useTheme 정리 |
| `api/backtestApi.ts` | fetch → axios 통합 |
| `components/PortfolioBacktestForm.tsx` | 임포트 경로 수정 |
| `components/portfolio-form/PortfolioTable.tsx` | aria-label 4개 |
| `components/results/ChartsSection/index.tsx` | ErrorBoundary 3개 |
| `components/results/LatestNewsSection.tsx` | NewsItem 통합 |
| `components/results/UnifiedInfoSection.tsx` | NewsItem/VolatilityEvent 통합 |
| `components/shared/ResultBlock.tsx` | role="img" + aria-label |
| `hooks/charts/useChartData.ts` | any → 구체적 타입 (24곳) |
| `hooks/useBacktestForm.ts` | 검증 통합 |
| `hooks/useExchangeRate.ts` | AbortController |
| `hooks/useStockData.ts` | AbortController |
| `hooks/useVolatilityNews.ts` | AbortController |
| `hooks/useFormValidation.ts` | **신규** (FSD 이동 + 통합) |
| `model/BacktestContext.tsx` | **삭제** (죽은 코드) |
| `model/backtestFormReducer.ts` | RESET_FORM 중복 제거 |
| `model/types/api-types.ts` | NewsItem re-export |
| `model/types/backtest-form-types.ts` | 동적 날짜 |
| `model/types/backtest-result-types.ts` | company 필드 |
| `model/types/volatility-news-types.ts` | NewsItem re-export |
| `utils/chartDataTransform.ts` | any → 구체적 타입 (12곳) |
| `pages/landing/HeroSection.tsx` | 이미지 최적화 |
| `shared/hooks/useFormValidation.ts` | **삭제** (FSD 이동) |

---

## Phase 6: Follow-up — 검증 보고서 기반 이슈 수정

> 독립적 검증/회귀 분석에서 발견된 4개 이슈를 수정한 후속 작업

### 6-1. Hero 이미지 `loading="lazy"` → `fetchPriority="high"` (LCP 개선)
- **파일:** `pages/landing/HeroSection.tsx` (L46)
- **문제:** 히어로 이미지(above-the-fold)에 `loading="lazy"` 적용 → LCP(Largest Contentful Paint) 성능 저하
- **수정:** `loading="lazy"` 제거, `fetchPriority="high"` 추가 → 브라우저가 최우선으로 이미지 로드

### 6-2. 차트 컨테이너 `role="img"` → `role="figure"` (접근성 수정)
- **파일:** `features/backtest/components/shared/ResultBlock.tsx` (L30)
- **문제:** `role="img"`는 내부의 인터랙티브 Recharts 요소(툴팁, 줌 등)를 접근성 트리에서 숨김
- **수정:** `role="figure"` 사용 → 하위 인터랙티브 요소 접근성 유지

### 6-3. AbortController signal을 실제 API 호출에 전달
- **파일:** `features/backtest/api/backtestApi.ts` — 6개 함수에 `signal?: AbortSignal` 파라미터 추가
- **파일:** `features/backtest/hooks/useStockData.ts` (L56) — `getStockData()` 호출 시 `controller.signal` 전달
- **파일:** `features/backtest/hooks/useExchangeRate.ts` (L49) — `getExchangeRate()` 호출 시 `controller.signal` 전달
- **파일:** `features/backtest/hooks/useVolatilityNews.ts` (L80) — `getStockVolatilityNews()` 호출 시 `controller.signal` 전달
- **문제:** AbortController를 생성하고 abort()도 호출하지만, signal이 axios에 전달되지 않아 실제 HTTP 요청은 취소되지 않음
- **수정:** 모든 API 함수에 `signal` 옵션 추가, 훅에서 `controller.signal`을 API 함수에 전달

### 6-4. `getDefaultDates()` 장시간 세션 시 날짜 갱신 보장
- **파일:** `features/backtest/model/types/backtest-form-types.ts` (L56) — `getDefaultDates` export 추가
- **파일:** `features/backtest/model/backtestFormReducer.ts` (L301) — `RESET_FORM`에서 `getDefaultDates()` 호출
- **파일:** `features/backtest/hooks/useBacktestForm.ts` (L35-38) — `useReducer` lazy initializer 적용
- **문제:** `getDefaultDates()`가 모듈 로드 시점에 한 번만 실행되어, 브라우저 탭을 오래 열어둔 경우 어제 날짜가 기본값으로 유지
- **수정:** `getDefaultDates`를 export하고, RESET_FORM과 useReducer 초기화 시 매번 새로 호출

### 6-5. CLAUDE.md 현대화
- **파일:** `CLAUDE.md`
- **변경:** 내용 압축 (141줄 → 73줄), `docs/` 참조 추가, 서브 에이전트 사용 가이드 추가

### 검증 결과

| 항목 | 결과 |
|------|------|
| BE 유닛 테스트 | 141 passed (0 failures) |
| FE 빌드 | 성공 (14.51s) |
| FE 테스트 | 94 passed / 4 failed (기존 ThemeSelector 실패, 회귀 없음) |
| TypeScript | 0 new errors (기존 useForm.test.ts 에러만 존재) |
