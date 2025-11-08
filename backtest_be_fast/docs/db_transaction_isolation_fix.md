# DB 트랜잭션 격리로 인한 데이터 미조회 문제 해결

## 문제 요약

**날짜**: 2025-11-08  
**심각도**: HIGH  
**영향 범위**: 포트폴리오 백테스트, 신규 종목 첫 실행

처음 사용하는 기간/종목에 대해 백테스트를 실행할 때, 첫 실행에서 잘못된 결과(급격한 손실, -77% 수익률 등)가 반환되고 동일한 조건으로 재실행하면 정상적인 결과가 나오는 문제가 발생했습니다.

## 증상

### 관찰된 현상

1. **첫 실행 시 비정상 결과**
   - 총 수익률: -77.46%
   - 포트폴리오 가치 그래프가 급격히 하락
   - 통계 수치가 비정상적

2. **두 번째 실행 시 정상 결과**
   - 동일한 파라미터로 재실행
   - 정상적인 수익률 및 차트 표시

3. **새로운 종목/기간에서 반복**
   - 이전에 조회한 적 없는 데이터에서만 발생
   - DB 캐시가 있는 경우는 정상 작동

### 로그 분석

```
2025-11-08 14:44:00 - AAPL 데이터 로드 중 (2015-01-01 ~ 2019-12-01)
2025-11-08 14:44:00 - DB에 누락된 기간을 yfinance에서 가져옵니다: AAPL 2014-12-29 -> 2020-01-01
2025-11-08 14:44:02 - 데이터 수집 완료: AAPL, 1261 레코드
[yfinance_db] Creating engine -> DB 저장 완료
2025-11-08 14:44:02 - [시도 1/3] AAPL 데이터 로드 실패: 티커 'AAPL'에 대한 데이터가 없습니다.
2025-11-08 14:44:02 - [재시도 대기] 2.0초 후 AAPL 데이터 재시도...
2025-11-08 14:44:04 - [시도 2/3] AAPL 데이터 로드 중...
2025-11-08 14:44:04 - [성공] AAPL 데이터 로드 완료: 1237행 (시도 2회)
```

**핵심 문제점**:
- yfinance에서 1261개 레코드를 가져와 DB에 저장 완료
- 바로 다음 줄에서 SELECT 쿼리 실행 시 "데이터가 없습니다" 오류
- 2초 후 재시도하면 성공 (1237행 조회)

## 원인 분석

### 1. 코드 흐름

`app/services/yfinance_db.py`의 `_load_ticker_data_internal()` 함수:

```python
def _load_ticker_data_internal(ticker: str, start_date=None, end_date=None):
    engine = _get_engine()
    conn = engine.connect()  # 커넥션 A 생성
    
    try:
        # ... stock_id 조회 ...
        
        # 누락된 데이터 범위 계산
        missing_ranges = [...]
        
        if missing_ranges:
            # yfinance에서 데이터 수집
            df_new = data_fetcher.get_stock_data(ticker, co_start, co_end)
            
            # 별도 커넥션으로 DB 저장 (커넥션 B)
            save_ticker_data(ticker, df_new)
            # save_ticker_data 내부에서 commit 후 커넥션 B 종료
            
        # 여전히 커넥션 A 사용 중
        # 데이터 조회 시도
        res = conn.execute(text(q), params)  # 데이터 없음!
        rows = res.fetchall()
        
        if not rows:
            raise ValueError("데이터가 없습니다")  # 여기서 실패
    finally:
        conn.close()
```

### 2. 트랜잭션 격리 수준

**MySQL의 REPEATABLE READ 격리 수준 특성**:

- 트랜잭션이 시작된 시점의 데이터 스냅샷을 유지
- 다른 트랜잭션이 커밋한 데이터라도 현재 트랜잭션에서는 보이지 않음
- "일관된 읽기(Consistent Read)"를 보장하기 위한 MVCC(Multi-Version Concurrency Control) 메커니즘

**문제 발생 시나리오**:

1. **커넥션 A**: `_load_ticker_data_internal`에서 SELECT 실행
   - 암묵적 트랜잭션 시작
   - 이 시점의 스냅샷: daily_prices 테이블에 AAPL 데이터 없음

2. **커넥션 B**: `save_ticker_data` 내부
   - 새 트랜잭션 시작
   - INSERT ... ON DUPLICATE KEY UPDATE 실행
   - 1261개 레코드 삽입
   - COMMIT 실행
   - 커넥션 종료

