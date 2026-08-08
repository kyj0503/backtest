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
> **분업이 실제로 갈렸다**: Codex는 컨테이너를 띄워 게이트를 **실행**했고(그래서
> P0를 찾았다), Claude는 실행 경로를 **정독**했다(그래서 계산 정확성 버그를 찾았다).
> 겹치는 항목보다 서로 못 본 항목이 많으므로, 어느 한쪽만 보면 절반을 놓친다.

## 작업 현황

| 우선순위 | 남은 항목 | 내용 |
|---|---:|---|
| **P0** | 1 | A-01 — FE lock 파일 high 취약점. **현재 배포가 막혀 있다** |
| **P1** | 7 | A-02~A-08 — 틀린 숫자 2건, 동시성·자원 보호 3건, 가용성·API 결합도 2건 |
| **P2** | 6 | A-09~A-12 · A-17 · A-18 — API 계약·DB 3건, 테스트 1건, 제품 확인 2건 |
| **P3** | 4 | A-13~A-16 — 죽은 코드, 문서 동기화, 대형 모듈 분리 |
| 저장소 밖 | 4 | 배포 스크립트 태그, MySQL 8.4 실기동, Alembic baseline, 부하 튜닝 |
| **합계** | **22** | |

## 권장 처리 순서

1. **A-01** — 배포 게이트 복구. 이게 빨간불인 동안은 무엇을 고쳐도 배포되지 않는다.
2. **A-02, A-03** — 사용자에게 틀린 숫자가 나가는 두 건. 재현 테스트를 먼저 고정할 것.
3. **A-04, A-05** — 동시성 상한과 실제 작업 취소 보장. A-05는 A-04의 전제이기도 하다.
4. **A-10** — 한 줄 변경이지만 Alembic 리비전 필요. 사고 예방 효과가 가장 크다.
5. **A-07** — readiness 도입. 배포 신뢰성 직결.
6. **A-09, A-12** — API 계약 통일 + 그 회귀망. 2번과 묶으면 효율적이다.
7. **A-14, A-15, A-13** — 문서·죽은 코드 정리. 저비용, 다음 사람의 오판 방지.
8. **A-06, A-08, A-11, A-16** — 정책 결정·구조 개선(계측 선행).
9. **A-17, A-18** — 이전 라운드가 바꾼 동작의 사후 확인. 코드 변경 없이 판단만 필요한
   건이라 위 순서 어디에든 끼워 넣을 수 있다.

---

## 검증 기준선 (2026-08-08 실측)

Codex 세션이 Docker로 실제 실행해 얻은 값이다. 문서에 적힌 값이 아니라 실측값이다.

| 항목 | 결과 |
|---|---|
| BE 단위 테스트 | **358개 통과** (경고 25개) |
| BE 커버리지 | **72%** |
| BE 통합 테스트 | 12개 수집 확인, 실행하지 않음 |
| FE 테스트 | **179개 통과** |
| FE 커버리지 | Statements 47.45% / Branches 35.85% / Functions 42.34% / Lines 48.53% |
| FE 정적 검증 | ESLint · type-check · type-check:test 전부 통과 |
| FE 프로덕션 빌드 | 통과 (`PortfolioPage` 청크 549.13kB, gzip 158.44kB) |
| BE 의존성 감사 | 통과 (Bokeh 1건은 도달 불가로 기존 예외 처리) |
| **FE 의존성 감사** | **실패 — high 2건. 현재 Jenkins 배포가 막혀 있다 → A-01** |

정적 계수(Claude 세션, 참고용): BE 앱 10,266줄 / 65파일, BE 테스트 10,557줄,
FE 프로덕션 12,999줄, FE 테스트 3,725줄. 최대 파일 `portfolio_manager_service.py`
1,010줄 · `dataSampling.ts` 736줄. 공개 라우트는 `POST /api/v1/backtest` 1개.

실행한 검증:

