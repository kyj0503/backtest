# 비동기/동기 경계 문제 (Race Condition)

## 요약

**상태**: 중요 버그, 리팩토링 중 재발
**영향**: 캐시에 없는 새로운 종목/기간으로 백테스트 첫 실행 시 결과 손상

## 문제 설명

### 증상

새로운 종목이나 날짜 범위로 백테스트를 실행할 때 다음과 같은 현상이 발생합니다.
- **첫 실행**: 비정상적인 결과 (비현실적인 그래프, 잘못된 통계)
- **두 번째 실행 (동일 조건)**: 정상적인 결과

이 문제는 이전에 해결되었던 경쟁 상태(Race Condition) 버그가 `portfolio_service.py` 리팩토링 과정에서 다시 발생한 것입니다.

## 근본 원인 분석

### 문제 위치: portfolio_service.py

리팩토링 과정에서 비동기/동기 경계가 지켜지지 않아 문제가 발생했습니다.

- **`calculate_dca_portfolio_returns` 내부**: 정적 메서드이지만 비동기 컨텍스트에서 호출되며, 내부에서 동기적인 DB 조회 함수(`get_ticker_info_from_db`, `load_ticker_data`)를 직접 호출합니다.
- **`run_buy_and_hold_portfolio_backtest` 내부**: 비동기 함수 내에서 `await`나 `asyncio.to_thread()` 없이 동기 함수(`load_ticker_data`)를 직접 호출합니다.

### 호출 체인

```
FastAPI 엔드포인트 (비동기)
  |
  v
portfolio_service.run_buy_and_hold_portfolio_backtest() (비동기)
  |
  +-- load_ticker_data() (동기) <-- 문제 지점
  |
  +-- portfolio_service.calculate_dca_portfolio_returns() (정적 동기 메서드)
        |
        +-- get_ticker_info_from_db() (동기) <-- 문제 지점
        |
        +-- load_ticker_data() (동기) <-- 문제 지점
```

### 손상 원리

비동기 컨텍스트에서 동기 I/O 작업을 스레드 분리 없이 호출하면 다음과 같은 문제가 발생합니다.

1.  **이벤트 루프 차단**: DB 조회나 API 호출이 비동기 이벤트 루프 전체를 차단합니다.
2.  **조기 반환**: I/O 작업이 완료되기 전에 코드가 계속 진행될 수 있습니다.
3.  **부분 데이터**: 데이터프레임이 비어 있거나 불완전한 상태로 사용됩니다.
4.  **경쟁 상태**: 실행 타이밍에 따라 결과가 달라집니다.

**첫 실행 시나리오**:
DB나 yfinance API에서 데이터를 가져오는 데 수 초가 걸리는 동안, 이벤트 루프가 다른 작업을 처리하거나 코드가 먼저 진행되어 비어있는 데이터로 백테스트를 수행하여 결과가 손상됩니다.

**두 번째 실행 시나리오**:
데이터가 DB 캐시에 있으므로 매우 빠르게(수십 ms) 반환됩니다. 이벤트 루프가 다른 곳으로 넘어가기 전에 데이터가 준비되므로 정상적으로 작동하는 것처럼 보입니다.

## 해결책

모든 동기 I/O 호출을 `asyncio.to_thread()`로 감싸서 별도의 스레드에서 실행하도록 수정해야 합니다.

### 수정 예시

#### `calculate_dca_portfolio_returns` 수정

이 정적 메서드를 `async`로 변경하고 내부의 동기 호출을 수정합니다.

```python
# portfolio_service.py

import asyncio # 상단에 추가

@staticmethod
async def calculate_dca_portfolio_returns(...):
    # ...
    # 동기 DB 호출 수정
    ticker_info = await asyncio.to_thread(
        get_ticker_info_from_db, symbol
    )
    # ...
    # 동기 데이터 로드 수정
    exchange_data = await asyncio.to_thread(
        load_ticker_data, exchange_ticker, exchange_start_date, end_date
    )
    # ...
```

#### `run_buy_and_hold_portfolio_backtest` 수정

```python
# portfolio_service.py

async def run_buy_and_hold_portfolio_backtest(...):
    # ...
    # 동기 데이터 로드 수정
    df = await asyncio.to_thread(
        load_ticker_data, symbol, request.start_date, request.end_date
    )
    # ...
```

## 교훈

### 1. 비동기/동기 경계 확인 목록

코드 수정 시, 특히 리팩토링 시 다음을 항상 확인해야 합니다.

- [ ] 비동기 함수 내의 모든 I/O 작업이 `await` 또는 `asyncio.to_thread()`로 감싸여 있는가?
- [ ] 비동기 컨텍스트에서 호출되는 일반/정적 메서드가 내부에 동기 I/O를 포함하고 있지 않은가?
- [ ] 모든 DB 조회 및 외부 API 호출이 스레드 분리 방식으로 처리되는가?

### 2. 정적 메서드의 함정

I/O를 수행하는 정적 메서드는 비동기 코드베이스에서 사용을 피하거나, 명시적으로 `async`로 만들어야 합니다. 동기적으로 보이지만 비동기 컨텍스트에서 호출되어 문제를 일으킬 수 있습니다.

### 3. 코드 리뷰 초점

코드 리뷰 시 다음 사항을 중점적으로 확인해야 합니다.
- `async def`로 정의된 함수 내부에 `await` 없는 동기 I/O 호출이 있는지 여부.
- 데이터베이스 조회나 API 호출 함수들이 어떻게 호출되는지.
