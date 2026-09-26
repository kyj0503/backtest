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

## 작업 현황

| 우선순위 | 남은 항목 | 내용 |
|---|---:|---|
| **P0** | 0 | — |
| **P1** | 0 | — |
| **P2** | 8 | A-21~A-25, A-33, A-34, A-36 — 틀린 숫자·조작값 5건, 응답 형태 통일 1건, 부가 수집 성능 1건, 깨진 운영 스크립트 1건 |
| **P3** | 9 | A-26~A-32, A-35, A-37 — 응답 크기, 스레드 풀 계측, 거부 사유 지표, FE/BE 상수 동기화, 특성화 테스트가 고정한 동작 판단, 모드 판정 통일, 정리 3건 |
| 저장소 밖 | 6 | 배포 태그, home-server 권고 묶음, 운영 MySQL 확인, 운영 DB 마이그레이션, 운영 상한 재조정, 운영 지표 확인 |
| **합계** | **23** | |

## 권장 처리 순서

1. **저장소 밖 1~2** — 배포 태그(롤백 지점)와 home-server 권고(헬스 체크 URL, nginx 앞단 방어). 배치9 기능이 운영에서 제대로 드러나려면 먼저 필요하다.
2. **A-36** — 일봉 갱신 스크립트가 import 오류로 깨져 있다. 운영 cron에서 쓰고 있다면 가장 먼저.
3. **A-33, A-34, A-21, A-22, A-23** — 사용자에게 나가는 틀린 숫자·조작값. A-33·A-34는 배치7 A-03·P2-07의 전략 경로판이다.
4. **A-24** — 응답 형태 통일. FE 타입 불일치를 함께 정리한다.
5. **A-25, A-26, A-27** — 부가 수집 성능·크기. 저장소 밖 6(운영 지표)으로 실측한 뒤 결정.
6. 나머지 P3.

---

## 검증 기준선 (2026-09-27 실측, 배치9 통합 후)

| 항목 | 결과 |
|---|---|
| BE 단위 테스트 | AGENTS.md Testing 절의 `Current baseline` 참고 |
| BE e2e (골든 마스터) | 통과 — `pytest tests/e2e -m e2e` (네트워크·DB 불필요) |
| FE 테스트 | AGENTS.md `Current baseline` 참고 |
| FE 정적 검증 | ESLint(경고 0) · type-check · type-check:test 통과 |
| 의존성 감사 | FE 예외 없이 통과, BE는 bokeh 1건 예외로 통과 |
| 스키마 정합성 | `scripts/check-schema-parity.sh` 통과(initdb 경로 = Alembic head, COMMENT까지) |

---

## P2

- [ ] **A-21 [be]** 단일 종목 결과의 나머지 NaN → 0.0 폴백 〔배치9 be-followups〕

  `backtest_engine._convert_result_to_response`의 `win_rate_pct`·`sharpe`·`sortino`·`calmar`·
  `avg/best/worst_trade`가 계산 불가일 때 `safe_float` 기본값 0.0이 된다. 응답의
  `strategy_details`로 나간다. `profit_factor`는 배치9에서 `optional_finite_float`로 None 처리했으니
  같은 방식으로 맞춘다. FE 타입(`StrategyStats`)도 null 허용으로.

- [ ] **A-22 [be]** buy&hold `individual_results`의 하드코딩 값 〔배치9 be-followups〕

  `sharpe_ratio: 0.0` 고정, `trades`가 DCA 매수 횟수와 무관하게 1, 현금 판별이 `asset_type`이
  아니라 `symbol == 'CASH'`(`portfolio_manager_service._format_individual_results_list`).
  FE는 지금 이 필드들을 표시하지 않지만 API 계약상 틀린 값이다.

- [ ] **A-23 [be]** buy&hold 종목별 수익률·최종 평가금이 수수료를 빼지 않은 것으로 보임 〔배치9 관찰, 원인 미검증〕

  골든 마스터에서 종목 10.53% vs 포트폴리오 10.30%, `final_equity` 9947.30 vs 9927.41.
  `individual_returns.return`은 시작가·종료가 비율로만 계산한다(`portfolio_manager_service`). 재현
  테스트로 원인을 확인하고, 종목별 값도 수수료 반영 기준으로 맞출지 결정.

- [ ] **A-24 [be/fe]** 응답 형태가 경로마다 다름 〔배치9 fe-followups〕

  `individual_returns`의 키가 전략 경로는 심볼, buy&hold는 unique_key, 현금은 `CASH`이고 필드 구성도
  다르다(가격 vs 금액). FE `api-types.ts`의 `PortfolioBacktestResponse`(`chart_data`, `stats` 등)는 실제
  응답과 달라 화면이 `PortfolioData`로 캐스팅해 읽는다. BE 항목 형태를 하나로 정하고 FE 타입을 합친다.

