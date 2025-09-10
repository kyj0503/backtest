# API 가이드

이 문서는 백테스팅 시스템의 모든 API 엔드포인트와 사용 방법을 설명합니다.

> 💡 **문제 발생 시**: API 관련 트러블슈팅은 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)를 참고하세요.

## 목차

1. [API 개요](#api-개요)
2. [인증](#인증)
3. [백테스트 API](#백테스트-api)
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

### 단일 종목 백테스트 실행
```http
POST /api/v1/backtest/run
Content-Type: application/json

{
  "ticker": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_cash": 100000,
  "strategy": "buy_and_hold",
  "strategy_params": {},
  "commission": 0.001,
  "spread": 0.0,
  "benchmark_ticker": "SPY"
}
```

**응답:**
```json
{
  "status": "success",
  "data": {
    "ticker": "AAPL",
    "strategy": "buy_and_hold",
    "summary_stats": {
      "start": "2023-01-01T00:00:00",
      "end": "2023-12-31T00:00:00",
      "duration": "365 days 00:00:00",
      "total_return_pct": 48.15,
      "annual_return_pct": 48.15,
      "volatility_pct": 25.32,
      "sharpe_ratio": 1.89,
      "max_drawdown_pct": 12.45,
      "total_trades": 2,
      "win_rate_pct": 100.0
    }
  }
}
```

### 백테스트 차트 데이터
```http
POST /api/v1/backtest/chart-data
Content-Type: application/json

{
  "ticker": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_cash": 100000,
  "strategy": "sma_crossover",
  "strategy_params": {
    "short_window": 10,
    "long_window": 30
  }
}
```

**응답:**
```json
{
  "status": "success",
  "data": {
    "ticker": "AAPL",
    "ohlc_data": [
      {
        "date": "2023-01-01",
        "open": 150.0,
        "high": 155.0,
        "low": 148.0,
        "close": 152.0,
        "volume": 1000000
      }
    ],
    "equity_data": [
      {
        "date": "2023-01-01",
        "equity": 100000,
        "drawdown": 0
      }
    ],
    "trades": [
      {
        "entry_date": "2023-01-15",
        "exit_date": "2023-02-10",
        "entry_price": 160.0,
        "exit_price": 170.0,
        "size": 625,
        "pnl": 6250.0,
        "return_pct": 6.25
      }
    ],
    "indicators": {
      "sma_short": [150.0, 151.0, 152.0],
      "sma_long": [148.0, 149.0, 150.0]
    },
    "summary_stats": {
      // ... 동일한 구조
    }
  }
}
```

### 포트폴리오 백테스트
```http
POST /api/v1/backtest/portfolio
Content-Type: application/json

{
  "portfolio": [
    {
      "symbol": "AAPL",
      "amount": 50000,
      "investment_type": "lump_sum",
      "asset_type": "stock"
    },
    {
      "symbol": "GOOGL",
      "amount": 30000,
      "investment_type": "dca",
      "dca_periods": 12,
      "asset_type": "stock"
    },
    {
      "symbol": "현금",
      "amount": 20000,
      "investment_type": "lump_sum",
      "asset_type": "cash"
    }
  ],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "commission": 0.001,
  "rebalance_frequency": "quarterly"
}
```

**응답:**
```json
{
  "status": "success",
  "data": {
    "portfolio_statistics": {
      "total_return_pct": 25.8,
      "annual_return_pct": 25.8,
      "volatility_pct": 18.5,
      "sharpe_ratio": 1.4,
      "max_drawdown_pct": 8.2
    },
    "equity_curve": [
      {
        "date": "2023-01-01",
        "value": 100000
      }
    ],
    "portfolio_composition": [
      {
        "symbol": "AAPL",
        "weight": 0.5,
        "value": 50000
      }
    ]
  }
}
```

### 주가 데이터 조회
```http
GET /api/v1/backtest/stock-data/AAPL?start_date=2023-01-01&end_date=2023-12-31
```

**응답:**
```json
{
  "ticker": "AAPL",
  "data": [
    {
      "date": "2023-01-01",
      "close": 152.0,
      "volume": 1000000
    }
  ]
}
```

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

## 에러 처리

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
- **DB 캐시 우선**: MySQL에 저장된 데이터를 우선 사용
- **외부 API 보강**: 누락된 데이터는 yfinance에서 조회 후 자동 저장
- **에러 분류**: 404(데이터 없음), 422(검증 실패), 429(레이트 제한), 0(네트워크 오류)

### 현금 자산 처리
- 심볼: `CASH` 또는 한글 `현금`
- 특성: 0% 수익률, 무변동성
- 주가/뉴스 조회 시 빈 배열 반환
