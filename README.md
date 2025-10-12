# 백테스트 플랫폼개발 스택 가이드



주식 포트폴리오 백테스팅 플랫폼입니다. FastAPI 백엔드와 React 프론트엔드로 구성되어 있으며, Docker Compose로 전체 스택을 실행할 수 있습니다.개발/운영 모두 Docker Compose로 FastAPI 백엔드와 React 프론트엔드를 함께 실행할 수 있다.



## 주요 기능실행

```bash

- 포트폴리오 백테스트 (단일/복수 종목)cd /backtest  # 또는 프로젝트 루트로 이동

- 일시불/분할매수(DCA) 투자 방식 지원docker compose -f compose.dev.yaml up -d --build

- 리밸런싱 시뮬레이션 (월간/분기/연간)```

- 실시간 주가 데이터 (yfinance)

- 환율 데이터 및 통계중지

- 급등/급락 이벤트 감지```bash

- 종목별 뉴스 제공 (네이버 뉴스 API)docker compose -f compose.dev.yaml down

- S&P 500, NASDAQ 벤치마크 비교```



## 기술 스택완전 제거(컨테이너/이미지/볼륨)

```bash

### 백엔드# --rmi all, --volumes는 로컬 이미지와 볼륨을 제거한다

- Python 3.11docker compose -f compose.dev.yaml down --rmi all --volumes --remove-orphans

- FastAPI```

- backtesting.py

- yfinance상태 확인

- MySQL/MariaDB```bash

- Redis (캐싱)# 관련 컨테이너 상태 확인

docker ps --filter "name=backtest" --format "table {{.Names}}\t{{.Status}}"

### 프론트엔드

- React 18# Compose 병합 설정 확인

- TypeScriptdocker compose -f compose.dev.yaml config

- Vite```

- Tailwind CSS

- shadcn/ui개별 컨테이너 제어

- Recharts```bash

# 서비스 단위 실행/중지/삭제

## Quick Startdocker compose -f compose.dev.yaml up -d backtest_be_fast backtest_fe

docker compose -f compose.dev.yaml stop backtest_be_fast backtest_fe

### 1. 환경 설정docker compose -f compose.dev.yaml rm -f backtest_be_fast backtest_fe

```

프로젝트 루트에 `.env` 파일을 생성합니다:

환경 변수

```bash- **모든 환경 변수는 루트 디렉토리의 `.env` 파일에서만 관리한다.**

# 데이터베이스- 서브 폴더(`backtest_be_fast/`, `backtest_fe/`)에는 `.env` 파일을 만들지 않는다.

MYSQL_ROOT_PASSWORD=your-root-password- `.env` 파일은 git에 추적되지 않으므로 각 환경에서 직접 생성해야 한다.

MYSQL_DATABASE=backtest_db

MYSQL_USER=backtest_user## 운영 서버 배포

MYSQL_PASSWORD=your-db-password

운영 서버에서는 호스트에 설치된 데이터베이스를 사용합니다.

# 백엔드

DEBUG=true### 초기 설정 (1회만)

SECRET_KEY=your-secret-key-here

HOST=0.0.0.0```bash

PORT=8000# 1. 운영 서버 디렉터리 생성

BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]sudo mkdir -p /opt/backtest/backend

cd /opt/backtest/backend

# 네이버 API (선택)

NAVER_CLIENT_ID=your-naver-client-id# 2. 환경 파일 생성

NAVER_CLIENT_SECRET=your-naver-client-secretsudo nano .env



# Redis# 3. compose 파일 복사 (git 저장소에서)

REDIS_PASSWORD=your-redis-passwordsudo cp /path/to/repo/compose.server.yaml ./compose.yaml

```

# 프론트엔드

VITE_API_BASE_URL=/api### 스택 관리

API_PROXY_TARGET=http://backtest_be_fast:8000

FASTAPI_PROXY_TARGET=http://backtest_be_fast:8000```bash

VITE_APP_VERSION=1.0.0cd /opt/backtest/backend

```

# 스택 시작

### 2. 실행docker compose up -d



전체 스택을 Docker Compose로 실행합니다:# 스택 중지

docker compose down

```bash

cd /home/kyj/backtest  # 프로젝트 루트로 이동# 스택 재시작

docker compose -f compose.dev.yaml up -d --builddocker compose restart

```

# 로그 확인

### 3. 접속docker compose logs -f



- 프론트엔드: http://localhost:5173# 상태 확인

- 백엔드 API: http://localhost:8000docker compose ps

- API 문서 (Swagger): http://localhost:8000/api/v1/docs```

- API 문서 (ReDoc): http://localhost:8000/api/v1/redoc

### 이미지 업데이트

## 개발 가이드

```bash

### 디렉터리 구조cd /opt/backtest/backend



```# 최신 이미지 pull

backtest/docker compose pull

├── backtest_be_fast/     # 백엔드 (FastAPI)

│   ├── app/# 스택 재배포 (무중단)

│   │   ├── api/         # API 엔드포인트docker compose up -d

│   │   ├── services/    # 비즈니스 로직

│   │   ├── repositories/# 데이터 액세스# 또는 Jenkins CI/CD 파이프라인 사용

│   │   ├── strategies/  # 백테스팅 전략```

