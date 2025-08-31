# 포트폴리오 백테스팅 플랫폼

## 최근 업데이트 (2025-09-01)

### 🔧 테스트 시스템 완전 재설계 및 오프라인 모킹 도입
- **완전 오프라인 테스트**: yfinance API와 MySQL DB 의존성을 완전히 제거한 오프라인 모킹 시스템 구축
- **수학적 데이터 생성**: Geometric Brownian Motion 알고리즘을 활용한 현실적 주식 데이터 생성
- **3-Tier 테스트 아키텍처**: unit/integration/e2e 구조로 체계적인 테스트 계층 설계
- **CI/CD 안정성**: Jenkins Ubuntu 환경에서 100% 성공률을 보장하는 완전 격리 테스트

### 🐛 해결된 CI/CD 문제점
- ✅ **네트워크 의존성 제거**: yfinance API 호출 완전 차단으로 빌드 안정성 확보
- ✅ **데이터베이스 격리**: MySQL 연결 없이도 실제 DB 스키마와 호환되는 모킹 데이터 사용
- ✅ **시나리오 기반 테스트**: 정상/비정상/극한 상황을 모두 커버하는 테스트 시나리오 구현
- ✅ **TypeScript 빌드**: Frontend의 unused variable 오류 해결

### 🛠 신규 테스트 인프라
- **MockStockDataGenerator**: DECIMAL(19,4) 정밀도를 지원하는 DB 호환 데이터 생성기
- **시나리오 시스템**: normal, empty, volatile 등 다양한 시장 상황 시뮬레이션
- **픽스처 관리**: 재사용 가능한 테스트 데이터와 예상 결과 중앙화
- **성능 최적화**: 단위 테스트 <30초, 통합 테스트 <2분, 종단 테스트 <5분 목표

---

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
| Bollinger Bands | 볼린저 밴드 기반 매매 | 기간, 표준편차 배수 |
| MACD Strategy | MACD 교차 기반 매매 | 빠른/느린/시그널 기간 |

## 기술 스택

- **백엔드**: FastAPI, Python 3.11+, pandas, yfinance, backtesting.py
- **프론트엔드**: React 18, TypeScript, Vite, React Bootstrap, Recharts  
- **데이터베이스**: MySQL (주식 데이터 캐싱)
- **테스트**: pytest (완전 오프라인 모킹), Vitest (프론트엔드)
- **컨테이너**: Docker, Docker Compose
- **CI/CD**: Jenkins, GitHub Container Registry
- **모니터링**: 시스템 정보 API, Git 커밋 추적

## 프로젝트 구조

```
backtest/
├── .github/                 # GitHub 설정 및 Copilot 지침
│   └── copilot-instructions.md
├── backend/                 # FastAPI 백엔드 API 서버
│   ├── app/                 # 애플리케이션 코드
│   │   ├── api/             # API 라우터
│   │   ├── core/            # 설정 및 예외 처리
│   │   ├── models/          # Pydantic 모델 (요청/응답)
│   │   ├── services/        # 비즈니스 로직 (백테스트, 포트폴리오, 전략)
│   │   ├── utils/           # 유틸리티 (데이터 수집, 직렬화)
│   │   └── main.py          # FastAPI 애플리케이션 엔트리포인트
│   ├── strategies/          # 투자 전략 구현체
│   ├── tests/               # 백엔드 테스트 코드
│   ├── doc/                 # 백엔드 개발 문서
│   ├── Dockerfile           # 백엔드 도커 이미지 설정
│   └── requirements.txt     # Python 의존성 패키지
├── frontend/                # React 프론트엔드
│   ├── src/                 # 소스 코드
│   │   ├── components/      # React 컴포넌트
│   │   ├── constants/       # 상수 정의
│   │   ├── hooks/           # 커스텀 훅
│   │   ├── services/        # API 서비스 계층
│   │   ├── test/            # 프론트엔드 테스트
│   │   ├── types/           # TypeScript 타입 정의
│   │   └── utils/           # 유틸리티 함수
│   ├── doc/                 # 프론트엔드 개발 문서
│   ├── Dockerfile           # 프로덕션 도커 이미지
│   ├── Dockerfile.dev       # 개발용 도커 이미지
│   └── package.json         # Node.js 의존성 및 스크립트
├── database/                # 데이터베이스 스키마 DDL
├── doc/                     # 프로젝트 전체 문서
├── nginx/                   # nginx 설정 (프로덕션)
├── scripts/                 # 배포 및 유틸리티 스크립트
├── docker-compose*.yml      # Docker Compose 설정
├── Jenkinsfile              # CI/CD 파이프라인
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
- **프로덕션 환경**: http://localhost:8082 (프론트엔드), http://localhost:8001 (백엔드)

## 테스트

### 백엔드 테스트 (완전 오프라인 시스템)

```bash
# 전체 테스트 실행
cd backend && pytest tests/ -v

# 티어별 테스트 실행
pytest tests/unit/          # 단위 테스트 (개별 함수/클래스)
pytest tests/integration/   # 통합 테스트 (서비스 간 상호작용)  
pytest tests/e2e/          # 종단 테스트 (전체 시나리오)

# 커버리지 리포트
pytest tests/ --cov=app --cov-report=html
```

### 프론트엔드 테스트

```bash
cd frontend && npm test
```

### CI/CD 테스트 (Docker 환경)

```bash
# 개발 환경에서 CI/CD와 동일한 조건으로 테스트
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 백엔드만 테스트
docker-compose exec backend pytest tests/ -v
```

### 테스트 아키텍처 특징

- **완전 격리**: yfinance API, MySQL DB 등 모든 외부 의존성 제거
- **수학적 모델링**: Geometric Brownian Motion 기반 현실적 주식 데이터
- **DB 스키마 호환**: stock_data_cache 테이블 구조 (DECIMAL 19,4) 완전 준수
- **시나리오 기반**: 정상/비정상/극한 상황 모든 케이스 커버
- **CI/CD 최적화**: Jenkins Ubuntu 환경에서 100% 성공률 보장

## CI/CD

프로젝트는 Jenkins를 통한 자동 배포를 지원합니다:

1. **main 브랜치 푸시** → 자동 빌드 트리거
2. **테스트 실행** → 빌드 과정에서 자동 테스트
3. **이미지 빌드** → Docker 이미지 생성 및 GHCR 푸시
4. **자동 배포** → 우분투 서버에 자동 배포

## 문제 해결

### 자주 발생하는 문제

1. **테스트 실패 (CI/CD 환경)**
   - yfinance API 네트워크 의존성: 완전 오프라인 모킹 시스템으로 해결됨
   - MySQL 연결 오류: 테스트 환경에서는 DB가 수학적 알고리즘으로 모킹됨
   - 데이터 일관성: Geometric Brownian Motion으로 현실적 주식 데이터 생성

2. **프론트엔드 빌드 실패**
   - TypeScript 컴파일 오류: 사용하지 않는 변수 제거
   - 예: `error TS6133: 'variable' is declared but its value is never read`

3. **Docker 빌드 문제**
   - 포트 충돌: 기존 컨테이너 종료 후 재시작
   - 캐시 문제: `docker system prune` 실행

### 개발 환경별 주의사항

- **Windows**: `host.docker.internal`로 MySQL 접근
- **Ubuntu/CI**: 모든 외부 의존성이 오프라인 모킹으로 대체됨
- **테스트 환경**: 실제 네트워크 없이도 100% 동작하는 격리된 테스트

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
