# AGENTS Guide

이 문서는 자율 에이전트가 이 모노레포 기반 포트폴리오 백테스팅 서비스를 이해하고 안전하게 작업하기 위한 핵심 정보를 제공합니다. 상세한 배경 지식은 `docs/` 내 문서에 있지만, 이 가이드는 에이전트가 빠르게 구조를 파악하고 의사결정을 내릴 수 있도록 요약과 가드레일을 제공합니다.

## 미션 요약
- **서비스 구성**: FastAPI 백엔드 + React(TS, Vite) 프론트엔드 + MySQL 캐시 + Redis. Docker Compose로 로컬/CI/운영 환경을 분리.
- **핵심 기능**: 단일 종목 및 포트폴리오 백테스트, 전략 파라미터 최적화, 차트/지표 시각화, 커뮤니티/인증, yfinance 데이터 캐싱, 이벤트 기반 알림.
- **AI 작업 기본 수칙**:
  - 사용자 데이터베이스나 외부 API(yfinance, Naver) 호출은 비용과 레이트리밋이 있으니 불필요한 반복 호출을 피하세요.
  - `node_modules/`, `dist/` 등 빌드 산출물은 수정하지 않습니다.
  - 변경 전후로 `scripts/test-runner.sh` 또는 서비스별 테스트를 실행하여 회귀를 조기에 감지하세요.

## 모노레포 지도
경로 기준은 리포지토리 루트입니다.

| 경로 | 역할 |
| --- | --- |
| `backend/app/` | FastAPI 애플리케이션. `main.py`가 엔트리이며, `api/`, `services/`, `domains/`, `events/`로 계층화됨. |
| `backend/strategies/` & `backend/app/strategies/implementations/` | backtesting.py 기반 전략 구현. 새 전략 추가 시 이 모듈과 팩토리를 확장. |
| `frontend/src/` | React 18 + TypeScript UI. `pages/`, `components/`, `hooks/`, `services/`로 분리. `pages/BacktestPage.tsx`가 주요 화면. |
| `database/` | MySQL 스키마 SQL (`schema.sql` 사용자/커뮤니티, `yfinance.sql` 시세 캐시). |
| `docs/` | 운영/개발/아키텍처 등 장문의 가이드 모음. |
| `compose.yml` & `compose/*.yml` | 기본 Compose 정의 + dev/prod/test 오버레이. |
| `scripts/` | `test-runner.sh`(통합 테스트 파이프라인), `remote_deploy.sh`(원격 배포). |
| `compose/compose.dev.yml` | 개발 모드 설정. 프론트엔드(포트 5174)와 백엔드(포트 8001) 핫리로드, Redis 포함. |

## 백엔드 개요 (`backend/app`)
- **엔트리포인트**: `main.py` → `FastAPI` 인스턴스 생성, `api.v1` 라우터 등록, CORS/전역 예외 설정.
- **레이어**:
  - `api/v1/endpoints/`: HTTP 라우트. 예) `backtest.py`는 `/api/v1/backtest/*` 엔드포인트를 제공하며 DB 캐시 → yfinance 순으로 데이터를 조회합니다.
  - `services/`: 도메인 서비스. `backtest_service.py`는 Repository/Factory 패턴으로 엔진, 최적화, 차트 생성을 조합. `portfolio_service.py`는 여러 자산, 현금, DCA 계산을 담당.
  - `repositories/` & `infrastructure/`: DB, 캐시(현재 MySQL 캐시 활용) 접근.
  - `events/`: 이벤트 버스(`event_bus`)와 핸들러(`backtest_handlers`, `portfolio_handlers`)가 메트릭/알림을 축적.
  - `domains/`: 점진적 DDD 모델 정의. Command/Query, 값 객체 등이 위치.
  - `cqrs/`: 명령/조회 분리 모델.
- **주요 엔드포인트** (`backend/app/api/v1/endpoints/backtest.py` 기준):
  - `POST /api/v1/backtest/execute`: 단일/포트폴리오 요청을 자동 판별해 실행, 벤치마크·환율 보강 후 표준 응답 리턴.
  - `POST /api/v1/backtest/run` & `/chart-data`: 레거시 단일 종목 백테스트 + Recharts용 데이터.
  - `POST /api/v1/backtest/portfolio`: 포트폴리오 백테스트.
  - `GET /api/v1/backtest/history|metrics|notifications|portfolio-analytics|portfolio-alerts`: 이벤트 시스템 및 히스토리 조회.
  - `GET /api/v1/backtest/stock-volatility-news/{ticker}`: 급등락 뉴스 및 `load_ticker_data` 활용.
