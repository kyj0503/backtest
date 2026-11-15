# TODO — 남은 작업 목록

> **완료된 작업의 이력은 [HISTORY.md](HISTORY.md)에 있다.** 이 문서에는 아직 하지
> 않은 일만 남긴다. 항목을 끝내면 체크만 하지 말고 HISTORY.md로 옮긴다.
>
> 2026-08-08. 두 독립 세션 분석의 통합본. 원본 문서(`todo-claude.md`,
> `todo-codex.md`)는 이 문서로 합친 뒤 삭제했다 — 원문이 필요하면 커밋
> `7965874`(Claude) / `ae94a60`(Codex)에 그대로 남아 있다.
>
> **표기**: 〔교차〕 = 두 세션이 독립적으로 동일 결론(확신도 최상).
> 〔C〕 = Claude 단독 발견. 〔X〕 = Codex 단독 발견. 대괄호 안 `C-0n`/`X-0n`은
> 원본 문서의 항목 번호로, 옛 커밋을 추적할 때 쓴다.
>
> **분업이 실제로 갈렸다**: Codex는 컨테이너를 띄워 검사 단계를 **실행**했고(그래서
> P0를 찾았다), Claude는 실행 경로를 **정독**했다(그래서 계산 정확성 버그를 찾았다).
> 겹치는 항목보다 서로 못 본 항목이 많으므로, 어느 한쪽만 보면 절반을 놓친다.

> **2026-09-27 배치9**: 위 두 세션이 남긴 A-04~A-19를 모두 처리했다(HISTORY.md 배치9).
> 아래 항목은 배치9 작업 중 에이전트들이 **새로 발견한 것**과 저장소 밖 후속 작업이다.
> 번호는 A-21부터 이어 붙인다.

> **2026-11-15 Go 전환**: 백엔드가 Go(`backtest_be_go`)로 바뀌었다(docs/go-migration.md). Python 파일을
> 가리키던 항목은 Go 위치로 고쳐 적었고, Go에서 해소된 A-21·A-25·A-27·A-37은 HISTORY.md로 옮겼다.
> 전환 후속 작업은 G-01부터 번호를 붙인다.

## 작업 현황

| 우선순위 | 남은 항목 | 내용 |
|---|---:|---|
| **P0** | 0 | — |
| **P1** | 3 | G-01~G-03 — 운영 DB 덤프 리허설·전환, 콘솔 계약 브랜치 배포, 운영 외부 연동 확인 |
| **P2** | 2 | A-24, G-04 — 응답 형태 통일, Python 시절 테이블 정리 |
| **P3** | 7 | A-26, A-28~A-32, A-35 — 응답 크기, 거부 사유 지표, FE/BE 상수 동기화, 특성화 테스트 판단, 정리, COMMENT, 모드 판정 |
| 저장소 밖 | 4 | 공통 게이트웨이 권고 묶음, 운영 MySQL 확인, 운영 상한 재조정, 운영 지표 확인 |
| **합계** | **16** | |

## 권장 처리 순서

1. **G-01 → G-02 → G-03** — 운영 전환. 리허설 결과로 00002 소요 시간을 보고 시간대를 정한다.
2. **저장소 밖 2, 6** — 공통 게이트웨이 방어와 운영 지표(전환 후 Go 지표로 실측).
3. **A-24** — 응답 형태 통일. 콘솔 타입과 함께.
4. 나머지.

---

## 검증 기준선 (2026-11-15, Go 전환 후)

| 항목 | 결과 |
|---|---|
| BE 단위 테스트 | `docker build --target test ./backtest_be_go` 통과(11개 패키지, -race, staticcheck) |
| BE 통합 테스트 | `bash scripts/test-go-integration.sh` 통과(migrate, 시세 캐시) |
| E2E | `compose.go-test.yaml` 통과(콘솔 rust-migration 계약 스펙) |
| 의존성 감사 | govulncheck 예외 없이 통과 |
| 스키마 정합성 | `scripts/check-schema-parity.sh` 통과(initdb = goose head, COMMENT까지) |

---

## P1

- [ ] **G-01 [db/infra]** 운영 DB 덤프로 전환 리허설 후 운영 적용 — OCI 서버에서 `scripts/load-devdb.sh`
  머리말의 `mysqldump`로 덤프를 떠 로컬 복사본에 적재하고 `detect → baseline 1 → up`, 실데이터 계산,
  00002 소요 시간을 확인한다. 그다음 운영 백업 → `backtestctl migrate baseline 1` → `up`
  (docs/go-migration.md "운영 전환 절차"). 합성 덤프와 로컬 dev DB로만 리허설했다.
