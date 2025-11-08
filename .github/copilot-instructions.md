# Backtest - AI Coding Instructions

## 프로젝트 개요

**라고할때살걸** - 트레이딩 전략 백테스팅 플랫폼 (v1.6.10)
- **Backend**: FastAPI + Python 3.x, backtesting.py 라이브러리 래퍼
- **Frontend**: React 18 + TypeScript + Vite, shadcn/ui 컴포넌트
- **배포**: Docker Compose 기반 개발/프로덕션 환경

## 아키텍처 핵심

### 백엔드 서비스 레이어 구조
```
API Layer (app/api/v1/) 
  → Service Layer (app/services/*_service.py)
  → Repository Layer (app/repositories/)
  → Strategy Layer (app/strategies/)
```

**핵심 서비스 체인**:
1. `backtest_service.py` - 단일 종목 백테스트 오케스트레이션
2. `portfolio_service.py` - 다중 종목 포트폴리오, DCA 전략, 리밸런싱
3. `backtest_engine.py` - backtesting.py 래퍼, 실제 백테스트 실행
4. `chart_data_service.py` - 프론트엔드용 차트 데이터 직렬화
5. `strategy_service.py` - 전략 클래스 관리 및 파라미터 검증

**싱글톤 패턴**: 모든 서비스는 모듈 레벨 인스턴스로 제공 (예: `strategy_service`, `validation_service`)

### 통화 정책 (중요!)
- **DB 저장**: 원본 통화 그대로 (KRW, JPY, EUR, GBP 등)
- **백테스트 계산**: 모든 가격을 USD로 변환 (13개 주요 통화 지원)
  - 직접 환율: `KRW=X`, `JPY=X` (1 USD = X 통화)
  - USD 환율: `EURUSD=X`, `GBPUSD=X` (1 통화 = X USD)
- **프론트엔드 표시**: 개별 종목 시장 데이터는 원본 통화, 백테스트 결과는 USD

### 프론트엔드 아키텍처
```
src/
  features/         # 기능별 모듈 (backtest, portfolio 등)
    backtest/
      api/          # API 호출 로직
      components/   # 백테스트 UI 컴포넌트
      hooks/        # 커스텀 훅
  shared/           # 공통 리소스
    ui/             # shadcn/ui 컴포넌트 (@/shared/ui/*로 임포트)
    hooks/          # 전역 훅 (useTheme 등)
    api/            # 공통 API 유틸
  pages/            # 라우트 페이지
  themes/           # 테마 JSON 파일 (4개 지원)
```

**라우팅**: `react-router-dom` 사용, `/backtest` 메인 페이지 (레거시 redirect 존재)

## CRITICAL: Async/Sync 경계 관리 (Race Condition 방지)

**중요도**: CRITICAL - 백테스트 결과 정확성에 직접 영향

### 문제 패턴

FastAPI는 async 프레임워크이지만, yfinance, SQLAlchemy 등 많은 라이브러리는 동기 I/O를 사용합니다. 동기 함수를 async 컨텍스트에서 직접 호출하면 **레이스 컨디션**이 발생하여 첫 실행 시 데이터 손상이 발생합니다.

**증상**:
- 첫 실행: 잘못된 결과 (그래프 급락, 통계 오류)
- 두 번째 실행 (동일 파라미터): 정상 결과
- 새로운 종목/날짜 범위에서 반복 발생

### 필수 규칙

**NEVER: 동기 I/O를 async 함수에서 직접 호출**
```python
# WRONG - 이벤트 루프 블로킹, 레이스 컨디션 발생
async def process():
    data = load_ticker_data(ticker, start, end)  # 동기 함수
    return data
```

**ALWAYS: asyncio.to_thread()로 래핑**
```python
# CORRECT - 스레드 풀에서 안전하게 실행
import asyncio

async def process():
    data = await asyncio.to_thread(
        load_ticker_data, ticker, start, end
    )
    return data
```

### 주의해야 할 함수들

**데이터베이스 호출** (동기):
- `yfinance_db.load_ticker_data()`
- `yfinance_db.save_ticker_data()`
- `yfinance_db.get_ticker_info_from_db()`