- **전략 확장 포인트**:
  - `app/strategies/implementations/*`: Bollinger, RSI, MACD 등 개별 전략 클래스.
  - `app/factories/strategy_factory.py`: 새로운 전략을 등록하고 파라미터 검증 로직 추가.
  - `frontend/src/constants/strategies.ts`: 프론트엔드 전략 선택 UI에 전략 메타데이터 추가.
- **데이터 소스**:
  - `services/yfinance_db.py`: `DATABASE_URL`(기본 `mysql+pymysql://root:password@127.0.0.1:3306/stock_data_cache`)로 MySQL 캐시에 접근. `load_ticker_data` → pandas DataFrame 반환.
  - `utils/data_fetcher.py`: yfinance 호출, 재시도, InvalidSymbol/RateLimit 예외 정의.
- **구성/환경 변수**: `core/config.py`의 `Settings`가 `.env` 로드. 주요 키는 `DATABASE_URL`, `BACKEND_CORS_ORIGINS`, `REDIS_URL`, `SECRET_KEY`, `LOG_LEVEL` 등.
- **의존성**: `requirements.txt`에 FastAPI, SQLAlchemy, yfinance, backtesting.py, redis, pydantic v2 등.

## 프론트엔드 개요 (`frontend/src`)
- **엔트리포인트**: `main.tsx` → `App.tsx`. 라우팅과 테마 적용.
- **주요 페이지**: `pages/BacktestPage.tsx`가 백테스트 폼/결과를 하나의 페이지로 제공.
- **상태 관리**: 로컬 상태 + 커스텀 훅 (`hooks/useBacktest.ts`, `hooks/useBacktestForm.ts`). Context 최소 사용.
- **API 연동**: `services/api.ts`의 `BacktestApiService`가 통합 백테스트(`/api/v1/backtest/execute`) 호출, 에러 유형 분류, 헬퍼 제공.
- **UI 컴포넌트**: `components/ui/`는 shadcn/ui 래퍼. `components/BacktestForm.tsx`, `BacktestResults.tsx`가 핵심.
- **전략/상수**: `constants/strategies.ts`에 전략 설명, 파라미터, 자산 타입, 리밸런싱 옵션 정의.
- **빌드/개발**: `vite.config.ts`가 `API_PROXY_TARGET` 환경변수 기반 프록시(`http://localhost:8001` 기본)를 설정. `npm run dev`(Vite), `npm run test`(Vitest) 등.

## 데이터 & 외부 연동
- **MySQL**: 두 개의 스키마.
  - `database/schema.sql`: 사용자, 커뮤니티, 백테스트 히스토리 관리.
  - `database/yfinance.sql`: 종목 기본 정보, `daily_prices`, 배당, 분할, 환율, 캐시 메타데이터.
- **Redis**: 채팅(WebSocket) 및 이벤트 큐 용도. Compose에서 `redis:7-alpine` 제공.
- **외부 API**:
  - yfinance: 시세 데이터. 과도한 호출 시 `YFinanceRateLimitError` 발생 → 백엔드에서 사용자 메시지 매핑.
  - 네이버 뉴스: `naver_news` 엔드포인트. `NAVER_CLIENT_ID/SECRET` 필요.

## 실행 & 개발 절차
1. **환경 변수 준비**: 루트에 `.env` 생성 (`docs/DEVELOPMENT_GUIDE.md` 참고). 최소 `DATABASE_URL`, `BACKEND_CORS_ORIGINS`.
2. **Docker Compose** (권장):
   ```bash
   docker compose -f compose.yml -f compose/compose.dev.yml up --build
   # 백그라운드 실행
   docker compose -f compose.yml -f compose/compose.dev.yml up -d
   ```
   - 백엔드: `http://localhost:8001`
   - 프론트엔드: `http://localhost:5174`
3. **로컬 직접 실행(선택)**:
   - 백엔드: `cd backend && uv pip install --system -r requirements.txt && python run_server.py`
   - 프론트엔드: `cd frontend && npm ci && npm run dev`