```bash
docker build --target test ./backtest_be_fast
docker build --target test ./backtest_fe
docker run --rm <be-test-image> pytest tests/unit -q --cov=app --cov-report=term
docker run --rm <fe-test-image> npm run test:coverage
docker build --target build --output=type=cacheonly ./backtest_fe
docker build --target audit --build-arg PIP_AUDIT_IGNORE=PYSEC-2026-1223 ./backtest_be_fast
docker build --target audit --build-arg NPM_AUDIT_ALLOWLIST=GHSA-qwww-vcr4-c8h2 ./backtest_fe
```

**실행하지 않은 것**: MySQL 통합 테스트, Playwright E2E, 실제 운영 DB/배포 스크립트.
아래 항목 중 런타임 관측이 아니라 코드 구조에서 추론한 것은 해당 항목에 명시했다.

---

## P0 — 현재 배포를 막는 문제

- [ ] **A-01 [fe/infra]** FE lock 파일의 high 취약점 2건 해결 〔X-01, Claude 교차 확인〕

  `scripts/audit-deps.sh fe`와 동일 조건으로 감사하면 Docker `audit` 타깃이 종료
  코드 1을 반환한다. `Jenkinsfile:70-96`의 `Dependency Audit`은 실패를 무시하지
  않으므로(`|| true` 없음) **현재 커밋은 배포에 도달하지 못한다.**

  | 패키지 | 설치 버전 | Advisory | 의존 경로 |
  |---|---:|---|---|
  | `js-yaml` | 4.3.0 | `GHSA-5p4m-2wfm-xmqj` (high) | `shadcn → cosmiconfig → js-yaml` |
  | `nanoid` | 3.3.16 | `GHSA-2v37-7h3g-55p8` (high) | `postcss → nanoid` |

  `hono 4.12.33`의 moderate 건도 `shadcn → @modelcontextprotocol/sdk` 경로에 있으나
  high 기준을 넘지 않아 차단하지는 않는다.

  교차 확인(Claude): 세 버전 모두 `backtest_fe/package-lock.json`에 실재하고
  (`:6355, :6762, :7560`), `scripts/audit-deps.sh`의 `NPM_ALLOWLIST`에는
  react-router 1건(`GHSA-qwww-vcr4-c8h2`)만 있어 두 건은 예외 처리되지 않는다.

  조치: `npm audit fix`가 제안하는 lock 변경을 먼저 검토하고, FE 품질 게이트 4종과
  프로덕션 빌드를 다시 실행한다. **개발 도구 경로라는 이유만으로 곧장 allowlist에
  넣지 말 것** — `postcss`는 실제 빌드 경로이며, allowlist는 "업그레이드 불가 +
  도달 불가"가 둘 다 성립할 때만 쓴다(`scripts/audit-deps.sh` 상단 주석 참고).

  완료 조건: 기존 react-router 예외만 유지한 상태에서 FE `audit` 타깃이 통과한다.

---

## P1 — 사용자에게 틀린 숫자가 서빙됨

두 건 모두 Claude 세션이 실행 경로를 정독해 찾았다. 표면적으로는 정상 200 응답이라
테스트도 게이트도 잡지 못한다.

- [ ] **A-02 [be/fe]** 전략 경로가 DCA·리밸런싱을 조용히 무시함 〔C-01 / 기존 P2-13의 잔여분〕

  FE는 전략 종류와 무관하게 `investment_type`과 `rebalance_frequency`를 항상 전송한다
  (`backtest_fe/src/features/backtest/components/PortfolioBacktestForm.tsx:54,68`).
  그런데 `run_strategy_portfolio_backtest`(`portfolio_manager_service.py:310-556`)에는
  `investment_type`을 읽는 코드가 **한 줄도 없고**, 응답의 `rebalance_history`는 빈
  배열로 하드코딩된다(`:533`, 주석 "전략 포트폴리오는 리밸런싱 없음").

  결과: **SMA + 매월 적립 + 분기 리밸런싱**을 설정하면 일시금·무리밸런싱 백테스트가
  실행되고 경고가 전혀 가지 않는다. 사용자는 자신이 설정한 전략의 성과를 보고 있다고
  믿는다.

  조치(택1, 위쪽 선호):
  - 스키마/엔드포인트에서 `strategy != buy_hold_strategy` && (`investment_type == 'dca'`
    || `rebalance_frequency != 'none'`) 조합을 422로 거부 + FE에서 해당 컨트롤 비활성화
  - 최소한 응답 `warnings`에 "이 전략에서는 DCA/리밸런싱이 적용되지 않습니다"를 실어 보냄

  완료 조건: 위 조합이 조용히 통과하지 않는다(422이거나, 응답에 경고가 존재한다).

