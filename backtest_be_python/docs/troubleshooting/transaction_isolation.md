# DB 트랜잭션 격리로 인한 데이터 미조회 문제

## 요약

**심각도**: 높음
**영향 범위**: 포트폴리오 백테스트, 신규 종목 첫 실행

처음 사용하는 기간/종목에 대해 백테스트를 실행할 때, 첫 실행에서 잘못된 결과가 반환되고 동일한 조건으로 재실행하면 정상적인 결과가 나오는 문제가 발생했습니다.

## 증상

### 관찰된 현상

1.  **첫 실행 시 비정상 결과**: 비정상적인 수익률 및 차트 표시
2.  **두 번째 실행 시 정상 결과**: 동일한 매개변수로 재실행 시 정상 작동
3.  **새로운 종목/기간에서 반복**: DB 캐시가 없는 데이터에서만 발생

### 로그 분석

- yfinance에서 데이터를 가져와 DB에 저장 완료
- 직후 SELECT 쿼리 실행 시 "데이터가 없습니다" 오류 발생
- 잠시 후 재시도하면 성공

**핵심 문제점**: 데이터를 DB에 저장(INSERT)한 직후, 동일한 함수 내에서 해당 데이터를 조회(SELECT)하지 못합니다.

## 원인 분석

### 1. 코드 흐름

`app/repositories/yfinance_repository.py`의 `_load_ticker_data_internal()` 함수에서, 데이터 조회를 위한 **커넥션 A**가 열린 상태에서, 누락된 데이터를 저장하기 위해 `save_ticker_data` 함수가 내부적으로 **커넥션 B**를 열어 데이터를 저장하고 닫습니다. 그 후 다시 **커넥션 A**를 사용해 데이터를 조회하려고 할 때 문제가 발생합니다.

### 2. 트랜잭션 격리 수준

**MySQL의 REPEATABLE READ 격리 수준 특성**:

-   트랜잭션이 시작된 시점의 데이터 스냅샷을 유지합니다.
-   다른 트랜잭션이 커밋한 데이터라도 현재 트랜잭션에서는 보이지 않습니다.

**문제 발생 시나리오**:

1.  **커넥션 A**가 트랜잭션을 시작합니다. 이 시점의 스냅샷에는 신규 데이터가 없습니다.
2.  **커넥션 B**가 새로운 트랜잭션을 열어 데이터를 저장하고 커밋합니다.
3.  다시 **커넥션 A**로 돌아와 데이터를 조회하면, 1번 시점의 스냅샷을 그대로 사용하므로 **커넥션 B**가 저장한 데이터가 보이지 않습니다.
4.  이로 인해 "데이터 없음" 오류가 발생합니다.
5.  잠시 후 재시도하면, 새로운 커넥션이 생성되어 최신 데이터가 반영된 스냅샷을 사용하므로 조회가 성공합니다.

## 해결 방법 (현재 구현)

`save_ticker_data()` 호출 후 커넥션을 명시적으로 재생성하여 새로운 트랜잭션 스냅샷을 얻도록 수정합니다. `sleep`은 필요하지 않습니다 — 아래 "왜 sleep이 필요 없는가"를 참고하세요.

#### 수정 전

```python
if df_new is not None and not df_new.empty:
    save_ticker_data(ticker, df_new)
# 커넥션 A가 계속 유지됨 - 문제 발생!

# 바로 SELECT 실행
res = conn.execute(text(q), params)
```

#### 수정 후 (현재 코드, `app/repositories/yfinance_repository.py`)

```python
if df_new is not None and not df_new.empty:
    self.save_ticker_data(ticker, df_new)

    # 데이터 저장 후 커넥션을 닫고 새로 연결하여 트랜잭션 격리 문제 방지
    conn.close()
    conn = engine.connect()  # 새 트랜잭션 스냅샷

# 이제 최신 데이터가 보이는 새 커넥션으로 SELECT 실행
res = conn.execute(text(q), params)
```

이 재연결 패턴은 `_ensure_stock_exists()`와 `_fetch_and_save_missing_data()` 내부에 현재도 존재합니다 (메서드명으로 검색하면 찾을 수 있습니다 — 리팩터링으로 줄 번호는 자주 바뀝니다). `_load_ticker_data_internal()`이 커넥션을 수동으로 열고 닫는 구조이기 때문에, 이 두 헬퍼도 `with engine.connect() as conn:` 컨텍스트 매니저 대신 수동 재연결을 그대로 씁니다 — 의도적인 예외입니다.

### 왜 sleep이 필요 없는가

