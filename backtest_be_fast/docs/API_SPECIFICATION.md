# 백테스트 플랫폼 API 명세서

> **최종 업데이트**: 2025-01-28  
> **API 버전**: v1  
> **베이스 URL**: `http://localhost:8000/api/v1`

## 목차
1. [백테스팅 API](#1-백테스팅-api)
2. [전략 관리 API](#2-전략-관리-api)
3. [최적화 API](#3-최적화-api)
4. [네이버 뉴스 API](#4-네이버-뉴스-api)

---

## 1. 백테스팅 API

### 1.1 포트폴리오 백테스트 실행 (통합 엔드포인트)
**엔드포인트**: `POST /backtest/portfolio`  
**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`, `usePortfolioBacktest.ts`)  
**설명**: 단일 종목 및 포트폴리오 백테스트를 모두 처리하는 통합 엔드포인트

> **참고**: 이전의 `/backtest/execute`는 삭제되었습니다. 모든 백테스팅 요청은 이 엔드포인트로 통합되었습니다.

**요청 (PortfolioBacktestRequest)**:
```json
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "weight": 50,
      "investment_type": "lump_sum"
    },
    {
      "symbol": "GOOGL",
      "weight": 50,
      "investment_type": "lump_sum"
    }
  ],
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "commission": 0.002,
  "rebalance_frequency": "monthly",
  "strategy": "buy_and_hold"
}
```

**응답**:
```json
{
  "status": "success",
  "data": {
    "portfolio_statistics": {
      "Start": "2024-01-02",
      "End": "2024-03-28",
      "Total_Return": 0.86,
      "Annual_Return": 3.72,
      "Sharpe_Ratio": 0.18,
      "Max_Drawdown": -13.14
    },
    "individual_returns": {
      "AAPL_0": {
        "symbol": "AAPL",
        "return": -7.51,
        "start_price": 184.08,
        "end_price": 170.26
      }
    },
    "equity_curve": {
      "2024-01-02": 100.0,
      "2024-01-03": 99.90
    }
  }
}
```

---

### 1.2 주가 데이터 조회
**엔드포인트**: `GET /backtest/stock-data/{ticker}`  
**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  
**설명**: 지정된 기간의 주가 데이터 조회

**쿼리 파라미터**:
- `start_date`: 시작 날짜 (YYYY-MM-DD)
- `end_date`: 종료 날짜 (YYYY-MM-DD)

**응답**:
```json
{
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "price_data": [
      {
        "date": "2024-01-02",
        "price": 185.64,
        "volume": 82488280
      }
    ]
  }
}
```

---

### 1.3 환율 데이터 조회
**엔드포인트**: `GET /backtest/exchange-rate`  
**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  
**설명**: 원달러 환율 데이터 조회

**쿼리 파라미터**:
- `start_date`: 시작 날짜 (YYYY-MM-DD)
- `end_date`: 종료 날짜 (YYYY-MM-DD)

**응답**:
```json
{
  "status": "success",
  "data": {
    "base_currency": "USD",
    "target_currency": "KRW",
    "exchange_rates": [
      {
        "date": "2024-01-02",
        "rate": 1305.50,
        "volume": 0
      }
    ]
  }
}
```

---

### 1.4 주가 급등/급락일 뉴스 조회
**엔드포인트**: `GET /backtest/stock-volatility-news/{ticker}`  
**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  
**설명**: 5% 이상 변동한 날의 뉴스 조회

**쿼리 파라미터**:
- `start_date`: 시작 날짜 (YYYY-MM-DD)
- `end_date`: 종료 날짜 (YYYY-MM-DD)
- `threshold`: 변동 임계값 (기본값: 5.0%)

**응답**:
```json
{
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "threshold": 5.0,
    "period": "2024-01-01 ~ 2024-03-31",
    "total_events": 3,
    "volatility_events": [
      {
        "date": "2024-03-15",
        "daily_return": 6.54,
        "close_price": 172.69,
        "volume": 95123400,
        "event_type": "급등"
      }
    ]
  }
}
```

---

## 2. 전략 관리 API

### 2.1 전략 목록 조회
**엔드포인트**: `GET /strategies/`  
**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`)  
**설명**: 사용 가능한 모든 백테스팅 전략 목록 반환