- [ ] **A-03 [be]** buy&hold 경로의 데이터 로드 실패가 무경고 원금 증발로 나타남 〔C-02 / 기존 P2-06〕

  `portfolio_data_loader.py:52-59`가 로드 실패·빈 결과 종목을 `logger.warning` 후
  `continue`로 버린다. 그런데 그 종목의 금액은 `amounts`에 남아 `total_amount`
  (= 수익률의 분모)에 계속 포함된다(`portfolio_manager_service.py:710`). 해당 종목은
  `_pre_calculate_prices`에서 가격 시리즈가 만들어지지 않아
  (`portfolio_simulation_engine.py:196-197`) 매수도 되지 않고 현금으로도 계상되지 않는다.

  결과: **투자금이 사라진 것처럼 수익률이 과소보고된다.**

  덧붙여 buy&hold 응답 dict에는 `warnings` 키 자체가 없다(전략 경로에만 존재 —
  `portfolio_manager_service.py:534`). FE는 `'warnings' in data`로 분기하므로
  (`BacktestResults.tsx:76`) 이 경로에서는 배너가 뜰 수 없다.

  조치: 실패 종목 금액을 분모에서 제외하거나 현금으로 계상 + 두 경로의 `warnings` 계약 통일.

  완료 조건: 종목 하나가 로드 실패한 요청에서 (a) 응답에 경고가 실리고, (b) 나머지
  종목만으로 계산한 수익률과 일치한다.

  > 이 항목은 [HISTORY.md](HISTORY.md)의 P2-06과 같은 건이다. 그쪽 체크박스가 `[x]`인데
  > 본문은 "⏸ 미착수"였다 — 2026-08-08 통합 시 `[ ]`로 정정하고 여기로 이관했다.

---

## P1 — 동시성·자원 보호

Codex 세션이 배포 구성(`compose.dev-prod.yaml`)과 대조해 찾은 항목들. 단일 프로세스만
가정한 기존 안전장치가 멀티 워커에서 성립하지 않는다는 공통 주제를 가진다.

- [ ] **A-04 [be/infra]** 백테스트 동시 실행 상한을 프로세스 전체 기준으로 재설계 〔X-02〕

  `app/api/v1/endpoints/backtest.py:45`의 `asyncio.Semaphore(8)`은 **프로세스 로컬
  객체**다. `compose.dev-prod.yaml`은 Uvicorn 워커 17개를 실행하므로 실제 상한은
  8건이 아니라 최대 **17 × 8 = 136건**이다.

  각 백테스트는 통합 데이터 수집에서 다시 최대 5스레드를 쓴다
  (`UnifiedDataService._MAX_PARALLEL_WORKERS = 5`). 요청 상한을 스레드·DB 커넥션·외부
  API fan-out과 함께 **워커 수까지 곱해서** 계산해야 한다(기존 P2-27의 풀 크기 산정과
  같은 축의 문제다).

  조치 후보: Redis/DB 기반 분산 세마포어 / 별도 작업 큐 + 고정 워커 풀 / 단일 API
  프로세스 + 제한된 계산 프로세스 풀 / 최소한 `workers × MAX_CONCURRENT_BACKTESTS`를
  운영 설정과 문서에 명시.

  완료 조건: 멀티 프로세스 부하 테스트에서 실제 동시 계산 수가 설정 상한을 넘지 않는다.

