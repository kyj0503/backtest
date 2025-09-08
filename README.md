# 백테스팅 시스템

FastAPI + React 기반의 투자 전략 백테스팅 시스템입니다.

## 프로젝트 소개

투자 전략의 과거 성과를 분석할 수 있는 웹 기반 백테스팅 도구입니다. 다양한 기술적 지표를 활용한 전략을 시뮬레이션하고, 리스크와 수익성을 분석할 수 있습니다.

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
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 백그라운드 실행
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 시스템 종료
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### 패키지 관리 및 실행환경
- **백엔드 Python 패키지**는 pip 대신 [uv](https://github.com/astral-sh/uv)로 설치 및 관리합니다.
- requirements.txt는 그대로 사용하며, 도커 빌드 시 uv로 설치됩니다.
- 로컬에서 직접 설치가 필요하다면:
     ```bash
     uv pip install --system -r requirements.txt
     ```
     (uv가 없다면 pip로 설치 가능)

> 모든 빌드와 실행은 도커 환경에서 진행하는 것이 표준입니다.

### 접속 정보
- `frontend`(Vite): http://localhost:5174
- `backend` API base: http://localhost:8001
- `OpenAPI Docs`: http://localhost:8001/api/v1/docs

### 테스트 실행
```bash
# 백엔드 테스트
docker-compose exec backend pytest tests/ -v

# 프론트엔드 테스트
docker-compose exec frontend npm test
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

docs: 배포 가이드 업데이트

## 개발 가이드

### 커밋 메시지 컨벤션
모노리포지토리 환경에 최적화된 커밋 메시지 규칙을 따릅니다.

**기본 형식**: `<type>(<scope>): <description>`

**주요 타입**:
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `refactor`: 코드 리팩터링
- `test`: 테스트 코드
- `docs`: 문서 변경
- `ci`: CI/CD 설정

**스코프 예시**:
- `backend`, `frontend`, `infra`, `docs`
- `backend/api`, `frontend/components` (세부 영역)

**예시**:
```bash
feat(backend): 포트폴리오 최적화 서비스 추가
fix(frontend/components): 차트 렌더링 버그 수정
refactor(backend): Phase 4 DDD 아키텍처 완료
docs: 배포 가이드 업데이트
```

자세한 내용은 [`COMMIT_CONVENTION.md`](COMMIT_CONVENTION.md)를 참조하세요.

## 문서 구조

### 핵심 문서
- [`COMMIT_CONVENTION.md`](COMMIT_CONVENTION.md) - 커밋 메시지 컨벤션 가이드

### 백엔드 문서 (`/backend/doc/`)
백엔드 개발자를 위한 전문 문서
- [`README.md`](backend/doc/README.md) - FastAPI 개발 가이드
- [`CASH_ASSETS.md`](backend/doc/CASH_ASSETS.md) - 현금 자산 처리 구현 상세
- [`TEST_ARCHITECTURE.md`](backend/doc/TEST_ARCHITECTURE.md) - 백엔드 테스트 구조

### 프론트엔드 문서 (`/frontend/doc/`)
프론트엔드 개발자를 위한 전문 문서
- [`README.md`](frontend/doc/README.md) - React 개발 가이드
- [`API_GUIDE.md`](frontend/doc/API_GUIDE.md) - 백엔드 API 연동 가이드 (VITE_API_BASE_URL 지원)
- [`STATE_MANAGEMENT.md`](frontend/doc/STATE_MANAGEMENT.md) - React 상태 관리 패턴
- [`COMPONENTS.md`](frontend/doc/COMPONENTS.md) - 컴포넌트 아키텍처

## 라이선스

이 프로젝트는 GNU AFFERO GENERAL PUBLIC LICENSE 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 확인하세요.