**응답 (StrategyListResponse)**:
```json
{
  "strategies": [
    {
      "name": "sma",
      "description": "단순이동평균(SMA) 크로스오버 전략",
      "parameters": {
        "short_window": {
          "type": "int",
          "default": 20,
          "min": 5,
          "max": 100,
          "description": "단기 이동평균 기간"
        },
        "long_window": {
          "type": "int",
          "default": 50,
          "min": 20,
          "max": 200,
          "description": "장기 이동평균 기간"
        }
      }
    },
    {
      "name": "rsi",
      "description": "RSI 과매수/과매도 전략",
      "parameters": {
        "rsi_period": {
          "type": "int",
          "default": 14,
          "min": 5,
          "max": 30
        },
        "oversold": {
          "type": "int",
          "default": 30,
          "min": 10,
          "max": 40
        },
        "overbought": {
          "type": "int",
          "default": 70,
          "min": 60,
          "max": 90
        }
      }
    }
  ],
  "total_count": 6
}
```

---

### 2.2 특정 전략 정보 조회
**엔드포인트**: `GET /strategies/{strategy_name}`  
**상태**: ❌ **미사용** (프론트엔드에서 호출 안함)  
**설명**: 특정 전략의 상세 정보 조회

---

## 3. 최적화 API

### 3.1 전략 파라미터 최적화
**엔드포인트**: `POST /optimize/run`  
**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`)  
**설명**: 주어진 전략의 파라미터를 최적화하여 최고 성능 탐색

**요청 (OptimizationRequest)**:
```json
{
  "ticker": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 10000.0,
  "strategy": "sma",
  "param_ranges": {
    "short_window": [5, 30],
    "long_window": [40, 100]
  },
  "method": "grid",
  "maximize": "SQN",
  "max_tries": 100
}
```

**응답 (OptimizationResult)**:
```json
{
  "best_params": {
    "short_window": 15,
    "long_window": 60
  },
  "best_performance": {
    "Return [%]": 23.45,
    "Sharpe Ratio": 1.67,
    "Max Drawdown [%]": -7.82
  },
  "all_results": [
    {
      "params": {"short_window": 10, "long_window": 50},
      "performance": {"Return [%]": 18.23}
    }
  ]
}
```

---

## 4. 네이버 뉴스 API

### 4.1 뉴스 검색
**엔드포인트**: `GET /naver-news/search`  
**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`, `backtestApi.ts`)  
**설명**: 네이버 뉴스 검색 API

**쿼리 파라미터**:
- `query`: 검색어 (필수)
- `display`: 검색 결과 수 (1-100, 기본값: 10)

**응답**:
```json
{
  "status": "success",
  "message": "'애플' 관련 뉴스 10건을 조회했습니다.",
  "data": {
    "query": "애플",
    "total_count": 10,
    "news_list": [
      {
        "title": "애플 AI 칩 개발 가속화",
        "link": "https://news.naver.com/...",
        "description": "애플이 AI 전용 칩 개발에 박차를 가하고 있다...",
        "pubDate": "Mon, 28 Jan 2025 10:30:00 +0900"
      }
    ]
  }
}
```

---

### 4.2 종목별 최신 뉴스 검색 (DB 캐싱)
**엔드포인트**: `GET /naver-news/ticker/{ticker}`  
**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  
**설명**: 특정 종목의 최신 뉴스 조회 (24시간 DB 캐시 지원)

**쿼리 파라미터**:
- `display`: 검색 결과 수 (1-100, 기본값: 10)
- `force_refresh`: DB 캐시 무시 여부 (기본값: false)

**응답**:
```json
{
  "status": "success",
  "message": "AAPL(애플 주식) 관련 뉴스 10건을 조회했습니다.",
  "data": {
    "ticker": "AAPL",
    "query": "애플 주식",
    "total_count": 10,
    "from_cache": false,
    "news_list": [...]
  }
}
```

---

### 4.3 종목별 날짜 뉴스 검색 (DB 캐싱)
**엔드포인트**: `GET /naver-news/ticker/{ticker}/date`  
**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  
**설명**: 특정 종목의 특정 날짜 범위 뉴스 조회 (DB 캐싱 지원)

**쿼리 파라미터**:
- `start_date`: 시작 날짜 (YYYY-MM-DD, 필수)
- `end_date`: 종료 날짜 (YYYY-MM-DD, 없으면 start_date와 동일)
- `display`: 검색 결과 수 (10-100, 기본값: 50)
- `force_refresh`: DB 캐시 무시 여부 (기본값: false)

**응답**:
```json
{
  "status": "success",
  "message": "AAPL(애플 주식) 관련 뉴스를 2024-03-15~2024-03-15 기간에서 5건 조회했습니다.",
  "data": {
    "ticker": "AAPL",
    "query": "애플 주식",
    "start_date": "2024-03-15",
    "end_date": "2024-03-15",
    "total_count": 5,
    "from_cache": true,
    "news_list": [...]
  }
}
```