- [ ] **A-25 [be]** 뉴스 수집이 종목별로 순차 실행 〔배치9 api〕

  종목당 10초 타임아웃, 20종목이면 최악 200초. 응답은 부가 수집 예산(15초)으로 막히고 남은 스레드는
  하위 취소 토큰으로 다음 확인 지점에서 멈추지만, 그 전까지 뉴스 외부 호출이 순차로 이어진다.
  병렬화 + 상한. 네이버 키가 있는 환경에서 실측 선행(배치9에서는 키가 없어 실측 못 함).

- [ ] **A-33 [be]** 전략 포트폴리오 경로의 실패 종목이 수익률 분모에 남음 〔배치9 A-16 발견〕

  `portfolio_execution.run_strategy_per_symbol`에서 백테스트에 실패한 종목의 금액이 `total_amount`에
  남아 수익률이 과소보고된다(스냅샷 `strategy_amount_mixed` −11.6%). buy&hold 경로는 배치7 A-03으로
  분모에서 빼고 `warnings`에 싣는다. 같은 규칙으로 맞춘다.

- [ ] **A-34 [be]** 전략 경로에서 같은 이름의 현금 항목이 서로 덮어씀 〔배치9 A-16 발견〕

  `portfolio_inputs.resolve_strategy_amounts`가 종목 이름을 키로 써서 뒤 항목이 앞 항목을 덮어쓴다. amount
  모드 총액은 입력값 합계라 dict 합계와 어긋난다. buy&hold 경로의 P2-07(현금마다 고유 키)과 같은 수정.

- [ ] **A-36 [infra]** `backtest_be_fast/scripts/daily_price_update.py`가 없는 `save_ticker_data`를 import해 실행되지 않는다 〔배치9 A-16 발견, 배치9 이전(4a4a8a3)부터 깨져 있었음〕

  운영에서 이 스크립트로 일봉을 갱신하고 있다면 조용히 멈춰 있을 수 있다. 올바른 저장 경로로 고치고
  실행 테스트를 추가한다. 운영 cron 사용 여부는 home-server 쪽에서 확인.

## P3

- [ ] **A-26 [be/fe]** 벤치마크 응답을 주말까지 날짜별로 채움 — `fill_missing_dates` 때문에 5년 기준 두 지수 합쳐 약 264KiB. 거래일만 보내거나 FE에서 맞춘다.
- [ ] **A-27 [be]** `collect_all_unified_data`의 스레드 풀 겹침 — 바깥 풀(5)과 가격 조회용 안쪽 풀(최대 5)이 겹쳐 한 요청이 프로세스당 DB 풀(4+2=6)보다 많은 스레드로 조회할 수 있다. `backtest_stage_duration_seconds`로 실제 풀 대기가 있는지 먼저 확인.
- [ ] **A-28 [be]** 백테스트 거부 사유별 카운터 — 429/503/504/499가 지금은 경고 로그뿐. 실행 중·대기 중 게이지(`backtest_jobs_running`/`waiting`)는 배치9에서 추가됨.
- [ ] **A-29 [be/fe]** 최소 기간 30일이 BE 설정(`min_backtest_period_days`)과 FE 상수(`VALIDATION_RULES.MIN_BACKTEST_PERIOD_DAYS`) 두 곳에 있다. 설정 노출 API나 빌드 시 주입으로 한 곳에서 관리할지 검토.
- [ ] **A-30 [fe]** A-16 특성화 테스트가 "현재 동작"으로 고정한 두 가지가 의도인지 판단 — (1) 월간 가격 샘플링에서 목표일이 휴장일이라 다음 날로 밀리면 이후 달의 기준 요일이 바뀐다. (2) 월간 수익률 집계에서 60개월 넘는 공백을 만나면 그 경계를 넘는 항목이 빠진다. 고치면 해당 특성화 테스트 기대값도 바꾼다.
- [ ] **A-31 [fe]** 정리 — 호출처가 없어진 `useBacktest.reset`, 쓰이지 않는 `PortfolioStats.win_rate`.
- [ ] **A-35 [be]** 금액/비중 모드 판정이 경로마다 다름 — 전략 경로는 포트폴리오 전체가 한 모드여야 하고 buy&hold는 종목마다 판정하며 거부 메시지도 다르다. 스키마는 "비중 합계 95~105%이면서 일부 종목만 amount·weight를 둘 다 비운" 요청을 통과시킨다. 스키마에서 거부할지 결정.
- [ ] **A-37 [infra]** `backtest_be_fast/.dockerignore`의 `__pycache__/`가 루트에만 적용돼 하위 폴더의 호스트 `.pyc`가 test 이미지에 복사된다(`**/__pycache__`로). 테스트 결과에는 영향 없음.
- [ ] **A-32 [db]** 기존 DB(운영·dev)의 COMMENT 정리 — schema.sql 초기화 당시 initdb 클라이언트 문자셋(latin1) 때문에 테이블 COMMENT 3개·컬럼 5개가 이중 인코딩돼 있고 나머지 컬럼은 COMMENT가 없다(배치9 A-11에서 원인 수정). 기능 영향 없음. 운영 `SHOW CREATE TABLE`을 저장소 정의와 비교한 뒤 결정.