3. **다시 커넥션 A로 복귀**
   - 여전히 1단계의 트랜잭션 스냅샷 사용
   - SELECT 쿼리 실행 → **커넥션 B가 저장한 데이터가 보이지 않음**
   - 빈 결과 반환 → 오류 발생

4. **2초 후 재시도**
   - 새로운 `load_ticker_data` 호출
   - 새 커넥션 생성 → 새로운 트랜잭션 스냅샷
   - 이제 커밋된 데이터가 보임 → 성공

### 3. 왜 재시도에서는 성공하는가?

- 재시도는 완전히 새로운 함수 호출
- 새로운 커넥션과 트랜잭션 생성
- 최신 커밋 상태를 반영한 스냅샷 사용
- 따라서 이전에 저장된 데이터가 정상적으로 조회됨

## 해결 방법

### 수정 사항

`save_ticker_data()` 호출 후 커넥션을 명시적으로 재생성하여 새로운 트랜잭션 스냅샷을 얻도록 수정:

#### 수정 전

```python
if df_new is not None and not df_new.empty:
    save_ticker_data(ticker, df_new)
# 커넥션 A가 계속 유지됨 - 문제 발생!

# 바로 SELECT 실행
res = conn.execute(text(q), params)
```

#### 수정 후

```python
if df_new is not None and not df_new.empty:
    save_ticker_data(ticker, df_new)
    
    # 데이터 저장 후 커넥션을 닫고 새로 연결
    conn.close()
    import time
    time.sleep(0.1)  # 100ms 대기 - DB 커밋 완료 보장
    conn = engine.connect()  # 새 트랜잭션 스냅샷

# 이제 최신 데이터가 보이는 새 커넥션으로 SELECT 실행
res = conn.execute(text(q), params)
```

### 수정된 위치

`backtest_be_fast/app/services/yfinance_db.py`:

1. **Line 473 부근**: 티커가 DB에 처음 추가되는 경우
   ```python
   save_ticker_data(ticker, df_new)
   # 커넥션 재생성 추가
   conn.close()
   time.sleep(0.1)
   conn = engine.connect()
   ```

2. **Line 520 부근**: 통합 누락 기간 데이터 수집 후
   ```python
   save_ticker_data(ticker, df_new)
   conn.close()
   time.sleep(0.1)
   conn = engine.connect()
   ```

3. **Line 540 부근**: 개별 누락 기간 데이터 수집 후 (fallback)
   ```python
   save_ticker_data(ticker, df_new)
   conn.close()
   time.sleep(0.1)
   conn = engine.connect()
   ```

### sleep(0.1)이 필요한 이유

1. **네트워크 레이턴시**: 원격 DB의 경우 커밋 완료까지 시간 소요
2. **디스크 플러시**: InnoDB 버퍼 풀에서 실제 디스크로 쓰기 완료
3. **복제 지연**: 읽기 복제본 사용 시 동기화 시간
4. **안전 마진**: 100ms는 무시할 수 있는 오버헤드이면서 충분한 대기 시간

## 이전 Race Condition 문제와의 차이

### Race Condition 문제 (이전)

- **원인**: async 컨텍스트에서 동기 I/O 함수를 직접 호출
- **증상**: 병렬 실행으로 인한 데이터 손상, 예측 불가능한 결과
- **해결**: `asyncio.to_thread()`로 래핑
- **문서**: `docs/race_condition_reintroduced_analysis.md`

### Transaction Isolation 문제 (현재)

- **원인**: 동일 커넥션에서 다른 트랜잭션의 커밋 데이터 미반영
- **증상**: 첫 실행 실패 → 재시도 성공 패턴
- **해결**: 저장 후 커넥션 재생성 + sleep
- **문서**: 본 문서

**두 문제는 독립적**:
- Race Condition: 비동기 실행 흐름 문제
- Transaction Isolation: DB 동기화 및 가시성 문제

## 검증 방법

### 테스트 시나리오

1. **DB에서 특정 종목 데이터 삭제**
   ```sql
   DELETE FROM daily_prices WHERE stock_id = (
       SELECT id FROM stocks WHERE ticker = 'TEST.SYMBOL'
   );
   ```

2. **백테스트 첫 실행**
   - yfinance에서 데이터 수집
   - DB 저장
   - 바로 백테스트 실행

3. **결과 확인**
   - 첫 실행에서 정상 결과 반환
   - 로그에 재시도 없음
   - 백테스트 통계가 합리적

