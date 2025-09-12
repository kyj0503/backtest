
# API 가이드 (2025-09 최신)

이 문서는 백테스팅 시스템의 모든 백엔드 API 엔드포인트, 기능, 입출력 예시, curl 예제, 도커 환경 기준 사용법을 체계적으로 설명합니다.

문제 발생 시: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 참고

## 목차

1. [API 개요](#api-개요)
2. [인증](#인증)
3. [백테스트 API](#백테스트-api)
  - [통합 백테스트](#통합-백테스트-execute)
  - [단일/포트폴리오/차트/히스토리/환율/뉴스/헬스체크](#기타-주요-api)
4. [전략 API](#전략-api)
5. [커뮤니티 API](#커뮤니티-api)
6. [기타 API](#기타-api)
7. [에러 처리](#에러-처리)

## API 개요

### 베이스 URL
- **개발**: `http://localhost:8001/api/v1`
- **프로덕션**: 환경변수 `VITE_API_BASE_URL` 또는 상대 경로 `/api/v1`

### 공통 헤더
```
Content-Type: application/json
Authorization: Bearer <token>  // 인증이 필요한 엔드포인트
```

### API 문서
- **Swagger UI**: `/api/v1/docs`
- **ReDoc**: `/api/v1/redoc`

## 인증

토큰 기반 인증을 사용합니다. 로그인 후 받은 토큰을 `Authorization` 헤더에 포함하여 요청하세요.

### 회원가입
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "investment_type": "moderate"  // conservative, moderate, aggressive
}
```

**응답:**
```json
{
  "message": "회원가입이 완료되었습니다.",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "investment_type": "moderate"
  }
}
```

### 로그인
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "password123"
}
```

**응답:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "investment_type": "moderate"
  }
}
```

### 로그아웃
```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

### 사용자 정보 조회
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```


## 백테스트 API

### [통합 백테스트] `/api/v1/backtest/execute`

단일 종목/포트폴리오 자동 구분, 환율·S&P500·NASDAQ 벤치마크 포함, 표준화된 결과 반환

#### 요청 예시 (비중/금액 모두 지원)

> **프론트엔드 UX 정책**
> - 포트폴리오 구성 시 각 종목의 "비중(%)" 칸에 값을 직접 입력하면, 해당 종목의 weight 필드가 API로 전송됩니다.
> - amount(투자금액) 칸을 수정하면 weight 입력이 해제되어 amount만 전송됩니다.
> - amount와 weight는 동시에 입력 불가, 혼용 불가(동일 포트폴리오 내에서 한 방식만 사용).
> - weight 입력 시 합계가 100%가 아니면 에러가 표시됩니다.
> - 모든 종목이 weight 기반이면 amount는 자동 계산되어 API로 전송될 수 있습니다(내부 변환).
```bash
# (1) 금액 기반 입력
curl -X POST http://localhost:8001/api/v1/backtest/execute \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [
      {"symbol": "AAPL", "amount": 10000, "asset_type": "stock"},
      {"symbol": "GOOGL", "amount": 5000, "asset_type": "stock"}
    ],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy": "buy_and_hold"
  }'

# (2) 비중(%) 기반 입력 (amount 대신 weight 사용, 합계 100)
curl -X POST http://localhost:8001/api/v1/backtest/execute \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [
      {"symbol": "AAPL", "weight": 60, "asset_type": "stock"},
      {"symbol": "GOOGL", "weight": 40, "asset_type": "stock"}
    ],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy": "buy_and_hold"
  }'

```
* amount와 weight는 동시에 입력 불가, 둘 중 하나만 입력 (weight는 0~100, 합계 100±0.01 허용)
* 포트폴리오 내 모든 종목이 동일 방식(amount 또는 weight)으로 입력되어야 함
* weight 입력 시 내부적으로 금액으로 자동 환산

#### PortfolioStock 필드
| 필드명         | 타입    | 설명                                 |
| -------------- | ------- | ------------------------------------ |
| symbol         | string  | 주식 심볼                            |
| amount         | float   | 투자 금액 (weight와 동시 입력 불가)   |
| weight         | float   | 비중(%) (amount와 동시 입력 불가)     |
| asset_type     | string  | 자산 타입 (stock, cash)              |
| investment_type| string  | 투자 방식 (lump_sum, dca)            |
| dca_periods    | int     | 분할 매수 기간 (개월, 옵션)           |
| custom_name    | string  | 현금 자산 커스텀명 (옵션)             |

#### 응답 예시 (요약)

#### 응답 예시 (요약)
```json
{
  "status": "success",
  "backtest_type": "portfolio", // 또는 "single_stock"
  "data": {
    "portfolio_composition": [ ... ],
    "summary_stats": { ... },
    "ohlc_data": [ ... ],
    "equity_data": [ ... ],
    "trade_markers": [ ... ],
    "indicators": [ ... ],
    "exchange_rates": [ ... ],
    "sp500_benchmark": [ ... ],
    "nasdaq_benchmark": [ ... ]
  }
}
```

#### 주요 특징
- 단일 종목: `portfolio`에 1개 종목, 현금 없음 → 단일 백테스트
- 포트폴리오: 2개 이상 종목 또는 현금 포함 → 포트폴리오 백테스트
- 환율(`exchange_rates`), S&P500(`sp500_benchmark`), NASDAQ(`nasdaq_benchmark`) 데이터 포함
- 모든 결과는 표준화된 구조로 반환

---

### 기타 주요 API

#### 1. 단일 종목 백테스트 `/run`
```bash
curl -X POST http://localhost:8001/api/v1/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_cash": 10000,
    "strategy": "buy_and_hold"
  }'
