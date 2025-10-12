# 백테스트 플랫폼 API 명세서# 백테스트 플랫폼 API 명세서# 백테스트 플랫폼 API 명세서



## 개요



- **베이스 URL**: `http://localhost:8000/api/v1`## 개요> **최종 업데이트**: 2025-01-28  

- **데이터 형식**: JSON

- **인증**: 불필요> **API 버전**: v1  



## 엔드포인트- **API 버전**: v1> **베이스 URL**: `http://localhost:8000/api/v1`



### 포트폴리오 백테스트 실행- **베이스 URL**: `http://localhost:8000/api/v1`



**`POST /api/v1/backtest`**- **프로토콜**: HTTP/HTTPS## 목차



포트폴리오 백테스트를 실행하고 필요한 모든 데이터를 반환합니다.- **데이터 형식**: JSON1. [백테스팅 API](#1-백테스팅-api)



#### 요청- **인증**: 현재 불필요 (향후 JWT 추가 예정)2. [전략 관리 API](#2-전략-관리-api)



```json3. [최적화 API](#3-최적화-api)

{

  "portfolio": [## 목차4. [네이버 뉴스 API](#4-네이버-뉴스-api)

    {

      "symbol": "AAPL",

      "weight": 50,

      "investment_type": "lump_sum",1. [백테스트 API](#백테스트-api)---

      "asset_type": "stock"

    },2. [응답 형식](#응답-형식)

    {

      "symbol": "GOOGL",3. [에러 처리](#에러-처리)## 1. 백테스팅 API

      "weight": 50,

      "investment_type": "dca",

      "dca_periods": 6,

      "asset_type": "stock"## 백테스트 API### 1.1 포트폴리오 백테스트 실행 (통합 엔드포인트)

    }

  ],**엔드포인트**: `POST /backtest/portfolio`  

  "start_date": "2024-01-01",

  "end_date": "2024-12-31",### 포트폴리오 백테스트 실행**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`, `usePortfolioBacktest.ts`)  

  "commission": 0.002,

  "rebalance_frequency": "monthly",**설명**: 단일 종목 및 포트폴리오 백테스트를 모두 처리하는 통합 엔드포인트

  "strategy": "buy_and_hold"

}**엔드포인트**: `POST /api/v1/backtest`

