# Copilot Instructions - Backtest Platform

이 프로젝트는 FastAPI 기반 백엔드(`backtest_be_fast`)와 React/TypeScript 프론트엔드(`backtest_fe`)로 구성된 금융 백테스팅 플랫폼입니다.

## Architecture Overview

### Backend (FastAPI)
- **Entry Point**: `app/main.py` - CORS 설정, API 라우터 등록, 헬스체크
- **API Structure**: `/api/v1` prefix, single unified backtest endpoint pattern
- **Core Library**: `backtesting.py` - 외부 백테스팅 라이브러리 (Monkey Patch 필요)
- **Data Source**: Yahoo Finance via `yfinance` + MySQL 캐싱 (`database/schema.sql`)

### Frontend (React/TypeScript)
- **Build Tool**: Vite with HMR, API proxy to backend (`/api/v1/*`)
- **UI Framework**: Radix UI components, Tailwind CSS, Recharts for visualization
- **Routing**: React Router - `/` (Home), `/backtest` (Portfolio)
- **State**: React Hook Form + Zod validation, local state management

### Development Environment
- **Always use Docker Compose**: `docker compose -f compose.dev.yaml up -d --build`
- Backend: http://localhost:8000 (API docs at `/api/v1/docs`)
- Frontend: http://localhost:5173 (proxies API calls to backend)
- Hot reload enabled for both services via volume mounts

## Critical Patterns

### 1. Repository Pattern (Backend)
모든 데이터 접근은 repository를 통해서만 수행:
```python
from app.repositories import data_repository  # Singleton instance
data = await data_repository.get_stock_data(ticker, start_date, end_date)
```
- `YFinanceDataRepository`: 실제 데이터 소스 (default)
- `MockDataRepository`: 테스트용
- Factory pattern으로 생성 (`DataRepositoryFactory`)

### 2. Strategy Pattern (Backtesting)
전략은 `backtesting.Strategy`를 상속, `init()`과 `next()` 메서드 구현:
```python
class MyStrategy(Strategy):
    def init(self):
        self.sma = self.I(SMA, self.data.Close, 20)  # Indicator setup
    
    def next(self):
        if crossover(self.data.Close, self.sma):
            self.buy()
```
- 모든 전략은 `app/strategies/` 디렉토리
- `strategy_service.py`에서 검증 및 Factory 패턴 사용
- 지원 전략: `sma_strategy`, `rsi_strategy`, `bollinger_strategy`, `macd_strategy`, `ema_strategy`, `buy_hold_strategy`

### 3. Service Layer Architecture
- **backtest_service**: 단일 종목 백테스트 실행, `backtesting.py` 호환성 패치 적용
- **portfolio_service**: 다중 종목, DCA/Lump-sum 투자, 리밸런싱
- **validation_service**: 요청 검증, 날짜 범위/파라미터 유효성
- **chart_data_service**: 프론트엔드용 차트 데이터 변환 (JSON 직렬화)
- 모든 서비스는 싱글톤 인스턴스로 import (e.g., `from app.services.backtest_service import backtest_service`)

### 4. Pydantic Models (API 계약)
- **Request**: `app/schemas/requests.py` - `BacktestRequest`, `StrategyType` enum
- **Response**: `app/schemas/responses.py` - 프론트엔드가 기대하는 정확한 형태
- **Internal**: `app/schemas/schemas.py` - `PortfolioBacktestRequest`, DB 모델
- 날짜는 `Union[date, str]` + `field_validator`로 자동 파싱

### 5. Frontend API Layer
- `src/features/backtest/api/backtestApi.ts` - 모든 API 호출의 중앙화
- Axios 기반, 에러 처리 (network, validation, server, rate_limit 타입 구분)
- 환경변수: `VITE_API_BASE_URL` (기본값 `/api`)

## Essential Commands

### Development
```bash
# Start all services
docker compose -f compose.dev.yaml up -d --build

# View backend logs
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# Stop services
docker compose -f compose.dev.yaml down
```

