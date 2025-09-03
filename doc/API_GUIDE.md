# API 가이드

FastAPI 기반 백테스팅 시스템의 REST API 문서입니다.

## 기본 정보

- **Base URL**: `http://localhost:8001` (개발), `https://api.backtest.com` (프로덕션)
- **API 버전**: v1
- **Content-Type**: `application/json`

## 백테스트 API

### 통합 백테스트 실행
단일 종목과 포트폴리오 백테스트를 통합 처리합니다.

```http
POST /api/v1/backtest
```

**요청:**
```json
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "amount": 4000,
      "investment_type": "lump_sum",
      "asset_type": "stock"
    },
    {
      "symbol": "현금",
      "amount": 2000,
      "asset_type": "cash"
    }
  ],
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "strategy": "buy_and_hold",
  "commission": 0.002
}
```

**응답:**
```json
{
  "success": true,
  "portfolio_statistics": {
    "Total_Return": 23.46,
    "Annual_Return": 11.23,
    "Sharpe_Ratio": 0.61,
    "Max_Drawdown": -8.23
  },
  "individual_returns": {
    "AAPL": { "return": 28.5, "weight": 0.67 },
    "현금": { "return": 0.0, "weight": 0.33 }
  }
}
```

### 차트 데이터 조회
단일 종목의 상세 차트 데이터를 조회합니다.

```http
POST /api/v1/backtest/chart-data
```

**요청:**
```json
{
  "ticker": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 10000,
  "strategy": "sma_crossover",
  "strategy_params": {
    "short_window": 10,
    "long_window": 20
  }
}
```

**응답:**
```json
{
  "ohlc_data": [
    {
      "date": "2023-01-03",
      "open": 130.28,
      "high": 130.90,
      "low": 124.17,
      "close": 125.07,
      "volume": 112117471
    }
  ],
  "equity_data": [
    {
      "date": "2023-01-03",
      "equity": 10000.0,
      "return_pct": 0.0,
      "drawdown_pct": 0.0
    }
  ],
  "trade_markers": [
    {
      "date": "2023-01-03",
      "price": 125.07,
      "type": "entry",
      "side": "buy",
      "size": 79.96
    }
  ],
  "indicators": [
    {
      "name": "SMA_10",
      "color": "#ff7300",
      "data": [{ "date": "2023-01-13", "value": 127.45 }]
    }
  ],
  "summary_stats": {
    "total_return_pct": 23.46,
    "total_trades": 15,
    "win_rate_pct": 66.67,
    "max_drawdown_pct": -8.23,
    "sharpe_ratio": 1.45
  }
}
```

## 뉴스 API

### 종목별 뉴스 검색
특정 종목의 뉴스를 검색합니다. 70+ 종목을 지원합니다.

```http
GET /api/v1/naver-news/ticker/{ticker}?display=10
```

**파라미터:**
- `ticker`: 종목 코드 (예: AAPL, 005930.KS)
- `display`: 결과 수 (1-100, 기본값: 10)

**응답:**
```json
{
  "status": "success",
  "message": "AAPL(애플 주가) 관련 뉴스 10건을 조회했습니다.",
  "data": {
    "ticker": "AAPL",
    "query": "애플 주가",
    "total_count": 10,
    "news_list": [
      {
        "title": "애플 주가 급등, 신제품 출시 기대감",
        "link": "https://n.news.naver.com/...",
        "description": "애플이 신제품 발표를 앞두고...",
        "pubDate": "Mon, 01 Sep 2025 21:01:00 +0900"
      }
    ]
  }
}
```

### 날짜별 뉴스 검색
특정 기간의 뉴스를 검색합니다.

```http
GET /api/v1/naver-news/ticker/{ticker}/date?start_date=2025-09-01&end_date=2025-09-01&display=50
```

## 투자 전략

### 지원 전략 목록

1. **Buy & Hold** (`buy_and_hold`)
   - 매수 후 보유
   - 파라미터: 없음

2. **SMA Crossover** (`sma_crossover`)
   - 단순이동평균 교차
   - 파라미터: `short_window`, `long_window`

3. **RSI Strategy** (`rsi_strategy`)
   - RSI 과매수/과매도
   - 파라미터: `rsi_period`, `rsi_overbought`, `rsi_oversold`

4. **Bollinger Bands** (`bollinger_bands`)
   - 볼린저 밴드 기반
   - 파라미터: `period`, `std_dev`

5. **MACD Strategy** (`macd_strategy`)
   - MACD 교차
   - 파라미터: `fast_period`, `slow_period`, `signal_period`

### 현금 자산 처리

현금 자산은 `asset_type: 'cash'`로 구분되며, 무위험 자산으로 처리됩니다.

- **수익률**: 0% 고정
- **변동성**: 없음
- **역할**: 포트폴리오 리스크 완화

## 에러 처리

### HTTP 상태 코드
- `200`: 성공
- `400`: 잘못된 요청
- `404`: 리소스 없음
- `422`: 유효성 검사 실패
- `500`: 서버 오류

### 에러 응답 형식
```json
{
  "detail": "Ticker 'INVALID' not found",
  "status_code": 404
}
```

## 제한사항

1. **데이터 지연**: 실시간이 아닌 지연 데이터 제공
2. **캐싱**: MySQL에 1일간 캐시 저장
3. **포트폴리오**: 최대 20개 종목
4. **백테스트 기간**: 최소 30일 이상 권장

## 업데이트 내역

- **v1.0**: 기본 백테스트 API
- **v1.1**: 포트폴리오 지원
- **v1.2**: 현금 자산 처리
- **v1.3**: DCA 투자 방식
- **v1.4**: 네이버 뉴스 API (70+ 종목)