---

## 부록 A — 물리 FK 전수 조사 (2026-08-08, 교차 검증됨)

> **2026-09-26 갱신: 아래의 유일한 물리 FK(`daily_prices_ibfk_1`)는 배치8에서 제거했다**
> (Alembic `7b2e9c4f1a30`, `schema.sql` 갱신). 제거는 "모든 테이블 간 참조를 논리
> 참조로 둔다"는 정책 결정이며, 아래 "현재 FK가 즉시 결함은 아닌 이유"와 "락·데드락"
> 분석은 그 결정 이전의 판단 기록으로 남겨 둔다. 데드락 재시도(`_retry_on_deadlock`)는
> FK와 무관한 동시 upsert 충돌 대비라 그대로 유지한다. 고아 점검은
> `backtest_be_fast/scripts/check_orphan_prices.py`. 운영 DB 적용 후에는 아래
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

저장소 밖 시스템(home-server, 운영 서버·DB)이 필요해 이 저장소에서 검증할 수 없는 항목이다.

- [ ] **1. 배포 스크립트가 `${BUILD_NUMBER}`를 실제 이미지 태그로 사용하도록 수정** 〔교차〕
      — Jenkinsfile이 태그를 넘기지만 `/opt/home-server/scripts/deploy-app.sh`가 무시하고 `:latest`를
      pull한다(빌드 #21 실측, 2026-09-27 운영 배포 #27에서도 재확인). **롤백 지점이 없고** 헬스 체크
      성공만으로 새 이미지 가동을 판단할 수 없다. 수정 위치는 home-server 저장소.
- [ ] **2. home-server 권고 묶음** (배치9 결과)
      - Jenkins 배포 후 헬스 체크 URL을 `/health` → `/health/ready`로(DB까지 확인, 실패 시 503). 컨테이너
        HEALTHCHECK는 재시작 폭주를 막으려 `/health` 유지.
      - nginx 앞단 방어: `/api/v1/backtest`에 `limit_req`(IP당 예: 10r/m, burst). `X-Forwarded-For`를
        `$proxy_add_x_forwarded_for`로 넘기는지 확인 — 안 넘기면 BE의 IP별 동시 실행 제한(A-06)이 꺼진다.
      - `scripts/check-schema-parity.sh`를 BE 파이프라인 단계로 연결(Docker·인터넷 필요, 약 20초).
      - 지표 알림: `backtest_supplemental_outcome_total{outcome=~"empty|timeout|error"}` 비율,
        `backtest_jobs_waiting`.
- [ ] **3. 운영 MySQL 서버 버전·인증 플러그인 확인** — `SELECT VERSION(); SELECT user,host,plugin FROM mysql.user;`.
      8.0이면 `database/README.md` 절차(덤프 → 정상 종료 → 8.4)로 올린다. 8.4는 `mysql_native_password`
      계정 로그인이 1524로 실패하므로 먼저 `caching_sha2_password`로 바꾼다(로컬 8.0.46→8.4.11 재현 완료).
- [ ] **4. 운영 DB에 `alembic upgrade head`** — 배치9 리비전 `1f574a9ba22e`(stock_id COMMENT만 변경,
      INSTANT) 적용. 기능 영향 없어 선택. 파이프라인·운영 이미지에 Alembic이 없어 수동.
- [ ] **5. 운영 동시 실행 상한 재조정** — 운영 BE의 워커 수·CPU 한도를 확인하고 `MAX_CONCURRENT_BACKTESTS`를
      "CPU 수 × 2" 기준으로 맞춘다(로컬 17 workers/4 CPU에서 8~12 포화, 16은 실행 p95 45초).
      BE 컨테이너를 여러 개 띄우면 상한이 컨테이너마다 따로라는 점도 재검토.
- [ ] **6. 운영 지표 확인** — 배포 후 `backtest_stage_duration_seconds`로 단계별 p50/p95(뉴스 포함),
      `ticker_popularity_total`의 `other` 비율을 본다. A-25~A-27 결정의 근거.

---

## 변경 시 공통 완료 기준

[HISTORY.md](HISTORY.md)의 "변경 시 공통 완료 기준"을 그대로 승계한다 — 수정 전 실패를 재현하는 테스트가
존재할 것, 아래 6개 명령이 전부 통과할 것.

```bash
docker compose -f compose.dev.yaml exec -T backtest-be-fast pytest tests/unit -q
docker compose -f compose.dev.yaml exec -T backtest-fe npm run lint
docker compose -f compose.dev.yaml exec -T backtest-fe npm run type-check
docker compose -f compose.dev.yaml exec -T backtest-fe npm run type-check:test
docker compose -f compose.dev.yaml exec -T backtest-fe npm run test:run
docker compose -f compose.dev.yaml exec -T backtest-fe npm run build
```