**외부 API 호출** (동기):
- `data_fetcher.get_stock_data()`
- `yf.Ticker().history()`
- `yf.download()`

**모두 `asyncio.to_thread()`로 래핑 필수!**

### 체크리스트

코드 작성/리뷰 시 반드시 확인:
- [ ] async 함수 내부의 모든 I/O 호출이 `await`로 시작하는가?
- [ ] 동기 I/O 함수가 `asyncio.to_thread()`로 래핑되었는가?
- [ ] 정적 메서드/일반 함수가 async 컨텍스트에서 호출되는 경우, 내부에 동기 I/O가 없는가?
- [ ] 리팩토링 시 async/sync 경계가 유지되는가?

### 참고 문서

상세 분석: `backtest_be_fast/docs/race_condition_reintroduced_analysis.md`

## 코드 컨벤션

### Python 백엔드

1. **독스트링 패턴 (필수)**: 모든 모듈, 클래스, 핵심 함수에 구조화된 독스트링
   ```python
   """
   [모듈명/기능명]

   **역할**:
   - 핵심 책임 1
   - 핵심 책임 2

   **주요 기능**:
   1. method_name(): 설명

   **의존성**:
   - app/path/to/module.py: 설명

   **연관 컴포넌트**:
   - Backend: app/...
   - Frontend: src/...
   """
   ```
   예시: `app/main.py`, `app/services/backtest_engine.py`, `app/strategies/sma_strategy.py`

2. **전략 구현**: `backtesting.Strategy` 상속, `init()`과 `next()` 메서드 필수
   - 파라미터는 클래스 속성으로 정의 (예: `sma_short = 10`)
   - `strategy_service.py`의 `STRATEGY_CLASSES` dict에 등록

3. **에러 핸들링**: `app/core/exceptions.py` 커스텀 예외 사용, 오류 ID 생성

4. **로깅**: 표준 `logging` 모듈, `logger = logging.getLogger(__name__)`
   - INFO: 백테스트 시작/종료, 데이터 로드
   - DEBUG: 데이터 컬럼, 상세 흐름
   - ERROR: 예외 상황

### TypeScript 프론트엔드

1. **임포트 경로**: `@/*` 별칭 사용 (`tsconfig.json` + `vite.config.ts`)
   ```typescript
   import { Button } from '@/shared/ui/button';
   import { useTheme } from '@/shared/hooks/useTheme';
   import { backtestApi } from '@/features/backtest/api/backtestApi';
   ```

2. **shadcn/ui 컴포넌트**: `@/shared/ui/*`에서 임포트 (`components.json` 설정됨)
   - 새 컴포넌트 추가: `npx shadcn@latest add <component-name>`
   - 커스텀 컴포넌트는 `@/components/*` 또는 `@/features/*/components/*`

3. **API 호출**: `fetch` 기반, Vite 프록시 사용 (`/api/v1/backtest` → FastAPI)
   - 에러 핸들링: `ApiError` 타입, status 기반 분류
   - 예시: `src/features/backtest/api/backtestApi.ts`

4. **테마 시스템**: `useTheme()` 훅, JSON 기반 테마 정의 (`src/themes/`)
   - CSS 변수 동적 적용, localStorage 영속화
   - 다크모드 지원 (`dark` 클래스 토글)

## 개발 워크플로우

### 로컬 개발 (Docker Compose 권장)
```bash
# 전체 스택 실행 (hot reload)
docker compose -f compose.dev.yaml up -d --build

# 로그 확인
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# 서비스 중지
docker compose -f compose.dev.yaml down
```

**접근**:
- Frontend: http://localhost:5173 (Vite dev server)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs (Swagger UI)

### 테스트 (Pytest)

**마커 기반 실행** (`pytest.ini` 설정):
```bash
# 유닛 테스트 (빠름)
pytest -m unit

# 통합 테스트
pytest -m integration

# 특정 파일
pytest tests/unit/test_sma_strategy.py -v
```

**픽스처 구조**:
- `tests/conftest.py`: 전역 픽스처 (mock 서비스, 샘플 데이터)
- `tests/fixtures/`: Factory 패턴 테스트 데이터 (`BacktestRequestFactory` 등)