```

#### 2. 포트폴리오 백테스트 `/portfolio`
```bash
# (1) 금액 기반 입력
curl -X POST http://localhost:8001/api/v1/backtest/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [
      {"symbol": "AAPL", "amount": 4000},
      {"symbol": "GOOGL", "amount": 3000},
      {"symbol": "MSFT", "amount": 3000}
    ],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }'

# (2) 비중(%) 기반 입력
curl -X POST http://localhost:8001/api/v1/backtest/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [
      {"symbol": "AAPL", "weight": 50},
      {"symbol": "GOOGL", "weight": 30},
      {"symbol": "MSFT", "weight": 20}
    ],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }'
```
* amount/weight 동시 입력 불가, 혼합 입력 불가, weight 합계 100±0.01

### 이벤트/메트릭/알림/분석/경고 API

#### 1. 백테스트 메트릭 요약 `/api/v1/backtest/metrics`
```http
GET /api/v1/backtest/metrics
```
* 전체 백테스트 실행/성공/실패/전략별/심볼별 성과 등 집계

#### 2. 백테스트 알림 조회 `/api/v1/backtest/notifications`
```http
GET /api/v1/backtest/notifications?limit=20
```
* 최근 백테스트 성공/실패/최적화 등 주요 알림 목록

#### 3. 포트폴리오 분석 통계 `/api/v1/backtest/portfolio-analytics`
```http
GET /api/v1/backtest/portfolio-analytics
GET /api/v1/backtest/portfolio-analytics?portfolio_id=abc123
```
* 전체/특정 포트폴리오의 생성, 리밸런싱, 최적화, 인기 자산 등 통계

#### 4. 포트폴리오 경고/알림 `/api/v1/backtest/portfolio-alerts`
```http
GET /api/v1/backtest/portfolio-alerts?limit=20
GET /api/v1/backtest/portfolio-alerts?portfolio_id=abc123&limit=10
```
* 거래비용 급증, 다변화 악화, 대규모 가중치 변화, 리스크 허용도 급변 등 경고/알림

#### 응답 예시 (메트릭)
```json
{
  "total_backtests": 12,
  "success_rate": 0.83,
  "failure_rate": 0.17,
  "avg_execution_time": 2.1,
  "strategy_performance": {
    "buy_and_hold": {"count": 7, "avg_annual_return": 0.12, "avg_sharpe_ratio": 1.1, "avg_trade_count": 2.3}
  },
  "symbol_performance": {
    "AAPL": {"count": 5, "avg_annual_return": 0.15, "best_strategy": "buy_and_hold", "best_return": 0.22}
  }
}
```

#### 응답 예시 (알림)
```json
[
  {"type": "high_return", "title": "높은 수익률 달성", "message": "AAPL (buy_and_hold): 32.00% 연간 수익률", "severity": "success", "timestamp": "2024-06-01T12:00:00"},
  {"type": "backtest_failed", "title": "백테스트 실패", "message": "AAPL (buy_and_hold): 데이터 없음", "severity": "error", "timestamp": "2024-06-01T12:01:00"}
]
```

#### 응답 예시 (포트폴리오 분석)
```json
{
  "total_portfolios": 3,
  "avg_rebalancing_per_portfolio": 1.7,
  "avg_optimization_per_portfolio": 0.3,
  "popular_assets": [["AAPL", 3], ["GOOGL", 2]],
  "total_rebalancing_events": 5
}
```

#### 응답 예시 (경고)
```json
[
  {"type": "high_transaction_cost", "title": "높은 거래비용 발생", "message": "포트폴리오 abc123: $1,200.00 거래비용", "severity": "warning", "portfolio_id": "abc123", "timestamp": "2024-06-01T12:00:00"},
  {"type": "diversification_decline", "title": "다변화 효과 악화", "message": "포트폴리오 abc123: 다변화 점수 -0.120", "severity": "warning", "portfolio_id": "abc123", "timestamp": "2024-06-01T12:01:00"}
]
```

#### 3. 차트 데이터 `/chart-data`
```bash
curl -X POST http://localhost:8001/api/v1/backtest/chart-data \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

