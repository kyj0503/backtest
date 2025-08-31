# 백엔드 API 문서

## 개요

백테스팅 플랫폼의 REST API 엔드포인트를 설명합니다. 모든 API는 JSON 형식으로 데이터를 주고받습니다.

## 기본 정보

- **Base URL**: `http://localhost:8001` (개발), `https://backtest-be.yeonjae.kr` (프로덕션)
- **API 버전**: v1
- **Content-Type**: `application/json`

## 인증

현재 API는 인증이 필요하지 않습니다. (향후 JWT 인증 계획)

## 주요 엔드포인트

### 1. 백테스트 API

#### 차트 데이터 조회

```http
POST /api/v1/backtest/chart-data
```

**요청 본문:**
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
  "ticker": "AAPL",
  "strategy": "sma_crossover",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "ohlc_data": [
    {
      "timestamp": "2023-01-03T00:00:00",
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
      "timestamp": "2023-01-03T00:00:00",
      "date": "2023-01-03",
      "equity": 10000.0,
      "return_pct": 0.0,
      "drawdown_pct": 0.0
    }
  ],
  "trade_markers": [
    {
      "timestamp": "2023-01-03T00:00:00",
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
      "type": "overlay",
      "color": "#ff7300",
      "data": [
        {
          "timestamp": "2023-01-13T00:00:00",
          "date": "2023-01-13",
          "value": 127.45
        }
      ]
    }
  ],
  "summary_stats": {
    "total_return_pct": 23.46,
    "total_trades": 15,
    "win_rate_pct": 66.67,
    "max_drawdown_pct": -8.23,
    "sharpe_ratio": 1.45,
    "profit_factor": 1.85
  }
}
```

#### 포트폴리오 백테스트 실행

```http
POST /api/v1/backtest/portfolio
```

**요청 본문:**
```json
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "amount": 4000,
      "investment_type": "lump_sum"
    },
    {
      "symbol": "GOOGL",
      "amount": 3000,
      "investment_type": "dca",
      "dca_periods": 12
    },
    {
      "symbol": "MSFT",
      "amount": 3000,
      "investment_type": "lump_sum"
    }
  ],
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "strategy": "buy_and_hold",
  "commission": 0.002,
  "rebalance_frequency": "monthly"
}
```

**응답:**
```json
{
  "status": "success",
  "data": {
    "portfolio_statistics": {
      "Start": "2023-01-01",
      "End": "2024-12-31",
      "Duration": "730 days",
      "Initial_Value": 10000.0,
      "Final_Value": 12345.67,
      "Peak_Value": 13000.0,
      "Total_Return": 23.46,
      "Annual_Return": 11.23,
      "Annual_Volatility": 18.45,
      "Sharpe_Ratio": 0.61,
      "Max_Drawdown": -8.23,
      "Total_Trading_Days": 504,
      "Positive_Days": 280,
      "Negative_Days": 224,
      "Win_Rate": 55.56
    },
    "individual_returns": {
      "AAPL": {
        "weight": 0.4,
        "return": 28.5,
        "start_price": 125.07,
        "end_price": 160.77,
        "investment_type": "lump_sum"
      },
      "GOOGL": {
        "weight": 0.3,
        "return": 18.2,
        "start_price": 89.12,
        "end_price": 105.35,
        "investment_type": "dca",
        "dca_periods": 12
      },
      "MSFT": {
        "weight": 0.3,
        "return": 22.8,
        "start_price": 239.82,
        "end_price": 294.51,
        "investment_type": "lump_sum"
      }
    },
    "portfolio_composition": [
      {
        "symbol": "AAPL",
        "weight": 0.4,
        "amount": 4000,
        "investment_type": "lump_sum"
      },
      {
        "symbol": "GOOGL",
        "weight": 0.3,
        "amount": 3000,
        "investment_type": "dca"
      },
      {
        "symbol": "MSFT",
        "weight": 0.3,
        "amount": 3000,
        "investment_type": "lump_sum"
      }
    ],
    "equity_curve": {
      "2023-01-03": 10000.0,
      "2023-01-04": 10123.45,
      "...": "..."
    },
    "daily_returns": {
      "2023-01-03": 0.0,
      "2023-01-04": 1.23,
      "...": "..."
    }
  }
}
```

### 2. 시스템 API

#### 시스템 정보 조회

```http
GET /api/v1/system/info
```

**응답:**
```json
{
  "backend": {
    "version": "1.0.0",
    "uptime": "2024-01-15T10:30:00Z",
    "status": "healthy",
    "git_commit": "fd358f3e",
    "git_branch": "main",
    "build_number": "123",
    "environment": "development"
  },
  "frontend": {
    "version": "1.0.0", 
    "git_commit": "fd358f3e",
    "build_number": "123"
  },
  "docker": {
    "backend_image": "ghcr.io/redyeji/backtest-backend:latest",
    "frontend_image": "ghcr.io/redyeji/backtest-frontend:latest"
  }
}
```

### 3. 최적화 API (v2, 미구현)

#### 전략 파라미터 최적화 실행

*주의: 이 기능은 아직 구현되지 않았습니다. v2 API에서 지원 예정입니다.*

#### 전략 파라미터 최적화 실행

```http
POST /api/v1/optimize/run
```

**요청 본문:**
```json
{
  "ticker": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 10000,
  "strategy": "sma_crossover",
  "parameter_ranges": {
    "short_window": [5, 20],
    "long_window": [20, 50]
  },
  "optimization_target": "total_return_pct",
  "method": "grid"
}
```

## 지원 전략 및 파라미터

### 1. Buy & Hold (`buy_and_hold`)
- **파라미터**: 없음
- **설명**: 매수 후 보유 전략

### 2. SMA Crossover (`sma_crossover`)
- **파라미터**:
  - `short_window` (int): 단기 이동평균 기간 (5-50, 기본값: 10)
  - `long_window` (int): 장기 이동평균 기간 (10-200, 기본값: 20)
- **설명**: 단순이동평균 교차 전략

### 3. RSI Strategy (`rsi_strategy`)
- **파라미터**:
  - `rsi_period` (int): RSI 계산 기간 (5-30, 기본값: 14)
  - `rsi_overbought` (int): 과매수 기준 (60-90, 기본값: 70)
  - `rsi_oversold` (int): 과매도 기준 (10-40, 기본값: 30)
- **설명**: RSI 과매수/과매도 기반 전략

### 4. Bollinger Bands (`bollinger_bands`)
- **파라미터**:
  - `period` (int): 이동평균 기간 (10-50, 기본값: 20)
  - `std_dev` (float): 표준편차 배수 (1.0-3.0, 기본값: 2.0)
- **설명**: 볼린저 밴드 기반 전략

### 5. MACD Strategy (`macd_strategy`)
- **파라미터**:
  - `fast_period` (int): 빠른 EMA 기간 (5-20, 기본값: 12)
  - `slow_period` (int): 느린 EMA 기간 (20-50, 기본값: 26)
  - `signal_period` (int): 시그널 라인 기간 (5-15, 기본값: 9)
- **설명**: MACD 교차 기반 전략

## 투자 방식 (Portfolio API)

### 1. 일시 투자 (`lump_sum`)
- 백테스트 시작일에 전체 금액을 한 번에 투자

### 2. 분할 매수 (`dca`)
- 설정된 기간에 걸쳐 일정 금액씩 분할 투자
- `dca_periods`: 분할 기간 (1-60개월, 기본값: 12)

## 에러 코드

| HTTP 상태 코드 | 설명 | 예시 |
|---------------|------|------|
| 200 | 성공 | 정상적으로 처리됨 |
| 400 | 잘못된 요청 | 파라미터 오류, 유효성 검증 실패 |
| 404 | 리소스 없음 | 존재하지 않는 티커 심볼 |
| 422 | 처리할 수 없는 엔티티 | 날짜 범위 오류, 데이터 부족 |
| 500 | 서버 내부 오류 | 백테스팅 엔진 오류, 데이터 처리 실패 |
| 503 | 서비스 사용 불가 | yfinance API 제한, 네트워크 오류 |

## 에러 응답 형식

```json
{
  "detail": "Ticker 'INVALID' not found or has insufficient data",
  "status_code": 404
}
```

## 주의사항

1. **데이터 제공**: yfinance를 통해 주식 데이터를 가져오므로 실시간이 아닌 지연된 데이터입니다.
2. **캐싱**: 주식 데이터는 MySQL 데이터베이스에 캐시되어 반복 요청 시 빠른 응답을 제공합니다.
3. **제한사항**: 너무 짧은 백테스트 기간이나 데이터가 없는 기간에서는 오류가 발생할 수 있습니다.
4. **성능**: 대량의 데이터나 복잡한 전략의 경우 응답 시간이 길어질 수 있습니다.
5. **포트폴리오**: 최대 10개 종목까지 포트폴리오 구성이 가능합니다.

## 업데이트 내역

- **v1.0**: 기본 백테스트 및 차트 데이터 API
- **v1.1**: 포트폴리오 백테스트 기능 추가
- **v1.2**: 최적화 API 추가 (베타)
- **v1.3**: 분할 매수(DCA) 기능 추가
