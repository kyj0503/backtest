# FastAPI 백엔드 (backtest_be_fast)

백테스트 실행, 결과 저장, 이벤트 처리 및 API 제공을 담당한다.

주요 기능
- HTTP API (FastAPI)
- 백테스트 실행 엔진 래퍼
- CQRS 및 이벤트 기반 작업
- MySQL, Redis 연동

## 요구 사항
- Python 3.11+
- (선택) Docker, Docker Compose

## 빠른 시작(로컬)
```bash
cd backtest_be_fast
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
python run_server.py
```

## 전체 스택(Compose)
프로젝트 루트에서 실행한다.
```bash
docker compose -f compose/compose.dev.yaml up -d --build
docker compose -f compose/compose.dev.yaml logs -f backtest_be_fast
```

## 주요 엔드포인트
- 헬스체크: GET /health
- API 문서: GET /api/v1/docs
- 백테스트 실행: POST /api/v1/backtest/run

## 환경 변수
- `HOST`(기본: 0.0.0.0), `PORT`(기본: 8000), `DEBUG`(기본: false)
- `BACKEND_CORS_ORIGINS`
- `SECRET_KEY`
- 데이터베이스: `DATABASE_URL` 또는 `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_NAME`
- 외부 API 키: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`

민감한 값은 환경 변수 또는 시크릿 매니저로 관리한다.

## 테스트
pytest로 실행한다.

로컬
```bash
cd backtest_be_fast
PYTHONPATH=. pytest -v
PYTHONPATH=. pytest -m unit --cov=app --cov-report=term
```

Compose(의존 서비스 필요 시)
```bash
docker compose -f compose/compose.dev.yaml up -d mysql redis
docker compose -f compose/compose.dev.yaml run --rm backtest_be_fast pytest -v
```

## 개발자 참고
- 설정: `app/core/config.py` (`Settings`)
- 디렉터리: `app/api`, `app/services`, `app/domains`, `app/repositories`, `app/events`, `app/cqrs`

자세한 내용: `docs/Development.md`, `docs/Test.md`, `docs/Architecture.md`