#### 4. 백테스트 히스토리 목록 `/history`
```bash
curl -X GET "http://localhost:8001/api/v1/backtest/history?limit=10&offset=0" -H "Authorization: Bearer <token>"
```

#### 5. 백테스트 히스토리 상세 `/history/{history_id}`
```bash
curl -X GET http://localhost:8001/api/v1/backtest/history/1 -H "Authorization: Bearer <token>"
```

#### 6. 백테스트 히스토리 삭제 `DELETE /history/{history_id}`
```bash
curl -X DELETE http://localhost:8001/api/v1/backtest/history/1 -H "Authorization: Bearer <token>"
```

#### 7. 환율 데이터 `/exchange-rate`
```bash
curl "http://localhost:8001/api/v1/backtest/exchange-rate?start_date=2023-01-01&end_date=2023-12-31"
```

#### 8. 변동성 이벤트 뉴스 `/stock-volatility-news/{ticker}`
```bash
curl "http://localhost:8001/api/v1/backtest/stock-volatility-news/AAPL?start_date=2023-01-01&end_date=2023-12-31&threshold=5.0"
```

#### 9. 백테스트 서비스 헬스체크 `/health`
```bash
curl http://localhost:8001/api/v1/backtest/health
```

---

### 환율 데이터 조회
```http
GET /api/v1/backtest/exchange-rate?start_date=2023-01-01&end_date=2023-12-31
```

### 변동성 이벤트 조회
```http
GET /api/v1/backtest/stock-volatility-news/AAPL?start_date=2023-01-01&end_date=2023-12-31&threshold=5.0
```

## 전략 API

### 전략 목록 조회
```http
GET /api/v1/strategies/
```

**응답:**
```json
[
  {
    "name": "buy_and_hold",
    "display_name": "Buy and Hold",
    "description": "매수 후 보유 전략",
    "parameters": {}
  },
  {
    "name": "sma_crossover",
    "display_name": "SMA Crossover",
    "description": "단순이동평균 교차 전략",
    "parameters": {
      "short_window": {
        "type": "int",
        "default": 10,
        "min": 5,
        "max": 50
      },
      "long_window": {
        "type": "int", 
        "default": 30,
        "min": 20,
        "max": 200
      }
    }
  }
]
```

### 특정 전략 정보 조회
```http
GET /api/v1/strategies/sma_crossover
```

### 전략 파라미터 검증
```http
GET /api/v1/strategies/sma_crossover/validate?short_window=10&long_window=30
```

## 커뮤니티 API

### 게시글 목록 조회
```http
GET /api/v1/community/posts?page=1&limit=20
```