- [ ] **A-05 [be]** 60초 타임아웃 이후에도 동기 작업이 계속되는 문제 〔X-03〕

  `asyncio.wait_for(..., timeout=60)`(`endpoints/backtest.py:171`)는 코루틴 대기를
  취소할 뿐, `asyncio.to_thread()`에서 **이미 실행 중인** 시뮬레이션·DB·외부 API
  스레드를 종료하지 못한다. 사용자는 504를 받지만 작업은 계속되고, 코루틴 취소로
  세마포어가 먼저 반환되면 그 슬롯으로 새 요청이 추가 실행된다 — 즉 상한이 실효를 잃는다.

  FE의 `AbortController`(`client.ts:78-89`)도 브라우저 요청만 끊을 뿐 서버 스레드의
  계산을 멈추지 못한다.

  조치 후보: 계산 루프에 협력적 cancellation token 전달, 또는 강제 종료 가능한 프로세스
  작업 단위/작업 큐로 격리.

  완료 조건: 타임아웃·클라이언트 취소 이후 계산과 외부 수집이 설정 시간 안에 종료되고,
  동시 실행 슬롯이 실제 작업 종료 전에는 재사용되지 않는다. 타임아웃 테스트가 504
  반환 속도뿐 아니라 **실행 중 작업 수 감소**까지 검증해야 한다.

- [ ] **A-06 [be/infra]** 공개 서비스라면 인증·rate limit 정책 결정 〔X-04〕

  백테스트 API에 인증도, 사용자/IP별 rate limit도 없고 프로세스 로컬 세마포어만 있다.
  공개 배포를 유지한다면 고비용 요청의 악용 방지 정책이 필요하다. (A-04와 함께 결정)

---

## P1 — 가용성·API 결합도

- [ ] **A-07 [be/infra]** liveness와 readiness 분리 〔X-05〕

  `/health`(`app/main.py:99-120`)는 `len(app.routes) > 0`만 검사한다. MySQL 연결이나
  캐시 접근이 실패해도 `healthy`를 반환하므로, `Jenkinsfile:174-201`의 헬스 체크가
  통과해도 실제 사용 가능성은 보장되지 않는다.

  조치: 프로세스 생존용 liveness는 현재처럼 가볍게 유지하고, MySQL에 제한 시간 내
  `SELECT 1`을 수행하는 readiness를 별도로 둔다. 외부 Yahoo/Naver API는 readiness의
  필수 조건으로 넣지 말고 별도 관측 지표로 다룬다(외부 장애가 배포 실패로 번지지 않도록).

- [ ] **A-08 [be/fe]** 단일 백테스트 응답의 부가 데이터 결합 완화 〔X-06〕

  `POST /api/v1/backtest` 한 요청이 시뮬레이션뿐 아니라 종목 메타데이터, 원본 주가,
  환율, 변동성 이벤트, S&P 500/Nasdaq, 뉴스까지 수집해 한 번에 반환한다
  (`endpoints/backtest.py:104-131`). 부가 외부 API가 느리면 핵심 결과도 함께 지연되고
  전체가 같은 타임아웃 예산(A-05)을 나눠 쓴다.

  조치 후보: 요청의 `include_*` 옵션 / 핵심 결과와 부가 데이터 API 분리 / 비동기 작업
  결과 조회 모델. **먼저 응답 크기와 각 수집 단계의 p50/p95를 계측할 것** — 계측 없이
  분리하면 실제 병목이 아닌 곳을 자를 수 있다.

---

## P2 — API 계약 / DB

