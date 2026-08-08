# Backtest - 트레이딩 전략 백테스팅 플랫폼

주식, 암호화폐 등 다양한 자산에 대한 투자 전략을 과거 데이터로 검증하고, 포트폴리오의 성과를 분석하여 데이터 기반의 합리적인 의사결정을 돕는 플랫폼입니다.

## 주요 기능

- **단일 종목 백테스트**: SMA, RSI 등 투자 전략 적용 및 성과 분석
- **포트폴리오 백테스트**: 여러 자산 조합의 과거 성과 시뮬레이션
- **자산 분배 전략**: 정적/동적 가중치 전략 테스트
- **정기 투자 (DCA) 시뮬레이션**: 적립식 투자 전략 성과 분석
- **리밸런싱 전략**: 주기적 자산 비중 조절 효과 검증
- **상세 분석 리포트**: 수익률, 변동성, 샤프 지수 등 통계 지표 제공

---

## 기술 스택

| 구분 | 기술 |
|:-----|:-----|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, pandas, numpy, backtesting.py 0.3.3 |
| **Frontend** | TypeScript 5, React 19, Vite 7, React hooks (`useState`/`useReducer`) + localStorage, Recharts 3, React Router 7, shadcn/ui, Tailwind CSS 4 |
| **Database** | MySQL 8.0 |
| **Infra** | Docker, Docker Compose, Nginx, Jenkins (`home-server`에서 중앙 관리) |
| **Test** | Pytest (BE), Vitest 4, React Testing Library, Playwright (FE) |

---

## 프로젝트 구조

```
backtest/
├── backtest_be_fast/       # Backend (FastAPI)
│   ├── app/                # 애플리케이션 코드
│   ├── tests/              # 테스트 코드
│   ├── Dockerfile          # 프로덕션 Docker 이미지
│   └── requirements.txt    # Python 의존성
├── backtest_fe/            # Frontend (React + Vite)
│   ├── src/                # 소스 코드 (테스트는 각 모듈 옆 __tests__/에 위치)
│   ├── e2e/                # Playwright E2E
│   └── Dockerfile          # 프로덕션 Docker 이미지 (test 스테이지 포함)
├── database/               # DB 스키마 및 초기화 스크립트
├── compose.dev.yaml        # 개발용 Docker Compose
└── README.md
```

---

## 네이티브 환경에서 실행

### Backend

```bash
cd backtest_be_fast

# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일 수정 (DB 연결 정보 등)

# 4. 서버 실행
python run_server.py
# 또는
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd backtest_fe

# 1. 의존성 설치
npm install

# 2. 개발 서버 실행
npm run dev
```

**접속 URL**
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

---

## 네이티브 환경에서 테스트

### Backend 테스트

```bash
cd backtest_be_fast

# 전체 테스트 실행
pytest

# 단위 테스트만 실행
pytest tests/unit

# 커버리지 리포트
pytest --cov=app --cov-report=html

# 특정 테스트 파일 실행
pytest tests/unit/test_backtest_engine.py -v
```

### Frontend 테스트

```bash
cd backtest_fe

# 전체 테스트 실행
npm test

# Watch 모드
npm run test:watch

# UI 모드로 테스트
npm run test:ui

# E2E 테스트 (Playwright)
npm run test:e2e
```

---

## Docker 환경에서 실행

```bash
# 0. 환경변수 설정 (저장소 루트의 .env를 compose가 참조)
cp .env.example .env
# .env 파일 수정 (네이버 API 키 등)

# 1. 개발용 컨테이너 빌드 및 실행
docker compose -f compose.dev.yaml up -d --build

# 2. 로그 확인
docker compose -f compose.dev.yaml logs -f

# 3. 특정 서비스 로그
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# 4. 서비스 중지
docker compose -f compose.dev.yaml down

# 5. 볼륨 포함 완전 삭제
docker compose -f compose.dev.yaml down -v
```

**접속 URL**
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

---

## Docker 환경에서 테스트

### Backend 테스트

```bash
# 전체 테스트
docker compose -f compose.dev.yaml exec backtest-be-fast pytest

# 단위 테스트
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit

# 커버리지
docker compose -f compose.dev.yaml exec backtest-be-fast pytest --cov=app
```

### Frontend 테스트

```bash
# 전체 테스트
docker compose -f compose.dev.yaml exec backtest-fe npm test

# UI 모드
docker compose -f compose.dev.yaml exec backtest-fe npm run test:ui

# 린트 및 타입 체크
docker compose -f compose.dev.yaml exec backtest-fe npm run lint
docker compose -f compose.dev.yaml exec backtest-fe npm run type-check       # 프로덕션 코드
docker compose -f compose.dev.yaml exec backtest-fe npm run type-check:test  # 테스트 코드
```