### Testing (Backend)
```bash
# Run all tests
docker compose -f compose.dev.yaml exec backtest-be-fast pytest

# Run specific test categories (pytest markers)
pytest tests/unit -v              # Fast, isolated
pytest tests/integration -v       # External dependencies
pytest tests/e2e -v              # Full workflow
pytest -m "not slow" -v          # Skip slow tests
pytest -m "db" -v                # Database-dependent
```

### Frontend
```bash
# Inside container or locally
npm run dev              # Development server
npm run test            # Vitest unit tests
npm run test:run        # Run once (CI)
npm run lint:fix        # ESLint auto-fix
npm run type-check      # TypeScript validation
```

## Key Configuration

### Environment Variables
- `compose.dev.yaml`에서 `.env` 파일 참조
- Backend: `DEBUG`, `LOG_LEVEL`, `DATABASE_URL`, `NAVER_CLIENT_ID/SECRET`
- Frontend: `VITE_API_BASE_URL`, `API_PROXY_TARGET`, `FASTAPI_PROXY_TARGET`

### Settings Singleton
- `app/core/config.py` - Pydantic Settings로 환경변수 로드
- `settings` 객체는 전역에서 import: `from app.core.config import settings`
- CORS origins은 JSON 배열 또는 쉼표 구분 문자열

## Database (MySQL)
- **Schema**: `database/schema.sql`
- **Tables**: `stocks`, `daily_prices`, `stock_news`
- `yfinance` 데이터를 캐싱하여 API 호출 최소화
- SQLAlchemy 없음 - 직접 pymysql 또는 pandas로 처리 (`services/yfinance_db.py`)

## Common Gotchas

### backtesting.py Compatibility
- **Timedelta 버그**: `services/backtest_service.py`에 Monkey Patch 필수 (`_patch_backtesting_stats()`)
- 반드시 `bt = Backtest(...)` 생성 전에 패치 적용
- pandas Timedelta와 float 비교 오류 발생 시 기본 통계 반환

### API Response Serialization
- pandas Timestamp → `isoformat()` 또는 `strftime('%Y-%m-%d')`
- numpy types → `.item()` 또는 `float()`
- Decimal → `float()` 변환 필수 (JSON 직렬화)
- `utils/serializers.py`에 헬퍼 함수 존재

### Frontend Proxy Configuration
- `vite.config.ts`의 proxy는 개발 환경 전용
- Docker 내부에서는 서비스 이름 사용: `http://backtest-be-fast:8000`
- 로컬 개발 시: `http://localhost:8000`

### Import Patterns
- Backend: `from app.services.x import service_name` (모듈에서 싱글톤 import)
- 절대 경로 사용: `from app.repositories import data_repository`
- Frontend: `@/` alias는 `src/` 디렉토리를 가리킴

## Testing Philosophy
- **Unit tests** (`tests/unit/`): 빠르고 독립적, 외부 API 호출 없음
- **Integration tests** (`tests/integration/`): DB/API 의존성 포함
- **E2E tests** (`tests/e2e/`): 전체 워크플로우 검증
- Fixtures: `tests/fixtures/` - backtest, portfolio 샘플 데이터
- Conftest: `tests/conftest.py` - 공유 fixtures 및 설정

## 문서화 스타일
- 모든 모듈 docstring에 **역할**, **주요 기능**, **의존성**, **연관 컴포넌트** 명시
- 함수는 Google style docstring (Args, Returns, Raises)
- 한글로 작성된 기술 문서 유지

## When Modifying

### Adding a New Strategy
1. Create `app/strategies/new_strategy.py` - inherit from `Strategy`
2. Add to `app/services/strategy_service.py` - factory method
3. Update `app/schemas/requests.py` - `StrategyType` enum
4. Update frontend `constants/strategies.ts`

### Adding New Endpoint
1. Create endpoint in `app/api/v1/endpoints/`
2. Register router in `app/api/v1/api.py`
3. Create request/response models in `app/schemas/`
4. Add API client in `backtest_fe/src/features/*/api/`

### Database Changes
1. Update `database/schema.sql` manually
2. Modify `services/yfinance_db.py` for data access
3. No migrations - manual SQL execution required