- [ ] **A-09 [be]** 같은 응답 필드가 실행 경로마다 다른 의미를 가짐 〔C-03〕

  | 필드 | 전략 경로 | buy&hold 경로 |
  |---|---|---|
  | `Win_Rate` | 거래 승률의 금액 가중평균 (`portfolio_manager_service.py:496`) | **상승일 비율** (`portfolio_calculator_service.py:91`) |
  | `Profit_Factor` (손실일 0일 때) | `0.0` (`portfolio_manager_service.py:124`) | `2.0` (`portfolio_calculator_service.py:67`) |

  FE는 두 경로의 응답을 같은 키로 같은 컴포넌트에 렌더하므로 **전략만 바꾸면 지표의
  정의가 바뀐다.** 특히 `2.0 if gross_profit > 0 else 1.0` 폴백은 [HISTORY.md](HISTORY.md)의 P3-21에서
  걷어낸 "조작된 통계"와 같은 부류의 잔재다.

  조치: 정의를 한쪽으로 통일(거래 기준/일 기준 중 택1, 필드명으로 구분하는 것도 방법)
  + 계산 불가 시 폴백 상수 대신 `None`.

- [ ] **A-10 [db]** `daily_prices`의 `ON DELETE CASCADE` 정책 결정 〔교차: C-04 = X-10〕

  부록 A의 전수 조사 결과, 물리 FK는 1개뿐이고 그 자체는 이 규모에서 급히 제거할
  이유가 약하다. **다만 `ON DELETE CASCADE`는 별도로 위험하다**:

  - `DELETE FROM stocks` 경로가 코드베이스에 없다 → CASCADE는 한 번도 발동한 적 없다
  - 실제 삭제 경로는 CASCADE에 기대지 않고 자식을 명시적으로 지운다
    (`scripts/manage_stock_splits.py:151,227`)
  - 앞으로 `stocks` 삭제 기능이 추가되면 **코드에 드러나지 않은 채** 모든 일봉이 함께
    삭제된다. 일괄 삭제 시 잠금·긴 트랜잭션·undo log 증가도 뒤따른다

  즉 지금은 **쓰이지 않는데 사고 시 피해만 큰 조합**이다.

  선택지:
  1. FK 유지 + `ON DELETE RESTRICT/NO ACTION`으로 변경해 명시적 삭제만 허용 ← 최소 비용
  2. 물리 FK 제거 + 애플리케이션이 삭제 순서와 고아 정리를 소유
  3. 현 상태 유지 + 삭제 정책·데이터 규모 한계를 ADR로 기록

  2번을 택한다면 아래를 **한 세트로** 처리해야 한다:
  - `database/schema.sql` 갱신
  - 기존 초기 리비전을 수정하지 말고 **새 Alembic 리비전 추가**
  - `(stock_id, date)` PK 유지
  - `daily_prices LEFT JOIN stocks ... WHERE stocks.id IS NULL` 고아 점검/정리 배치
  - 부모 삭제 시 자식을 먼저 지우는 명시적 트랜잭션

- [ ] **A-11 [db]** `schema.sql`과 Alembic의 스키마 정의 이중화 — 정합성 검증 부재 〔C-05〕

  `database/schema.sql`(최초 부팅 initdb)과 `alembic/versions/`(이후 변경)가 같은 DDL을
  각각 들고 있다. 의도된 설계이고 이유도 문서화돼 있지만
  (`622933e2fe2e_initial_schema.py` docstring), autogenerate용 `target_metadata`가 없어
  (ORM 미사용) **두 파일의 정합은 순전히 사람 손에 달려 있다.**

  실제로 초기 리비전은 이미 어긋난다 — `idx_ticker`, `idx_stock_date_desc`를
  만들었다가(`:79,103`) 다음 리비전 `d5c3763b29e6`에서 지운다. 최종 상태는 같지만
  빈 DB에 `upgrade head`를 돌리는 경로와 initdb 경로가 중간 상태에서 다르다.

  조치: 빈 DB에 initdb 적용한 결과와 `upgrade head` 적용한 결과의 `SHOW CREATE TABLE`을
  비교하는 CI 검증 추가, 또는 장기적으로 단일 소스 통합.

---

## P2 — 테스트