- [ ] **G-02 [fe/infra]** 콘솔 계약 브랜치 배포 — Go API는 rust 계약(`asset_id`, `Time_Weighted_Return`,
  `calculation_assumptions`, `total_amount` 입력 등)을 따른다. backtest-console rust-migration 브랜치(F03 30일
  근사, F12 주간 버킷, F13 매수·매도 마커, F16 CSV 따옴표 수정 포함)를 develop·main으로 올려 백엔드와 같은 때
  배포한다. develop 콘솔은 새 필드를 모른다.
- [ ] **G-03 [infra]** 운영 외부 연동 확인 — OCI 관리형 MySQL TLS(`DATABASE_SSL_CA`, 호스트명 검사 끔) 실접속,
  Turnstile 실토큰, 유효한 네이버 키(개발 `.env` 키는 401), ARM64 이미지 실행. 배포 직후 `/health/ready`,
  `backtest_supplemental_outcome_total`, G01 경고 로그를 본다.

## P2

- [ ] **G-04 [db]** Python 시절 테이블 정리 — 운영 전환이 안정되면 `alembic_version` 테이블을 지운다
  (`schema.sql`과 goose에는 없다). 새 goose 파일 없이 수동 DROP으로 한다(이력 테이블일 뿐이다).

- [ ] **A-24 [be/fe]** 응답 형태가 경로마다 다름 〔배치9 fe-followups〕

  `individual_returns`의 키가 전략 경로는 심볼, buy&hold는 unique_key, 현금은 `CASH`이고 필드 구성도
  다르다(가격 vs 금액). FE `api-types.ts`의 `PortfolioBacktestResponse`(`chart_data`, `stats` 등)는 실제
  응답과 달라 화면이 `PortfolioData`로 캐스팅해 읽는다. BE 항목 형태를 하나로 정하고 FE 타입을 합친다.

  2026-10-25: FE의 포트폴리오 응답 타입은 실제 `PortfolioData`로 통일하고 fixture의
  이중 캐스팅을 제거했다. 계산/참고 조회 분리는 HISTORY의 A-38. 위 항목 중 남은
  작업은 서버의 종목별 항목 키·필드 의미를 일관되게 정하는 것이다.

  2026-11-15(Go): 키는 두 경로 모두 `asset_id`로 통일됐다. 필드 구성은 아직 다르다 —
  `internal/engine/response.go`의 `HoldingReturn`(buy&hold: 시작·끝 가격, 적립 회차)과
  `StrategyReturn`(전략: 초기·최종 평가액, 승률).

## P3

- [ ] **A-26 [be/fe]** 벤치마크 응답을 주말까지 날짜별로 채움 — `internal/api/reference.go`의 `benchmark`가 요청 기간의 모든 달력일을 채운다(5년 기준 두 지수 합쳐 약 264KiB). 포트폴리오도 달력일 평가라 지금은 맞물리지만, 크기가 문제면 거래일만 보내고 FE에서 맞춘다.
- [ ] **A-28 [be]** 백테스트 거부 사유별 카운터 — 429/503/504/499가 지금은 로그뿐(`internal/api/backtest.go`의 `writeErr`). 실행 중·대기 중 게이지(`backtest_jobs_running`/`waiting`)는 있다.
- [ ] **A-29 [be/fe]** 최소 기간 30일이 BE 설정(`MIN_BACKTEST_PERIOD_DAYS`)과 FE 상수(`VALIDATION_RULES.MIN_BACKTEST_PERIOD_DAYS`) 두 곳에 있다. 설정 노출 API나 빌드 시 주입으로 한 곳에서 관리할지 검토.
- [ ] **A-30 [fe]** A-16 특성화 테스트가 "현재 동작"으로 고정한 두 가지가 의도인지 판단 — (1) 월간 가격 샘플링에서 목표일이 휴장일이라 다음 날로 밀리면 이후 달의 기준 요일이 바뀐다. (2) 월간 수익률 집계에서 60개월 넘는 공백을 만나면 그 경계를 넘는 항목이 빠진다. 고치면 해당 특성화 테스트 기대값도 바꾼다.
- [ ] **A-31 [fe]** 정리 — 호출처가 없어진 `useBacktest.reset`, 쓰이지 않는 `PortfolioStats.win_rate`.
- [ ] **A-35 [be]** 일부 종목만 amount·weight를 둘 다 비운 요청 — 경로 간 판정 차이는 Go에서 해소했다(HISTORY 2026-11-15). 남은 것: "비중 합계 95~105%이면서 일부 종목만 amount·weight를 둘 다 비운" 요청이 통과하고 그 종목은 0원으로 계산된다(`internal/api/validate.go` `portfolioRules`, `internal/engine/request.go` `Validate`). 거부할지 결정.
- [ ] **A-32 [db]** 기존 DB(운영·dev)의 COMMENT 정리 — schema.sql 초기화 당시 initdb 클라이언트 문자셋(latin1) 때문에 테이블 COMMENT 3개·컬럼 5개가 이중 인코딩돼 있고 나머지 컬럼은 COMMENT가 없다(배치9 A-11에서 원인 수정). 기능 영향 없음. 운영 `SHOW CREATE TABLE`을 저장소 정의와 비교한 뒤 결정.

