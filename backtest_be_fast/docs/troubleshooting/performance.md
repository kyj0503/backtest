# 성능 최적화 가이드

## 현재 성능 병목 지점

1.  **yfinance API (첫 데이터 로드)**: 전체 시간의 60-70% 차지
2.  **백테스트 실행**: 전체 시간의 20-30% 차지
3.  **MySQL 쿼리**: 전체 시간의 5-10% 차지
4.  **데이터 검증 및 변환**: 전체 시간의 5-10% 차지

## 적용된 최적화 전략

### 1. 다계층 캐싱 (DataRepository)

-   **인메모리 캐시**: 가장 빠른 캐시. 동일한 요청에 대해 즉시 응답합니다. `app/repositories/data_repository.py`가 `cachetools.TTLCache(maxsize=500, ttl=3600)`로 구현합니다 — 모든 항목이 균일하게 1시간(3600초) 후 만료됩니다. (과거에는 과거 데이터 24시간 / 최신 데이터 1시간으로 TTL을 다르게 주는 방식이었으나, DB 캐시(L2)와 yfinance(L3)가 이미 존재해 단순화되었습니다. 최신 데이터가 1시간 이상 오래된 캐시를 반환할 수 있다는 뜻이므로, 실시간성이 중요한 용도라면 `invalidate_cache()`로 명시적으로 무효화해야 합니다.)
-   **DB 캐시 (MySQL)**: 인메모리 캐시가 없을 경우, DB에서 데이터를 조회합니다.

### 2. 데이터베이스 인덱싱

-   `daily_prices` 테이블에 `PRIMARY KEY (stock_id, date)` 복합 기본키를 설정하여, 특정 종목의 특정 기간 데이터를 조회하는 핵심 쿼리 성능을 최적화했습니다 (`database/schema.sql` 참고). 별도의 인덱스 검증 스크립트는 없습니다.

### 3. 비동기 처리 최적화

-   `asyncio.to_thread()`를 사용하여 모든 동기 I/O(DB 조회, API 호출)를 별도 스레드에서 처리함으로써, 이벤트 루프 차단을 방지하고 경쟁 상태(Race Condition)를 해결했습니다.

### 4. 데이터 처리 최적화

-   Pandas 데이터프레임 처리 시, 여러 단계의 작업을 단일 체인으로 연결하여 불필요한 중간 과정과 메모리 할당을 줄였습니다.

    ```python
    # 최적화 전
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna()

    # 최적화 후
    data = data.replace([np.inf, -np.inf], np.nan).dropna()
    ```

## 이미 적용된 항목 (과거에는 "향후 계획"으로 적혀 있었음)

### 병렬 데이터 로딩

포트폴리오 백테스트 시 여러 종목의 데이터를 `asyncio.gather` + `asyncio.to_thread`로 병렬 로드합니다. `app/services/portfolio/portfolio_data_loader.py`의 `PortfolioDataLoader.load_stock_data_parallel()`(가격 데이터), `app/utils/currency_converter.py`의 `CurrencyConverter.load_multiple_exchange_rates()`(환율 데이터)가 이를 구현합니다.

### DB 커넥션 풀 튜닝

`app/services/database/pool_config.py`가 `pool_size`/`max_overflow`를 `DATABASE_POOL_SIZE`/`DATABASE_MAX_OVERFLOW` 환경 변수로 조정할 수 있게 이미 분리해 두었습니다. 다중 워커 배포에서 `workers × (pool_size + max_overflow) ≤ MySQL max_connections`를 지키도록 기본값이 계산되어 있으므로, 워커 수나 MySQL 설정을 바꿀 때는 이 모듈의 docstring을 먼저 확인하세요.

## 향후 최적화 계획

### 1. 결과 캐싱

-   동일한 백테스트 요청(종목, 기간, 전략, 매개변수 등)에 대해서는 백테스트 결과 자체를 캐싱하여 즉시 반환하는 기능을 구현할 수 있습니다. (현재는 가격/환율/티커 메타데이터만 캐싱되고, 백테스트 결과 자체를 캐싱하는 계층은 없습니다.)

### 2. 비동기 DB 드라이버 도입

-   장기적으로 `aiomysql`과 같은 비동기 DB 드라이버와 SQLAlchemy 2.0의 비동기 지원을 도입하여, 데이터베이스 관련 작업을 완전히 비동기적으로 처리하는 것을 고려할 수 있습니다. (현재는 동기 SQLAlchemy + `asyncio.to_thread()` 조합입니다.)