- [ ] **A-12 [fe]** 결과 화면의 사용자 흐름 테스트 강화 〔X-07〕

  FE statement 커버리지 47.45%. 계산 유틸과 API 클라이언트는 비교적 잘 검증되지만
  결과 조합 컴포넌트에 0% 구간이 많다:

  - `BacktestResults`, `StatsSummary`, `TradesChart`
  - `PortfolioTable`, `RebalanceHistoryTable`, `WeightHistoryChart`
  - `ChartsSection` 하위 포트폴리오/벤치마크 조합
  - `reportGenerator`

  **A-02·A-03이 정확히 이 구간에서 사용자에게 드러난다** — 경고 배너 미표시, 무시된
  설정값 표시가 모두 여기다. 두 버그를 고칠 때 회귀망을 같이 까는 것이 효율적이다.

  조치: 단순 스냅샷보다 정상 / 부분 데이터 / 빈 데이터 / 경고 / API 오류 시나리오를
  RTL로 검증. Playwright smoke는 전체 스택이 필요하므로 배포 전 별도 단계로 분리.

---

## P2 — 2026-08-02 라운드가 바꾼 사용자 노출 동작 (제품 확인 필요)

두 건 다 **이전 라운드에서 의도적으로 넣은 제약**이고 코드는 이미 그렇게 동작한다.
남은 것은 "이 값이 맞는가"라는 판단뿐이다. 근거 기록은 [HISTORY.md](HISTORY.md)의
"⚠️ 이번 작업으로 바뀐 사용자 노출 동작"에 있다.

- [ ] **A-17 [be]** 백테스트 최소 기간 30일 제약이 적절한지 제품 판단 〔2026-08-02 라운드 이월〕

  P2-04(검증 통합)에서 `MIN_BACKTEST_PERIOD_DAYS = 30`을 도입해 **30일 미만 요청이
  이제 422로 거부된다.** 연환산 지표(Sharpe·CAGR)가 30일 미만에서 무의미해지므로
  방어 가능한 규칙이지만, **기존에 되던 요청이 거부되는 변경**이다.

  검증 위치가 스키마가 아니라 엔드포인트인 것도 의도적이다 — DCA/시뮬레이션 내부를
  3~14일 구간으로 검증하는 기존 단위 테스트가 스키마 레벨 하한과 충돌한다
  (HTTP 요청 정책 vs 데이터 형태 검증의 분리로도 설명된다).

  조치: 30일이 과한지 판단하고, 조정한다면 `Settings.min_backtest_period_days`로 값만
  바꾼다. 유지하기로 하면 이 항목을 닫고 제약을 README/API 문서에 명시한다.

  완료 조건: 값이 확정되고 사용자 문서에 하한이 적혀 있다.

- [ ] **A-18 [be/infra]** Prometheus 티커 라벨 상한 200개의 메트릭 품질 저하 〔2026-08-02 라운드 이월〕

  P2-15에서 카디널리티 폭증을 막으려고 알려진 티커 200개 + `other` 버킷으로 상한을
  걸었다. 문제는 **LRU가 없는 first-N-seen 방식**이라는 것이다 — 초반에 무작위 티커가
  슬롯을 채우면 이후 실제 인기 티커가 전부 `other`로 묶인다.

  카디널리티 위험은 해소됐으므로 급하지 않지만, 지금 상태의 티커 인기 메트릭은
  신뢰하고 쓸 수 없다.

  조치 후보: 주기적 슬롯 리셋 / 사전 화이트리스트 / 실제 LRU. 어느 쪽이든 먼저
  현재 `other` 비율을 확인해 실제로 품질이 나빠졌는지부터 볼 것.

---

## P3 — 정리 / 문서

- [ ] **A-13 [be]** 죽은 코드가 테스트에 붙잡혀 있음 〔C-06〕

  `BacktestEngine._create_fallback_result`(`backtest_engine.py:195-275`, 80줄)는
  프로덕션 호출부가 0인데 `tests/unit/test_backtest_engine.py:363-425`가 계속 테스트한다.
  `tests/unit/test_validation_service_fallback_stats.py:14-18`이 "테스트가 참조하니
  `create_fallback_stats`를 통째로 지울 수 없다"고 스스로 적어두고 있다 —
  **테스트가 삭제를 막고 있는 구조.**

  조치: 프로덕션 메서드와 그것만을 위한 테스트를 함께 삭제.

