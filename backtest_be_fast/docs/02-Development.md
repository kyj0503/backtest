# 02. 개발 가이드 — FastAPI 백엔드

요구 사항
- Python 3.11+
- Docker (전체 스택 개발용)

빠른 시작 (로컬)
```bash
cd backtest_be_fast
pip install -r requirements.txt
python run_server.py
```

빠른 시작 (Compose)
```bash
docker compose -f compose.yml -f compose/compose.dev.yml up --build
```

환경변수(주요)
- `HOST`, `PORT`, `DEBUG`, `BACKEND_CORS_ORIGINS`

테스트
```bash
pytest -v
pytest --cov=app --cov-report=term-missing
```

코드 구조 요약
- 서비스: `app/services/`
- CQRS: `app/cqrs/`
- 이벤트: `app/events/`