**비동기 테스트**: `asyncio_mode = strict`, `async def test_*` 형식 사용

### 프론트엔드 개발
```bash
cd backtest_fe

# 개발 서버 (Docker 외부)
npm run dev

# 빌드
npm run build

# 테스트 (Vitest)
npm run test
npm run test:ui  # UI 모드
```

## 주요 패턴 및 베스트 프랙티스

### 백테스트 실행 흐름
1. API 요청 → `backtest.py` 엔드포인트
2. `validation_service` → 입력 검증 (날짜 범위, 티커, 전략 파라미터)
3. `backtest_service` or `portfolio_service` → 로직 분기
4. `backtest_engine` → backtesting.py 실행, 통화 변환 (`_convert_to_usd`)
5. `chart_data_service` → 직렬화 (`_serialize_numpy`, datetime → ISO 8601)
6. 응답 반환 (백테스트 결과 + 차트 데이터 + 통계)

### 새 전략 추가 방법
1. `app/strategies/new_strategy.py` 생성
   ```python
   class NewStrategy(Strategy):
       param1 = 10  # 기본값
       
       def init(self):
           self.indicator = self.I(SomeIndicator, self.data.Close, self.param1)
       
       def next(self):
           if self.should_buy:
               self.buy()
           elif self.should_sell:
               self.sell()
   ```

2. `app/schemas/requests.py`에 `StrategyType` Enum 추가

3. `app/services/strategy_service.py`에 등록:
   ```python
   STRATEGY_CLASSES = {
       "new_strategy": NewStrategy,
   }
   ```

4. 프론트엔드 `StrategySelector.tsx`에 UI 추가

### 데이터 직렬화 주의사항
- **Numpy 타입**: `_serialize_numpy()` 함수로 Python 네이티브 타입 변환
- **Datetime**: `.isoformat()` 사용 (ISO 8601 문자열)
- **NaN/Infinity**: `None`으로 치환 또는 제거

### CORS 설정
- `app/core/config.py`의 `backend_cors_origins` 설정 (JSON 배열 또는 쉼표 구분)
- 기본값: `localhost:5173`, `localhost:8000`, 프로덕션 도메인

## 트러블슈팅

### 백엔드 디버깅
- **로그 레벨**: `.env`에서 `LOG_LEVEL=DEBUG` 설정
- **API 문서**: http://localhost:8000/api/v1/docs에서 직접 테스트
- **Health Check**: `GET /health` 엔드포인트로 서버 상태 확인

### 프론트엔드 디버깅
- **HMR 이슈**: `DISABLE_HMR=true` 환경변수로 WebSocket 비활성화
- **Proxy 오류**: `vite.config.ts`의 `FASTAPI_PROXY_TARGET` 확인
- **빌드 경고**: 청크 크기 1MB 초과 시 `manualChunks` 조정

### 테스트 실패
- **비동기 타임아웃**: `pytest-asyncio` 설정 확인
- **Mock 오류**: `tests/conftest.py`의 mock fixture 사용
- **DB 테스트**: `@pytest.mark.db` 마커로 격리

### 중복 종목 차단
- **정책**: 포트폴리오에 같은 종목을 여러 번 추가할 수 없음 (현금 제외)
- **이유**: UI 복잡도 감소, 실제 투자 패턴과 일치, 코드 단순화
- **구현**:
  - 프론트엔드: `backtestFormReducer.ts`의 `validatePortfolio()`에서 중복 검증
  - 백엔드: `app/schemas/schemas.py`의 `PortfolioBacktestRequest.validate_portfolio()`에서 중복 검증
- **대안**: 같은 종목에 더 많은 비중을 주려면 `amount` 또는 `weight`를 조정

## 참고 파일
- 아키텍처: `app/main.py`, `app/api/v1/api.py`
- 핵심 로직: `app/services/portfolio_service.py`, `app/services/backtest_engine.py`
- 설정: `app/core/config.py`, `compose.dev.yaml`
- 테스트: `backtest_be_fast/pytest.ini`, `tests/conftest.py`
- UI: `backtest_fe/components.json`, `src/App.tsx`
