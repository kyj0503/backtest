# 백테스팅 시스템

FastAPI + React 기반의 투자 전략 백테스팅 시스템입니다.

## 프로젝트 소개

투자 전략의 과거 성과를 분석하는 웹 기반 백테스팅 도구입니다. 다양한 기술적 지표로 전략을 시뮬레이션하고 리스크와 수익성을 분석합니다.

### 주요 특징
- 포트폴리오 및 단일 종목 백테스트 지원
- 현금 자산을 포함한 리스크 관리
- 실시간 주식 데이터 연동 (yfinance API)
- 종목별 뉴스 검색 기능 (네이버 검색 API)
- 시각적 차트 및 성과 분석

### 시스템 구조
```
Frontend (React + TypeScript) ←→ Backend (FastAPI + Python) ←→ Database (MySQL)
     ↓                                    ↓                        ↓
Vite + Tailwind CSS             backtesting.py               yfinance API
```

## 빠른 시작


### 개발 환경 실행
```bash
# 개발 환경 시작 (Windows PowerShell + Docker Desktop)
docker compose -f compose.yml -f compose/compose.dev.yml up --build

# 백그라운드 실행
docker compose -f compose.yml -f compose/compose.dev.yml up -d

# 시스템 종료
docker compose -f compose.yml -f compose/compose.dev.yml down
```

### 패키지 관리 및 실행환경
- **백엔드 Python 패키지**는 pip 대신 [uv](https://github.com/astral-sh/uv)로 설치 및 관리합니다.
- requirements.txt는 그대로 사용하며, 도커 빌드 시 uv로 설치됩니다.
- 로컬에서 직접 설치가 필요하다면:
     ```bash
     uv pip install --system -r requirements.txt
     ```
     (uv가 없다면 pip로 설치 가능)

> 모든 빌드와 실행은 Docker 환경에서 진행하는 것이 표준입니다.

### 접속 정보
- `frontend`(Vite): http://localhost:5174
- `backend` API base: http://localhost:8001
- `OpenAPI Docs`: http://localhost:8001/api/v1/docs

### 테스트 실행
```bash
# 백엔드 테스트
docker compose exec backend pytest tests/ -v

# 프론트엔드 테스트
docker compose exec frontend npm test
```

## 기술 스택
### 프론트엔드
- **React 18** + TypeScript - 현대적 웹 UI 개발
- **Vite** - 고속 빌드 도구
- **Tailwind CSS** - 유틸리티 기반 CSS 프레임워크
- **Recharts** - 데이터 시각화

### 백엔드
- **FastAPI** + Python - 고성능 API 서버
- **Pydantic V2** - 데이터 검증 및 직렬화
- **MySQL** - 주가 데이터 캐시
- **backtesting.py** - 백테스트 엔진
- **uv** - Python 패키지 초고속 설치/관리 도구 (pip 대체)

### 인프라
- **Docker** + Docker Compose - 컨테이너 환경
- **Jenkins** - CI/CD 파이프라인
- **nginx** - 프로덕션 웹 서버

## 개발 가이드 / 문서

- 문서 인덱스: `docs/README.md`
- 시작 가이드: `docs/GETTING_STARTED.md`
- 테스트 아키텍처: `docs/TEST_ARCHITECTURE.md`
- DDD 개요: `docs/DDD_ARCHITECTURE.md`
- API 연동: `docs/API_GUIDE.md`
- 프론트 구조: `docs/STATE_MANAGEMENT.md`, `docs/COMPONENTS.md`
- 운영 런북: `docs/RUNBOOK.md`
- TODO/Roadmap: `docs/TODO.md`

커밋/기여 규칙은 루트의 [`COMMIT_CONVENTION.md`](COMMIT_CONVENTION.md), [`CONTRIBUTING.md`](CONTRIBUTING.md)를 참고하세요. 커밋 시 `.githooks/pre-commit`이 `scripts/verify-before-commit.sh`를 실행하여 빌드/테스트/헬스체크를 수행합니다.

## 라이선스

이 프로젝트는 GNU AFFERO GENERAL PUBLIC LICENSE 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 확인하세요.
