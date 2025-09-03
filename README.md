# 백테스팅 시스템

FastAPI + React 기반의 투자 전략 백테스팅 시스템입니다.

## 프로젝트 소개

투자 전략의 과거 성과를 분석할 수 있는 웹 기반 백테스팅 도구입니다. 다양한 기술적 지표를 활용한 전략을 시뮬레이션하고, 리스크와 수익성을 분석할 수 있습니다.

### 주요 특징
- 포트폴리오 및 단일 종목 백테스트 지원
- 현금 자산을 포함한 리스크 관리
- 실시간 주식 데이터 연동
- 종목별 뉴스 검색 기능
- 시각적 차트 및 성과 분석

### 시스템 구조
```
Frontend (React + TypeScript) ←→ Backend (FastAPI + Python) ←→ Database (MySQL)
     ↓                                    ↓                        ↓
Vite + Bootstrap                 backtesting.py               yfinance API
```

## 빠른 시작

### 개발 환경 실행
```bash
# 개발 환경 시작
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 백그라운드 실행
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 시스템 종료
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### 접속 정보
- **프론트엔드**: http://localhost:5174
- **백엔드 API**: http://localhost:8001
- **API 문서**: http://localhost:8001/docs

### 테스트 실행
```bash
# 백엔드 테스트
docker-compose exec backend pytest tests/ -v

# 프론트엔드 테스트
docker-compose exec frontend npm test
```

## 기술 스택

### 프론트엔드
- React 18 + TypeScript
- Vite (빌드 도구)
- React Bootstrap (UI 프레임워크)
- Recharts (차트 라이브러리)

### 백엔드
- FastAPI + Python
- Pydantic V2 (데이터 검증)
- MySQL (데이터 캐시)
- backtesting.py (백테스트 엔진)

### 인프라
- Docker + Docker Compose
- Jenkins (CI/CD)
- nginx (프로덕션 웹 서버)

## 문서 구조

### 루트 문서 (`/doc/`)
전체 시스템 관점의 통합 문서
- `API_GUIDE.md` - 전체 API 엔드포인트 및 스펙
- `TEST_GUIDE.md` - 종합 테스트 전략 및 실행 방법
- `ARCHITECTURE.md` - 시스템 아키텍처 및 기술 스택 상세
- `DEVELOPMENT_GUIDE.md` - 개발 규칙 및 전략 개발 방법
- `ROADMAP.md` - 향후 개발 계획 및 로드맵
- `JENKINS_RECOVERY_ROADMAP.md` - CI/CD 운영 가이드

### 백엔드 문서 (`/backend/doc/`)
백엔드 개발자를 위한 전문 문서
- `README.md` - FastAPI 기반 백엔드 개발 가이드
- `CASH_ASSETS.md` - 현금 자산 처리 구현 상세
- `TEST_ARCHITECTURE.md` - 백엔드 테스트 구조 및 모킹

### 프론트엔드 문서 (`/frontend/doc/`)
프론트엔드 개발자를 위한 전문 문서
- `README.md` - React + TypeScript 프론트엔드 개발 가이드
- `API_GUIDE.md` - 백엔드 API 연동 및 타입 정의

## 라이선스

이 프로젝트는 GNU 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 확인하세요.