│   │   ├── schemas/     # Pydantic 스키마

│   │   ├── core/        # 설정 및 예외볼륨 정리

│   │   └── utils/       # 유틸리티```bash

│   ├── tests/           # 테스트# 프로젝트 볼륨만 삭제

│   └── docs/            # 백엔드 문서docker volume rm backtest_fe_node_modules backtest_be_fast_venv || true

├── backtest_fe/          # 프론트엔드 (React)

│   ├── src/# 불필요 볼륨 정리(주의)

│   │   ├── features/    # 기능별 모듈docker volume prune -f

│   │   ├── shared/      # 공통 컴포넌트/훅```

│   │   ├── pages/       # 라우트 페이지

│   │   └── themes/      # 테마 설정| 레이어 | Spring 비교 | 역할 |

│   └── docs/            # 프론트엔드 문서| --- | --- | --- |

├── database/            # DB 스키마| api/ | @RestController | HTTP 요청/응답 처리 |

├── compose.dev.yaml     # 개발 환경 Compose| schemas/ | DTO | API 입출력 모델 정의 |

└── .env                 # 환경 변수 (생성 필요)| repositories/ | @Repository + 캐싱 로직 | 데이터 소스 추상화 + 캐싱 전략 |

```| services/ | @Service | 비즈니스 로직 |



### 개별 컨테이너 제어

```bash
# 특정 서비스만 시작
docker compose -f compose.dev.yaml up -d backtest_be_fast backtest_fe

# 특정 서비스 중지
docker compose -f compose.dev.yaml stop backtest_be_fast backtest_fe

# 특정 서비스 삭제
docker compose -f compose.dev.yaml rm -f backtest_be_fast backtest_fe
```

### 로그 확인

```bash
# 전체 로그
docker compose -f compose.dev.yaml logs -f

# 특정 서비스 로그
docker compose -f compose.dev.yaml logs -f backtest_be_fast
docker compose -f compose.dev.yaml logs -f backtest_fe
```

### 테스트 실행

**백엔드 테스트:**
```bash
cd backtest_be_fast
PYTHONPATH=. pytest -v
PYTHONPATH=. pytest --cov=app --cov-report=term-missing
```

**프론트엔드 테스트:**
```bash
cd backtest_fe
npm run test:run
npm run test:coverage
```

### 중지 및 정리

```bash
# 스택 중지
docker compose -f compose.dev.yaml down

# 볼륨 포함 완전 제거
docker compose -f compose.dev.yaml down --rmi all --volumes --remove-orphans
```

## 운영 서버 배포

### 초기 설정

```bash
# 1. 운영 서버 디렉터리 생성
sudo mkdir -p /opt/backtest/backend
cd /opt/backtest/backend

# 2. 환경 파일 생성
sudo nano .env

# 3. compose 파일 복사
sudo cp /path/to/repo/compose.server.yaml ./compose.yaml
```

### 스택 관리

```bash
cd /opt/backtest/backend

# 스택 시작
docker compose up -d

# 스택 중지
docker compose down

# 스택 재시작
docker compose restart

# 로그 확인
docker compose logs -f

# 상태 확인
docker compose ps
```

### 이미지 업데이트

```bash
cd /opt/backtest/backend

# 최신 이미지 pull
docker compose pull

# 스택 재배포 (무중단)
docker compose up -d
```

## 아키텍처

### 백엔드 계층 구조

| 레이어 | 역할 |
|--------|------|
| api/ | HTTP 요청/응답 처리 (Controller) |
| schemas/ | API 입출력 모델 정의 (DTO) |
| services/ | 비즈니스 로직 (Service) |
| repositories/ | 데이터 소스 추상화 (Repository) |
| strategies/ | 백테스팅 전략 구현 |

### 프론트엔드 패턴

- Feature-based 구조
- Custom Hooks로 비즈니스 로직 분리
- API 클라이언트 레이어 분리
- shadcn/ui 기반 컴포넌트

## 상태 확인

```bash
# 관련 컨테이너 상태 확인
docker ps --filter "name=backtest" --format "table {{.Names}}\t{{.Status}}"

# Compose 설정 확인
docker compose -f compose.dev.yaml config
```

## 문서

### 백엔드 문서
- `backtest_be_fast/docs/API_SPECIFICATION.md`: API 명세서
- `backtest_be_fast/docs/Architecture.md`: 아키텍처 설명
- `backtest_be_fast/docs/Development.md`: 개발 가이드
- `backtest_be_fast/docs/Test.md`: 테스트 가이드

### 프론트엔드 문서
- `backtest_fe/docs/Development.md`: 개발 환경 설정
- `backtest_fe/docs/Test.md`: 테스트 가이드
- `backtest_fe/docs/Theme.md`: 테마 시스템

## 환경 변수 관리

- **모든 환경 변수는 루트 디렉터리의 `.env` 파일에서만 관리합니다.**
- 서브 폴더(`backtest_be_fast/`, `backtest_fe/`)에는 `.env` 파일을 만들지 않습니다.
- `.env` 파일은 git에 추적되지 않으므로 각 환경에서 직접 생성해야 합니다.

## 라이선스

이 프로젝트는 교육 목적으로 개발되었습니다.