---

## 부록 A — 물리 FK 전수 조사 (2026-08-08, 교차 검증됨)

> **2026-09-26 갱신: 아래의 유일한 물리 FK(`daily_prices_ibfk_1`)는 배치8에서 제거했다**
> (Alembic `7b2e9c4f1a30`, `schema.sql` 갱신). 제거는 "모든 테이블 간 참조를 논리
> 참조로 둔다"는 정책 결정이며, 아래 "현재 FK가 즉시 결함은 아닌 이유"와 "락·데드락"
> 분석은 그 결정 이전의 판단 기록으로 남겨 둔다. 데드락 재시도(`_retry_on_deadlock`)는
> FK와 무관한 동시 upsert 충돌 대비라 그대로 유지한다(Go: `MySQLStore.Save`의 1213/1205 재시도). 고아 점검은
> `backtestctl check-orphans`(당시 `check_orphan_prices.py`). 운영 DB 적용 후에는 아래
> "운영 DB 확인 SQL"이 0행을 반환해야 한다. → **2026-09-27 운영 DB 적용 완료**
> (`7b2e9c4f1a30`, FK 0개, 고아 0건 — [HISTORY.md](HISTORY.md) 운영 반영 섹션).

두 세션이 **독립적으로 동일한 결론**에 도달했다. 확신도 최상.

### 결론

소스와 Alembic에 존재하는 물리 FK는 **정확히 1개**다.

| 자식 | 부모 | 정의 | 판단 |
|---|---|---|---|
| `daily_prices.stock_id` | `stocks.id` | `ON DELETE CASCADE` | 물리 FK 존재. FK 자체보다 cascade가 문제 → A-10 |
| `stock_news.ticker` | `stocks.ticker` | **FK 없음** | 가격·뉴스 저장 순서가 보장되지 않아 의도적으로 느슨하게 결합 |

근거: `database/schema.sql:73` / `alembic/versions/622933e2fe2e_initial_schema.py:92`
/ `database/schema.sql:91-98`(`stock_news`에 FK를 두지 않은 사유).

SQLAlchemy `ForeignKey`·`relationship()`은 0건 — ORM을 쓰지 않고 raw SQL/Core만 쓰므로
JPA 연관관계 매핑류의 문제는 애초에 해당하지 않는다. git 히스토리상 `stock_news`에 FK가
존재한 적도 없다(`git log --all -S "REFERENCES stocks(ticker)"` → 소스 커밋 0건,
문서 1건은 A-15).

### 현재 FK가 즉시 결함은 아닌 이유

- 하나의 FastAPI 서비스만 동일 MySQL DB에 접근한다
- `stocks`와 `daily_prices`는 같은 캐시 aggregate이며 생명주기가 강하게 결합돼 있다
- `save_ticker_data()`는 한 트랜잭션에서 부모 upsert → ID 조회 → 자식 배치 upsert
  순서로 실행한다(`yfinance_repository.py:214-222`)
- `daily_prices`의 PK `(stock_id, date)`가 FK 조회에 필요한 인덱스를 이미 제공한다
- `DELETE FROM stocks` 경로가 발견되지 않았다

### 원칙별 해당 여부

| 물리 FK를 피하는 근거 | 이 저장소 |
|---|---|
| 락·데드락 확대 | ⚠️ 부분 해당 (아래 주의) |
| 대량 배치 INSERT 성능 | 🔸 미미 — 500행 청크 upsert(`yfinance_repository.py:199-202`), 종목당 10년 ≈ 2,500행. 부모가 PK 단일 행이라 체크 비용이 사실상 상수 |
| 온라인 스키마 변경 곤란 | ❌ 미해당 — 테이블 3개, pt-osc류를 쓸 규모가 아님 |
| 샤딩·서비스 분리 걸림돌 | ❌ 미해당 — 단일 캐시 DB |
| CASCADE 대량 삭제 위험 | ⚠️ **해당 → A-10** |
| JPA 연관관계 매핑 문제 | ❌ 미해당 — ORM 미사용 |

### 락·데드락에 대한 주의

`save_ticker_data`에는 **이미 `_retry_on_deadlock`이 붙어 있다**
(`yfinance_repository.py:38-60`, 에러 1213 / Lock wait timeout 감지). 데드락이 실제로
관측된 적이 있다는 신호다.

