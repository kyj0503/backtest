## 성능 개선

### N+1 쿼리 패턴 최적화

asyncio.gather()를 사용하여 순차적 데이터베이스 쿼리를 병렬 실행으로 변환했습니다.

#### 포트폴리오 데이터 로딩
- 테스트 환경: 18개 종목, 5년치 데이터 (2020-2024)
- 결과:
  - 순차 로딩: 2.00초
  - 병렬 로딩: 1.09초
  - 성능 향상: **1.8배**
- 분석: 데이터 양이 많아질수록(5년치) DB I/O 및 데이터프레임 변환(CPU) 부하가 커져 병렬화의 이점이 다소 감소함 (소량 데이터에서는 5~6배 향상).
- 위치: app/services/portfolio_service.py 라인 1490-1510 부근

구현:
```python
load_tasks = [
    asyncio.to_thread(load_ticker_data, symbol, start_date, end_date)
    for symbol in symbols_to_load
]
load_results = await asyncio.gather(*load_tasks, return_exceptions=True)
```

#### 환율 데이터 로딩
- 이전: 순차 로딩
- 이후: asyncio.gather()를 사용한 병렬 로딩
- 성능 향상: 포트폴리오 데이터 로딩과 유사한 수준의 병렬화 이점 제공 (약 3-5배 예상)
- 위치: app/utils/currency_converter.py 라인 360-390 부근

### 데이터베이스 쿼리 최적화

- 티커 정보 일괄 조회 구현 (N+1 문제 해결)
- 테스트 결과 (18개 종목):
  - 개별 조회: 0.37초
  - 배치 조회: 0.02초
  - 성능 향상: **16.4배**
- 데이터베이스 왕복 횟수 감소: N회 → 1회
- 위치: app/services/yfinance_db.py

### 주가 데이터 조회와 티커 정보 조회 구현이 다른 이유

두 방식이 다른 이유는 데이터의 성격과 로직의 복잡성 때문입니다.

1. 티커 정보 (Metadata) -> IN 절 사용 (Batch Query)
성격: 데이터 크기가 작고(종목당 1행), 단순 조회(SELECT)만 수행합니다.
구현: "여러 종목의 정보를 줘"라는 쿼리 하나로 DB에서 가져오기만 하면 끝납니다.
이유: 구현이 매우 간단하고, DB 왕복 횟수를 줄이는 효과가 확실하기 때문에 IN 절을 사용했습니다.

2. 주가 데이터 (Time Series) -> 병렬 실행 (asyncio.gather)
성격: 데이터 양이 많고(종목당 수천 행), **"캐시 확인 -> 누락 구간 파악 -> 외부 API(yfinance) 데이터 수집 -> DB 저장 -> 조회"**라는 복잡한 로직이 포함됩니다.
이유:
로직 재사용: 이미 단일 종목에 대해 "누락된 기간만 채워넣는" 복잡한 로직(_load_ticker_data_internal)이 잘 구현되어 있습니다. 이를 배치(Batch)로 다시 짜려면, 각 종목마다 제각각인 누락 기간을 한 번에 처리하는 매우 복잡한 로직이 필요합니다.
외부 API 제약: DB 조회는 IN 절로 한 번에 할 수 있지만, 외부 API(yfinance)에서 데이터를 가져올 때는 어차피 종목별로 요청해야 하는 경우가 많습니다.
병렬성의 이점: asyncio.gather를 쓰면 여러 종목의 DB 조회와 외부 API 요청을 동시에 진행하므로, 복잡한 로직을 그대로 쓰면서도 전체 시간을 획기적으로 단축할 수 있습니다.

결론:
단순 조회는 **Batch Query (IN 절)**가 좋음.
복잡한 로직(캐싱, 외부 요청 등)이 섞여 있을 때는 병렬 실행이 구현 난이도 대비 성능 효율이 가장 좋음.

## 성능 테스트 방법

``` docker exec backtest-be-fast-dev python scripts/benchmark_performance.py 2>&1 | tee /tmp/benchmark_results.txt ```