### CI 게이트를 그대로 재현

```bash
docker build --target test ./backtest_fe        # lint → type-check ×2 → vitest
docker build --target test ./backtest_be_fast   # pytest tests/unit
```

현재 기준선은 BE 189건(`tests/unit`), FE 112건이며 모두 통과합니다. 실패가 보이면 회귀입니다. (BE에는 이 외에 DB가 필요한 `tests/integration` 스위트가 별도로 있으며, Quality Gate에는 포함되지 않습니다.)

---

## GHCR에 이미지 Push

### 수동 Push

```bash
# 1. GHCR 로그인
echo $GITHUB_TOKEN | docker login ghcr.io -u kyj0503 --password-stdin

# 2. Backend 이미지 빌드 및 Push
docker build --platform linux/amd64 -t ghcr.io/kyj0503/backtest-be:latest ./backtest_be_fast
docker push ghcr.io/kyj0503/backtest-be:latest

# 3. Frontend 이미지 빌드 및 Push
docker build --platform linux/amd64 -t ghcr.io/kyj0503/backtest-fe:latest ./backtest_fe
docker push ghcr.io/kyj0503/backtest-fe:latest
```

### 중앙 CI/CD (Jenkins)

Backend와 Frontend 파이프라인은 각각 아래 경로에서 관리합니다.

- `home-server/cicd/jenkins/pipeline/backtest-be/`
- `home-server/cicd/jenkins/pipeline/backtest-fe/`

Jenkins의 `backtest-be`, `backtest-fe` Job을 수동 실행하고 `APP_ENV`를 선택합니다.
각 Job은 해당 Dockerfile의 `test` 스테이지와 의존성 감사를 통과한 뒤 이미지를 빌드합니다.

- `dev`: `dev` 브랜치를 빌드해 `:dev` 이미지로 Push
- `prod`: `main` 브랜치를 빌드해 `:latest` 이미지로 Push한 뒤 배포 및 헬스 체크

Quality Gate가 실패하면 이미지 빌드와 배포에 도달하지 못합니다. 이 게이트는 **배포**를 막는 것이며 병합 자체를 막지는 않습니다.

---

## 커밋 컨벤션

### 기본 포맷

```
태그(스코프): 제목 (50자 내외)

- 본문 (선택 사항)
```

### 스코프 (Scope)

| 스코프 | 설명 |
|:-------|:-----|
| `be` | Backend 관련 코드 |
| `fe` | Frontend 관련 코드 |
| `common` | 프로젝트 전체 설정 (README, .gitignore 등) |
| `infra` | 배포, Docker, CI/CD 등 |

### 태그 (Type)

| 태그 | 설명 | 예시 |
|:-----|:-----|:-----|
| `feat` | 새로운 기능 추가 | API 개발, 컴포넌트 추가 |
| `fix` | 버그 수정 | 로직 오류, 오타 수정 |
| `docs` | 문서 수정 | README, Swagger, 주석 |
| `style` | 코드 포맷팅 | 들여쓰기, 세미콜론 |
| `refactor` | 코드 리팩토링 | 기능 변경 없이 구조 개선 |
| `test` | 테스트 코드 | 테스트 추가/수정 |
| `chore` | 기타 잡무 | 빌드 설정, 라이브러리 추가 |

### 예시

```
feat(be): 포트폴리오 백테스트 API 구현
fix(fe): 차트 렌더링 오류 수정
docs(common): README 설치 가이드 추가
chore(infra): Docker Compose 설정 최적화
```

---

## 관련 문서

- [Backend 문서](./backtest_be_fast/docs/README.md)
- [Frontend 문서](./backtest_fe/docs/README.md)
- [2026-02-06 개선 변경 로그](./docs/CHANGELOG-improvement-2026-02-06.md) — Phase 1-5 상세 변경 내역
- [2026-02-06 개선 검증 리포트](./docs/VERIFICATION-REPORT-2026-02-06.md) — 독립 검증 및 회귀 분석
- [코드베이스 분석 리포트](./docs/improvement_analysis.md) — 2026-02-06 시점 초기 분석
- [nginx-gateway DNS 캐싱 이슈](./docs/ISSUE-nginx-gateway-dns-caching.md) — 미해결 이슈 (home-server 저장소 조치 필요)
