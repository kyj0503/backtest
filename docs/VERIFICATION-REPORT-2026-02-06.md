# Verification & Regression Analysis Report (2026-02-06)

> CHANGELOG-improvement-2026-02-06.md 에 기술된 전체 변경사항에 대한 독립 검증 결과
> 3개 전문 에이전트가 병렬로 분석: BE 아키텍트 리뷰어, FE 아키텍트 리뷰어, 테스트 러너

---

## 목차

1. [회귀 테스트 결과](#1-회귀-테스트-결과)
2. [Backend 변경 검증 (9건)](#2-backend-변경-검증)
3. [Frontend 변경 검증 (14건)](#3-frontend-변경-검증)
4. [발견된 이슈 (4건)](#4-발견된-이슈)
5. [결론](#5-결론)

---

## 1. 회귀 테스트 결과

### 테스트 스위트 실행 결과

| 테스트 스위트 | 상태 | 세부 결과 |
|--------------|------|-----------|
| BE 단위 테스트 | **141/141 통과** | 0.80s, 경고 8건 (pandas FutureWarning, Sortino Ratio div/zero — 기존) |
| FE 프로덕션 빌드 | **성공** | `tsc -p tsconfig.build.json && vite build` — 18개 에셋, 11.79s |
| BE API 스모크 테스트 | **HTTP 200** | 2종목 포트폴리오 + SMA 전략 — 정상 응답 |
| FE 단위 테스트 | **94 통과 / 4 실패** | 실패 4건은 변경 전과 동일한 기존 실패 |
| FE TypeScript (strict) | **42 에러 (테스트 파일만)** | 프로덕션 소스 코드: 0 에러 |

### FE 기존 테스트 실패 상세 (변경과 무관)

| 테스트 파일 | 실패 수 | 원인 |
|------------|---------|------|
| `portfolioCalculations.test.ts` | 3 | `"weekly_4"` 등 삭제된 DcaFrequency 값 참조, `getDcaWeeks` 미존재 함수 호출 |
| `ThemeSelector.test.tsx` | 1 | "라이트" 버튼을 찾지 못함 — 테마 선택기 UI 리디자인 후 테스트 미갱신 |

### FE 테스트 파일 TypeScript 에러 (프로덕션 빌드에 미포함)

| 테스트 파일 | 에러 수 | 원인 |
|------------|---------|------|
| `useForm.test.ts` | 14 | `TestFormData` → `Record<string, unknown>` 인덱스 시그니처 불일치 |
| `portfolioCalculations.test.ts` | 12 | 삭제된 `weekly_4` enum, `getDcaWeeks` export |
| `backtestFormReducer.test.ts` | 6 | `Object is possibly 'undefined'` |
| `UnifiedInfoSection.test.tsx` | 6 | `VolatilityEvent`에 `volume` 필드 누락 |
| `useBacktestForm.test.ts` | 2 | `Object is possibly 'undefined'` |
| `backtestService.integration.test.ts` | 1 | `DefaultBodyType` → `BacktestRequest` 타입 불일치 |
| `chartUtils.test.ts` | 1 | `string \| undefined` → `string` |

> 모든 에러는 `tsconfig.build.json`이 제외하는 테스트 파일에만 존재하며, 프로덕션 빌드에 영향 없음.

---

## 2. Backend 변경 검증

### 2-1. asyncio.to_thread 래핑 (backtest.py, unified_data_service.py)

- **문제 유효성:** 유효. `collect_all_unified_data()`는 내부에서 `urllib.request.urlopen()`, DB 조회 등 동기 I/O를 수행하는 순수 동기 메서드. async 엔드포인트에서 직접 호출 시 이벤트 루프 블로킹 발생.
- **구현 정확성:** 정확. `unified_data_service`는 싱글톤이며, 내부 속성(`stock_repo`, `news_service`)은 초기화 시 한 번 설정되고 호출 중 변경되지 않아 스레드 안전성 문제 없음. SQLAlchemy engine은 스레드 안전.
- **회귀 위험:** **낮음**. 기능적으로 동일하며 동시 요청 처리 성능이 개선됨.

### 2-2. time.sleep(0.1) 제거 (yfinance_repository.py)

- **문제 유효성:** 유효. `save_ticker_data()`가 `engine.begin()` 컨텍스트 매니저를 사용하므로 블록 종료 시 `conn.commit()`이 동기적으로 완료됨. MySQL 8.0 InnoDB의 `READ COMMITTED` / `REPEATABLE READ` 격리 수준에서 커밋된 트랜잭션은 새 커넥션에 즉시 가시적.
- **구현 정확성:** 정확. sleep은 방어적 프로그래밍(cargo-cult)이었으며, 기존 재시도 로직(3회, 2s/4s/6s 지수 백오프)이 혹시 모를 일시적 문제에 대한 안전망 역할.
- **회귀 위험:** **낮음**. 극단적 MySQL 부하 시 이론적 위험이 있으나 실질적 가능성 매우 낮음.

### 2-3. 커넥션 컨텍스트 매니저 (yfinance_repository.py)

- **문제 유효성:** 유효. 수동 `conn.close()` 패턴은 복잡한 중첩에서 누수 가능성 있음.
- **구현 정확성:** 정확.
  - 읽기 메서드(`get_ticker_info_from_db`, `get_ticker_info_batch_from_db`, `load_news_from_db`): `with engine.connect() as conn:` 적용. `fetchall()`로 결과를 메모리에 적재하므로 `with` 블록 밖에서 처리 가능.
  - 쓰기 메서드(`save_news_to_db`): `with engine.begin() as conn:` 적용. 자동 커밋/롤백 보장.
  - `_update_ticker_info()`: 별도 추출. 독립 `engine.begin()` 트랜잭션으로 읽기/쓰기 분리.
  - `_load_ticker_data_internal()`: 의도적으로 수동 관리 유지. 내부의 `_ensure_stock_exists`와 `_fetch_and_save_missing_data`가 커넥션을 닫고 재연결하는 패턴을 사용하므로 `with` 블록 적용 불가. **이 판단은 타당함.**
- **회귀 위험:** **낮음**. 동일 시맨틱 유지.

### 2-4. TTLCache (data_repository.py)

- **문제 유효성:** 유효. 원본 `Dict`에 크기/시간 제한 없어 OOM 위험. 만료 항목이 자동 제거되지 않음.
- **구현 정확성:** 정확.
  - **스레드 안전성:** `TTLCache`는 자체적으로 스레드 안전하지 않으나, 이 코드에서 캐시 접근은 메인 이벤트 루프 스레드에서만 발생 (무거운 작업만 `to_thread`로 위임). 단일 워커 uvicorn에서 안전. 다중 워커(gunicorn)는 프로세스별 독립 캐시이므로 문제 없음.
  - **maxsize=500 적정성:** DataFrame 1개 ≈ 12KB → 500개 ≈ 6MB. 합리적 범위.
  - **동작 변경:** 원본은 과거/최근 데이터에 다른 TTL을 적용했으나 새 코드는 균일 3600초. DB(L2)와 yfinance(L3) 캐시가 존재하므로 단순화 수용 가능.
  - `invalidate_cache()`에서 `pop(key, None)` 사용 — TTL로 이미 제거된 키 처리 올바름.
- **회귀 위험:** **낮음**. 테스트(`test_data_repository.py`)에서 TTLCache 동작 검증 완료.

### 2-5. 에러 마스킹 수정 (backtest_engine.py)

- **문제 유효성:** **매우 유효. 치명적 버그 수정.** 원본 코드는 모든 예외를 catch하여 0으로 채운 가짜 성공 응답을 반환. `InvalidSymbolError`, `TypeError`, `ValueError` 등 실제 오류도 묻힘.
- **구현 정확성:** 정확. 내부 try/except 제거 후:
  - 백테스트 실행 결과가 유효하지 않은 경우만 fallback 사용
  - `HTTPException` (422 InvalidSymbol 등)은 그대로 재발생
  - 기타 에러는 500으로 처리
- **회귀 위험:** **중간**.
  - 이전에 조용히 무시되던 에러가 이제 사용자에게 표시됨 (이것이 올바른 동작)
  - 데이터 품질/연결 문제가 숨겨져 있었다면 이제 드러남
  - 프론트엔드는 `@handle_portfolio_errors` 데코레이터 패턴으로 에러 응답을 이미 처리하도록 설계됨
  - **배포 후 모니터링으로 새로 노출되는 에러 패턴 확인 권장**

### 2-6. failed_symbols 추적 (portfolio_manager_service.py)

- **문제 유효성:** 유효. 개별 종목 실패 시 `continue`로 건너뛰고 사용자에게 미통지.
- **구현 정확성:** 정확. 응답에 `warnings` 필드 추가. 프론트엔드 타입 정의에 `warnings?: string[]`이 이미 존재하고, `WarningBanner.tsx` 컴포넌트도 이미 구현됨.
- **API 스키마 호환성:** 하위 호환. `warnings`는 선택적(optional) 필드로 추가됨.
- **비대칭 참고:** `run_buy_and_hold_portfolio_backtest()` 경로에는 동일한 `failed_symbols`/`warnings` 처리가 없음. 신규 기능의 갭이며 회귀는 아님.
- **회귀 위험:** **낮음**.

### 2-7. 예외 클래스 통합 (data_fetcher.py, exceptions.py)

- **문제 유효성:** 유효. 동일 이름의 예외가 `data_fetcher.py`(plain Exception)와 `core/exceptions.py`(HTTPException) 양쪽에 정의.
- **구현 정확성:** 정확. 모든 호출 사이트 검증 완료:
  - `raise YfinanceRateLimitError("문자열")` → 새 생성자의 `else` 분기 처리
  - `raise DataNotFoundError(ticker, start, end)` → 새 생성자의 `if start_date and end_date:` 분기 처리
  - `raise DataNotFoundError("단일 문자열")` → 새 생성자의 `else` 분기 처리
  - `raise InvalidSymbolError("긴 문자열")` → `len(symbol) > 30` 분기로 원문 통과
- **설계 참고:** `InvalidSymbolError`의 `len(symbol) > 30` 휴리스틱은 다소 취약. `@classmethod` 팩토리 패턴이 더 견고하나, 현재 모든 호출 사이트에서 올바르게 동작.
- **회귀 위험:** **낮음**.

### 2-8. 통화 변환 벡터화 (currency_converter.py)

- **문제 유효성:** 유효. 행 단위 Python 루프 → 1000일 × 4컬럼 = 4000회 개별 연산.
- **구현 정확성:** **수학적 동치 검증 완료.**
  - EUR/GBP/AUD/CAD/CHF: `multipliers = exchange_rates_aligned` ≡ 원본 `multiplier = exchange_rate`
  - KRW/JPY/CNY 등: `1.0 / exchange_rates_aligned.where(>0, 1.0)` ≡ 원본 `1.0 / exchange_rate if > 0 else 1.0`
  - `_remove_timezone()`이 한 번만 호출 (원본은 행마다 호출) → 동일 결과, 더 효율적
  - `valid_mask`로 NaN이 아닌 행만 변환 → 원본의 `pd.notna()` 체크와 동일
- **회귀 위험:** **낮음**. 성능 10-100배 개선 가능.

### 2-9. 헬퍼 메서드 추출 (portfolio_manager_service.py)

- **문제 유효성:** 유효. `run_strategy_portfolio_backtest()`와 `run_buy_and_hold_portfolio_backtest()` 간 통계 계산/결과 포맷팅 중복.
- **구현 정확성:** 정확. 3개 `@staticmethod` 추출.
  - `_calculate_weighted_stats()`: 원본과 동일한 가중 평균 계산
  - `_calculate_daily_return_stats()`: 원본과 동일한 일별 수익률 통계
  - `_format_individual_results_list()`: `mode='strategy'`/`mode='buy_hold'` 분기로 양쪽 경로 처리
- **동작 변경 참고:** `profit_factor` 계산이 "가중 평균 개별 전략 profit factor" → "포트폴리오 일별 수익률 기반 profit factor"로 변경. 후자가 포트폴리오 수준 지표로 더 정확함.
- **회귀 위험:** **낮음**.

### Backend 변경 요약

| 변경 | 문제 유효 | 구현 정확 | 회귀 위험 |
|------|----------|----------|----------|
| asyncio.to_thread 래핑 | O | O | 낮음 |
| time.sleep 제거 | O | O | 낮음 |
| 커넥션 컨텍스트 매니저 | O | O | 낮음 |
| TTLCache | O | O | 낮음 |
| 에러 마스킹 수정 | O | O | **중간** |
| failed_symbols 추적 | O | O | 낮음 |
| 예외 클래스 통합 | O | O | 낮음 |
| 통화 변환 벡터화 | O | O | 낮음 |
| 헬퍼 메서드 추출 | O | O | 낮음 |

---

## 3. Frontend 변경 검증

### 3-1. Route-level 코드 스플리팅 (App.tsx)

- **문제 유효성:** 유효. 초기 번들에 모든 페이지 코드 포함 → 불필요한 초기 로드.
- **구현 정확성:** 정확. `HomePage.tsx`(L22)와 `PortfolioPage.tsx`(L95) 모두 default export 확인. `Suspense`가 `Router` 내부, `Routes` 외부에 배치 — 올바른 위치.
- **발견 사항:** Suspense fallback이 빈 `<div>`로 로딩 인디케이터 없음. 느린 네트워크에서 빈 화면 표시. 기능적 문제는 아니나 UX 개선 여지 있음.
- **회귀 위험:** **낮음**.

### 3-2. 미사용 npm 패키지 제거 (package.json)

- **문제 유효성:** 유효.
- **구현 정확성:** 정확. 전체 `src/` 디렉터리에서 7개 패키지 모두 import 검색 → **0건**. 트랜지티브 의존성도 문제 없음 (`zod`는 `@hookform/resolvers`의 peer dependency이나 함께 제거됨).
- **회귀 위험:** **없음**.

### 3-3. useTheme 이중화 수정 (App.tsx)

- **문제 유효성:** 유효. `App.tsx`와 `useTheme` 훅 양쪽에서 독립적으로 DOM 조작.
- **구현 정확성:** 정확. `useTheme` 훅(L46-50)이 `document.documentElement`의 `dark` 클래스, CSS 변수 등 모든 DOM 업데이트를 처리. `useState` 초기값이 `localStorage`에서 동기적으로 읽히므로 첫 렌더에서 올바른 상태.
- **회귀 위험:** **없음**.

### 3-4. API 클라이언트 통합 (backtestApi.ts)

- **문제 유효성:** 유효. `fetch`와 `axios` 이중 사용 → 에러 처리 불일치.
- **구현 정확성:** 대부분 정확.
- **발견 사항:** `toApiError()`에서 `'isAxiosError' in error` 덕 타이핑 사용. `axios.isAxiosError(error)` 타입 가드가 더 안전함. `as unknown as` 캐스트는 타입 안전성을 우회하나 런타임에는 정상 동작.
- **회귀 위험:** **낮음**. 기능적으로 동치.

### 3-5. AbortController (useStockData, useExchangeRate, useVolatilityNews)

- **문제 유효성:** 유효. 빠른 파라미터 변경 시 레이스 컨디션, 언마운트 시 메모리 누수.
- **구현 정확성:** **부분적.**
- **발견 사항: AbortController signal이 axios에 전달되지 않음.** `abortControllerRef.current?.abort()` 호출은 있으나, `getStockData()` → `apiClient.get()` 호출 시 `{ signal: controller.signal }` 옵션이 누락됨. 따라서 **HTTP 요청은 실제로 취소되지 않음**. 현재 구현은 "오래된 응답 무시" 가드로만 동작하며, 이것만으로도 레이스 컨디션 방지에 유효하나, 네트워크 대역폭은 낭비됨.
- **useCallback 의존성 배열:** 올바름. `validSymbols.join(',')` 패턴으로 안정적 문자열 비교.
- **메모리 누수:** 없음. `useEffect` cleanup에서 `abort()` 호출.
- **회귀 위험:** **낮음**. 상태 업데이트 가드로는 정상 동작.

### 3-6. FSD 위반 수정 (useFormValidation 이동)

- **문제 유효성:** 유효. `shared/` → `features/backtest/` 타입 임포트는 FSD 위반.
- **구현 정확성:** 정확. 모든 임포트 경로 갱신 확인. 이전 경로(`shared/hooks/useFormValidation`)에서의 임포트 0건.
- **회귀 위험:** **없음**.

### 3-7. `any` 타입 제거 (useChartData.ts, chartDataTransform.ts)

- **문제 유효성:** 유효. 차트 파이프라인에 36개의 `any` → 타입 안전성 저하.
- **구현 정확성:** 대부분 정확. 두 파일 모두 `any` 0건 확인.
- **발견 사항:** `null as any` → `undefined` / `0` 변경. Recharts에서 `null`과 `undefined` 모두 `connectNulls={true}` 옵션으로 연결됨 — 동작 동일. 다만 `PortfolioCharts.tsx`의 리밸런싱 마커에서 `null as unknown as number`이 여전히 사용되어 불일치 존재 (이번 변경 범위 밖).
- **회귀 위험:** **낮음**.

### 3-8. NewsItem 타입 통합

- **문제 유효성:** 유효. 5곳에 독립 정의 → 필드 구조 불일치.
- **구현 정확성:** 정확. canonical 타입에 `company?: string` 추가 (optional이므로 하위 호환). 2개 파일에서 re-export, 2개 컴포넌트에서 인라인 정의 삭제 → 임포트로 교체.
- **회귀 위험:** **없음**.

### 3-9. 동적 날짜 계산 (backtest-form-types.ts, backtestFormReducer.ts)

- **문제 유효성:** 유효. 하드코딩된 날짜는 시간이 지나면 의미 없어짐.
- **구현 정확성:** **부분적.**
- **발견 사항: `getDefaultDates()`가 모듈 로드 시점에 1회 호출됨.** `initialBacktestFormState`는 모듈 수준 상수로, import 시점에 날짜가 고정됨. 브라우저 탭이 자정을 넘기면 `endDate`가 어제 날짜로 고정. `RESET_FORM`도 `{ ...initialBacktestFormState }`를 사용하므로 동일한 문제.
  - **개선안:** `RESET_FORM` 리듀서 케이스와 `useReducer` 초기화 함수에서 `getDefaultDates()`를 직접 호출하도록 변경.
- **회귀 위험:** **낮음~중간**. 하드코딩보다는 개선됐으나 장시간 세션에서 날짜 고착 가능.

### 3-10. 죽은 코드 삭제 (BacktestContext.tsx)

- **문제 유효성:** 유효.
- **구현 정확성:** 정확. `BacktestContext`, `BacktestProvider`, 관련 `useBacktest` 임포트 0건 확인. 현재 사용 중인 `useBacktest`는 `hooks/usePortfolioBacktest.ts`에서 export되는 완전히 별개의 함수.
- **회귀 위험:** **없음**.

### 3-11. 검증 로직 통합 (useFormValidation.ts, useBacktestForm.ts)

- **문제 유효성:** 유효. 3곳에 중복 검증 로직.
- **구현 정확성:** 정확. `validateBacktestForm()`이 `backtestFormHelpers.validatePortfolio()` + 날짜/수수료 검증을 통합. `useBacktestForm`의 인라인 검증 25줄이 1줄 호출로 대체. 모든 검증 규칙 보존 확인.
- **회귀 위험:** **없음**.

### 3-12. ErrorBoundary 차트 섹션별 (ChartsSection/index.tsx)

- **문제 유효성:** 유효. 글로벌 ErrorBoundary만 존재 → 차트 1개 에러로 전체 앱 크래시.
- **구현 정확성:** 정확. `ErrorBoundary` 컴포넌트가 `fallback` prop을 받는 것 확인 (`ErrorBoundary.tsx` L7, L88-89). 3개 섹션(포트폴리오/종목, 벤치마크, 부가 정보)에 개별 래핑.
- **회귀 위험:** **없음**. 장애 격리 개선만 제공.

### 3-13. ARIA 라벨 (ResultBlock.tsx, PortfolioTable.tsx)

- **문제 유효성:** 부분적. 접근성 라벨 추가는 유효하나 `role` 선택에 문제.
- **구현 정확성:** **부분적.**
  - `PortfolioTable.tsx`의 `aria-label` 4개: **정확**. 입력 필드에 의미 있는 컨텍스트 제공.
  - `ResultBlock.tsx`의 `role="img"`: **부적절.** `role="img"`는 요소의 전체 하위 트리를 단일 이미지로 취급하여 **내부의 모든 인터랙티브 자식 요소를 접근성 트리에서 숨김**. Recharts 차트는 툴팁, 호버 상태 등 인터랙티브 콘텐츠를 포함하므로, 스크린 리더 사용자에게 이 콘텐츠가 보이지 않게 됨.
  - **수정안:** `role="figure"` 또는 `<figure>` 요소 사용 — 자식 요소의 접근성을 유지하면서 차트 컨테이너에 라벨 제공.
- **회귀 위험:** **중간**. 스크린 리더 사용자의 차트 인터랙션 접근성 저하.

### 3-14. Hero 이미지 최적화 (HeroSection.tsx)

- **문제 유효성:** 부분적. `width`/`height` 추가(CLS 방지)와 상세 `alt` 텍스트는 유효.
- **구현 정확성:** **`loading="lazy"` 부적절.**
  - Hero 이미지는 페이지 최상단(above the fold)에 위치. `loading="lazy"`는 뷰포트 근처에 도달할 때까지 로딩을 지연시킴.
  - Above-the-fold 이미지에 lazy loading 적용 시 **Largest Contentful Paint (LCP) 성능 저하** — 텍스트가 먼저 렌더링된 후 이미지가 뒤늦게 나타남.
  - **수정안:** `loading="lazy"` 제거 (기본값 `eager` 사용) 또는 `fetchpriority="high"` 추가.
- **회귀 위험:** **중간**. LCP 점수 저하, 느린 네트워크에서 이미지 깜빡임.

### Frontend 변경 요약

| 변경 | 문제 유효 | 구현 정확 | 회귀 위험 | 비고 |
|------|----------|----------|----------|------|
| Route 코드 스플리팅 | O | O | 낮음 | 빈 fallback |
| 미사용 패키지 제거 | O | O | 없음 | |
| useTheme 이중화 수정 | O | O | 없음 | |
| API 클라이언트 통합 | O | 대부분 | 낮음 | 덕 타이핑 |
| AbortController | O | **부분적** | 낮음 | signal 미전달 |
| FSD 위반 수정 | O | O | 없음 | |
| `any` 타입 제거 | O | 대부분 | 낮음 | |
| NewsItem 통합 | O | O | 없음 | |
| 동적 날짜 | O | **부분적** | 낮음~중간 | 모듈 로드 시 고정 |
| 죽은 코드 삭제 | O | O | 없음 | |
| 검증 통합 | O | O | 없음 | |
| ErrorBoundary | O | O | 없음 | |
| ARIA 라벨 | 부분적 | **부분적** | **중간** | `role="img"` 부적절 |
| Hero 이미지 | 부분적 | **아니오** | **중간** | lazy → LCP 저하 |

---

## 4. 발견된 이슈

### 이슈 1: Hero 이미지 `loading="lazy"` (회귀)

| 항목 | 내용 |
|------|------|
| **파일** | `backtest_fe/src/pages/landing/HeroSection.tsx` L46 |
| **심각도** | 중간 |
| **영향** | LCP(Largest Contentful Paint) 점수 저하, 느린 네트워크에서 이미지 팝인 |
| **원인** | Above-the-fold 이미지에 lazy loading 적용 |
| **수정안** | `loading="lazy"` 제거 또는 `fetchpriority="high"` 추가 |

### 이슈 2: `role="img"` 차트 컨테이너 (접근성 회귀)

| 항목 | 내용 |
|------|------|
| **파일** | `backtest_fe/src/features/backtest/components/shared/ResultBlock.tsx` L30 |
| **심각도** | 중간 |
| **영향** | 스크린 리더가 차트 내부의 인터랙티브 콘텐츠(툴팁, 호버)를 인식 불가 |
| **원인** | `role="img"`가 전체 하위 트리를 단일 이미지로 취급 |
| **수정안** | `role="img"` → `role="figure"` 변경 |

### 이슈 3: AbortController signal 미전달 (불완전 구현)

| 항목 | 내용 |
|------|------|
| **파일** | `useStockData.ts`, `useExchangeRate.ts`, `useVolatilityNews.ts` + `backtestApi.ts` |
| **심각도** | 낮음 |
| **영향** | HTTP 요청이 실제 취소되지 않아 네트워크 대역폭 낭비. 상태 업데이트 가드로는 정상 동작. |
| **원인** | `AbortController.signal`이 `apiClient.get()` 호출에 전달되지 않음 |
| **수정안** | API 함수에 `signal` 파라미터 추가 → `apiClient.get(url, { signal, params })` |

### 이슈 4: `getDefaultDates()` 모듈 로드 시 고정 (설계 개선)

| 항목 | 내용 |
|------|------|
| **파일** | `backtest-form-types.ts` L64, `backtestFormReducer.ts` L301 |
| **심각도** | 낮음 |
| **영향** | 브라우저 탭을 장시간 열어두면 기본 날짜가 과거로 고착 |
| **원인** | `getDefaultDates()`가 `initialBacktestFormState` 모듈 상수에서 1회만 호출 |
| **수정안** | `RESET_FORM` 리듀서에서 `getDefaultDates()` 직접 호출, `useReducer` 초기화 함수에서도 호출 |

---

## 5. 결론

### 전체 평가

- **23개 변경 중 19개**가 문제 유효성, 구현 정확성, 회귀 안전성 모두 검증 통과.
- **4개 이슈** 발견 (2개 중간 위험, 2개 낮은 위험). 모두 프로덕션 크래시를 유발하지는 않으나 성능/접근성에 영향.
- **프로덕션 빌드 및 전체 테스트 스위트에 새로운 실패 없음** (기존 4개 실패 유지).
- BE 에러 마스킹 수정(Change 2-5)은 아키텍처적으로 올바르나, 이전에 숨겨진 에러가 노출될 수 있으므로 **배포 후 에러율 모니터링 권장**.

### 위험도 분류

| 위험도 | 변경 수 | 해당 항목 |
|--------|---------|-----------|
| 없음 | 10 | 패키지 제거, useTheme, FSD, NewsItem, 죽은 코드, 검증 통합, ErrorBoundary, failed_symbols, 예외 통합, time.sleep |
| 낮음 | 9 | asyncio.to_thread, 컨텍스트 매니저, TTLCache, 벡터화, 헬퍼 추출, 코드 스플리팅, API 통합, `any` 제거, AbortController |
| 낮음~중간 | 1 | 동적 날짜 |
| 중간 | 3 | 에러 마스킹 수정, ARIA `role="img"`, Hero `loading="lazy"` |