- [ ] **A-14 [docs]** 기준선·운영 문서 동기화 〔교차: C-07 ⊂ X-08〕

  - `README.md:197`: "BE 189개 / FE 112개" — 실측은 358 / 179. 감사 전(141/113)도
    후(358/179)도 아닌 값이라 어느 시점 기준인지도 불명이다.
  - `README.md:22` 기술 스택은 MySQL **8.0**이지만 개발 Compose는 **8.4**
    (`compose.dev.yaml:47`, P2-24에서 올림).
  - 일부 내부 주석이 이미 변경된 값(과거 DB 풀 크기 등)을 참조한다.

  조치: 변하기 쉬운 테스트 개수는 CI 배지/자동 생성으로 대체하거나 릴리스 체크리스트에
  문서 갱신을 넣는다.

- [ ] **A-15 [docs]** `docs/improvement_analysis.md:282`가 코드베이스 결론과 정반대로 유도 〔C-08〕

  > **Fix:** Add `FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE`.

  `stock_news`에 FK를 **추가하라**는 2026-02 시점 권고다. 이후 `schema.sql:91-98`에서
  정확히 그 반대 결론을 근거와 함께 내렸다(뉴스/가격 저장이 독립 트랜잭션이라 FK를 걸면
  정상 저장이 실패할 수 있음). 이 문서를 보고 작업하면 의도적으로 피한 FK를 되살리게 된다.

  조치: 해당 항목에 "채택하지 않음 + 사유 + `schema.sql:91-98` 참조"를 달거나 삭제.
  문서 상단 historical 스탬프도 방법.

- [ ] **A-16 [be/fe]** 대형 모듈의 책임 분리 〔교차: C-09 ⊂ X-09〕

  | 파일 | 줄 수 |
  |---|---:|
  | `portfolio_manager_service.py` | 1,010 |
  | `yfinance_repository.py` | 767 |
  | `portfolio_simulation_engine.py` | 660 |
  | `dataSampling.ts` | 736 |
  | `useChartData.ts` | 510 |

  특히 `portfolio_manager_service.py`는 buy&hold 시뮬레이터 경로와 전략 합산 경로가
  한 파일에 있고 amount/weight 환산·현금 처리·통계 조립 규칙이 각각 따로 구현돼 있다
  (weight→금액 환산만 해도 `:334`와 `:640`에 중복). **A-02와 A-09가 이 구조에서
  파생된다.**

  기능 변경과 분리를 한 번에 하지 말 것. 기존 테스트로 동작을 고정한 뒤 입력 변환 →
  실행 → 통계 조립 → 응답 직렬화 순으로 단계적으로 추출한다.

---

## 부록 A — 물리 FK 전수 조사 (2026-08-08, 교차 검증됨)

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

## 저장소 밖 운영 후속 작업

두 세션 모두 동일하게 지목했고, [HISTORY.md](HISTORY.md)의 "저장소 밖 필수 후속 조치"와도 이어진다.
저장소 밖 시스템 또는 실제 DB 상태가 필요해 이번에도 검증하지 못했다.

- [ ] **배포 스크립트가 `${BUILD_NUMBER}`를 실제 이미지 태그로 사용하도록 수정** 〔교차〕
      — `Jenkinsfile:164-166`이 태그를 넘기지만 `/opt/home-server/scripts/deploy-app.sh`가
      무시하고 `:latest`를 pull하는 것이 빌드 #21에서 실측됨. **롤백 지점이 없다.**
      이미지는 이미 `:${BUILD_NUMBER}`로 GHCR에 있으므로 저장소 쪽 준비는 끝났다.
- [ ] 기존 MySQL 8.0 데이터 볼륨을 8.4로 올리는 실기동 검증
- [ ] `schema.sql`로 생성된 기존 DB에 Alembic baseline(`alembic stamp head`) 적용 절차 검증
- [ ] 동시 실행 8건·60초 제한을 실제 부하로 튜닝 (A-04·A-05와 함께)

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
