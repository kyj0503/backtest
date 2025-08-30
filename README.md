# 포트폴리오 백테스팅 플랫폼

## 개요

포트폴리오 기반 투자 전략을 분석하고 백테스트하는 웹 플랫폼입니다. FastAPI 백엔드와 React 프론트엔드로 구성되어 있으며, 단일 종목부터 다중 종목 포트폴리오까지 다양한 투자 전략을 테스트할 수 있습니다.

## 주요 기능

- **포트폴리오 백테스팅**: 투자 금액 기반 포트폴리오 구성 및 성과 분석
- **투자 전략**: Buy & Hold, SMA Crossover, RSI 전략 지원
- **성과 분석**: 20가지 이상의 성과 지표 및 시각화 차트
- **실시간 처리**: DB 기반 데이터 캐싱으로 빠른 백테스트 실행

## 사용법

1. **포트폴리오 구성**: 종목 심볼과 투자 금액 입력 (예: AAPL $10,000, GOOGL $15,000)
2. **전략 선택**: Buy & Hold, SMA Crossover, RSI 전략 중 선택
3. **백테스트 실행**: 기간 설정 후 백테스트 실행
4. **결과 분석**: 성과 지표 및 차트로 결과 확인

## 지원하는 투자 전략

| 전략 | 설명 | 파라미터 |
|------|------|----------|
| Buy & Hold | 매수 후 보유 | 없음 |
| SMA Crossover | 단순이동평균 교차 | 단기/장기 기간 |
| RSI Strategy | RSI 기반 매매 | RSI 기간, 과매수/과매도 기준 |

## 기술 스택

- **백엔드**: FastAPI, Python 3.11+, pandas, yfinance
- **프론트엔드**: React 18, TypeScript, Vite, Bootstrap
- **데이터베이스**: MySQL
- **컨테이너**: Docker, Docker Compose

## 프로젝트 구조

```
backtest/
├── .github/                 # GitHub 설정 및 Copilot 지침, 개발 계획 및 할일
├── backend/                 # FastAPI 백엔드 API 서버
│   ├── app/                 # 애플리케이션 코드
│   │   ├── api/v1/          # API 엔드포인트
│   │   ├── core/            # 핵심 설정
│   │   ├── models/          # Pydantic 모델
│   │   ├── services/        # 비즈니스 로직
│   │   └── utils/           # 유틸리티 함수
│   ├── strategies/          # 투자 전략 구현
│   ├── data_cache/          # 주식 데이터 캐시
│   └── doc/                 # 백엔드 문서
├── frontend/                # React 프론트엔드
│   ├── src/                 # 소스 코드
│   │   ├── components/      # React 컴포넌트
│   │   └── types/           # TypeScript 타입 정의
│   └── doc/                 # 프론트엔드 문서
├── database/                # 데이터베이스 DDL 파일
├── nginx/                   # Nginx 설정 파일
├── docker-compose*.yml      # Docker 설정 파일
└── README.md                # 프로젝트 메인 문서
```

## 빠른 시작

### 필수 요구사항

- Docker Desktop 또는 Docker Engine
- Docker Compose v2.0+

### 실행

```bash
# 리포지토리 클론
git clone <repository-url>
cd backtest

# 개발 환경 실행
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# 또는 프로덕션 환경 실행
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### 접속

- **개발 환경**: http://localhost:5174 (프론트엔드), http://localhost:8001 (백엔드)
- **프로덕션 환경**: http://localhost:8081 (프론트엔드), http://localhost:8001 (백엔드)

## 문서

- **백엔드 개발**: [backend/doc/README.md](backend/doc/README.md)
- **프론트엔드 개발**: [frontend/doc/README.md](frontend/doc/README.md)
- **API 가이드**: [backend/doc/api.md](backend/doc/api.md)

## 커밋 규칙

### 커밋 메시지 기본 구조

```
<타입>(<스코프>): <제목>

(한 줄 비우고)

<본문 (선택 사항)>

(한 줄 비우고)

<꼬리말 (선택 사항)>
```

### 타입 (Type): 변경의 종류

커밋이 어떤 성격의 변화를 나타내는지 설명.

- feat: 새로운 기능 추가
- fix: 버그 수정
- docs: 문서 수정
- style: 코드 포맷팅, 세미콜론 누락 등 기능 변경이 없는 코드 스타일 수정
- refactor: 코드 리팩토링
- test: 테스트 코드 추가 또는 수정
- chore: 빌드 관련 파일 수정, 패키지 매니저 설정 변경 등

### 스코프 (Scope): 변경이 발생한 위치

변경된 코드의 위치나 범위를 명시.

- front: 프론트엔드에 대한 변경
- back: 백엔드에 대한 변경
- ui: 공통 UI 컴포넌트 패키지에 대한 변경
- core: 여러 패키지에서 공통으로 사용하는 로직 (ex: 유틸 함수, 타입 정의)
- root: package.json 등 최상위 레벨의 설정 파일 변경
- front, back: 프론트엔드와 백엔드에 모두 영향을 주는 변경 (여러 스코프 명시)

## 라이선스

이 프로젝트는 GNU Affero General Public License v3.0 하에 배포됩니다.