InnoDB가 자식 행 INSERT 시 부모 행에 공유 락을 거는 것은 사실이므로 FK가 락 표면을
넓히는 것은 맞다. 다만 이 구조에서 **더 유력한 용의자는 같은 `stocks` 행에 대한 동시
`ON DUPLICATE KEY UPDATE`(배타 락)** 다 — 동일 티커에 캐시 미스가 동시에 나면 FK가
없어도 충돌한다. FK를 떼도 데드락은 남을 가능성이 높다.

**→ 조치 전에 `SHOW ENGINE INNODB STATUS`의 `LATEST DETECTED DEADLOCK`을 먼저 확인할 것.**
추측으로 FK를 제거하면 원인은 그대로 둔 채 무결성 보장만 잃는다.
(이 항목은 코드 구조에서 추론한 것이며 런타임으로 관측하지 않았다.)

### FK를 제거할 경우 반드시 함께 가야 하는 것

`daily_prices`의 PK는 `(stock_id, date)`이고 `stock_id`는 `stocks.id` 대리 키다. 읽기
경로는 항상 `ticker → stocks.id → daily_prices`이므로(`yfinance_repository.py:600`),
고아 행이 생기면 그 가격 데이터는 **영원히 조회 불가능한 채 디스크만 차지한다**
(조용한 캐시 미스 + 용량 누수). 고아 정리 배치가 세트로 필요하다. → A-10 선택지 2

### 운영 DB 확인 SQL

저장소 정의와 실제 DB가 migration drift로 다를 수 있으므로 운영 DB에서는 다음으로
최종 상태를 확인한다.

```sql
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'stock_data_cache'
  AND REFERENCED_TABLE_NAME IS NOT NULL;
```

---


---

## 저장소 밖 운영 후속 작업

저장소 밖 시스템(공통 게이트웨이, 운영 서버·DB)이 필요해 이 저장소에서 검증할 수 없는 항목이다.

- [ ] **2. 공통 게이트웨이·관측 권고 묶음** (배치9 결과)
      - nginx 앞단 방어: `/api/v1/backtest`에 `limit_req`(IP당 예: 10r/m, burst). `X-Forwarded-For`를
        `$proxy_add_x_forwarded_for`로 넘기는지 확인 — 안 넘기면 BE의 IP별 동시 실행 제한(A-06)이 꺼진다.
      - 지표 알림: `backtest_supplemental_outcome_total{outcome=~"empty|timeout|error"}` 비율,
        `backtest_jobs_waiting`.
- [ ] **3. 운영 MySQL 서버 버전·인증 플러그인 확인** — `SELECT VERSION(); SELECT user,host,plugin FROM mysql.user;`.
      8.0이면 `database/README.md` 절차(덤프 → 정상 종료 → 8.4)로 올린다. 8.4는 `mysql_native_password`
      계정 로그인이 1524로 실패하므로 먼저 `caching_sha2_password`로 바꾼다(로컬 8.0.46→8.4.11 재현 완료).
- [ ] **5. 운영 동시 실행 상한 재조정** — Go 서버는 프로세스 하나라 Python의 "17 workers" 측정 근거가 더는
      맞지 않는다. 운영 CPU 한도를 확인하고 `MAX_CONCURRENT_BACKTESTS`·`DATABASE_MAX_OPEN_CONNS`를 실측으로
      정한다(rust 비교에서 같은 계산의 순차 중앙값 Python ~100ms, 컴파일 언어 ~4ms).
- [ ] **6. 운영 지표 확인** — 배포 후 `backtest_stage_duration_seconds`로 단계별 p50/p95(뉴스 포함),
      `ticker_popularity_total`의 `other` 비율을 본다. A-26 결정의 근거.

---

## 변경 시 공통 완료 기준

[HISTORY.md](HISTORY.md)의 "변경 시 공통 완료 기준"을 그대로 승계한다 — 수정 전 실패를 재현하는 테스트가
존재할 것, 아래 명령이 전부 통과할 것(2026-11-15부터 백엔드는 Go).

```bash
docker build --target test ./backtest_be_go
bash scripts/test-go-integration.sh
sh scripts/check-schema-parity.sh
docker compose -f ../backtest-console/compose.dev.yaml exec -T console npm run lint
docker compose -f ../backtest-console/compose.dev.yaml exec -T console npm run type-check
docker compose -f ../backtest-console/compose.dev.yaml exec -T console npm run type-check:test
docker compose -f ../backtest-console/compose.dev.yaml exec -T console npm run test:run
docker compose -f ../backtest-console/compose.dev.yaml exec -T console npm run build
```