4. **DB 마이그레이션 없음**: 초기 세팅은 SQL 스크립트를 수동 실행해야 합니다 (MySQL 8.0 가정).

## 테스트 & 품질 게이트
- **통합 스크립트**: `./scripts/test-runner.sh <unit|integration|e2e|all|lint|coverage>`
  - Docker 이미지 빌드 → (필요 시) `compose/compose.test.yml`로 MySQL/Redis 띄움 → pytest/Vitest 실행.
- **백엔드 개별 테스트**: `docker compose exec backend-test python -m pytest ...` 또는 로컬 `pytest` (`tests/unit`, `tests/integration`, `tests/e2e`).
- **프론트엔드 테스트**: `npm run test` / `npm run test:run` (Vitest). Radix UI Select 등 커스텀 컴포넌트는 클릭 이벤트 기반 테스트 필요 (`README.md` 참고).
- **정적 분석**: `test-runner.sh lint`가 `black`, `isort`, `npm run lint` 실행. Type check는 `npm run type-check` 별도.

## 관측성 & 운영
- **헬스체크**:
  - 백엔드 루트: `GET /health` (`backend/app/main.py`). 라우터 로딩 여부 확인.
  - 백테스트 모듈: `GET /api/v1/backtest/health` → yfinance 연결 검증.
- **모니터링 데이터**: 이벤트 시스템(`events/event_system.py`)이 백테스트 메트릭·알림을 메모리에 유지. API로 조회 가능.
- **로그**: Python `logging` 기본 설정(`INFO`). Compose 환경에서는 stdout으로 노출. 백엔드 예외는 전역 핸들러가 500 응답과 메시지를 생성.
- **배포 스크립트**: `scripts/remote_deploy.sh <backend-image> <frontend-image> [deploy-path]`
  - `docker-compose.yml` 이미지 태그 치환 → `docker compose up -d` → `/health` 등 간단한 헬스체크 → 실패 시 백업 복원.

## 작업 가드레일 (AI 체크리스트)
- **환경/시크릿**: `.env`에 민감 정보가 있으므로 노출 금지. 코드에서 하드코딩된 비밀번호(`root:password`)는 개발용 기본값이므로 운영에선 교체 전제.
- **데이터 호출**: yfinance 호출은 비용이 있으니 테스트 시 `load_ticker_data`를 우선 사용하거나 stub/fixture를 고려.
- **DB 접근**: `services/yfinance_db.py`는 기본적으로 로컬 MySQL을 사용하므로 통합 테스트 시 Compose 환경을 우선 사용하세요. 직접 로컬에 쓰지 않도록 `DATABASE_URL` 확인.
- **전략 추가**: 백엔드/프론트 양쪽에 전략 정의를 모두 반영해야 UI와 API가 일관됩니다.
- **포트폴리오 한도**: 백엔드 검증은 최대 10종목, 현금 자산 특수 케이스를 고려합니다. 폼 검증과 서비스 검증을 동시에 수정해야 합니다.
- **채팅/Redis**: `REDIS_URL`이 필요하며, 테스트 중 Redis 의존 기능을 호출하면 Redis 컨테이너가 실행 중인지 확인.
- **노드 버전**: `frontend/package.json`은 Node >=16. 변경 작업 시 CI와 호환되는 버전 유지.
- 커밋 메시지는 CONTRIBUTING.md 문서를 참고해 작성한다.
- 모든 빌드, 실행, 테스트는 도커 환경 내부에서 진행한다.

## 참고 문서
- `docs/ARCHITECTURE_GUIDE.md`: 전체 아키텍처, 도메인, 이벤트 시스템 상세.
- `docs/DEVELOPMENT_GUIDE.md`: 환경 세팅, API 목록, 프론트/백엔드 디렉토리 설명.
- `docs/TESTING_GUIDE.md`: 테스트 전략과 모킹 지침.
- `docs/RUNBOOK.md`, `docs/OPERATIONS_GUIDE.md`: 장애 대응, 운영 체크리스트.
- `docs/API_GUIDE.md`: 엔드포인트별 스펙.

에이전트는 위 정보를 바탕으로 변경 범위를 명확히 정의하고, 관련 테스트를 실행한 뒤 로그/알림 시스템까지 확인하는 것을 권장합니다.