---

### 4.4 날짜별 뉴스 검색
**엔드포인트**: `GET /naver-news/search-by-date`  
**상태**: ❌ **미사용** (프론트엔드에서 호출 안함)  
**설명**: 특정 날짜 범위의 뉴스 검색 (캐싱 없음)

---

### 4.5 네이버 뉴스 API 테스트
**엔드포인트**: `GET /naver-news/test`  
**상태**: ❌ **개발/테스트용**  
**설명**: 네이버 뉴스 API 연동 테스트

---

## API 사용 현황 요약

| 엔드포인트 | 메서드 | 상태 | 프론트엔드 사용처 |
|-----------|--------|------|------------------|
| `/backtest/portfolio` | POST | ✅ 사용중 | `backtestService.ts`, `usePortfolioBacktest.ts` |
| `/backtest/stock-data/{ticker}` | GET | ✅ 사용중 | `backtestApi.ts` |
| `/backtest/exchange-rate` | GET | ✅ 사용중 | `backtestApi.ts` |
| `/backtest/stock-volatility-news/{ticker}` | GET | ✅ 사용중 | `backtestApi.ts` |
| `/strategies/` | GET | ✅ 사용중 | `backtestService.ts` |
| `/strategies/{name}` | GET | ❌ 미사용 | - |
| `/optimize/run` | POST | ✅ 사용중 | `backtestService.ts` |
| `/naver-news/search` | GET | ✅ 사용중 | `backtestService.ts`, `backtestApi.ts` |
| `/naver-news/ticker/{ticker}` | GET | ✅ 사용중 | `backtestApi.ts` |
| `/naver-news/ticker/{ticker}/date` | GET | ✅ 사용중 | `backtestApi.ts` |
| `/naver-news/search-by-date` | GET | ❌ 미사용 | - |
| `/naver-news/test` | GET | ⚠️ 테스트용 | - |

**통계**:
- **총 엔드포인트**: 12개 (-1, `/backtest/execute` 삭제)
- **프론트엔드 사용중**: 9개 (75%)
- **미사용 (삭제 후보)**: 2개 (17%)
- **테스트/개발용**: 1개 (8%)

---

## 에러 응답 형식

모든 API는 실패 시 다음 형식으로 에러를 반환합니다:

```json
{
  "detail": "사용자 친화적 에러 메시지 (오류 ID: abc123)"
}
```

**HTTP 상태 코드**:
- `200 OK`: 정상 처리
- `400 Bad Request`: 잘못된 요청 파라미터
- `404 Not Found`: 데이터를 찾을 수 없음
- `405 Method Not Allowed`: 허용되지 않는 HTTP 메서드
- `500 Internal Server Error`: 서버 내부 오류

---

## 프록시 설정 (프론트엔드)

Vite 개발 서버는 다음과 같이 프록시를 설정합니다 (`vite.config.ts`):

```typescript
proxy: {
  '/api/v1/backtest': {
    target: 'http://localhost:8000',  // 백엔드 FastAPI 서버
    changeOrigin: true,
  },
  '/api/v1/naver-news': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

이를 통해 프론트엔드(5173 포트)에서 `/api/v1/*` 요청을 백엔드(8000 포트)로 프록시합니다.

---

## 데이터 소스

- **주가 데이터**: yfinance (MySQL DB 캐싱)
- **뉴스 데이터**: 네이버 검색 API (MySQL DB 캐싱)
- **환율 데이터**: yfinance (KRW=X 심볼)

---

## 변경 이력

### 2025-01-28
- ✅ `/backtest/portfolio` 엔드포인트 추가 및 정상 작동 확인
- ✅ 프론트엔드 API 경로 수정 (`/v1/` → `/api/v1/`)
- ✅ `strategy_service.py`에 `get_available_strategies()` 메서드 추가
- ✅ 전략 파라미터 직렬화 버그 수정 (Python `type` → `str`)
- ✅ 모든 API 엔드포인트 문서화 완료
- ✅ 프론트엔드 사용 현황 분석 완료
- ✅ **종합 테스트 통과**: 6개 주요 API 정상 작동 확인
- ✅ **백테스트 엔드포인트 통합**: `/backtest/execute` 삭제, `/backtest/portfolio`로 통합

---

**문의**: 백엔드 팀  
**OpenAPI 문서**: http://localhost:8000/api/v1/docs  
**상태**: ✅ 프로덕션 준비 완료
