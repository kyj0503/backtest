# 개발 가이드 — FastAPI 백엔드

로컬 개발, 디렉터리 구조, 설정, 테스트 실행 방법을 정리한다.

## 필수 항목
- Python 3.11+
- (선택) Docker, Docker Compose

## 디렉터리
- `app/api/` API 라우터
- `app/services/` 비즈니스 로직
- `app/domains/` 도메인 모델
- `app/repositories/` 데이터 액세스
- `app/events/` 이벤트 시스템
 - `app/factories/`, `app/strategies/`, `app/models/`

## 로컬 실행
```bash
cd backtest_be_fast
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
python run_server.py
```

환경 변수로 포트/호스트를 바꿀 수 있다.
```bash
HOST=0.0.0.0 PORT=8000 python run_server.py
```

## 전체 스택(Compose)
프로젝트 루트에서 전체 스택을 실행한다.
```bash
docker compose -f compose.dev.yaml up -d --build
```

의존 서비스만 기동하려면 다음을 사용한다.
```bash
docker compose -f compose.dev.yaml up -d mysql redis
```

## 테스트
pytest로 실행한다.
```bash
cd backtest_be_fast
PYTHONPATH=. pytest -v
PYTHONPATH=. pytest --cov=app --cov-report=term-missing
```

의존 리소스가 필요하면 Compose로 mysql, redis를 먼저 띄운다.
```bash
docker compose -f compose.dev.yaml up -d mysql redis
PYTHONPATH=. pytest -v
```

## 설정
- `app/core/config.py`의 `Settings`로 관리한다.
- 주요 변수: `HOST`, `PORT`, `DEBUG`, `BACKEND_CORS_ORIGINS`, `SECRET_KEY`, DB 관련 변수, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`
- 민감한 값은 환경 변수 또는 시크릿 매니저에 보관한다.

## 디버깅 팁
- `LOG_LEVEL`로 로그 레벨을 조정한다.
- `pytest -x -q` 등 옵션으로 실패 지점을 빠르게 찾는다.
- 비동기 테스트는 `pytest-asyncio` 호환성을 확인한다.

자세한 내용은 `docs/Test.md`를 참고한다.
