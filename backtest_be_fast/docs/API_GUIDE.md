# 03. API 가이드 — FastAPI 백테스팅 서비스

## 기본 정보
- **Base URL**: `http://localhost:8000/api/v1`
- **인증**: `Authorization: Bearer <token>` (인증 필요 엔드포인트)
- **문서**: `/api/v1/docs` (Swagger UI), `/api/v1/redoc`

## 주요 엔드포인트

### 시스템
- `GET /health` - 헬스체크

### 인증
- `POST /api/v1/auth/register` - 사용자 등록
- `POST /api/v1/auth/login` - 로그인

### 백테스팅
- `POST /api/v1/backtest/run` - 단일 백테스트 실행
- `POST /api/v1/backtest/portfolio` - 포트폴리오 백테스트
- `POST /api/v1/backtest/execute` - 통합 실행 엔드포인트
- `POST /api/v1/backtest/chart-data` - 차트 데이터 조회
- `GET /api/v1/backtest/metrics` - 집계 메트릭
- `GET /api/v1/backtest/history` - 백테스트 이력 (인증 필요)

### 전략
- `GET /api/v1/strategies` - 사용 가능한 전략 목록

### 채팅 (WebSocket)
- `WS /api/v1/chat/ws/{room}` - 채팅룸 WebSocket 연결

## 요청/응답 모델
모든 API는 Pydantic v2 모델을 사용합니다:
- **요청 스키마**: `app/models/requests.py`
- **응답 스키마**: `app/models/responses.py`

## 인증이 필요한 엔드포인트
다음 엔드포인트들은 `Authorization: Bearer <token>` 헤더가 필요합니다:
- 백테스트 이력 조회
- 포트폴리오 관련 작업
- 커뮤니티 기능

## 예시 요청
```bash
# 헬스체크
curl http://localhost:8000/health

# 전략 목록 조회
curl http://localhost:8000/api/v1/strategies

# 백테스트 실행 (예시)
curl -X POST http://localhost:8000/api/v1/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "start_date": "2023-01-01", "end_date": "2023-12-31", "strategy": "sma_cross"}'
```