```

> **참고**: 이전의 `/backtest/execute`는 삭제되었습니다. 모든 백테스팅 요청은 이 엔드포인트로 통합되었습니다.

**필드 설명:**

**설명**: 포트폴리오 백테스트를 실행하고 필요한 모든 데이터를 한 번에 반환합니다. 단일 종목 백테스트도 이 엔드포인트로 처리합니다.

- `portfolio` (array, required): 포트폴리오 구성 종목 리스트 (1~10개)

  - `symbol` (string, required): 주식 심볼 (예: AAPL, GOOGL)**요청 (PortfolioBacktestRequest)**:

  - `weight` (float, optional): 비중(%) (0~100, amount와 동시 사용 불가)

  - `amount` (float, optional): 투자 금액 (USD, weight와 동시 사용 불가)**프론트엔드 사용처**:```json

  - `investment_type` (string, optional): 투자 방식 (lump_sum, dca) 기본값: lump_sum

  - `dca_periods` (integer, optional): 분할 매수 기간(개월) (1~60) 기본값: 12- `src/features/backtest/api/backtestService.ts`{

  - `asset_type` (string, optional): 자산 유형 (stock, cash) 기본값: stock

- `src/features/backtest/hooks/useBacktest.ts`  "portfolio": [

- `start_date` (string, required): 시작 날짜 (YYYY-MM-DD)

- `end_date` (string, required): 종료 날짜 (YYYY-MM-DD)    {

- `commission` (float, optional): 거래 수수료율 (0~0.1) 기본값: 0.002

- `rebalance_frequency` (string, optional): 리밸런싱 주기 (monthly, quarterly, yearly) 기본값: monthly#### 요청 스키마      "symbol": "AAPL",

- `strategy` (string, optional): 전략명 기본값: buy_and_hold

      "weight": 50,

#### 응답

**Content-Type**: `application/json`      "investment_type": "lump_sum"

```json

{    },

  "status": "success",

  "data": {```json    {

    "portfolio_statistics": {

      "Start": "2024-01-02",{      "symbol": "GOOGL",

      "End": "2024-12-30",

      "Total_Return": 12.45,  "portfolio": [      "weight": 50,

      "Annual_Return": 12.50,

      "Sharpe_Ratio": 1.23,    {      "investment_type": "lump_sum"

      "Max_Drawdown": -8.45,

      "Win_Rate": 65.4      "symbol": "AAPL",    }

    },

    "equity_curve": {      "weight": 50,  ],

      "2024-01-02": 10000.0,

      "2024-01-03": 10050.5      "investment_type": "lump_sum",  "start_date": "2024-01-01",

    },

    "individual_returns": {      "asset_type": "stock"  "end_date": "2024-03-31",

      "AAPL_0": {

        "symbol": "AAPL",    },  "commission": 0.002,

        "return": 15.2,

        "start_price": 184.08,    {  "rebalance_frequency": "monthly",

        "end_price": 212.15,

        "weight": 50.0      "symbol": "GOOGL",  "strategy": "buy_and_hold"

      }

    },      "weight": 50,}

    "stock_data": {

      "AAPL": [      "investment_type": "dca",```

        {"date": "2024-01-02", "price": 184.08, "volume": 82488280}

      ]      "dca_periods": 6,

    },

    "exchange_rates": [      "asset_type": "stock"**응답**:

      {"date": "2024-01-02", "rate": 1305.50, "volume": 0}

    ],    }```json

    "exchange_stats": {

      "start_rate": 1305.50,  ],{

      "end_rate": 1320.80,

      "avg_rate": 1312.45,  "start_date": "2024-01-01",  "status": "success",

      "min_rate": 1295.20,

      "max_rate": 1335.90,  "end_date": "2024-12-31",  "data": {

      "rate_change_pct": 1.17

    },  "commission": 0.002,    "portfolio_statistics": {

    "volatility_events": {

      "AAPL": [  "rebalance_frequency": "monthly",      "Start": "2024-01-02",

        {

          "date": "2024-03-15",  "strategy": "buy_and_hold"      "End": "2024-03-28",

          "daily_return": 6.54,

          "close_price": 172.69,}      "Total_Return": 0.86,

          "volume": 95123400,

          "event_type": "급등"```      "Annual_Return": 3.72,

        }

      ]      "Sharpe_Ratio": 0.18,

    },

    "latest_news": {#### 요청 필드 설명      "Max_Drawdown": -13.14

      "AAPL": [

        {    },

          "title": "애플 AI 칩 개발 가속화",

          "link": "https://news.naver.com/...",**portfolio** (array, required)    "individual_returns": {

          "description": "애플이 AI 전용 칩 개발에 박차를 가하고 있다...",

          "pubDate": "Mon, 28 Jan 2025 10:30:00 +0900"- 포트폴리오 구성 종목 리스트      "AAPL_0": {

        }

      ]- 최소 1개, 최대 10개        "symbol": "AAPL",

    },

    "sp500_benchmark": [        "return": -7.51,

      {"date": "2024-01-02", "price": 4742.83, "volume": 0}

    ],**portfolio[].symbol** (string, required)        "start_price": 184.08,

    "nasdaq_benchmark": [

      {"date": "2024-01-02", "price": 14765.94, "volume": 0}- 주식 심볼 (예: AAPL, GOOGL, TSLA)        "end_price": 170.26

    ]

  }- 영문자만 허용, 대소문자 구분 없음      }

}

```- 특수 심볼: "CASH" (현금 자산)    },



**응답 필드:**    "equity_curve": {



- `portfolio_statistics`: 포트폴리오 전체 성과 지표**portfolio[].weight** (float, optional)      "2024-01-02": 100.0,

- `equity_curve`: 일별 자산 가치 곡선

- `individual_returns`: 개별 종목 수익률- 포트폴리오 내 비중 (%)      "2024-01-03": 99.90

- `stock_data`: 종목별 일별 주가 데이터

- `exchange_rates`: 원달러 환율 데이터- 0 ~ 100 범위    }

- `exchange_stats`: 환율 통계

- `volatility_events`: 종목별 급등/급락 이벤트 (5% 이상 변동)- amount와 동시 입력 불가  }

- `latest_news`: 종목별 최신 뉴스 (최대 15건)

- `sp500_benchmark`: S&P 500 지수 데이터- 모든 종목의 weight 합계는 100이어야 함}

- `nasdaq_benchmark`: NASDAQ 지수 데이터

```

## 에러 응답

**portfolio[].amount** (float, optional)

### HTTP 상태 코드

- 투자 금액 (USD)---

- `200 OK`: 요청 성공

- `400 Bad Request`: 잘못된 요청 파라미터- 양수만 허용

- `404 Not Found`: 데이터를 찾을 수 없음

- `422 Unprocessable Entity`: 유효성 검증 실패- weight와 동시 입력 불가### 1.2 주가 데이터 조회

- `500 Internal Server Error`: 서버 내부 오류

**엔드포인트**: `GET /backtest/stock-data/{ticker}`  

### 에러 형식

**portfolio[].investment_type** (string, optional)**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  

```json

{- 투자 방식**설명**: 지정된 기간의 주가 데이터 조회

  "detail": "에러 메시지 (오류 ID: abc123)"

}- 기본값: "lump_sum"

```

- 허용값:**쿼리 파라미터**:

유효성 검증 실패 시:

  - `lump_sum`: 일시불 투자- `start_date`: 시작 날짜 (YYYY-MM-DD)

```json

{  - `dca`: 분할 매수 (Dollar Cost Averaging)- `end_date`: 종료 날짜 (YYYY-MM-DD)

  "detail": [

    {

      "loc": ["body", "portfolio", 0, "symbol"],

      "msg": "field required",**portfolio[].dca_periods** (integer, optional)**응답**:

      "type": "value_error.missing"

    }- 분할 매수 기간 (개월)```json

  ]

}- investment_type이 "dca"일 때만 유효{

```

- 기본값: 12  "status": "success",

## 데이터 소스

- 범위: 1 ~ 60  "data": {

- **주가 데이터**: yfinance (MySQL 캐싱)

- **환율 데이터**: yfinance (KRW=X 심볼)    "symbol": "AAPL",

- **뉴스 데이터**: 네이버 검색 API (MySQL 캐싱)

**portfolio[].asset_type** (string, optional)    "price_data": [

## API 문서

- 자산 유형      {

- **Swagger UI**: http://localhost:8000/api/v1/docs

- **ReDoc**: http://localhost:8000/api/v1/redoc- 기본값: "stock"        "date": "2024-01-02",

- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

- 허용값:        "price": 185.64,

  - `stock`: 주식        "volume": 82488280

  - `cash`: 현금      }

    ]

**start_date** (string, required)  }

- 백테스트 시작 날짜}

- 형식: YYYY-MM-DD```

- end_date보다 이전이어야 함

---

**end_date** (string, required)

- 백테스트 종료 날짜### 1.3 환율 데이터 조회

- 형식: YYYY-MM-DD**엔드포인트**: `GET /backtest/exchange-rate`  

- start_date보다 이후여야 함**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  

**설명**: 원달러 환율 데이터 조회

**commission** (float, optional)

- 거래 수수료율**쿼리 파라미터**:

- 기본값: 0.002 (0.2%)- `start_date`: 시작 날짜 (YYYY-MM-DD)

- 범위: 0 ~ 0.1- `end_date`: 종료 날짜 (YYYY-MM-DD)



**rebalance_frequency** (string, optional)**응답**:

- 리밸런싱 주기```json

- 기본값: "monthly"{

- 허용값:  "status": "success",

  - `monthly`: 매월  "data": {

  - `quarterly`: 분기별    "base_currency": "USD",

  - `yearly`: 연간    "target_currency": "KRW",

    "exchange_rates": [

**strategy** (string, optional)      {

- 백테스트 전략명        "date": "2024-01-02",

- 기본값: "buy_and_hold"        "rate": 1305.50,

- 현재는 buy_and_hold만 지원        "volume": 0

      }

#### 응답 스키마    ]

  }

**Status Code**: `200 OK`}

```

```json

{---

  "status": "success",

  "data": {### 1.4 주가 급등/급락일 뉴스 조회

    "portfolio_statistics": {**엔드포인트**: `GET /backtest/stock-volatility-news/{ticker}`  

      "Start": "2024-01-02",**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  

      "End": "2024-12-30",**설명**: 5% 이상 변동한 날의 뉴스 조회

      "Total_Return": 12.45,

      "Annual_Return": 12.50,**쿼리 파라미터**:

      "Sharpe_Ratio": 1.23,- `start_date`: 시작 날짜 (YYYY-MM-DD)

      "Max_Drawdown": -8.45,- `end_date`: 종료 날짜 (YYYY-MM-DD)

      "Win_Rate": 65.4- `threshold`: 변동 임계값 (기본값: 5.0%)

    },

    "equity_curve": {**응답**:

      "2024-01-02": 10000.0,```json

      "2024-01-03": 10050.5,{

      "2024-01-04": 10025.3  "status": "success",

    },  "data": {

    "individual_returns": {    "symbol": "AAPL",

      "AAPL_0": {    "threshold": 5.0,

        "symbol": "AAPL",    "period": "2024-01-01 ~ 2024-03-31",

        "return": 15.2,    "total_events": 3,

        "start_price": 184.08,    "volatility_events": [

        "end_price": 212.15,      {

        "weight": 50.0        "date": "2024-03-15",

      },        "daily_return": 6.54,

      "GOOGL_0": {        "close_price": 172.69,

        "symbol": "GOOGL",        "volume": 95123400,

        "return": 9.7,        "event_type": "급등"

        "start_price": 140.93,      }

        "end_price": 154.60,    ]

        "weight": 50.0  }

      }}

    },```

    "stock_data": {

      "AAPL": [---

        {

          "date": "2024-01-02",## 2. 전략 관리 API

          "price": 184.08,

          "volume": 82488280### 2.1 전략 목록 조회

        }**엔드포인트**: `GET /strategies/`  

      ],**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`)  

      "GOOGL": [**설명**: 사용 가능한 모든 백테스팅 전략 목록 반환

        {

          "date": "2024-01-02",**응답 (StrategyListResponse)**:

          "price": 140.93,```json

          "volume": 23453210{

        }  "strategies": [

      ]    {

    },      "name": "sma",

    "exchange_rates": [      "description": "단순이동평균(SMA) 크로스오버 전략",

      {      "parameters": {

        "date": "2024-01-02",        "short_window": {

        "rate": 1305.50,          "type": "int",

        "volume": 0          "default": 20,

      }          "min": 5,

    ],          "max": 100,

    "exchange_stats": {          "description": "단기 이동평균 기간"

      "start_rate": 1305.50,        },

      "end_rate": 1320.80,        "long_window": {

      "avg_rate": 1312.45,          "type": "int",

      "min_rate": 1295.20,          "default": 50,

      "max_rate": 1335.90,          "min": 20,

      "rate_change_pct": 1.17          "max": 200,

    },          "description": "장기 이동평균 기간"

    "volatility_events": {        }

      "AAPL": [      }

        {    },

          "date": "2024-03-15",    {

          "daily_return": 6.54,      "name": "rsi",

          "close_price": 172.69,      "description": "RSI 과매수/과매도 전략",

          "volume": 95123400,      "parameters": {

          "event_type": "급등"        "rsi_period": {

        }          "type": "int",

      ]          "default": 14,

    },          "min": 5,

    "latest_news": {          "max": 30

      "AAPL": [        },

        {        "oversold": {

          "title": "애플 AI 칩 개발 가속화",          "type": "int",

          "link": "https://news.naver.com/...",          "default": 30,

          "description": "애플이 AI 전용 칩 개발에 박차를 가하고 있다...",          "min": 10,

          "pubDate": "Mon, 28 Jan 2025 10:30:00 +0900"          "max": 40

        }        },

      ]        "overbought": {

    },          "type": "int",

    "sp500_benchmark": [          "default": 70,

      {          "min": 60,

        "date": "2024-01-02",          "max": 90

        "price": 4742.83,        }

        "volume": 0      }

      }    }

    ],  ],

    "nasdaq_benchmark": [  "total_count": 6

      {}

        "date": "2024-01-02",```

        "price": 14765.94,

        "volume": 0---

      }

    ]### 2.2 특정 전략 정보 조회

  }**엔드포인트**: `GET /strategies/{strategy_name}`  

}**상태**: ❌ **미사용** (프론트엔드에서 호출 안함)  

```**설명**: 특정 전략의 상세 정보 조회



#### 응답 필드 설명---



**status** (string)## 3. 최적화 API

- 응답 상태

- 값: "success" 또는 "error"### 3.1 전략 파라미터 최적화

**엔드포인트**: `POST /optimize/run`  

**data** (object)**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`)  

- 백테스트 결과 및 부가 데이터**설명**: 주어진 전략의 파라미터를 최적화하여 최고 성능 탐색



**data.portfolio_statistics** (object)**요청 (OptimizationRequest)**:

- 포트폴리오 전체 성과 지표```json

- Start: 실제 시작일{

- End: 실제 종료일  "ticker": "AAPL",

- Total_Return: 총 수익률 (%)  "start_date": "2024-01-01",

- Annual_Return: 연간 수익률 (%)  "end_date": "2024-12-31",

- Sharpe_Ratio: 샤프 비율  "initial_cash": 10000.0,

- Max_Drawdown: 최대 낙폭 (%)  "strategy": "sma",

- Win_Rate: 승률 (%)  "param_ranges": {

    "short_window": [5, 30],

**data.equity_curve** (object)    "long_window": [40, 100]

- 일별 자산 가치 곡선  },

- 키: 날짜 (YYYY-MM-DD)  "method": "grid",

- 값: 자산 가치 (USD)  "maximize": "SQN",

  "max_tries": 100

**data.individual_returns** (object)}

- 개별 종목 수익률```

- 키: "{종목심볼}_{인덱스}"

- symbol: 종목 심볼**응답 (OptimizationResult)**:

- return: 수익률 (%)```json

- start_price: 시작 가격{

- end_price: 종료 가격  "best_params": {

- weight: 포트폴리오 내 비중 (%)    "short_window": 15,

    "long_window": 60

**data.stock_data** (object)  },

- 종목별 일별 주가 데이터  "best_performance": {

- 키: 종목 심볼    "Return [%]": 23.45,

- 값: 날짜별 가격/거래량 배열    "Sharpe Ratio": 1.67,

    "Max Drawdown [%]": -7.82

**data.exchange_rates** (array)  },

- 원달러 환율 데이터  "all_results": [

- date: 날짜    {

- rate: 환율 (KRW/USD)      "params": {"short_window": 10, "long_window": 50},

- volume: 거래량 (항상 0)      "performance": {"Return [%]": 18.23}

    }

**data.exchange_stats** (object)  ]

- 환율 통계}

- start_rate: 기간 시작 환율```

- end_rate: 기간 종료 환율

- avg_rate: 평균 환율---

- min_rate: 최저 환율

- max_rate: 최고 환율## 4. 네이버 뉴스 API

- rate_change_pct: 환율 변동률 (%)

### 4.1 뉴스 검색

**data.volatility_events** (object)**엔드포인트**: `GET /naver-news/search`  

- 종목별 급등/급락 이벤트**상태**: ✅ **사용중** (프론트엔드: `backtestService.ts`, `backtestApi.ts`)  

- 키: 종목 심볼**설명**: 네이버 뉴스 검색 API

- 5% 이상 변동일만 포함

- event_type: "급등" 또는 "급락"**쿼리 파라미터**:

- `query`: 검색어 (필수)

**data.latest_news** (object)- `display`: 검색 결과 수 (1-100, 기본값: 10)

- 종목별 최신 뉴스 (최대 15건)

- 네이버 뉴스 API 사용**응답**:

- pubDate: RFC 2822 형식```json

{

**data.sp500_benchmark** (array)  "status": "success",

- S&P 500 지수 데이터  "message": "'애플' 관련 뉴스 10건을 조회했습니다.",

- 벤치마크 비교용  "data": {

    "query": "애플",

**data.nasdaq_benchmark** (array)    "total_count": 10,

- NASDAQ 지수 데이터    "news_list": [

- 벤치마크 비교용      {

        "title": "애플 AI 칩 개발 가속화",

## 응답 형식        "link": "https://news.naver.com/...",

        "description": "애플이 AI 전용 칩 개발에 박차를 가하고 있다...",

모든 API 응답은 다음 구조를 따릅니다:        "pubDate": "Mon, 28 Jan 2025 10:30:00 +0900"

      }

### 성공 응답    ]

  }

```json}

{```

  "status": "success",

  "data": { ... }---

}

```### 4.2 종목별 최신 뉴스 검색 (DB 캐싱)

**엔드포인트**: `GET /naver-news/ticker/{ticker}`  

### 실패 응답**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  

**설명**: 특정 종목의 최신 뉴스 조회 (24시간 DB 캐시 지원)

```json

{**쿼리 파라미터**:

  "detail": "에러 메시지 (오류 ID: abc123)"- `display`: 검색 결과 수 (1-100, 기본값: 10)

}- `force_refresh`: DB 캐시 무시 여부 (기본값: false)

```

**응답**:

## 에러 처리```json

{

### HTTP 상태 코드  "status": "success",

  "message": "AAPL(애플 주식) 관련 뉴스 10건을 조회했습니다.",

- `200 OK`: 요청 성공  "data": {

- `400 Bad Request`: 잘못된 요청 파라미터    "ticker": "AAPL",

- `404 Not Found`: 데이터를 찾을 수 없음    "query": "애플 주식",

- `422 Unprocessable Entity`: 유효성 검증 실패    "total_count": 10,

- `500 Internal Server Error`: 서버 내부 오류    "from_cache": false,

- `503 Service Unavailable`: 서비스 일시 중단    "news_list": [...]

  }

### 에러 응답 예시}

```

#### 유효성 검증 실패 (422)

---

```json

{### 4.3 종목별 날짜 뉴스 검색 (DB 캐싱)

  "detail": [**엔드포인트**: `GET /naver-news/ticker/{ticker}/date`  

    {**상태**: ✅ **사용중** (프론트엔드: `backtestApi.ts`)  

      "loc": ["body", "portfolio", 0, "symbol"],**설명**: 특정 종목의 특정 날짜 범위 뉴스 조회 (DB 캐싱 지원)

      "msg": "field required",

      "type": "value_error.missing"**쿼리 파라미터**:

    }- `start_date`: 시작 날짜 (YYYY-MM-DD, 필수)

  ]- `end_date`: 종료 날짜 (YYYY-MM-DD, 없으면 start_date와 동일)

}- `display`: 검색 결과 수 (10-100, 기본값: 50)

```- `force_refresh`: DB 캐시 무시 여부 (기본값: false)



#### 비즈니스 로직 에러 (400)**응답**:

```json

```json{

{  "status": "success",

  "detail": "포트폴리오 비중의 합이 100%가 아닙니다. (현재: 95%) (오류 ID: a1b2c3)"  "message": "AAPL(애플 주식) 관련 뉴스를 2024-03-15~2024-03-15 기간에서 5건 조회했습니다.",

}  "data": {

```    "ticker": "AAPL",

    "query": "애플 주식",

#### 데이터 없음 (404)    "start_date": "2024-03-15",

    "end_date": "2024-03-15",

```json    "total_count": 5,

{    "from_cache": true,

  "detail": "INVALID 종목의 데이터를 찾을 수 없습니다. (오류 ID: d4e5f6)"    "news_list": [...]

}  }

```}

```

#### 서버 오류 (500)

---

```json

{### 4.4 날짜별 뉴스 검색

  "detail": "백테스트 실행 중 오류가 발생했습니다. (오류 ID: g7h8i9)"**엔드포인트**: `GET /naver-news/search-by-date`  

}**상태**: ❌ **미사용** (프론트엔드에서 호출 안함)  

```**설명**: 특정 날짜 범위의 뉴스 검색 (캐싱 없음)



### 에러 ID---



모든 에러 응답에는 고유 에러 ID가 포함됩니다. 이 ID는 로그 추적 및 디버깅에 사용됩니다.### 4.5 네이버 뉴스 API 테스트

**엔드포인트**: `GET /naver-news/test`  

## 데이터 소스**상태**: ❌ **개발/테스트용**  

**설명**: 네이버 뉴스 API 연동 테스트

- **주가 데이터**: yfinance (Yahoo Finance API)

- **환율 데이터**: yfinance (KRW=X 심볼)---

- **뉴스 데이터**: 네이버 검색 API

- **캐싱**: MySQL 데이터베이스 (24시간)## API 사용 현황 요약



## 프록시 설정| 엔드포인트 | 메서드 | 상태 | 프론트엔드 사용처 |

|-----------|--------|------|------------------|

프론트엔드 개발 환경에서는 Vite 프록시를 사용합니다 (`vite.config.ts`):| `/backtest/portfolio` | POST | ✅ 사용중 | `backtestService.ts`, `usePortfolioBacktest.ts` |

| `/backtest/stock-data/{ticker}` | GET | ✅ 사용중 | `backtestApi.ts` |

```typescript| `/backtest/exchange-rate` | GET | ✅ 사용중 | `backtestApi.ts` |

proxy: {| `/backtest/stock-volatility-news/{ticker}` | GET | ✅ 사용중 | `backtestApi.ts` |

  '/api/v1/backtest': {| `/strategies/` | GET | ✅ 사용중 | `backtestService.ts` |

    target: 'http://localhost:8000',| `/strategies/{name}` | GET | ❌ 미사용 | - |

    changeOrigin: true,| `/optimize/run` | POST | ✅ 사용중 | `backtestService.ts` |

  },| `/naver-news/search` | GET | ✅ 사용중 | `backtestService.ts`, `backtestApi.ts` |

}| `/naver-news/ticker/{ticker}` | GET | ✅ 사용중 | `backtestApi.ts` |

```| `/naver-news/ticker/{ticker}/date` | GET | ✅ 사용중 | `backtestApi.ts` |

| `/naver-news/search-by-date` | GET | ❌ 미사용 | - |

프로덕션 환경에서는 Nginx 리버스 프록시를 사용합니다.| `/naver-news/test` | GET | ⚠️ 테스트용 | - |



## API 문서**통계**:

- **총 엔드포인트**: 12개 (-1, `/backtest/execute` 삭제)

- **Swagger UI**: http://localhost:8000/api/v1/docs- **프론트엔드 사용중**: 9개 (75%)

- **ReDoc**: http://localhost:8000/api/v1/redoc- **미사용 (삭제 후보)**: 2개 (17%)

- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json- **테스트/개발용**: 1개 (8%)



## 변경 이력---



### 2025-01-28## 에러 응답 형식

- 포트폴리오 백테스트 통합 엔드포인트 구현

- 단일 응답으로 모든 데이터 제공모든 API는 실패 시 다음 형식으로 에러를 반환합니다:

- 종목별 데이터 수집 자동화

```json

### 2025-01-27{

- 초기 API 설계 및 구현  "detail": "사용자 친화적 에러 메시지 (오류 ID: abc123)"

- 기본 백테스트 기능 제공}

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
