# 백테스팅 시스템

FastAPI + React 기반의 투자 전략 백테스팅 시스템입니다.

## 프로젝트 소개

투자 전략의 과거 성과를 분석하는 웹 기반 백테스팅 도구입니다. 다양한 기술적 지표로 전략을 시뮬레이션하고 리스크와 수익성을 분석합니다.

### 주요 특징
- 포트폴리오 및 단일 종목 백테스트 지원
- 현금 자산 포함 리스크 관리
- 실시간 주가 데이터(yfinance), 뉴스(네이버) 연동
- 시각적 차트 및 성과 분석

### 주요 폴더 구조
```
backend/app/
	├── api/         # FastAPI 라우터
	├── services/    # 서비스 로직
	├── domains/     # 도메인 모델
	└── ...
frontend/src/
	├── components/  # UI 컴포넌트
	├── hooks/       # 커스텀 훅
	├── pages/       # 라우트별 페이지
	└── ...
database/
	├── schema.sql   # DB 스키마
	└── yfinance.sql # 주가 데이터 캐시 스키마
docs/              # 개발/운영/테스트/아키텍처 문서
scripts/           # 테스트/배포 스크립트
```

> 상세 구조와 역할은 docs/DEVELOPMENT_GUIDE.md, docs/ARCHITECTURE_GUIDE.md 참고

## 빠른 시작

### 개발 환경 실행
```bash
# 개발 환경 시작
docker compose -f compose.yml -f compose/compose.dev.yml up --build -d

# 백그라운드 실행
docker compose -f compose.yml -f compose/compose.dev.yml up -d

# 시스템 종료
docker compose -f compose.yml -f compose/compose.dev.yml down

# 프론트엔드 npm 패키지 추가/수정 후에는 반드시 아래 명령어로 강제 재빌드 (캐시 무시, 백그라운드 실행 아님)
docker compose -f compose.yml -f compose/compose.dev.yml build --no-cache
```
### 접속 정보
- **프론트엔드**: http://localhost:5174
- **백엔드 API**: http://localhost:8001
- **API 문서**: http://localhost:8001/api/v1/docs

### 테스트 실행
```bash
# 백엔드/프론트엔드 테스트는 scripts/test-runner.sh로 실행
./scripts/test-runner.sh unit         # 단위 테스트
./scripts/test-runner.sh integration  # 통합 테스트
./scripts/test-runner.sh all          # 전체 테스트
```
### Radix UI 등 커스텀 Select/Dropdown 테스트 가이드

Radix UI 등 커스텀 셀렉트(Select/Dropdown) 컴포넌트는 실제 `<select>` 엘리먼트를 사용하지 않으므로, Testing Library의 `user.selectOptions` 대신 드롭다운 트리거를 클릭하고 옵션을 클릭하는 방식으로 테스트해야 합니다.

## 기술 스택

- **프론트엔드**: React 18, TypeScript, Vite, Tailwind CSS, Recharts
- **백엔드**: FastAPI, Python, Pydantic, MySQL, backtesting.py
- **인프라**: Docker, Jenkins, nginx

## 문서

자세한 개발/운영/테스트/아키텍처/기여 가이드는 [`docs/`](docs/) 폴더에서 관리합니다.

## 라이선스

이 프로젝트는 GNU AFFERO GENERAL PUBLIC LICENSE 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 확인하세요.