**응답:**
```json
{
  "posts": [
    {
      "id": 1,
      "title": "AAPL 백테스트 결과 공유",
      "content": "애플 주식으로 백테스트를 해봤는데...",
      "author": {
        "username": "testuser",
        "profile_image": null
      },
      "view_count": 15,
      "like_count": 3,
      "created_at": "2023-01-01T10:00:00",
      "updated_at": "2023-01-01T10:00:00"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

### 게시글 상세 조회
```http
GET /api/v1/community/posts/1
```

### 게시글 작성 (인증 필요)
```http
POST /api/v1/community/posts
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "백테스트 결과 공유",
  "content": "오늘 백테스트를 해본 결과입니다..."
}
```

### 댓글 작성 (인증 필요)
```http
POST /api/v1/community/posts/1/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "좋은 결과네요!"
}
```

### 게시글 좋아요/취소 (인증 필요)
```http
POST /api/v1/community/posts/1/like
Authorization: Bearer <token>
```

### 게시글 신고 (인증 필요)
```http
POST /api/v1/community/posts/1/report
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "spam",
  "reason": "스팸성 게시글입니다."
}
```

### 공지사항 조회
```http
GET /api/v1/community/notices
```

## 기타 API

### 최적화 API
```http
POST /api/v1/optimize/run
Content-Type: application/json

{
  "ticker": "AAPL",
  "start_date": "2023-01-01", 
  "end_date": "2023-12-31",
  "strategy": "sma_crossover",
  "parameter_ranges": {
    "short_window": [5, 20],
    "long_window": [25, 50]
  },
  "optimization_target": "sharpe_ratio",
  "method": "grid"
}
```

### 데이터 캐시 API
```http
POST /api/v1/yfinance/fetch-and-cache?ticker=AAPL&start=2023-01-01&end=2023-12-31&interval=1d
```

### 뉴스 검색 API
```http
GET /api/v1/naver-news/search?query=애플&display=10
```

참고: 날짜 범위 기반 엔드포인트(`/api/v1/naver-news/search-by-date`, `/api/v1/naver-news/ticker/{ticker}/date`)는 `display` 최소값이 10입니다. 일반 검색(`/search`, `/ticker/{ticker}`)은 1 이상 허용됩니다.

```http
GET /api/v1/naver-news/ticker/AAPL/date?start_date=2023-01-01&end_date=2023-01-31&display=5
```

### 채팅 WebSocket
```javascript
const ws = new WebSocket(`ws://localhost:8001/api/v1/chat/ws/general?token=${token}`);

ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('받은 메시지:', message);
};

ws.send(JSON.stringify({
  type: 'message',
  content: '안녕하세요!'
}));
```

### 헬스체크
```http
GET /health
```

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T10:00:00Z"
}
```


## 에러 처리 및 정책

### 에러 응답 형식
```json
{
  "detail": "사용자 친화적 에러 메시지",
  "error_id": "uuid-for-debugging"
}
```

### 주요 HTTP 상태 코드
- **200**: 성공
- **400**: 잘못된 요청
- **401**: 인증 필요
- **403**: 권한 없음
- **404**: 리소스 없음
- **422**: 유효성 검사 실패
- **429**: 요청 한도 초과
- **500**: 서버 내부 오류

### 유효성 검사 오류 예시
```json
{
  "detail": [
    {
      "loc": ["body", "start_date"],
      "msg": "시작 날짜는 YYYY-MM-DD 형식이어야 합니다",
      "type": "value_error"
    }
  ]
}
```


### 데이터 소스 정책
- **DB 캐시 우선**: MySQL에 저장된 데이터 우선 사용
- **외부 API 보강**: 누락된 데이터는 yfinance에서 조회 후 자동 저장
- **에러 분류**: 404(데이터 없음), 422(검증 실패), 429(레이트 제한), 0(네트워크 오류)

### 현금 자산 처리
- 심볼: `CASH` 또는 한글 `현금`
- 특성: 0% 수익률, 무변동성
- 주가/뉴스 조회 시 빈 배열 반환

---

## 도커 환경에서의 빌드/실행/테스트

### 빌드 및 실행
```bash
# 전체 개발 환경 빌드 및 실행
docker compose -f compose.yml -f compose/compose.dev.yml up --build

# 백엔드만 재시작
docker compose -f compose.yml -f compose/compose.dev.yml restart backend
```

### 테스트
```bash
# 백엔드 단위/통합 테스트 (컨테이너 내부)
docker compose exec backend pytest -q

# 커버리지 포함
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

---

## 문서 개선/기여

문서 개선, API 예시 추가, 신규 기능 반영은 PR 또는 이슈로 언제든 환영합니다.