`save_ticker_data()`는 내부적으로 `with engine.begin() as conn: ...`을 사용합니다. SQLAlchemy는 이 `with` 블록을 벗어나는 시점에 `conn.commit()`을 **동기적으로** 완료시킵니다 — 즉 `save_ticker_data()` 호출이 반환되었다는 것 자체가 이미 "커밋이 끝났다"는 보장입니다. MySQL 8.0 InnoDB의 격리 수준(`READ COMMITTED`/`REPEATABLE READ`)에서 커밋된 트랜잭션은 그 시점 이후 새로 시작하는 트랜잭션(= 재연결한 커넥션)에 즉시 보입니다. 따라서 "커밋이 물리적으로 끝날 시간을 벌어주는" 임의의 대기는 애초에 아무것도 보장해 주지 않는 방어 코드였습니다.

## 과거 수정 이력: `time.sleep(0.1)` (2026-02 제거됨)

문제를 처음 고쳤을 때는 재연결 앞에 `time.sleep(0.1)`을 끼워 넣었습니다. **이 코드는 더 이상 존재하지 않습니다.** 새로 코드를 작성할 때 아래 패턴을 참고하지 마세요 — 왜 한때 이렇게 했었는지 기록해 두는 용도입니다.

```python
# 과거 코드 — 2026-02 개선에서 제거됨
if df_new is not None and not df_new.empty:
    save_ticker_data(ticker, df_new)

    conn.close()
    import time
    time.sleep(0.1)  # DB 커밋 완료 보장(이라고 생각했던 것)을 위한 짧은 대기
    conn = engine.connect()
```

`save_ticker_data()`가 `engine.begin()`으로 커밋을 동기적으로 완료시킨다는 점을 위에서 확인했듯, 이 `sleep(0.1)`은 실질적인 안전장치가 아니라 "혹시 몰라서" 넣은 방어적 코드(cargo-cult)였습니다. 20종목 포트폴리오 백테스트 기준 2~6초의 순수 지연을 유발했습니다. `app/repositories/yfinance_repository.py`의 3곳(`save_ticker_data()` 호출 직후 재연결하던 지점들)에서 모두 제거되었고, `conn.close(); conn = engine.connect()` 재연결 자체는 유지되었습니다. 상세 내역은 `docs/CHANGELOG-improvement-2026-02-06.md` §1-2, 독립 검증은 `docs/VERIFICATION-REPORT-2026-02-06.md` §2-2를 참고하세요.

**현재 코드에 남아있는 `time.sleep` 호출은 이 패턴과 무관합니다.** 데드락/일시 오류 재시도용 지수 백오프(`_retry_on_deadlock` 헬퍼, `load_ticker_data()`의 재시도 루프)뿐이며, `grep -n 'time.sleep' app/repositories/yfinance_repository.py`로 확인할 수 있습니다.

## 이전 비동기 문제와의 차이

-   **비동기 경쟁 상태 문제**: 비동기 컨텍스트에서 동기 I/O 함수를 직접 호출하여 발생. `asyncio.to_thread()`로 해결.
-   **트랜잭션 격리 문제 (현재)**: 동일 커넥션 내에서 다른 트랜잭션의 커밋 데이터가 보이지 않아 발생. 커넥션 재생성으로 해결.

두 문제는 독립적이지만, 모두 데이터 불일치를 유발할 수 있는 중요한 문제입니다.

## 교훈

-   **DB 트랜잭션 격리 수준 이해**: 특히 `REPEATABLE READ` 환경에서는 쓰기 후 읽기(Read-After-Write) 패턴에 주의해야 합니다.
-   **로깅의 중요성**: 상세한 로그(시도 횟수, 타이밍) 덕분에 문제의 원인을 파악할 수 있었습니다.
-   **재시도 메커니즘의 양면성**: 재시도는 일시적인 오류를 해결해주지만, 근본적인 원인을 가릴 수 있습니다. 재시도가 반복적으로 성공한다면 그 원인을 반드시 조사해야 합니다.
-   **"안전을 위한" sleep을 의심할 것**: `time.sleep(0.1)`은 근본 원인(트랜잭션 스냅샷)을 고치지 않고도 증상을 가려서 "고쳐진 것처럼" 보이게 했습니다. 커밋 시점을 실제로 보장하는 메커니즘(여기서는 `engine.begin()`의 컨텍스트 매니저 종료)이 무엇인지 먼저 확인하고, 그래도 불안하면 임의의 대기 대신 재현 가능한 회귀 테스트로 검증하는 것이 낫습니다.
