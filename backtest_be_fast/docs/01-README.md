# 01. FastAPI 백엔드 개요 (backtest_be_fast)

개요
- FastAPI 기반 백테스팅 서비스의 백엔드입니다. API 제공, 백테스트 실행, 결과 저장 및 이벤트 처리 기능을 담당합니다.

기술 스택
- Python 3.11+, FastAPI, Pydantic v2
- MySQL, Docker Compose
- CQRS 및 이벤트 기반 보조 처리

빠른 시작
```bash
# 로컬 단독 실행
cd backtest_be_fast
pip install -r requirements.txt
python run_server.py

# 전체 스택 (Compose)
docker compose -f compose.yml -f compose/compose.dev.yml up --build
```

환경변수(주요)
- `HOST`, `PORT`: 서버 바인딩 설정 (기본 `0.0.0.0:8000`)
- `DEBUG`: 개발 모드(리로드)
- `BACKEND_CORS_ORIGINS`: CORS 허용 오리진(콤마 또는 JSON 배열)

디렉터리 개요
- `app/api/`: FastAPI 라우터 및 엔드포인트
- `app/services/`: 비즈니스 로직
- `app/cqrs/`: 명령/쿼리 및 핸들러
- `app/domains/`: 도메인 모델
- `app/repositories/`: 데이터 액세스
- `app/events/`: 이벤트 시스템