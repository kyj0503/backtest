# 백엔드 개발 가이드````markdown

# 개발 가이드 — FastAPI 백엔드

## 환경 준비

로컬 개발, 디렉터리 구조, 설정, 테스트 실행 방법을 정리한다.

- Python 3.11+

- Docker, Docker Compose (권장)## 필수 항목

- Python 3.11+

## 로컬 실행- (선택) Docker, Docker Compose



```bash## 디렉터리

cd backtest_be_fast- `app/api/` - API 라우터 및 엔드포인트

python3 -m venv .venv- `app/services/` - 비즈니스 로직

source .venv/bin/activate- `app/repositories/` - 데이터 액세스 계층

pip install -r requirements.txt -r requirements-test.txt- `app/strategies/` - 백테스팅 전략 구현

python run_server.py- `app/schemas/` - Pydantic 요청/응답 스키마

```- `app/factories/` - 객체 생성 팩토리 패턴

- `app/events/` - 이벤트 핸들러

포트/호스트 변경:- `app/core/` - 설정 및 예외 처리

```bash- `app/utils/` - 유틸리티 함수

HOST=0.0.0.0 PORT=8000 python run_server.py

```## 로컬 실행

```bash

## Docker 실행cd backtest_be_fast

python3 -m venv .venv

프로젝트 루트에서:source .venv/bin/activate

```bashpip install -r requirements.txt -r requirements-test.txt

docker compose -f compose.dev.yaml up -d --buildpython run_server.py

``````



의존 서비스만 실행:환경 변수로 포트/호스트를 바꿀 수 있다.

```bash```bash

docker compose -f compose.dev.yaml up -d mysql redisHOST=0.0.0.0 PORT=8000 python run_server.py

``````



## 테스트## 전체 스택(Compose)

프로젝트 루트에서 전체 스택을 실행한다.

```bash```bash

cd backtest_be_fastdocker compose -f compose.dev.yaml up -d --build

PYTHONPATH=. pytest -v```

PYTHONPATH=. pytest --cov=app --cov-report=term-missing

```의존 서비스만 기동하려면 다음을 사용한다.

```bash

테스트 전 의존 서비스 실행:docker compose -f compose.dev.yaml up -d mysql redis

```bash```

docker compose -f compose.dev.yaml up -d mysql redis

PYTHONPATH=. pytest -v## 테스트

```pytest로 실행한다.

```bash

## 환경 설정cd backtest_be_fast

PYTHONPATH=. pytest -v

`app/core/config.py`의 `Settings` 클래스로 관리됩니다.PYTHONPATH=. pytest --cov=app --cov-report=term-missing

```

주요 환경 변수:

- `HOST`, `PORT`: 서버 주소/포트의존 리소스가 필요하면 Compose로 mysql, redis를 먼저 띄운다.

- `DEBUG`: 디버그 모드```bash

- `SECRET_KEY`: 보안 키docker compose -f compose.dev.yaml up -d mysql redis

- `BACKEND_CORS_ORIGINS`: CORS 허용 도메인PYTHONPATH=. pytest -v

- `MYSQL_*`: 데이터베이스 설정```

- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`: 네이버 API

## 설정
- `app/core/config.py`의 `Settings`로 관리한다.
- 주요 변수: `HOST`, `PORT`, `DEBUG`, `BACKEND_CORS_ORIGINS`, `SECRET_KEY`, DB 관련 변수, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`
- 민감한 값은 환경 변수 또는 시크릿 매니저에 보관한다.

## 디버깅 팁
- `LOG_LEVEL`로 로그 레벨을 조정한다.
- `pytest -x -q` 등 옵션으로 실패 지점을 빠르게 찾는다.
- 비동기 테스트는 `pytest-asyncio` 호환성을 확인한다.

자세한 내용은 `docs/Test.md`를 참고한다.
