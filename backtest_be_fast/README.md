# FastAPI 백테스팅 백엔드 (backtest_be_fast)

백테스팅 기능을 담당하는 FastAPI 기반 백엔드 서비스입니다.

## 빠른 시작
```bash
# 로컬 단독 실행
python run_server.py

# Docker Compose (전체 스택)
docker compose -f compose.yml -f compose/compose.dev.yml up --build
```

## 주요 엔드포인트
- 헬스체크: `GET /health`
- API 문서: `GET /api/v1/docs`
- 백테스팅: `POST /api/v1/backtest/run`

## 문서
자세한 내용은 [`docs/`](./docs/) 디렉터리를 참조하세요.
