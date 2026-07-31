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
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, pandas, numpy, backtesting.py |
| **Frontend** | TypeScript, React, Vite, Zustand, Recharts, shadcn/ui, Tailwind CSS |
| **Database** | MySQL 8.0 |
| **Infra** | Docker, Docker Compose, Nginx, Jenkins |
| **Test** | Pytest (BE), Vitest, React Testing Library, Playwright (FE) |

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
│   ├── src/                # 소스 코드
│   ├── __tests__/          # 테스트 코드
│   └── Dockerfile          # 프로덕션 Docker 이미지
├── database/               # DB 스키마 및 초기화 스크립트
├── compose.dev.yaml        # 개발용 Docker Compose
├── Jenkinsfile             # CI/CD 파이프라인
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
pytest tests/unit/test_backtest.py -v
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
```

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

### 자동 Push (Jenkins)

`main` 브랜치에 Push하면 Jenkins가 자동으로:
1. Backend/Frontend 이미지 빌드
2. GHCR에 Push (`latest` + 빌드 번호 태그)
3. home-server 배포 트리거

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