### 로그 확인 포인트

**수정 전 (문제 있음)**:
```
[시도 1/3] 데이터 로드 실패
[재시도 대기] 2.0초 후 재시도...
[시도 2/3] 데이터 로드 완료
```

**수정 후 (정상)**:
```
[시도 1/3] 데이터 로드 중...
[성공] 데이터 로드 완료: XXX행 (시도 1회)
```

## 성능 영향

### 추가 오버헤드

- 커넥션 재생성: ~10-50ms (네트워크 상태에 따라)
- sleep(0.1): 100ms 고정
- **총 영향**: 신규 데이터 수집 시에만 발생, 약 100-150ms 추가

### 전체 백테스트 성능

- 신규 종목 첫 실행: 기존 대비 +0.1초 (무시 가능)
- 캐시된 데이터 사용 시: 영향 없음 (코드 경로 다름)
- yfinance API 호출 시간(수 초)에 비해 미미함

**결론**: 정확성 향상 대비 성능 영향은 무시할 수 있는 수준

## 대안 검토

### 1. 명시적 트랜잭션 관리

```python
with engine.begin() as conn:
    # 트랜잭션 명시적 시작/커밋
    pass
```

**평가**: 코드 복잡도 증가, 현재 구조와 맞지 않음

### 2. READ COMMITTED 격리 수준 사용

```python
conn.execution_options(isolation_level="READ COMMITTED")
```

**평가**: 
- 장점: 다른 트랜잭션의 커밋이 즉시 반영
- 단점: 일관성 보장 약화, 전역 설정 변경 필요
- 결정: 다른 부분에 영향 가능성으로 보류

### 3. 커넥션 풀 플러시

```python
engine.dispose()
```

**평가**: 과도한 조치, 모든 커넥션 재생성으로 성능 저하

### 4. 선택된 방법: 로컬 커넥션 재생성 + sleep

**장점**:
- 최소 침습적 (해당 위치만 수정)
- 명확한 의도 표현 (주석 포함)
- 안정적이고 예측 가능
- 성능 영향 최소

## 교훈

### 1. DB 트랜잭션 격리 수준 이해 필수

- 멀티 커넥션 환경에서는 격리 수준이 중요
- REPEATABLE READ는 일관성은 높지만 가시성 문제 가능
- 쓰기 후 읽기(Read-After-Write) 패턴 주의

### 2. 로깅의 중요성

- 상세한 로그 덕분에 문제 파악 가능
- 시도 횟수, 데이터 건수, 타이밍 정보가 핵심

### 3. 재시도 메커니즘의 양면성

- 일시적 오류 복구에는 유용
- 하지만 근본 원인을 숨길 수 있음
- 재시도가 항상 성공한다면 원인 조사 필요

### 4. 비동기 환경에서의 동기 DB 호출

- `asyncio.to_thread()`로 race condition은 해결
- 하지만 DB 자체의 동기화 문제는 별도 해결 필요

## 관련 문서

- `docs/race_condition_reintroduced_analysis.md`: Async/Sync 경계 관리
- `docs/bugfix_race_condition_report.md`: 초기 레이스 컨디션 수정
- `.github/copilot-instructions.md`: 아키텍처 가이드 (통화 정책, 서비스 구조)

## 후속 조치

### 단기

- [x] `yfinance_db.py`의 3개 위치에 커넥션 재생성 로직 추가
- [ ] 통합 테스트에 신규 종목 첫 실행 케이스 추가
- [ ] 성능 모니터링 (100ms 추가로 인한 영향 확인)

### 장기

- [ ] SQLAlchemy ORM 도입 검토 (트랜잭션 관리 개선)
- [ ] 읽기 전용 커넥션과 쓰기 커넥션 분리
- [ ] Redis 캐시 레이어 추가 고려 (DB 부하 감소)
- [ ] DB 커넥션 풀 설정 최적화

## 참고 자료

### MySQL Documentation

- [InnoDB Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html)
- [Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.0/en/innodb-consistent-read.html)

### Python/SQLAlchemy

- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Transaction Isolation Level](https://docs.sqlalchemy.org/en/20/core/connections.html#setting-transaction-isolation-levels)

### 내부 코드

- `app/services/yfinance_db.py`: 데이터 로드/저장 로직
- `app/services/portfolio_service.py`: 비동기 래핑 호출
- `app/utils/data_fetcher.py`: yfinance API 호출
