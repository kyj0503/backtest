# 02. 개발 가이드 — FastAPI 백테스팅 서비스

## 요구 사항
- Python 3.11+
- Docker (전체 스택 개발용)

## 빠른 시작 (로컬 단독)
```bash
cd backtest_be_fast
pip install -r requirements.txt
python run_server.py
```

서버가 `http://localhost:8000`에서 실행되며, API 문서는 `/api/v1/docs`에서 확인할 수 있습니다.

## 빠른 시작 (Docker Compose 전체 스택)
```bash
# 개발 환경 (핫 리로드 포함)
docker compose -f compose.yml -f compose/compose.dev.yml up --build

# 로그 확인
docker compose logs -f
```

## 환경변수
`app/core/config.py`에서 관리되는 주요 설정:
- `HOST`: 서버 바인딩 호스트 (기본 `0.0.0.0`)
- `PORT`: 서버 포트 (기본 `8000`)
- `DEBUG`: 개발 모드, `true` 시 핫 리로드 활성화
- `BACKEND_CORS_ORIGINS`: CORS 허용 오리진 (콤마 또는 JSON 배열)

예시 (.env):
```bash
DEBUG=true
HOST=0.0.0.0
PORT=8000
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5174
```

## 테스트 실행
```bash
# 단위 테스트
pytest -v

# 커버리지 포함
pytest --cov=app --cov-report=term-missing
```

## 코드 구조
- **서비스 레이어**: `app/services/` - 비즈니스 로직, 비동기 처리
- **CQRS**: `app/cqrs/` - 명령/쿼리 분리, 핸들러 등록은 `service_manager.py`
- **이벤트**: `app/events/` - 비동기 이벤트 처리, 메트릭/알림
- **팩토리**: `app/factories/` - 서비스 의존성 주입

## 헬스체크
```bash
curl http://localhost:8000/health
```

## 트러블슈팅
- 포트 충돌 시: `PORT=8001 python run_server.py`
- CORS 오류: `BACKEND_CORS_ORIGINS`에 프론트엔드 주소 추가
- 의존성 문제: `pip install -r requirements.txt` 재실행
