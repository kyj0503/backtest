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

## 성능 테스트 방법

``` docker exec backtest-be-fast-dev python scripts/benchmark_performance.py 2>&1 | tee /tmp/benchmark_results.txt ```