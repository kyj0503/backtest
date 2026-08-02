# 비동기/동기 경계 문제 (Race Condition)

## 요약

**상태**: 해결됨 — 현재 코드에서 `calculate_dca_portfolio_returns`와 `run_buy_and_hold_portfolio_backtest`는 모두 `async def`이며, 동기 I/O는 `PortfolioDataLoader`(내부적으로 `asyncio.to_thread`/`asyncio.gather` 사용)에 위임되어 있습니다. 이 문서는 과거 발생했던 회귀와 그 수정 내용을 기록한 것입니다.
**영향(과거)**: 캐시에 없는 새로운 종목/기간으로 백테스트 첫 실행 시 결과 손상

## 문제 설명 (과거 증상)

새로운 종목이나 날짜 범위로 백테스트를 실행할 때 다음과 같은 현상이 발생했습니다.
- **첫 실행**: 비정상적인 결과 (비현실적인 그래프, 잘못된 통계)
- **두 번째 실행 (동일 조건)**: 정상적인 결과

이 문제는 이전에 해결되었던 경쟁 상태(Race Condition) 버그가, 포트폴리오 로직을 담당하던 서비스(현재의 `PortfolioManagerService`, 당시 `portfolio_service.py`)의 리팩토링 과정에서 다시 발생한 것이었습니다.

## 근본 원인 분석 (당시)

### 문제 위치: `PortfolioManagerService` (`app/services/portfolio_manager_service.py`)

리팩토링 과정에서 비동기/동기 경계가 지켜지지 않아 문제가 발생했습니다.

- **`calculate_dca_portfolio_returns` 내부**: 정적 메서드였지만 비동기 컨텍스트에서 호출되었고, 내부에서 동기적인 DB 조회 함수(`get_ticker_info_from_db`, `load_ticker_data`)를 직접 호출했습니다.
- **`run_buy_and_hold_portfolio_backtest` 내부**: 비동기 함수 내에서 `await`나 `asyncio.to_thread()` 없이 동기 함수(`load_ticker_data`)를 직접 호출했습니다.

### 호출 체인 (당시)

```
FastAPI 엔드포인트 (비동기)
  |
  v
PortfolioManagerService.run_buy_and_hold_portfolio_backtest() (비동기)
  |
  +-- load_ticker_data() (동기) <-- 문제 지점
  |
  +-- PortfolioManagerService.calculate_dca_portfolio_returns() (정적 동기 메서드)
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

## 해결책 (현재 코드에 적용된 상태)

모든 동기 I/O 호출을 `asyncio.to_thread()`로 감싸서 별도의 스레드에서 실행하도록 수정했습니다. 단, 각 메서드에서 직접 `asyncio.to_thread()`를 호출하는 대신, I/O 책임 자체를 `PortfolioDataLoader`(`app/services/portfolio/portfolio_data_loader.py`)라는 별도 클래스로 위임하고 그 안에서 `asyncio.to_thread()`/`asyncio.gather()`를 사용하는 방식으로 정리되었습니다. `PortfolioManagerService.__init__`이 `self.data_loader = PortfolioDataLoader(...)`를 생성해 두고, 아래 두 메서드는 이 인스턴스를 통해서만 데이터를 로드합니다.

### 현재 구현

#### `calculate_dca_portfolio_returns` (`app/services/portfolio_manager_service.py`)

정적 메서드에서 `PortfolioManagerService`의 일반 `async` 인스턴스 메서드로 바뀌었고, 동기 호출은 `self.data_loader`에 위임합니다.

```python
# app/services/portfolio_manager_service.py

async def calculate_dca_portfolio_returns(
    self,
    portfolio_data, amounts, dca_info, start_date, end_date,
    rebalance_frequency="weekly_4", commission=0.0
) -> pd.DataFrame:
    # ...
    # 종목별 통화 정보 로드 — PortfolioDataLoader 내부에서 asyncio.to_thread 사용
    ticker_currencies = await self.data_loader.load_ticker_currencies(symbols)
    # ...
```

#### `run_buy_and_hold_portfolio_backtest` (`app/services/portfolio_manager_service.py`)

```python
# app/services/portfolio_manager_service.py

async def run_buy_and_hold_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
    # ...
    # 여러 종목의 가격 데이터를 병렬 로드 — 내부에서 asyncio.to_thread + asyncio.gather 사용
    portfolio_data = await self.data_loader.load_stock_data_parallel(
        symbols_to_load, request.start_date, request.end_date
    )
    # ...
```

#### `PortfolioDataLoader.load_stock_data_parallel` (`app/services/portfolio/portfolio_data_loader.py`)

동기 I/O를 스레드로 위임하는 지점은 결국 여기입니다.

```python
load_tasks = [
    asyncio.to_thread(self.stock_repository.load_stock_data, symbol, start_date, end_date)
    for symbol in symbols_to_load
]
load_results = await asyncio.gather(*load_tasks, return_exceptions=True)
```

## 교훈

### 1. 비동기/동기 경계 확인 목록

코드 수정 시, 특히 리팩토링 시 다음을 항상 확인해야 합니다.

- [ ] 비동기 함수 내의 모든 I/O 작업이 `await` 또는 `asyncio.to_thread()`로 감싸여 있는가?
- [ ] 비동기 컨텍스트에서 호출되는 일반/정적 메서드가 내부에 동기 I/O를 포함하고 있지 않은가?
- [ ] 모든 DB 조회 및 외부 API 호출이 스레드 분리 방식으로 처리되는가?

### 2. 정적 메서드의 함정

I/O를 수행하는 정적 메서드는 비동기 코드베이스에서 사용을 피하거나, 명시적으로 `async`로 만들어야 합니다. 동기적으로 보이지만 비동기 컨텍스트에서 호출되어 문제를 일으킬 수 있습니다. (`calculate_dca_portfolio_returns`는 이 교훈에 따라 현재 `@staticmethod`가 아닌 일반 `async` 인스턴스 메서드입니다.)

### 3. 코드 리뷰 초점

코드 리뷰 시 다음 사항을 중점적으로 확인해야 합니다.
- `async def`로 정의된 함수 내부에 `await` 없는 동기 I/O 호출이 있는지 여부.
- 데이터베이스 조회나 API 호출 함수들이 어떻게 호출되는지.
