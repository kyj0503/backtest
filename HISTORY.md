# HISTORY — 완료 작업 이력

> **아직 남은 작업은 [TODO.md](TODO.md)에 있다.** 이 문서는 이미 처리한 항목의
> 보관소다. 무엇을 왜 그렇게 고쳤는지의 근거가 남아 있어, 같은 코드를 다시 만질 때
> 판단 근거로 쓴다. 새 백로그를 여기에 적지 말 것.
>
> 항목을 완료하면 TODO.md에서 이 문서로 옮기고, 체크박스를 `[x]`로 바꾼 뒤
> 날짜와 실제로 한 일을 괄호에 적는다.

---

## 2026-09-27 라운드 (배치9)

> TODO.md에 남아 있던 A-04~A-19(A-10 제외, 배치8 완료)와 저장소 밖 항목 중 로컬에서 재현
> 가능한 두 건(MySQL 8.4 업그레이드, 부하 튜닝)을 처리했다. 서브 에이전트 여러 개가 격리된
> worktree에서 병렬로 작업하고(1차 6개, 2차 3개, 3차 1개) `integration/batch9`에서 통합했다.
> 1차 작업 중 새로 발견된 버그는 2차에서 고쳤고, 나머지는 TODO.md A-21 이후로 남겼다.
> 사용자 위임 결정: A-19 시간가중, A-09 일 기준 통일, A-06 인증 없이 IP별 제한, A-17 30일 유지.

### 검증 기준선 (통합 후 실측)

- [x] BE 단위 테스트 전부 통과(370 → AGENTS.md `Current baseline`), 골든 마스터 e2e 통과
- [x] FE 테스트 전부 통과(188 → AGENTS.md `Current baseline`), statements 커버리지 약 48% → 74%
- [x] ESLint 경고 0, type-check(prod·test), 프로덕션 빌드, Docker `--target test` 양쪽, 운영 이미지 빌드
- [x] `scripts/check-schema-parity.sh` 통과, dev 스택 기동 + 실데이터 스모크

### P1 — 동시성·자원 보호

- [x] **A-04 [be/infra]** ✅ 2026-09-27 (락 파일 슬롯, `app/core/file_slots.py`) — 프로세스 로컬 `Semaphore(8)` × 17 workers = 최대 136건이던 상한을 같은 컨테이너 워커들이 공유하는 N개 `fcntl.flock` 락 파일 슬롯으로 교체. 프로세스가 죽으면 OS가 해제. MySQL `GET_LOCK`은 작업 내내 커넥션을 점유하고 끊기면 풀려서 기각. 로컬 17 workers 부하: 옛 코드 동시 약 32건 → 새 코드 정확히 8건.
- [x] **A-05 [be]** ✅ 2026-09-27 (작업 전용 이벤트 루프 + 협력적 취소 토큰, `app/services/backtest_runner.py`, `app/core/cancellation.py`) — 타임아웃·연결 끊김 시 전용 루프의 태스크를 취소(모든 await가 취소 지점)하고, 스레드 안 긴 구간(시뮬레이션 일별 루프, Yahoo·DB·뉴스 재시도 대기)에 확인 지점을 뒀다. 병렬 수집에는 `submit_with_context`로 토큰을 넘긴다. `BacktestCancelled`는 `except Exception`에 삼켜지지 않도록 `BaseException`. 슬롯은 작업이 만든 스레드가 모두 끝난 뒤에만 반환. 60초는 실행 시간만(대기는 30초 후 503). 실측 취소 후 종료 p50 1.1초/최대 2.1초. 끊을 수 없는 구간: `bt.run()` 한 번(약 0.04초), 외부 HTTP·DB 호출 한 번.
  - 통합 시 A-08과의 결합: 부가 수집 시간 예산을 넘긴 스레드가 슬롯 반환 뒤에도 계속 돌 수 있어, 수집 스레드에 작업 토큰과 연결된 하위 토큰을 주고 예산 초과 시 하위 토큰만 취소한다(`test_supplemental_cancellation.py`, 하위 토큰 취소를 빼면 2건 실패).
- [x] **A-06 [be/infra]** ✅ 2026-09-27 (공개 유지, 인증 없음, IP별 동시 2건 → 429, `app/core/client_ip.py`) — `X-Forwarded-For`를 오른쪽부터 읽어 신뢰 대역(`TRUSTED_PROXY_CIDRS`) 밖의 첫 주소를 클라이언트로 본다. 비신뢰 피어는 헤더 무시, 식별 불가 시 IP별 제한 미적용(전체 사용자가 프록시 주소 하나로 묶이는 사고 방지), IPv6는 /64. nginx 레벨 rate limit은 home-server 후속(TODO 저장소 밖 2).
- [x] **(저장소 밖) 동시 실행 8건·60초 부하 튜닝** ✅ 2026-09-27 (로컬 측정) — 17 workers/4 CPU에서 상한 4/8/12/16의 처리량 0.63/0.91/0.95/0.64 rps, 16은 실행 p95 45초. 기본값 8·60초·대기 30초 유지, 기준 "CPU 수 × 2". 운영 재조정은 TODO 저장소 밖 5.

### P1 — 가용성·API 결합도

- [x] **A-07 [be/infra]** ✅ 2026-09-27 — `/health`는 liveness로 그대로 두고 `GET /health/ready` 추가(운영 풀과 별개인 전용 연결 + 드라이버 타임아웃으로 `SELECT 1`, 기본 2초, 실패 시 503 `checks.database=timeout|unavailable`, 한 번에 하나만 실행). 외부 API는 조건에서 제외. Dockerfile HEALTHCHECK는 재시작 폭주를 막으려 liveness 유지. 로컬 mysql:8.4 pause/stop/재시작으로 200→503→200 실측.
- [x] **A-08 [be/fe]** ✅ 2026-09-27 — 계측 먼저: `backtest_stage_duration_seconds{stage}`와 요청당 요약 로그. 워밍 실측에서 부가 데이터가 응답의 67~74%, 시뮬레이션+부가 시간의 p50 60%. 하위 호환 `include_*` 5개(기본 True), 부가 수집 시간 예산 `SUPPLEMENTAL_DATA_TIMEOUT_SECONDS`=15초, `data.supplemental_status`와 `backtest_supplemental_outcome_total{section,outcome}` 추가, 부가 수집 전체 실패도 핵심 결과는 200. 전부 끄면 응답 64~70%, 소요 p50 51~69% 감소. FE는 timeout/error 섹션을 결과 상단에 한 줄로 안내.

### P2 — API 계약 / 지표

- [x] **A-19 [be]** ✅ 2026-09-27 (시간가중) — DCA 연환산 수익률이 총 납입액을 첫날 투자한 것처럼 계산돼, 매 영업일 0.05% 오르는 종목에 월 적립하면 가격 연환산 13.96%가 7.16%로 보고됐다. `Daily_Return` 누적곱으로 연환산하도록 `metrics_math.time_weighted_annual_return`으로 통합(Sharpe도 이 값). 첫날 매수 수수료는 엔진이 `attrs['twr_start_ratio']`로 넘긴다. 일시금·전략 경로 결과 불변, `Total_Return` 유지, FE에 "연환산 수익률 (시간가중)" 카드.
- [x] **A-09 [be]** ✅ 2026-09-27 (일 기준 통일) — 전략 경로도 `Win_Rate`(상승일 비율)·`Profit_Factor`(일간 이익 합/손실 합)·변동성·상승/하락일·연속일(0 하드코딩이었음)을 buy&hold와 같은 계산에서 가져온다. `Profit_Factor`는 손실일이 없으면 폴백 상수 대신 null. 거래 기준 승률은 `Trade_Win_Rate`로 분리하면서 투자금 비중 대신 거래 수로 가중(현금 비중만큼 깎이던 문제 수정). FE는 null을 "—"/N/A로 표시.
- [x] **A-11 [db]** ✅ 2026-09-27 — 빈 DB 두 개 실측에서 인덱스·제약은 같고 COMMENT만 달랐다. initdb 쪽은 컬럼 COMMENT 24개가 없었고, 있던 한글 COMMENT 8개는 **공식 이미지 initdb 클라이언트의 연결 문자셋(latin1) 때문에 이중 인코딩**돼 있었다. schema.sql에 Alembic과 같은 COMMENT 절 + `SET NAMES utf8mb4`, 새 리비전 `1f574a9ba22e`(stock_id COMMENT '(Foreign Key)' → '논리 참조 (물리 FK 없음)', INSTANT). 검사 스크립트 `scripts/check-schema-parity.sh`(바인드 마운트·호스트 포트 없이 동작, 차이 있으면 exit 1). 가이드 `database/README.md`.
- [x] **(저장소 밖) MySQL 8.0 → 8.4 실기동** ✅ 2026-09-27 (로컬 재현) — 8.0.46 볼륨(FK 있는 이전 스키마)으로 8.4.11 기동 시 DD 80023→80300, 서버 80046→80411 자동 업그레이드, 데이터·제약 보존, 이어 `stamp d5c3763b29e6` → `upgrade head`로 FK 제거까지 확인. `caching_sha2_password` 계정은 영향 없고 `mysql_native_password` 계정은 1524로 로그인 실패. 8.4 볼륨으로 8.0 기동은 거부 → 업그레이드 전 덤프 필수. 운영 확인은 TODO 저장소 밖 3.

### P2 — 테스트 / 제품 확인 / 지표 품질

- [x] **A-12 [fe]** ✅ 2026-09-27 — 결과 화면 조합 컴포넌트(BacktestResults·StatsSummary·TradesChart·PortfolioTable·RebalanceHistoryTable·WeightHistoryChart·ChartsSection 하위·reportGenerator)와 PortfolioPage(실제 useBacktest + MSW)를 정상/부분/빈 데이터/warnings 배너/API 오류 시나리오로 RTL 고정. 테스트 중 **주식+현금 리밸런싱 결과의 CSV 다운로드가 TypeError로 실패하던 버그**(현금 조정 거래에 `shares` 없음)를 찾아 수정.
- [x] **A-17 [be/fe]** ✅ 2026-09-27 (30일 유지) — README·OpenAPI에 하한과 근거 명시, FE `VALIDATION_RULES.MIN_BACKTEST_PERIOD_DAYS` + 제출 전 검증(BE와 같은 셈법·문구). 30일 미만은 서버 422 전에 FE에서 안내.
- [x] **A-18 [be/infra]** ✅ 2026-09-27 — first-N-seen 대신 허용 목록 102개 + 빈도 기반 승격(보장 횟수 3 이상, 워커당 동적 30개, 회수 없음 — multiprocess 모드는 라벨 삭제 미지원). 17 workers 상한 3401 → 613. 시뮬레이션 `other` 96.9% → 26.4%, 인기 티커 라벨 0/26 → 26/26.

### P3 — 정리 / 문서 / 구조

- [x] **A-13 [be]** ✅ 2026-09-27 — 호출부 없는 `BacktestEngine._create_fallback_result`·`ValidationService.create_fallback_stats`와 그 전용 테스트 8건 삭제. `app/validators/`는 살아 있는 경로라 유지.
- [x] **A-14 [docs]** ✅ 2026-09-27 — 테스트 개수 고정값을 AGENTS.md `Current baseline` 참조로, README MySQL 8.4, Jenkinsfile 서술을 home-server 중앙 Jenkinsfile·`Pre-deploy Tests` 기준으로, 낡은 DB 풀 주석과 FE README lint 상한(3 → 0) 정정.
- [x] **A-15 [docs]** ✅ 2026-09-27 — `docs/improvement_analysis.md` 상단에 과거 분석 표기, stock_news FK 권고에 "채택하지 않음 + 사유", Jenkinsfile·풀 권고에 반영 현황.
- [x] **A-16 [be/fe]** ✅ 2026-09-27 — FE: 특성화 테스트 28개로 동작을 먼저 고정한 뒤 `dataSampling.ts`(736줄)를 `dataSampling/` 디렉터리 5개 모듈 + 공개 `index.ts`로, `useChartData.ts`(510줄)를 훅 267줄 + `chartDataSelectors`·`chartSeriesBuilders`로 나눴다. 네 곳에 복제돼 있던 수익률 버킷 재구성을 `alignToReturnBuckets` 하나로. 특성화 테스트가 고정한 애매한 동작 2개는 TODO A-30. BE: 응답 스냅샷 특성화 테스트(두 경로 7개 시나리오, 키 순서까지)와 yfinance 특성화 테스트를 먼저 추가한 뒤, `portfolio_manager_service.py`(1,044줄)를 흐름 조율만 남기고(365줄) `portfolio_inputs`(입력 변환) / `portfolio_execution`(실행) / `portfolio_statistics_builder`(통계 조립) / `portfolio_response_builder`(응답 구성)로 나눴다. weight→금액 환산 중복은 `weight_to_amount` 하나로. `portfolio_simulation_engine.py`(684→547줄)에서 가격·환율·거래 가능 마스크 사전 정렬을 `portfolio_price_alignment`로, `yfinance_repository.py`(769→511줄)에서 티커 메타데이터·뉴스 캐시를 믹스인으로 뺐다. 기존 공개 이름과 테스트 patch 경로는 그대로 동작하고, 분리 전후 응답은 스냅샷 시나리오에서 바이트까지 같았다. 두 경로가 실제로 다른 규칙(금액/비중 모드 판정, 같은 이름 현금 키, 실패 종목 분모)은 합치지 않고 TODO A-33~A-35로 남겼다.

### 배치9 중 새로 발견해 고친 것

- [x] **리포트 개별 종목 수익률 100배 표기** ✅ 2026-09-27 — BE `individual_returns.return`은 이미 백분율인데 리포트가 다시 ×100(8% → 800%). 테스트 픽스처도 0.08로 버그를 고정하고 있었다. 전략 경로는 `start_price`/`end_price`가 없어 리포트 다운로드가 TypeError로 실패하던 것도 수정.
- [x] **null `Profit_Factor`에서 리포트 다운로드 실패** ✅ 2026-09-27 — A-09로 null이 가능해지면서 `.toFixed()`가 TypeError. N/A로 표기.
- [x] **실패 시 이전 결과 잔존 / 오류 닫기가 결과까지 삭제** ✅ 2026-09-27 — 새 실행이 실패하면 결과를 지우고(요청 식별 표시가 없어 "이전 결과" 라벨보다 혼동이 적다), Alert 닫기는 오류만 지우는 `clearError`로 분리.
- [x] **응답 타입 최상위 필드 정리** ✅ 2026-09-27 — BE가 보내지 않는 최상위 `warnings`/`message`/`backtest_type`을 타입에서 삭제, `warnings`는 `data`에 선언.
- [x] **골든 마스터 e2e 복구** ✅ 2026-09-27 — 최소 기간 30일 이후 422로 실패하던 것을 58일 구간으로 늘리고 기대 출력 재생성(차이는 A-03 warnings 키, A-20 부동소수점, A-19 Annual_Return·Sharpe, 납입일 수수료 귀속으로 설명됨).
- [x] **DCA 납입일 수수료 귀속** ✅ 2026-09-27 — `(V−P−F)/P`가 새 납입금의 매수 수수료를 기존 자본 P만으로 나눠, 첫 매수가 늦어진 10+990 포트폴리오에서 가격 불변인데 하루 −19.84%, 연환산 −20.2%였다. 유입 시점 재평가 TWR `(V_pre/P)·(V/(V_pre+F)) − 1`로 교체. `P+F` 분모는 종가 체결 모델에서 납입일 시장 수익률을 희석해 불채택. 일시금·수수료 0 DCA 불변식 유지.
- [x] **A-09 잔여 조작값** ✅ 2026-09-27 — 단일 종목 `profit_factor`가 NaN이면 0.0이던 것을 None으로, 종목별 `win_rate`(buy&hold 100/0 지어낸 값)를 None으로. 나머지 폴백은 TODO A-21·A-22.
- [x] **동시 실행 게이지** ✅ 2026-09-27 — `backtest_jobs_running`/`backtest_jobs_waiting`(livesum). uvicorn에는 죽은 워커 정리 훅이 없어 모듈 임포트 시 죽은 pid와 자기 pid의 live 게이지 파일을 정리.

### ⚠️ 이번 작업으로 바뀐 사용자 노출 동작

- 동시 실행 초과 응답: 같은 IP 동시 3건째는 즉시 **429**(Retry-After 10), 슬롯 대기 30초 초과는 **503**, 실행 60초 초과는 **504**. 60초는 이제 실행 시간만 센다.
- DCA 결과의 `Annual_Return`·`Sharpe_Ratio`가 시간가중 기준으로 바뀐다(일시금·전략 경로는 불변). 수수료가 있는 DCA는 납입일 수익률·MDD도 바뀐다(손실이 작아지는 방향).
- 전략 경로 `Win_Rate`가 거래 기준에서 일 기준으로 바뀌고 거래 기준은 `Trade_Win_Rate`로 분리. `Profit_Factor`는 null일 수 있다.
- 새 엔드포인트 `GET /health/ready`, 새 요청 필드 `include_*` 5개(기본 True), 새 응답 필드 `data.supplemental_status`.
- FE: 30일 미만 기간은 제출 전 오류, 실패 시 이전 결과 숨김, 부가 데이터 실패 안내.

---

## 2026-09-27 운영 반영

> 배치7·배치8·LF 정규화를 묶은 main `cb74a50`(PR #59)을 운영에 배포하고, 배치8의
> 운영 DB 마이그레이션을 적용했다. TODO.md 「저장소 밖 운영 후속 작업」 중 완료된
> 1건을 여기로 옮긴다. 나머지 3건(배포 태그, MySQL 8.4 실기동, 부하 튜닝)은 아직
> 끝나지 않아 TODO.md에 남아 있다.

- [x] **`schema.sql`로 생성된 기존 운영 DB에 Alembic baseline 적용 + FK 제거 리비전 반영** ✅ 2026-09-27
  - 운영 DB 조회 결과: Alembic 리비전 `7b2e9c4f1a30`(head), 물리 FK 0개, `daily_prices` 고아 행 0건
  - 적용 순서는 배치8의 "배포 주의"대로 `stamp d5c3763b29e6` → `upgrade head`다. `stamp head`를 쓰면 FK가 남은 DB가 "제거됨"으로 기록된다
  - 이 DB는 이제 Alembic 관리 하에 있으므로, 다음 스키마 변경부터는 `alembic upgrade head`만 실행하면 된다. 다만 파이프라인과 운영 이미지에 Alembic이 없어 여전히 수동 실행이다
- [x] **main `cb74a50` 운영 배포** ✅ 2026-09-27
  - Jenkins `backtest-be` #27, `backtest-fe` #3 성공 (`APP_ENV=prod`)
  - 배포 스크립트가 `latest` 태그를 쓰므로 헬스체크만으로는 새 이미지인지 알 수 없다. 운영 API에 전략+DCA 요청을 보내 배치7의 422 응답과 메시지를 받는 것으로 새 코드 가동을 확인했다
  - 앞선 `backtest-be` #26은 코드 문제가 아니라 Jenkins 컨테이너의 Docker 소켓 연결 문제로 빌드 전에 실패했다(home-server 쪽 사안, Jenkins 컨테이너 재생성으로 복구)

---

## 2026-09-26 라운드 (배치8 — 물리 FK 제거)

> 정책 결정: 모든 테이블 간 참조를 논리 참조로 두고 물리 FK는 쓰지 않는다.
> 저장소와 dev DB를 전수 조사한 결과 물리 FK는 `daily_prices_ibfk_1` 하나였다
> (`stock_news`는 원래 FK 없음, ORM relationship 0건).

- [x] **A-10 [db]** ✅ 2026-09-26 (선택지 2: 물리 FK 제거) — `daily_prices.stock_id → stocks.id ON DELETE CASCADE` 제거.
  - `database/schema.sql`: FOREIGN KEY 줄 삭제, 논리 참조와 무결성 책임(저장 트랜잭션 순서, 명시적 삭제, 고아 점검)을 주석으로 명시
  - Alembic `7b2e9c4f1a30`(down `d5c3763b29e6`): 초기 리비전은 수정하지 않고 새 리비전 추가. FK 이름은 `information_schema`에서 찾아 지운다(운영 DB의 자동 명명이 달라도 동작, FK가 이미 없으면 no-op). downgrade는 같은 CASCADE FK를 복원
  - `(stock_id, date)` PK 유지 — stock_id 조회 인덱스를 이미 제공하므로 인덱스 변경 없음
  - `scripts/check_orphan_prices.py`: 고아 일봉 점검(기본, 발견 시 종료 코드 1) / `--delete`로 정리
  - 실측 검증(mysql:8.4):
    - dev DB(FK·데이터 있음): `stamp d5c3763b29e6` → `upgrade head`(FK 0개) → `downgrade -1`(CASCADE FK 복원) → `upgrade head`, 행 수 불변(stocks 6 / daily_prices 4,815)
    - 빈 DB 두 개: schema.sql initdb 경로와 `alembic upgrade head` 경로 모두 FK 0개, COMMENT 절을 뺀 `SHOW CREATE TABLE` 3개 동일(컬럼 COMMENT 유무 차이는 기존부터 있던 것 — A-11)
    - FK 제거 후 신규 종목 저장(NVDA·GOOGL 각 502행) 정상, 고아 0
    - 고아 행 2개 주입 → 점검 exit 1 → `--delete` 2행 삭제 → 재점검 exit 0
  - **배포 주의**: schema.sql로 만든 기존 운영 DB는 `alembic stamp head`가 아니라 `stamp d5c3763b29e6` → `upgrade head`로 적용해야 FK가 실제로 지워진다(TODO.md "저장소 밖 운영 후속 작업"). → 2026-09-27 운영 적용 완료(위 운영 반영 섹션).

---

## 2026-09-26 라운드 (배치7)

> TODO.md의 권장 순서 1·2번(A-01~A-03)과, 재감사 중 새로 찾은 DCA 낙폭 버그를
> 처리했다. 수정 전 상태를 Docker dev 스택 + 실데이터(yfinance) 요청으로 먼저
> 재현하고, 각 버그는 수정 전 코드에서 실패하는 테스트로 고정했다
> (`tests/unit/test_audit_batch7_fixes.py` — 수정 전 6건 실패, 수정 후 12건 통과).

### 검증 기준선 (2026-09-26 실측)

- [x] BE 단위 테스트 **370개** 통과 (358 → 370), Docker `--target test` 통과
- [x] FE 테스트 **188개** 통과 (179 → 188), ESLint 경고 0 · type-check(prod·test) · 프로덕션 빌드 통과
- [x] 의존성 감사: FE **예외 없이** 통과, BE 기존 bokeh 예외만으로 통과
- [x] dev 스택(compose.dev.yaml) 기동 + FE 프록시 경유 실데이터 스모크 6종(일시금·DCA+리밸런싱·SMA·한국 종목 등) 정상

### P0

- [x] **A-01 [fe/infra]** ✅ 2026-09-26 (`npm update js-yaml nanoid browserslist fast-uri`, BE `tornado` 6.5.7→6.5.8) — 배포 전 검사 단계 복구. TODO 작성(08-08) 이후 권고가 늘어 **FE high 4건**(js-yaml·nanoid에 browserslist·fast-uri 추가), **BE도 tornado 3건**(PYSEC-2026-3928 등, bokeh 전이 의존성)으로 FE·BE 의존성 감사가 모두 배포를 막고 있었다. `npm audit fix`는 npm 10.9 내부 오류(`Cannot read properties of null (reading 'edgesOut')`)로 중단되므로 대상 패키지를 직접 `npm update`했다. 이때 lock 파일에 남아 있던 `patch-package` 트리(package.json에서는 이미 제거된 잔재)가 함께 정리됐다. react-router 예외(`GHSA-qwww-vcr4-c8h2`)는 7.18.2가 더 이상 범위로 보고되지 않아 제거 — 예외 목록을 비운 상태로 FE audit 통과 확인.

### P1 — 사용자에게 틀린 숫자

- [x] **A-02 [be/fe]** ✅ 2026-09-26 (스키마 422 + FE 검증·전송값 정리) — 기술적 전략 + DCA/리밸런싱 조합이 조용히 일시금·무리밸런싱으로 실행되던 문제. `PortfolioBacktestRequest.validate_strategy_supports_dca_and_rebalancing`이 DCA 종목 또는 **명시적으로 보낸** `rebalance_frequency != 'none'`을 거부한다(기본값 `monthly_1` 때문에 필드를 생략한 기존 호출은 막지 않도록 `model_fields_set`만 검사). FE는 `supportsDcaAndRebalancing`/`resolveRebalanceFrequency`(`model/constants/rebalancing.ts`)로 판단을 한곳에 모았다 — 드롭다운은 `none`으로 보이는데 state의 `monthly_3`이 그대로 전송되던 불일치도 이것으로 해소. 기술적 전략 + DCA는 제출 전 검증 오류로 안내한다.
- [x] **A-03 [be]** ✅ 2026-09-26 — 로드 실패 종목의 금액이 분모에 남아 수익률이 과소보고되던 문제(실데이터 재현: AAPL + 없는 종목 반반 → 0.96%, 경고 없음). 로드 후 가격 데이터가 없는 주식 항목을 `amounts`/`dca_info`에서 제외하고 `warnings`에 사유와 제외 금액을 싣는다. buy&hold 응답(현금 전용 결과 포함)에도 `warnings` 키가 항상 있어 전략 경로와 계약이 같아졌다.
- [x] **A-20 [be]** ✅ 2026-09-26 (재감사 신규 발견) — **DCA의 MDD가 납입금에 가려 축소 보고됨.** 두 통계 구현(`PortfolioCalculator`, `PortfolioMetrics`)이 낙폭을 `Portfolio_Value`(평가금)로 쟀는데, DCA는 납입금이 평가금을 계속 신고점으로 밀어 올린다. 재현: 2년간 100→60(-40%) 꾸준히 하락하는 종목에 월 적립 → 총수익률 -24%인데 **MDD -2.85%**. 이미 납입금을 제외해 계산되는 `Daily_Return`의 누적곱(시간가중 지수)으로 낙폭을 재도록 `metrics_math.drawdown_from_returns`로 통합했다. 납입이 없으면 지수가 평가금과 비례하므로 일시금·전략 경로 결과는 불변(기존 테스트 전부 통과). 누적곱의 부동소수점 오차(완전 회복일이 0.9999…)가 가짜 낙폭일을 만들어 `Avg_Drawdown`을 반토막 내는 문제가 있어 `DRAWDOWN_EPSILON`으로 0 처리한다.

### ⚠️ 이번 작업으로 바뀐 사용자 노출 동작

- 기술적 전략(SMA·RSI·MACD·EMA·Bollinger)에 DCA 종목이나 명시적 리밸런싱 주기를 보내면 이제 **422**다. 이전에는 200으로 통과했지만 그 설정은 한 번도 적용된 적이 없다.
- 데이터를 못 불러온 종목은 결과(`portfolio_composition` 포함)에서 빠지고 경고 배너로 안내된다. 수익률은 나머지 종목 기준으로 바뀐다.
- DCA 포트폴리오의 MDD·평균 낙폭이 커진다(정확해진다). 일시금은 변화 없음.

---

## 2026-08-02 라운드

> 2026-08-02. 두 독립 분석의 통합본:
> - **Claude**: 5영역(BE 로직 / FE / 테스트 / 인프라·CI·DB / 문서) 병렬 감사 — 전 항목 `파일:라인` 근거, P1 전체·주요 P2는 코드 스팟체크로 재확인
> - **Codex**: P0~P3 작업 계획 — 재현 사례·완료 조건 중심
>
> 표기: 〔교차〕 = 두 분석이 독립적으로 동일 결론(확신도 최상). 〔Codex〕 = Codex 단독 발견(검증 상태 병기). 무표기 = Claude 단독 발견(검증 완료).
>
> 아래에서 `[ ]`로 남은 소수 항목은 **이 라운드에서 끝나지 않아 TODO.md로 이관한
> 것**이다. 추적을 위해 지우지 않고 이관처를 표기해 둔다.

### 검증 기준선

**분석 시점 (2026-08-02 오전)**
- BE 단위 테스트 141개 / FE 단위 테스트 113개 통과, FE 타입 검사·프로덕션 빌드·`pip check` 통과
- ESLint 경고 정확히 3개(허용 한도 `--max-warnings 3`과 동일 — 사실상 예산 소진)

**전체 배치 완료 후 (2026-08-03, 실측)**
- [x] BE 단위 테스트 **358개** + 통합 **12개** 통과 (분석 시점 141 → 358)
- [x] FE 단위 테스트 **179개** 통과
- [x] ESLint **경고 0개**, 예산 `--max-warnings 0` / 타입 검사(prod·test) 통과
- [x] CI 배포 전 테스트 단계 양쪽 재현 통과 (`docker build --target test`: BE 358 / FE 179)
- [x] E2E **1개** (Playwright config + 스모크 spec, dev 스택 대상 실제 통과 확인)
- [x] 커버리지 재측정 (2026-08-03): **BE 71.55%** (분석 시점 ~42%), 핵심 금융 모듈은 82~98% — `portfolio_metrics` 98.6%, `portfolio_rebalancer` 95.0%, `portfolio_calculator_service` 97.0%, `portfolio_simulation_engine` 82.7%. **FE 구문 47.79% / 라인 48.9%** (분석 시점 21.8% / 22.62%). 남은 저커버리지: `data_fetcher` 41%, validators 23~32%(죽은 코드가 아니라 `backtest_engine.py:45`를 통해 살아 있는 경로 — 커버리지 공백), `currency_converter` 57%

---

### P1 — 즉시 (정확성·안전에 직접 영향)

#### 보안

- [x] **P1-01 [fe]** ✅ 2026-08-02 수정 (`dangerouslySetInnerHTML` 2곳 → 엔티티 디코드 후 JSX 텍스트 렌더. 파서 기반 디코드는 의도적으로 배제 — happy-dom 실측에서 `<img …>` 구간 텍스트가 통째로 사라짐. 정규식 디코더에 `0x10FFFF` 상한 가드 포함(리뷰에서 `String.fromCodePoint` RangeError 렌더 크래시 발견 → RED 재현 후 수정). 같은 패턴 보유한 죽은 `NewsModal.tsx`·`UnifiedInfoSection.tsx`+테스트 삭제. 회귀 테스트 5개) **잔여**: BE `news_service.py:37`의 우회 가능한 `<.*?>` 정규식은 그대로 — FE가 이제 텍스트로만 렌더하므로 XSS는 차단됐지만, 서버측 정화를 제대로 고치는 것은 별도 항목(P2-44)) — 뉴스 렌더링 XSS 표면 제거 — 외부(네이버 API) 뉴스 제목/본문을 `dangerouslySetInnerHTML`로 주입(`LatestNewsSection.tsx:98,102`, 직접 확인 — `SupplementaryCharts.tsx:169`에서 실제 렌더)하는데 유일한 방어가 BE의 우회 가능한 정규식 `re.compile('<.*?>')`(`news_service.py:37`). 닫는 `>` 없는 페이로드(`<img src=x onerror=...`)는 통과하고 innerHTML 파서가 자동 완성해 실행. 같은 패턴의 죽은 컴포넌트 `NewsModal.tsx:63,67`·`UnifiedInfoSection.tsx:162,166`도 존재. 조치: 텍스트 렌더 + HTML 엔티티 디코드로 전환(또는 DOMPurify), 죽은 중복 2개 삭제.

#### BE 금융 로직 정확성 (사용자에게 틀린 숫자가 서빙되는 버그 — 전부 코드로 확인됨)

- [x] **P1-02 [be]** ✅ 2026-08-02 수정 — SMA 전략 파라미터가 조용히 무시됨 — 공개 파라미터명 `short_window`/`long_window`(`strategy_service.py:30,37`) vs 클래스 속성 `sma_short`/`sma_long`(`strategies.py:63-64`). `backtest_engine.py:183-190`의 `hasattr` 필터에서 전부 탈락 → **어떤 입력이든 SMA는 기본값 10/20으로 실행**. 단위 테스트는 검증기를 identity mock해서 못 잡음(`test_backtest_engine.py:220`). 조치: 속성명 통일(전 전략 전수 점검) + mock 없는 회귀 테스트.
  - **결과**: 전 6개 전략 전수 점검 결과 불일치는 SMA 단독(나머지는 RED 단계에서 이미 통과해 무결 입증). `SmaCrossStrategy.sma_short/sma_long` → `short_window/long_window` 리네임, `init()` 사용처 갱신, 이를 직접 구동하던 `test_sma_strategy.py`의 하드코딩 인자 갱신. 신규 `tests/unit/test_strategy_param_override.py` 5개 — 실제 `StrategyService.validate_strategy_params`를 mock 없이 통과시키는 회귀망.
- [x] **P1-03 [be]** ✅ 2026-08-02 수정 (`total_amount = sum(amounts.values())`; 회귀 테스트 2개 — 비중 합 95에서 평평한 시장 수익률 −5.0%→0.0% 확인) — weight 모드 전략 포트폴리오 수익률 ±5%p 왜곡 — `total_amount = 100.0` 하드코딩(`portfolio_manager_service.py:294-295`)인데 실투자금은 weight 합(스키마 95~105 허용) → weight 합 95면 평평한 가격에서 −5% 보고(`:408`). 조치: `total_amount = sum(amounts.values())`.
- [x] **P1-04 [be]** ✅ 2026-08-02 수정 (전략 경로와 동일하게 비중을 금액으로 환산 — `ZeroDivisionError` 재현 후 수정, DCA+weight 조합 포함 테스트) 〔교차〕 buy&hold 경로 weight 모드 미구현 → ZeroDivisionError가 200으로 — `per_period_amount = 0`("나중에 처리" 주석뿐, `portfolio_manager_service.py:572-574`) → `portfolio_metrics.py:83`에서 0 나눗셈. Codex 재현: `weight=100` 정상 요청이 `float division by zero` 실패(FE는 비중을 금액으로 환산해 보내므로 공개 API 결함이 가려져 있음). 조치(계약 확정): weight 지원 시 총투자금 필수 필드 추가 + 서버 환산, 미지원 시 스키마에서 제거. 어느 쪽이든 0 나눗셈은 422로 사전 차단.
- [x] **P1-05 [be]** ✅ 2026-08-02 수정 (`commission=request.commission` 전달; 회귀 테스트 2개 — 0.03 요청이 0.002로 바뀌던 것 확인 후 수정) 〔교차〕 전략 포트폴리오에서 사용자 수수료 무시 — 종목별 `BacktestRequest` 생성 시 `commission` 미전달(`portfolio_manager_service.py:354-361`) → 스키마 기본 0.002 적용. Codex 재현: 수수료 3% 요청이 내부 실행에서 0.2%로 바뀜. 조치: `commission=request.commission` 전달 + 회귀 테스트(P2-36).
- [x] **P1-06 [be]** ✅ 2026-08-02 수정 (거래가능 풀 = TPV − 상장폐지 가치. 측정된 왜곡: 2종목·수수료0에서 총액 $200→$300(+50%), 3종목·수수료2%에서 수수료가 $0.10 대신 $1.10(11배). "리밸런싱 전후 총액 = 수수료만큼만 감소" 불변식 테스트 5개. 후속: P3-27) — 상장폐지 종목 보유 시 리밸런싱마다 유령 자산 생성 — 조정 타깃 비중은 거래가능 종목 합 1.0으로 재정규화되고 각자 `TPV × target_weight` 배정(`portfolio_rebalancer.py:167`), 상장폐지 종목은 주식 수 유지(`:197-198,213`)하면서 그 가치가 TPV에도 포함(`portfolio_simulation_engine.py:131-134`의 마지막 유효가 주입) → 리밸런싱 직후 총액 = TPV + 상장폐지분(중복 계상). 조치: 거래가능 자산에는 `(TPV − 상장폐지 가치)`만 배분. 구조적 해법은 P2-14 참조.
- [x] **P1-07 [be]** ✅ 2026-08-02 수정 (`generate_periodic_schedule`로 시뮬레이션과 동일한 Nth-weekday 예정일을 생성해 `dca_periods = 1 + 예정일 수`로 산출, 초회 매수를 `executed_count`에 계상. 완료 기준 충족: 고정가·수수료0 DCA 총수익률 0.0% — 수정 전 월간 −7.69%, 분기 −20%. 테스트 14개) 〔교차〕 DCA 계획 회차 vs 실행 회차 불일치 → 미집행 투자금이 손실처럼 증발 — 분모는 30일 근사 계획 총액(`portfolio_manager_service.py:551-563`), 실제 매수는 Nth-weekday 달력 + 가격 없으면 스킵(초회 매수 미카운트, `portfolio_dca_manager.py:149-177`). Codex 재현: 2024년 전체·월 $1,000·고정 주가 $100·수수료 0에서 실제 12회 매수인데 분모 $13,000 → 총수익률 −7.69%. FE도 30일 근사를 별도 계산(`calculateDcaPeriods.ts`)해 BE와 어긋날 수 있음. 조치: 실제 스케줄 생성기를 단일 소스로, 미집행 회차는 현금 계상, 납입 누계/평가금 시계열 분리(시간가중수익률 검토), FE 표시값 동기화. **완료 조건: 고정 주가·수수료 0 DCA의 총수익률 = 0%.**
- [x] **P1-08 [be]** ✅ 2026-08-02 수정 (`PortfolioState.pending_initial_keys`로 초기 매수 대상을 추적해 각 종목이 처음 가격을 갖는 날 매수. 수정 전 2종목 중 1종목 누락 시 −50% 보고) — 시뮬레이션 첫날 가격 없는 자산은 영원히 미매수 → 자본 증발 — `execute_initial_purchases`가 스킵 후 재시도 없음(`portfolio_dca_manager.py:55-58`; `is_first_day` 1회성, `portfolio_simulation_engine.py:353-366`; 선두 ffill 불가). 혼합 KR/US 포트폴리오에서 한쪽 휴장일 시작이면 재현(예: 2024-07-04). 조치: 첫 가격 등장일에 초기 매수 재시도.
- [x] **P1-09 [be/fe]** ✅ 2026-08-02 수정 (catch-all 3곳 → 로깅 후 재-raise, 엔드포인트 통과 분기 제거. 검증: 일반 예외→500이며 유출 문자열 부재·불투명 에러 ID 존재, ValidationError→422, DataNotFoundError→404, 성공 형태 불변. 잘못된 계약을 고정하던 통합 테스트 1건도 422 기대로 수정) 〔교차〕 모든 포트폴리오 실패가 HTTP 200 + 원시 예외 문자열 — 매니저 catch-all(`portfolio_manager_service.py:265-271,497-506,913-922`)을 엔드포인트가 그대로 통과(`backtest.py:78-79`) → `@handle_portfolio_errors`의 4xx/5xx 매핑·에러 ID 체계 무력화, 내부 문자열 노출. FE는 이 오류 payload를 성공 결과처럼 저장할 수 있음(Codex). 조치: 매니저 재-raise → 데코레이터 매핑, 성공/오류 응답 타입 분리, FE에서 오류 payload 저장 차단. **완료 조건: 실패 응답이 200으로 반환되지 않는다.**
- [x] **P1-10 [be]** ✅ 2026-08-02 수정 (종목별 마지막 관측값 추적으로 진짜 forward fill. 스파이크 아티팩트 +36%→−26% 반전 제거 확인. 라이브 코드임을 호출 경로로 검증 — `portfolio_manager_service.py:422`→통계 산출) — 전략 포트폴리오 equity curve 중간 갭을 '직전 값'이 아닌 '최종 값'으로 채움 — 주석은 forward fill, 실제는 `result.get('final_value', ...)`(`portfolio_calculator_service.py:177-179`) → 혼합 시장 휴일에 기말 가치 스파이크 주입, 파생 통계(`Annual_Volatility`/`Profit_Factor`/`Positive_Days`) 오염. 조치: 직전일 값 carry.

#### 배포·테스트 신뢰성

- [x] **P1-11 [infra]** ✅ 2026-08-02 수정 (10회 실패 시 `exit 1`로 파이프라인 실패. 롤백·readiness 분리는 미착수 — 별도 항목으로 남김) 〔교차〕 Jenkins `Health Check` 스테이지가 실패할 수 없는 구조 — 10회 실패해도 echo 후 exit 0(`Jenkinsfile:110-130`) → 배포 실패가 초록불. 조치: 루프 소진 시 `exit 1`, 직전 `${BUILD_NUMBER}` 태그 롤백(이미지는 이미 태그별 푸시됨), liveness/readiness 분리 검토(Codex).
- [x] **P1-12 [test]** ✅ 2026-08-03 (portfolio_metrics 22 + daily 7, 시뮬레이션 엣지 7, DCA 매니저 7, dca_calculator 5, fallback 3 — 손으로 도출한 기댓값으로 검증. 작성 중 프로덕션 버그 6건 발견 → P1-16~18로 수정) — 〔교차〕 포트폴리오 시뮬레이션 스택(~1,300줄) 단위 테스트 신설 — 어떤 테스트도 임포트하지 않음: `portfolio_simulation_engine.py`(492줄), `portfolio_rebalancer.py`(309), `portfolio_dca_manager.py`(179), `portfolio_metrics.py`(198), `dca_calculator.py`, `portfolio_calculator_service.py`. **바로 이 모듈들에서 P1-03~P1-10이 확인됨 — 버그 수정의 회귀망으로 최우선.** 소형 결정적 가격 DataFrame으로 DCA 수량·리밸런스 거래·지표 검증부터.
- [x] **P1-13 [test]** ✅ 2026-08-03 (상태 문자열 비교 → `data` 재귀 깊은 비교, 기대 파일 부재 시 자동 생성 대신 실패. 재생성은 `REGENERATE_GOLDEN_MASTER=1` 명시 필요) — "골든 마스터"가 상태 문자열만 비교 — 유일한 실질 단언이 `assert result['status'] == expected['status']`(`tests/e2e/test_golden_master.py:117-127`, 직접 확인), 기대 파일 부재 시 현재 출력으로 자동 생성. 조치: `result['data']`를 수치 허용오차로 비교, 부재 시 생성 대신 실패. (P1 금융 버그 수정 후 골든 파일 재생성 필요 — 수정과 순서 조율)
- [x] **P1-14 [test/fe]** ✅ 2026-08-02 수정 (사본 테스트·죽은 모듈·barrel 참조 일괄 삭제 — 저장소 유일 FSD 위반도 함께 해소) `chartUtils.test.ts`(22개, FE 스위트의 19%)가 파일 내 복사본을 테스트 — vitest 외 임포트 없음(`src/lib/__tests__/chartUtils.test.ts:10-15`). 대응 "실제" 모듈 `shared/lib/utils/chartUtils.ts`(332줄)도 임포터 0의 죽은 파일 + 저장소 유일의 FSD 위반(`shared`→`features` 임포트, `:5`). 조치: 사본 테스트·죽은 모듈·barrel 참조 일괄 삭제, 테스트 투자는 살아 있는 파이프라인(P2-35)으로. (삭제 시 FE 기준선 113 → 91로 갱신: CLAUDE.md 반영)

---

### P2 — 권장 (견고성·보안·재현성)

#### 백엔드

- [x] **P2-01 [be]** ✅ 2026-08-02 수정 (asyncio.to_thread 오프로드 — 검증: 시뮬레이션 도중 다른 코루틴 0회 스케줄되던 것 해소) — CPU-bound 시뮬레이션이 이벤트 루프 점유 — `async def execute_simulation`에 await 0개, 10년×N종목 pandas 루프가 루프 스레드에서 실행(`portfolio_simulation_engine.py:256-492`; `_calculate_realistic_equity_curve` 동일). 조치: `asyncio.to_thread` 오프로드.
- [x] **P2-02 [be]** ✅ 2026-08-02 수정 (환율 실패 시 예외 발생 — KRW 50,500 단위가 USD로 취급되던 폴백 제거, 이를 고정하던 기존 테스트 2개 교체) — 환율 로드 실패 시 무변환 가격이 조용히 USD 계산에 유입 — `except: return data`(`currency_converter.py:234-236`; `portfolio_simulation_engine.py:209-215` 동일). KRW 70,000원대 가격이 USD initial_cash와 섞여 성공으로 반환. 테스트가 이 동작을 고정 중(`test_currency_converter.py:151-168`). 조치(제품 결정): 변환 필수 시 실패 처리, 최소한 응답 warning.
- [x] **P2-03 [be]** ✅ 2026-08-02 수정 (기본값 `buy_hold_strategy` + StrategyType 멤버십 `field_validator` 추가 — 이제 임의 문자열도 422로 거부. 테스트 3개) 〔교차〕 스키마 기본 전략값이 무효한 `"buy_and_hold"` — `schemas.py:150`(직접 확인). 전략 생략 시 `!= "buy_hold_strategy"` 분기로 전략 경로 → 종목별 enum 검증 전멸 → "모든 종목 실패" 200 에러. 조치: `StrategyType` enum + 기본 `buy_hold_strategy`.
- [x] **P2-04 [be]** ✅ 2026-08-03 (임포터 0이던 `PortfolioValidator` 삭제, 필드 순서 의존 검증을 model_validator로 전환 — 한글 현금명이 422로 거부되던 죽은 분기 복구. rebalance_frequency 멤버십·미래 종료일·최소 기간 검증 추가) — 〔교차〕 포트폴리오 검증 통합 — `portfolio_validator.py`(233줄) 임포트 0 → 미래 날짜/최소 기간/`rebalance_frequency` 멤버십 검증 부재(자유 문자열, 미지 값은 `rebalance_helper.py:217-220`이 조용히 리밸런싱 비활성화; 미래 end_date는 P1-07 분모 부풀리기로 직결). **+ 현금 이름 필드 검증 순서 버그(직접 확인)**: `symbol`(75행)이 `asset_type`(80행)보다 먼저 검증돼 `info.data`에 asset_type 부재 → 항상 'stock' 폴백 → 현금 유연 분기(`schemas.py:106-110`)는 죽은 코드, 한글 현금 심볼은 422(FE가 'CASH'를 보내 가려짐; endpoint의 `'현금'` 필터와 모순). 조치: enum/Literal화(전략·자산·투자방식·주기), 필드 순서 의존 검증을 model-level validator로, validator 연결 또는 스키마 이동 + 테스트.
- [x] **P2-05 [be]** ✅ 2026-08-02 수정 (검증 실패 시 `ValidationError`로 요청 거부, 오류 메시지에 문제 파라미터 명시. RED로 `rsi_period=0`이 그대로 적용되던 것 확인 후 수정, 테스트 4개) — 파라미터 검증 실패 시 원본 값 강행 — raise 시 경고 후 raw params 적용(`backtest_engine.py:175-181`, 직접 확인) → min/max 캡 우회(`rsi_period: 0` → `ewm(alpha=1/0)` 크래시). 조치: 검증 실패는 요청 거부.
- [ ] **P2-06 [be]** ⏸ 미착수 → **[TODO.md](TODO.md)의 A-03으로 이관** (2026-08-08 통합 시 체크박스 정정: 본문이 "미착수"인데 `[x]`로 표기돼 있었다) — buy&hold 데이터 로드 실패 종목 무경고 드랍 — 자본은 분모 잔류로 수익률 과소보고, 전략 경로와 달리 warnings 필드 없음(`portfolio_data_loader.py:52-59`). 조치: warnings 통일 또는 실패 처리.
- [x] **P2-07 [be]** ✅ 2026-08-02 수정 (현금 항목마다 유니크 키 부여 — 1000+500+300 입력에 Initial_Value 1300·비중 합 1.38이던 것 정정) — 현금 중복 항목 총액/비중 불일치 — 중복 검증 현금 면제(`schemas.py:166`) + `amounts[symbol]` 덮어쓰기·`cash_amount` 누적(`portfolio_manager_service.py:586,602`) → "CASH" 500+300 → 총액 300, 표시 800. 조치: 유니크 키 또는 사전 합산.
- [x] **P2-08 [be]** ✅ 2026-08-02 수정 (`_calculate_true_portfolio_stats`로 통합 equity curve에서 실측 — MDD −20%→실제 −10%, Sharpe 2.0→실제 0.0, Peak_Value·거래일 수 정정) — 전략 포트폴리오 통계가 근사치를 실측처럼 — 상관 무시 가중평균 Sharpe, 개별 MDD 가중평균, `Avg_Drawdown = MDD/2`(창작), `Peak_Value`=최종값, `Trading_Days`=달력일(`portfolio_manager_service.py:432-438`). 조치: 이미 계산되는 통합 equity curve 기반 실측치로.
- [x] **P2-09 [be]** ✅ 2026-08-03 (`asset_type == "cash"` 기준으로 판별 — 커스텀 이름 현금이 티커 조회·yfinance 재시도로 흘러가던 것 차단) — 현금 자산 판별을 심볼 문자열로 — `not in ['CASH', '현금']`(`backtest.py:37-41`, 직접 확인) → 이름이 "예금"류면 티커 조회+yfinance+재시도 유발. 조치: `asset_type == 'cash'` 기준.
- [x] **P2-10 [be]** ✅ 2026-08-02 수정 (트랜잭션 열기 전 fetch 완료 — 가짜 엔진으로 커넥션 개방 중 fetch 여부 직접 검증) — DB 트랜잭션 쥔 채 yfinance 호출 — `engine.begin()`/`connect()` 안에서 외부 fetch(`yfinance_repository.py:61-68,279-289`) → 풀/락 점유. 조치: fetch 후 트랜잭션.
- [x] **P2-11 [be]** ✅ 2026-08-02 수정 (빈 결과는 재시도 없이 즉시 `DataNotFoundError`(404) — 내부 로더 호출 1회·sleep 0회 단언으로 ~6초 지연 제거 검증, 진짜 예외의 백오프 재시도는 유지. 테스트 5개) — 빈 조회 결과 3회 재시도 — 영구 조건을 2s+4s 백오프 후 bare ValueError → 500(`yfinance_repository.py:221-243`; 404가 맞음). 조치: 즉시 `DataNotFoundError`.
- [x] **P2-12 [be]** ✅ 2026-08-02 수정 (가격 이력 1회 로드 공유 + 5개 분기 병렬화, 5종목 기준 2.0초 → 0.35초) — 〔교차〕 `unified_data_service` 순차 + 이중 로드 — docstring "병렬"이지만 순차, 종목당 가격 이력 2회 로드(`unified_data_service.py:4,79-90,155-169`). 조치: gather 병렬화 + 로드 공유, 동일 데이터 동시 요청 single-flight 검토(Codex).
- [x] **P2-13 [be]** ✅ 2026-08-03 (`DcaCalculator`가 `PortfolioDcaManager`에 위임 — 갭+5% 수수료 케이스에서 표시값 +5.0% vs 실제 −0.27%로 부호까지 뒤집혀 있던 것 해소) — 한 응답에 DCA 실행 모델 2개 + DCA×기술전략 계약 부재 — 표시용 `DcaCalculator`(수수료 무시)와 시뮬레이션(스킵+수수료)이 불일치(`dca_calculator.py:73-99` vs `portfolio_dca_manager.py:149-177`). **+ 기술전략 경로는 `investment_type=dca`를 조용히 무시하고 일시금 실행**(종목별 `BacktestRequest`에 DCA 필드 자체가 없음 — 구조 확인, Codex 교차). UI에서 숨긴 옵션의 stale 상태가 payload에 남을 가능성도 점검(Codex, 미검증). 조치: 실행 모델 단일화, 미지원 조합은 422 + UI 차단.
- [x] **P2-14 [be]** ✅ 2026-08-03 (평가용 ffill 가격과 당일 실관측 마스크 분리 — 미관측일 체결·상장폐지 미감지 해소. 56일간 데이터 없는 종목이 `delisted_stocks`에 안 잡히고 정지 가격에 체결되던 것 확인 후 수정) — 〔Codex, 구조 타당성 확인〕 평가 가격과 거래 가능 가격 분리 — 합집합 날짜에 ffill한 가격을 평가·거래·상장폐지 감지에 모두 사용 → 타 시장 휴장일에 stale price로 체결 가능, 상장폐지 감지 왜곡(P1-06/P1-08의 구조적 원인). 조치: 평가용 ffill 가격과 거래가능 마스크 분리, DCA/리밸런싱은 거래가능일에만 체결, 상장폐지는 원본 마지막 관측일 기준. KR/US 혼합·휴장·상장폐지 fixture 필수.
- [x] **P2-15 [be]** ✅ 2026-08-03 (알려진 티커 200개 + `other` 버킷으로 카디널리티 상한, 현금은 메트릭에서 제외) — 〔Codex, 코드 확인〕 Prometheus 라벨에 사용자 입력 ticker 직접 사용 — `TICKER_POPULARITY_TOTAL.labels(ticker=item.symbol).inc()`(`portfolio_manager_service.py:300-301`, 정의 `custom_metrics.py:11`) — 검증 전 시점 + 무한 카디널리티(시계열 폭증). 조치: 화이트리스트/정규화 후 라벨링 또는 라벨 제거.
- [x] **P2-44 [be]** ✅ 2026-08-02 수정 (stdlib HTMLParser로 교체, 의존성 추가 없음) — 뉴스 서버측 정화 정상화 — `news_service.py:35-38`의 `re.compile('<.*?>')`는 닫는 `>`가 없는 태그를 통과시킴. FE가 텍스트 렌더로 바뀌어 XSS는 차단됐지만(P1-01), 서버가 반환하는 데이터 자체는 여전히 마크업 잔재를 포함할 수 있고 다른 소비자(향후 API 클라이언트)에는 방어가 없음. 조치: 정규식 대신 `html.unescape` + `bleach`/`html.parser` 기반 태그 제거로 교체 + 미종료 태그 테스트.
- [x] **P2-16 [be]** ✅ 2026-08-03 (동시 실행 세마포어 + 총 소요시간 상한, 초과 시 504) — 〔Codex, 미검증〕 고비용 요청 한도 부재 — 백테스트 요청 동시 실행 한도·시간 제한·크기 제한 없음. 조치: 한도 도입, 필요 시 작업 큐+상태 조회 전환 검토.

#### 인프라 / CI / DB

- [x] **P2-17 [infra]** ✅ 2026-08-02 수정 (`nginx.prod.conf`·`nginx.conf` 양쪽: location 트레일링 슬래시 제거 + `proxy_pass`에서 URI 제거해 원본 URI 보존, `/api/` 404 location으로 SPA fallback 차단, connect 10s/read 180s 타임아웃. `nginx -t` 문법 검증 통과) 〔교차〕 FE nginx API location trailing slash — `location /api/v1/backtest/`(`nginx.prod.conf:21-22`, 직접 확인)인데 FE는 슬래시 없이 POST(`backtestService.ts:20`) → nginx 301 → 브라우저 POST→GET → 405. 저장소 설정만으로는 프로드 API 호출 불가(실서비스 정상이면 엣지 프록시가 우회 중 — 확인·문서화). + 그 외 `/api/*` 경로는 SPA fallback이 HTML 200으로 삼킴(Codex), 장시간 백테스트용 proxy read timeout 미설정. 조치: `location /api/v1/backtest`(슬래시 제거), `/api/` 전용 location 분리(404 반환), 타임아웃 명시.
- [x] **P2-18 [infra]** ✅ 2026-08-02 수정 (builder/test/runtime 3-스테이지 분리, runtime은 클린 slim + venv COPY만. **2.85GB → 801MB**. 런타임에서 gcc·pytest 부재 실측) 〔교차〕 BE 프로덕션 이미지 다이어트 — base가 `build-essential gcc g++ cargo rustc`(`Dockerfile:10-21`) + `requirements-test.txt`(`:40-42`)까지 설치, runtime이 `FROM base`(`:59`). 조치: builder 스테이지 → `COPY --from`, 테스트 의존성은 test 스테이지로.
- [x] **P2-19 [infra]** ✅ 2026-08-02 수정 (레이어 삭제. `entrypoint.sh`·`Dockerfile.dev`·`scripts/` 전수 확인 결과 uv 사용처 없음) 〔교차〕 빌드 중 `curl | sh`(uv 설치) 제거 — 미검증 원격 스크립트 root 실행, 사용처 없음(`Dockerfile:32-33`).
- [x] **P2-20 [infra]** ✅ 2026-08-02 수정 (전용 시스템 계정 `app`으로 실행 — `whoami` 실측, chmod 777 → 소유권+0755, entrypoint의 chown root 제거) 〔교차〕 BE 컨테이너 non-root 실행 — USER 부재 + `entrypoint.sh:18` chown root 재보장 + `chmod 777`(`Dockerfile:80`). 조치: 전용 유저, 최소 권한.
- [x] **P2-21 [infra]** ✅ 2026-08-02 수정 (양쪽 conf에 `server_tokens off` + X-Content-Type-Options/X-Frame-Options/Referrer-Policy/CSP, `always` 플래그로 404 응답까지 적용 — `/health`·`/`·`/api/*` 실측. CSP `style-src 'unsafe-inline'`은 Radix 스크롤 락의 nonce 없는 `<style>` 주입 때문임을 번들에서 확인해 주석으로 문서화) — `nginx.prod.conf` 보안 헤더 — `X-Content-Type-Options`/`X-Frame-Options`(또는 CSP)/`Referrer-Policy` 부재, `server_tokens off` 미설정(`:1-29`). TLS/HSTS는 저장소 밖 엣지 소관.
- [x] **P2-22 [infra]** ✅ 2026-08-02 수정 (requirements.lock.txt / requirements-test.lock.txt, Dockerfile이 lock 설치) — BE 의존성 lock 부재 — `requirements.txt:11-21` 범위 지정뿐 → CI 빌드마다 다른 버전 가능. 조치: pip-compile/uv lock.
- [x] **P2-23 [infra]** ✅ 2026-08-02 수정 (`127.0.0.1:3306:3306` 바인드) dev MySQL 노출 — `0.0.0.0:3306` + 커밋된 기본 비밀번호 폴백(`compose.dev.yaml:36-37,45-48`). 조치: `127.0.0.1:3306:3306`.
- [x] **P2-24 [infra]** ✅ 2026-08-02 수정 (mysql:8.4, throwaway 컨테이너에서 스키마 초기화 검증) — `mysql:8.0` EOL(2026-04) → `mysql:8.4` LTS(`compose.dev.yaml:32`; 스키마는 8.4 호환).
- [x] **P2-25 [infra]** ✅ 2026-08-02 수정 (바인드 마운트·venv 볼륨 제거, 이미지 태그·컨테이너 이름 충돌도 분리) — `compose.dev-prod.yaml`이 프로드 이미지를 검증 못 함 — 바인드 마운트가 이미지 코드를 가리고 venv 볼륨이 최초 시딩 후 고착(`:23-25`, 직접 확인; 볼륨은 프로젝트 프리픽스로 dev와 별개). 조치: 두 볼륨 제거.
- [x] **P2-26 [infra]** ✅ 2026-08-02 수정 (BUILD_NUMBER 태그 전달 — 운영 스크립트 갱신 필요, 상단 섹션 참조) — 〔교차〕 배포를 불변 태그로 — Deploy가 외부 스크립트에 위임, 사실상 `:latest` 추적, 롤백 없음(`Jenkinsfile:94-105`). 조치: `${BUILD_NUMBER}` 전달.
- [x] **P2-27 [infra]** ✅ 2026-08-02 수정 (환경변수화, 기본값 17워커 × 6 = 102 ≤ 151) — 〔Codex, 수치 확인〕 DB 풀 × 워커 수 과다 — `pool_size 40 + max_overflow 80 = 프로세스당 120`(`pool_config.py:21-22`, 직접 확인) × dev-prod 17워커(`compose.dev-prod.yaml:28`) ≈ 잠재 2,040 연결 vs MySQL 기본 max_connections 151. 조치: env로 설정화 + `워커 × 프로세스당 최대 ≤ DB 한도` 보장, 풀 고갈 메트릭.
- [x] **P2-28 [db]** ✅ 2026-08-02 수정 (Alembic 도입, upgrade/downgrade 왕복 검증) — 〔교차〕 스키마 마이그레이션 도구 부재 — `schema.sql`이 DROP+CREATE뿐(`:18-20`), 라이브 DB 변경 수단 없음. 조치: alembic(SQLAlchemy 기존 의존) 도입, 빈 DB 업그레이드 CI 검증(Codex).

#### 프론트엔드

- [x] **P2-29 [fe]** ✅ 2026-08-02 수정 (죽은 `extractErrorMessage`를 detail 인지 버전으로 재구현·export해 훅/폼이 공유, 에러 표시는 페이지 Alert 하나로 통일하고 폼 모달은 제출 전 클라이언트 검증 전용으로 축소) 〔교차〕 API 에러 표면 이원화 — 훅은 일반 axios 메시지를 Alert에(`usePortfolioBacktest.ts:23-26`+`PortfolioPage.tsx:41-62`), 폼은 FastAPI `detail`을 모달에(`PortfolioBacktestForm.tsx:76-107`) — 모달 닫으면 무용 문자열만 잔존. `client.ts:43-52` `extractErrorMessage`는 FastAPI가 안 보내는 키를 보는 죽은 코드. 조치: detail-인지 추출을 client.ts로 승격, 표면 단일화(P1-09와 연계).
- [x] **P2-30 [fe]** ✅ 2026-08-02 수정 (185초 타임아웃 + AbortController, 언마운트·재제출 시 취소) — API 타임아웃·취소 부재 — `axios.create({ baseURL })`뿐(`client.ts:23-25`) → 정지 시 폼 영구 잠김, 이탈 시 요청 계속. 조치: `timeout`(여유 있게) + AbortController.
- [x] **P2-31 [fe]** ✅ 2026-08-02 수정 (ThemeProvider Context로 단일화 — Zustand 미사용 확인 후 Context 선택) — 〔교차〕 `useTheme` 전역 상태가 인스턴스별 3벌 — `App.tsx:13`, `Header.tsx:16`, `ThemeSelector.tsx:102`가 각자 useState, DOM/localStorage 부수효과로만 동기화 — 렌더 구조 변경 시 desync. 조치: 진짜 전역(Context 또는 Zustand 도입)으로, CLAUDE.md "Zustand" 서술 정정과 연계(P2-42).
- [x] **P2-32 [fe]** ✅ 2026-08-02 수정 (useId 기반 htmlFor/id 연결, 모바일 카드·요약 컨트롤에 접근 가능한 이름) — 폼 라벨 접근성 — `FormField.tsx:104-110` Label에 `htmlFor`/`id` 연결 없음 → 전략/날짜/수수료 입력 전부 스크린리더 무명(`PortfolioSummary.tsx:41-53` 등 동일; `PortfolioTable`은 모범). 조치: `React.useId` 연결, 맨몸 Select에 aria-label.
- [x] **P2-33 [fe]** ✅ 2026-08-02 수정 (렌더 시점 innerWidth 직독 → 뷰포트 관측, 회귀 테스트 추가) — 〔Codex, 코드 확인〕 차트 반응형이 렌더 시점 `window.innerWidth` 직독 — `StockPriceChart.tsx:248-257`, `BenchmarkIndexChart.tsx:207-216`(라이브 2개; `EquityChart.tsx:46-49`는 도달불가 서브트리 — P3-15에서 삭제 예정) → 리사이즈에 미반응. 조치: 반응형 훅/ResizeObserver로 교체.
- [x] **P2-34 [fe]** ✅ 2026-08-02 수정 (`getParamLabel`을 순수 함수로 모듈 스코프 이동 → 의존성 경고 2건 소멸, 죽은 `useAsync.ts`+테스트 삭제 → 3번째 경고 소멸, `--max-warnings 0`. disable 주석 0개) 〔Codex, 실측 확인〕 lint 경고 3 → 0 — `useStrategyParams.ts:55,90`(getParamLabel 의존성 누락 2건; 함수를 useCallback화 또는 내부로), `useAsync.ts:85`(spread 의존성 — 죽은 코드라 파일 삭제가 정답, P3-15와 연계). 완료 시 `--max-warnings 3` → `0`(`package.json`).

#### 테스트 / CI 검사 단계

- [x] **P2-35 [test]** ✅ 2026-08-03 (chartDataTransform 30, dataSampling 23, useChartData 12 — 빈 입력·단일 포인트·NaN·비정렬·중복 날짜 포함) — FE 차트 데이터 파이프라인 테스트 — 커버리지 0%: `useChartData.ts`(506줄), `chartDataTransform.ts`(177줄), `dataSampling.ts`(736줄, src 최대). 조치: 순수 함수부터 픽스처 테스트(빈 입력/단일 포인트/NaN/비정렬).
- [x] **P2-36 [test]** ✅ 2026-08-03 (P1-05 수정 시 회귀 테스트 포함, DCA 매니저 수수료 경계 테스트 추가) — 〔교차〕 수수료 경로 테스트 — 엔진 테스트는 `_execute_backtest` mock, 전략 테스트 전부 `commission=0` → "0.3.3 진입 시 수수료" 동작 무고정. 조치: commission>0 실백테스트 1건 + P1-05 회귀.
- [x] **P2-37 [test]** ✅ 2026-08-03 (mock 저장소 + TestClient 스모크를 tests/unit으로 승격 — CI 테스트 단계가 엔드포인트를 커버) — 메인 엔드포인트 스모크를 CI로 — `POST /api/v1/backtest`+`@handle_portfolio_errors`가 CI 미실행 경로. 조치: mock 저장소 + TestClient를 `tests/unit`으로 승격. 상태코드·응답 스키마 계약 검증 포함(Codex).
- [x] **P2-38 [test]** ✅ 2026-08-03 (playwright.config.ts + 스모크 spec 1개, dev 스택 대상으로 실제 2회 통과 확인. Docker CI 테스트 단계에는 넣지 않음 — 브라우저·백엔드가 없음) — 〔교차〕 E2E 결정 — Playwright 의존성·스크립트는 있는데 config 부재, 유일 spec은 100% 주석(0개 실행 가능). 조치: config + 스모크 spec(`입력→실행→결과/오류`) 작성 후 CI 연결, 또는 전면 제거 + CLAUDE.md 정정.
- [x] **P2-39 [test]** ✅ 2026-08-03 (`chart_data_service` 자체가 죽은 코드로 삭제되어 테스트 파일 동반 삭제) — `tests/unit/test_chart_data_service.py:387-401` — 본문 `pass`인 placeholder가 CI에서 항상 초록불. `chart_data_service.py` 자체가 도달 불가(P3-19) — 모듈 거취와 함께 처리.
- [x] **P2-40 [test]** ✅ 2026-08-03 (integration 마커 부여, print를 실제 단언으로 전환, 라이브 서버 의존 제거) — `test_nth_weekday_integration.py` — 마커 없음 + print만(단언 없음). 조치: `@pytest.mark.integration` + 기대 거래 수 단언.

#### 문서 (개발자를 잘못된 코드로 유도)

- [x] **P2-41 [docs]** ✅ 2026-08-02 수정 — `transaction_isolation.md`가 제거된 안티패턴을 "수정 후"로 안내 — `time.sleep(0.1)` 패턴은 2026-02에 의도적으로 제거됨(CHANGELOG §1-2). 따르면 포트폴리오당 2~6초 낭비 재도입(`troubleshooting/transaction_isolation.md:62-78`). 조치: 현행 방식으로 재작성.
- [x] **P2-42 [docs]** ✅ 2026-08-02 수정 (5개 문서에서 제거) — Zustand 허구 제거(6곳) — CLAUDE.md·README.md:21·FE docs 4개 파일이 존재한 적 없는 Zustand를 서술(`git log --all -S` 공집합), `state_management.md`는 가상 스토어 코드 샘플까지. 조치: P2-31과 연계해 실도입 또는 "React hooks + localStorage"로 정정.
- [x] **P2-43 [docs]** ✅ 2026-08-02 수정 — BE docs 유령 심볼 일괄 정정 — `portfolio_service.py`/`PortfolioService`(3개 문서), `yfinance_db.py`, `verify_split.py`, DB명 `backtest_db`, 전략명 `sma_cross_strategy`/`bollinger_bands_strategy`(API에 넣으면 422), 동적 TTL 서술(실제 균일 3600s) 등. 조치: 실심볼 일괄 리네임, 적용 완료 문서는 historical 스탬프.

---

### P1 (신규) — 커버리지 작업 중 발견된 실버그

- [x] **P1-16 [be]** ✅ 2026-08-03 수정 (`app/utils/metrics_math.py`의 `VOLATILITY_EPSILON` 기반 가드로 양쪽 구현 통일. 실측 4.57e14 → 0.0) — Sharpe Ratio가 3.57e17로 폭발 — `annual_volatility > 0` 가드가 부동소수점 노이즈에 취약하다. 동일한 값 10개 이상의 `Series.std()`가 정확한 0이 아니라 ~1e-18을 반환할 수 있어, 가드를 통과한 뒤 나눗셈에서 천문학적 값이 나온다. 가격이 전혀 변하지 않는 포트폴리오(현금 100% 등)에서 재현. 조치: 절대 허용오차 기반 비교(`> 1e-12` 등)로 교체.
- [x] **P1-17 [be]** ✅ 2026-08-03 수정 (단일 포인트에서 `std()` NaN을 0.0으로 정규화) — 단일 데이터 포인트 백테스트에서 `Annual_Volatility`가 raw `NaN`으로 응답에 유출 — Sharpe는 `NaN > 0`이 False라 우연히 0으로 안전하지만, 변동성 자체는 NaN이 그대로 나간다. 조치: NaN 방어 후 0.0 또는 명시적 null.
- [x] **P1-18 [be]** ✅ 2026-08-03 수정 (`_is_tradeable_price`로 0·음수·NaN 가격 체결 차단, 경고 로그 후 건너뜀) — 가격 0이면 `ZeroDivisionError`, 음수면 조용히 음수 주식 수 — `PortfolioDcaManager`가 가격 유효성을 검사하지 않는다. 데이터 품질 이슈가 크래시나 무의미한 포지션으로 이어진다. 조치: 매수 전 `price > 0` 검증, 위반 시 건너뛰고 경고 수집.
- [x] **P3-31 [fe]** ✅ 2026-08-03 수정 (`!== undefined` 비교로 교체, 4곳). 참고: "미사용"이라던 초기 판단은 틀렸다 — `adaptiveSampling`이 폴백으로 `sampleData`를 호출하므로 살아 있는 경로였다.

### ⚠️ 이번 작업으로 바뀐 사용자 노출 동작 (제품 확인 필요)

> 이 라운드에서 결론이 나지 않아 전부 [TODO.md](TODO.md)로 이관했다. 아래는 **왜 그렇게
> 바꿨는지**의 근거 기록이며, 실제 일감은 이관처에서 관리한다.

- [ ] → **TODO.md A-17** — **백테스트 최소 기간 30일 제약 신설** — P2-04(검증 통합)의 "최소 기간 검증 부재"를 메우면서 `MIN_BACKTEST_PERIOD_DAYS = 30`을 도입했다. 30일 미만 요청은 이제 422로 거부된다. 30일 미만 백테스트는 연환산 지표(Sharpe·CAGR)가 무의미해지므로 방어 가능한 규칙이지만, **기존에 되던 요청이 거부되는 변경**이므로 제품 관점 확인이 필요하다. 값이 과하면 조정할 것. 위치는 스키마가 아닌 엔드포인트 — DCA/시뮬레이션 내부를 3~14일 구간으로 검증하는 기존 단위 테스트가 스키마 레벨 하한과 충돌하기 때문(HTTP 요청 정책 vs 데이터 형태 검증의 분리로도 설명 가능).
- [ ] → **TODO.md 「저장소 밖 운영 후속 작업」의 부하 튜닝 항목** (A-04·A-05와 함께) — **백테스트 동시 실행 8건·타임아웃 60초 제약 신설** — P2-16. 초과 요청은 큐잉되고, 총 소요(대기+실행)가 60초를 넘으면 504를 반환한다. `Settings`(`min_backtest_period_days`/`max_concurrent_backtests`/`backtest_timeout_seconds`)로 통합해 환경변수로 조정 가능하다(2026-08-03). **실사용 부하 기준 튜닝은 여전히 필요** — 현재 값은 관측 없이 정한 보수적 초기값이다.
- [ ] → **TODO.md A-18** — **Prometheus 티커 라벨 상한 200개** — 201번째부터는 `other`로 합산된다. LRU가 없는 first-N-seen 방식이라, 초반에 무작위 티커가 슬롯을 채우면 이후 실제 인기 티커가 전부 `other`로 묶인다. 카디널리티 폭증은 막았으나 메트릭 품질은 저하 가능 — 필요하면 주기적 리셋이나 사전 화이트리스트로 개선.

### ⚠️ 저장소 밖 필수 후속 조치 (운영)

> 세 건 모두 저장소 밖 시스템이 필요해 이 라운드에서 검증하지 못했고, [TODO.md](TODO.md)의
> 「저장소 밖 운영 후속 작업」으로 이관했다. 아래는 근거 기록이다.

- [ ] → **TODO.md 「저장소 밖 운영 후속 작업」** — **`/opt/home-server/scripts/deploy-app.sh`가 두 번째 인자(이미지 태그)를 실제로 사용하도록 갱신** — 빌드 #21에서 실측 확인됨(2026-08-03). Jenkinsfile이 `deploy-app.sh backtest-be 21`로 태그를 넘기는데, 스크립트는 **인자를 거부하지 않지만(배포 안 깨짐 ✅) 무시하고 `ghcr.io/kyj0503/backtest-be:latest`를 pull한다(목표 미달성 ❌)**. 로그 근거: `Image ghcr.io/kyj0503/backtest-be:latest Pulling`. 따라서 P2-26의 취지인 불변 태그 배포·롤백 지점은 아직 확보되지 않았다. 조치: 스크립트가 `$2`를 받아 해당 태그를 pull/기동하도록 수정(이미지는 이미 `:${BUILD_NUMBER}`로 GHCR에 푸시되어 있으므로 저장소 쪽 준비는 끝났다).
- [ ] → **TODO.md 「저장소 밖 운영 후속 작업」** — **MySQL 8.4 실기동 확인** — compose 이미지 태그는 8.4로 올렸고 throwaway 컨테이너에서 `schema.sql` 초기화를 검증했지만, 기존 dev 볼륨(8.0 데이터 디렉터리)으로 8.4를 띄우는 것은 검증하지 못했다. 재시작 시 데이터 디렉터리 업그레이드가 필요할 수 있음.
- [x] ✅ 2026-09-27 운영 적용(맨 위 「2026-09-27 운영 반영」, `stamp head`가 아니라 `stamp d5c3763b29e6` → `upgrade head`로 정정) — **Alembic 초기 마이그레이션과 기존 라이브 DB 정합** — 새 DB에서는 검증됐으나, 이미 `schema.sql`로 만들어진 기존 DB에는 `alembic stamp head`로 baseline을 찍어야 한다.

### P3 — 여유 있을 때 (정리·폴리시)

- [x] **P3-01 [test]** ✅ 2026-08-03 (마커 누락 파일에 `pytestmark` 추가, `addopts`에 기본 제외 — bare `pytest`가 362 통과 + 13 제외로 정상 동작) — 유닛 마커 규율 — `tests/unit/` 16개 중 10개에 `@pytest.mark.unit` 부재, bare `pytest`는 integration/e2e까지 수집. 조치: `pytestmark` 추가 + `addopts` 기본 제외.
- [x] **P3-02 [test]** ✅ 2026-08-02 수정 (실제 함수 export해 공유, DCA 분기 커버리지 추가) — `recalcAmountsByWeight` 사본 테스트 — reducer 내부 클로저의 70줄 사본을 테스트 중. 조치: export 순수 함수로 추출해 공유.
- [x] **P3-03 [test]** ✅ 2026-08-03 (coverage 설정을 `.coveragerc`로 이동, 죽은 픽스처 2개 삭제) — 테스트 위생 — `pytest.ini:41-61` coverage 설정은 읽히지 않는 위치(`.coveragerc`로); `tests/fixtures/*_fixtures.py` 임포터 0; MSW `onUnhandledRequest: 'warn'`→`'error'`; `TradeSignalsChart.test.tsx` 스모크 단언.
- [x] **P3-04 [infra]** ✅ 2026-08-02 수정 — FE nginx 이미지 HEALTHCHECK 추가(conf에 `/health` 이미 존재).
- [x] **P3-05 [infra]** ✅ 2026-08-02 수정 (node:22-alpine, nginx 고정 버전) — 베이스 이미지 수명 — `node:20.19.0-alpine` EOL → 22; `nginx:stable-alpine` 부동 태그 고정(운영 이미지는 digest 고정 검토, Codex).
- [x] **P3-06 [infra]** ✅ 2026-08-02 수정 (`/app/requirements.txt`로 경로 교정, `|| true` 제거 — P2-18/20과 함께 처리) — `entrypoint.sh:10-13` 죽은 복구 경로 — `/requirements.txt`(실제 `/app/requirements.txt`) + `|| true`. 조치: 경로 수정, `|| true` 제거.
- [x] **P3-07 [infra]** ✅ 2026-08-02 수정 (restart 정책·리소스 상한·npm ci) — compose 정리 — dev-prod FE 태그 충돌(`backtest-fe:dev`), mysql 서비스 부재로 dev 스택에 암묵 의존, restart 정책·리소스 제한 부재(17-worker BE), FE `Dockerfile.dev` `npm install`→`npm ci`.
- [x] **P3-08 [infra]** ✅ 2026-08-02 부분 수정 (timeout·docker logout 적용, junit 아카이빙은 검사 단계 약화 위험으로 보류) — Jenkinsfile 위생 — 파이프라인 timeout 부재, junit 아카이빙 없음, `docker logout` 없음.
- [x] **P3-09 [db]** ✅ 2026-08-03 (`uq_ticker_date_link` UNIQUE 추가 — 중복 삽입이 1062로 거부됨을 실제 확인. FK는 뉴스/가격 저장이 독립 트랜잭션이라 미추가) — `stock_news` UNIQUE/FK 부재 — 중복 방지가 앱 delete-then-insert 의존(`schema.sql:78-92`). 조치: `UNIQUE (ticker, news_date, link(255))` 류.
- [x] **P3-10 [db]** ✅ 2026-08-03 (중복 인덱스 3개 제거 — schema.sql과 Alembic 양쪽, `EXPLAIN`으로 Backward index scan 확인해 회귀 없음 검증) — 중복 인덱스 3개 제거 — `stocks.idx_ticker`, `daily_prices.idx_stock_date_desc`, `stock_news.idx_ticker`(`schema.sql:41,69,88`) — 쓰기 증폭만.
- [x] **P3-11 [fe]** ✅ 2026-08-02 수정 — 메타데이터·의존성 정리 — `"license": "MIT"` vs 저장소 AGPL-3.0, placeholder repo URL, `@types/node`가 dependencies에, **미사용 `jsdom`(happy-dom 사용 중)·`patch-package`(patches/ 부재인데 postinstall 실행) 제거(Codex, 직접 확인)**.
- [x] **P3-12 [be]** ✅ 2026-08-02 수정 — `config.py:90` 죽은 `secret_key` 기본값 제거.
- [x] **P3-13 [infra]** ✅ 2026-08-02 수정 — nginx gzip + 해시된 `/assets/` 장기 Cache-Control.
- [x] **P3-14 [ci]** ✅ 2026-08-03 (npm audit + pip-audit 차단 스테이지. 업그레이드 불가·도달 불가 건은 `scripts/audit-deps.sh` 예외 목록에서 근거와 함께 통과 — 빈 예외 목록으로 종료코드 1 확인해 "실제로 실패할 수 있는 검사 단계"임을 검증. trivy·커버리지는 근거와 함께 보류) — CI 선택 도입 — BE integration 테스트, 이미지 스캔, 의존성 감사, 커버리지 리포팅(핵심 모듈 우선 기준, Codex), SBOM.
- [x] **P3-15 [fe]** ✅ 2026-08-02 부분 수정 (모듈 9개 삭제. 도달 불가 단일 종목 차트 서브트리는 제품 결정 필요로 보류) — FE 죽은 코드 정리 — ~~`useAsync`~~(✅ P2-34에서 삭제), ~~`NewsModal`/`UnifiedInfoSection`~~(✅ P1-01에서 삭제), 잔여: `useForm`/`use-mobile`, `useStrategies`+중복 상수, `ErrorMessage`/`LoadingSpinner` 미사용 export, `PerformanceMonitor` 미사용부, 미호출 `validateParams`, `getErrorTitle`, `shared/types/index.ts`의 고아 `AsyncState<T>`(useAsync 삭제로 발생), **도달불가 단일 종목 차트 서브트리 전체**(제품 결정 필요), 미호출 `Toaster`+`next-themes`.
- [x] **P3-16 [fe]** ✅ 2026-08-02 수정 — 다크모드 하드코딩 팔레트 — `ChartsSection/index.tsx:84`, `BacktestResults.tsx:52,64`, `ErrorBoundary.tsx:136`, `PortfolioForm.tsx:71` → `dark:` 변형으로.
- [x] **P3-17 [fe]** ✅ 2026-08-02 수정 — 숫자 입력 인체공학 — `parseFloat||0`으로 비울 수 없음, `strategy_params` 문자열 전송(BE가 캐스팅). 조치: 입력 중 문자열 유지, 제출 시 숫자.
- [x] **P3-18 [fe]** ✅ 2026-08-02 수정 — FE 소소 — `alert()`→toast, `CustomTooltip` 본문 내 정의, `EquityPoint`를 `number|null`로.
- [x] **P3-30 [be]** ✅ 2026-08-03 정리 — `BacktestService`의 무호출 위임 메서드 3개와 그로 인해 고아가 된 속성·임포트 제거, `app/interfaces/` 패키지 전체 삭제(`YFinanceDataSource`의 유일한 생성 지점이 삭제된 DI 컨테이너였음). **validators 3개는 삭제하지 않았다** — 커버리지가 23~32%로 낮아 죽은 코드처럼 보이지만, `backtest_engine.py:45` → `validation_service` → `BacktestValidator` 경로로 실제 호출된다(확인함). 라우트 수 7→7 불변.
- [x] **P3-19 [be]** ✅ 2026-08-03 수정 (**2,210줄 순삭제** — DI 패키지, `chart_data_service`+indicators 7개, `handle_backtest_errors`, `BuyAndHoldStrategy`, `spread`/`benchmark_ticker` 필드, 죽은 벤치마크 블록. 라우트 수 7→7 불변, 그룹별 삭제 후 매번 스위트 확인. buy&hold가 레지스트리에서 빠져 생긴 함정은 `test_strategy_registry_coverage.py`로 가드) — BE 죽은 코드 ~2,000줄 — 라이브 라우트는 3개뿐: `chart_data_service.py`(497), `indicators/*`(~840), `di/container.py`(210), `handle_backtest_errors`, `BuyAndHoldStrategy`, `spread`/`benchmark_ticker` 필드 등. 죽은 벤치마크 블록(`backtest_engine.py:337-376`)에 잠재 버그 2개 — 되살리려면 수정 먼저.
- [x] **P3-20 [be]** ✅ 2026-08-02 수정 — 오류 처리 잔손질 — 자기 무력화 re-raise(`backtest_engine.py:109-120`), ValidationError 400 정의 vs 422 재포장+"400:" 누출(`decorators.py:148-152`), TTLCache TOCTOU(`data_repository.py:56-58`).
- [x] **P3-21 [be]** ✅ 2026-08-02 수정 — 가공 폴백 통계 제거 — `Win Rate 50%` 몽키패치(`backtest_service.py:25-70`), `create_fallback_stats`의 비연환산 변동성+`Win 100%` — 200 성공으로 서빙됨.
- [x] **P3-27 [be]** ✅ 2026-08-02 수정 (수수료를 거래 가능 자산에서만 차감) — 수수료 비례 축소가 상장폐지 종목 주식 수까지 감소시킴 — `portfolio_rebalancer.py`의 `scale_factor` 블록이 `new_shares` 전체에 적용되어, 거래 불가여야 할 상장폐지 보유 수량이 리밸런싱마다 미세하게 줄어든다. P1-06 수정으로 총액 불변식은 성립하므로 급하지 않지만, 모델링상 수수료는 현금/거래가능 자산에서 차감되는 것이 옳다. 조치: 수수료를 거래가능 풀에서만 차감하도록 변경 + 수수료>0에서도 상장폐지 주식 수 불변을 단언하는 테스트 추가(현재 `test_delisted_position_share_count_unchanged`는 commission=0 전제).
- [x] **P3-28 [be]** ✅ 2026-08-02 도달 불가 증명 (cash_holdings가 dca_info에서 파생되므로 미매칭 불가 — 불변식 테스트 3개로 고정, 코드 변경 없음) — `available_cash`에 대응하는 `cash` 타입 `dca_info` 항목이 없으면 리밸런싱 후 해당 현금이 유실됨 — P1-06 작업 중 발견된 선재 이슈(테스트 픽스처는 이 조건을 회피). 조치: 미매칭 현금을 보존하거나 명시적으로 거부.
- [x] **P1-15 [be]** ✅ 2026-08-02 수정 — **변동성이 항상 0으로 보고되던 버그**. `backtesting==0.3.3`은 연환산 변동성을 `'Volatility (Ann.) [%]'`로 내보내는데 `backtest_engine.py:383`이 존재하지 않는 `'Volatility [%]'`를 읽고 `.get` 기본값 0.0을 반환했다. RED로 실측 50.37% 대신 0.0이 나오는 것 확인 후 수정. 라이브러리가 실제로 쓰는 키 이름을 고정하는 테스트 포함(업그레이드 시 조용한 0.0 재발 방지). P3-20 작업 중 발견.
- [x] **P3-29 [be]** ✅ 2026-08-03 (충돌 인지 키잉 — 일반적인 경우 표시 심볼 유지, 동명 현금이 둘 이상일 때만 unique_key로 폴백) — 리밸런싱 감사 dict가 표시용 symbol로 키를 잡음 — `portfolio_rebalancer.execute_rebalancing_trades`의 `weights_before`/`weights_after`가 `unique_key`가 아닌 `dca_info[...].symbol`로 키를 만들어, 동명 현금 항목이 여러 개면 리밸런싱 리포트에서 충돌한다. P2-07(현금 중복)을 유니크 키 방식으로 수정하면서 발견. 총액·비중·individual_returns는 이미 정합하므로 리포트 표시만의 문제. 조치: 해당 dict도 unique_key 기반으로 전환.
- [x] **P3-22 [be]** ✅ 2026-08-02 수정 (블록리스트 정확 매칭·다운로드 전 검증, DB 접속 정보 print 제거) — BE 소소 — 블록리스트 substring 매치(`ZZZ.TO` 오차단)+다운로드 후 검증(`data_fetcher.py:182-196`), USD-quote 리스트 3중 하드코딩, `portfolio_metrics.py` 중복+매일 재인스턴스화, `database_config.py` print+root 폴백, 캐시 반환 DataFrame 방어적 copy 검토(Codex, 미검증).
- [x] **P3-23 [fe]** ✅ 프로덕션 빌드 실측 확인(빌드 #21): `chart-vendor` 청크 소멸, HomePage 12.55 kB / PortfolioPage 549 kB로 분리 — ✅ 2026-08-03 (측정 결과 chart-vendor 청크가 차트 없는 홈 화면에서도 modulepreload되고 있었음 — vite manualChunks 항목 제거로 해소, 재측정으로 확인) — 〔Codex〕 번들 측정 기반 최적화 — chart vendor chunk ~427KB의 초기 필요성 측정, 결과 차트의 실행 후 로드 검토(현재 이미 lazy — 실측으로 검증).
- [x] **P3-24 [docs]** ✅ 2026-08-02 수정 (실제 conftest·flat 구조 기준 재작성) — BE 테스트 문서 3종 재작성 — `execution.md`(가짜 디렉터리·테스트명), `fixtures.md`(가짜 픽스처·엔드포인트), `async.md`(가짜 파일·픽스처). 실제 conftest 기준으로.
- [x] **P3-25 [docs]** ✅ 2026-08-02 수정 — FE docs 스테일 — 존재하지 않는 훅 4종 서술(`chart_performance.md`/`data_sampling.md`), 삭제된 `api/` 레이어(`README.md:122,133` 등), `refactoring-plan.md` 아카이브.
- [x] **P3-26 [docs]** ✅ 2026-08-02 수정 — 문서 소소 — 깨진 링크(`stock_split.md`), `../CLAUDE.md` 경로, "Test Count: 59" 자기모순, `.env.example`의 `DATABASE_NAME=backtest`(실제 `stock_data_cache`), `backtestApi.ts` 잔재, README 죽은 예시, `BACKEND_CORS_ORIGINS` no-op, 루트 docs/ 인덱스 누락.

---

### 권장 실행 순서 (Codex 안 + 통합 조정)

1. 저난이도·고효과 독립 수정 일괄: P1-02/03/05(1~수줄), P2-03, P1-11, P2-17, P2-19, P2-23 — 각각 회귀 테스트 동반
2. P1-04/07/08/09/10 수정 + P1-12 테스트 신설(재현 사례를 테스트로 먼저 고정)
3. P1-13/14 테스트 신뢰성 복구, P2-36/37 CI 검사 단계 강화
4. P2-04(검증 통합)·P2-13/14(거래일 모델) — 구조 변경
5. P2-18/20/22/26/27/28 인프라·배포 안전성
6. P2-38 E2E, P2-29~34 FE 개선
7. P3 정리 + 문서(P2-41~43, P3-24~26)
8. 측정 기반 성능(P2-01/12, P3-23)

### 변경 시 공통 완료 기준 (Codex)

> 아래는 백로그 항목이 아니라 **모든 변경에 매번 적용하는 기준**이다.
> 체크박스로 두면 "완료되지 않은 일감"처럼 보이므로 목록으로 둔다.

- 수정 전 실패를 재현하는 테스트가 존재한다
- BE 단위 테스트·FE 테스트·타입 검사·린트·프로덕션 빌드 전부 통과
- API 계약/사용자 동작 변경 시 문서 동반 갱신
- 배포 구성 변경은 readiness·프록시 스모크로 검증

```bash
docker compose -f compose.dev.yaml exec -T backtest-be-fast pytest tests/unit -q
docker compose -f compose.dev.yaml exec -T backtest-fe npm run lint
docker compose -f compose.dev.yaml exec -T backtest-fe npm run type-check
docker compose -f compose.dev.yaml exec -T backtest-fe npm run type-check:test
docker compose -f compose.dev.yaml exec -T backtest-fe npm run test:run
docker compose -f compose.dev.yaml exec -T backtest-fe npm run build
```

---

### 검증 노트 (2026-08-02)

- 테스트 기준선 재확인: 컨테이너에서 BE 141 passed / FE 113 passed. 단, 이 초록불의 실질 범위는 좁음(P1-12~14 참조).
- 시크릿 커밋 없음(`.env.example` placeholder만), 빌드 산출물 미커밋, Jenkins `withCredentials` 정상.
- `schema.sql` 기본기 견실: `DECIMAL(19,4)`, `utf8mb4`, NOT NULL/FK/CHECK, PK-쿼리 정합. Docker 레이어 순서·캐시 마운트·`.dockerignore`·FE lockfile 양호.
- BE 스팟체크(전부 코드 일치): SMA 파라미터 체인, weight 분모 100, buy&hold weight=0, commission 미전달, 200 에러 통과, 현금 심볼명 판별, 무효 기본 전략, 리밸런서 상장폐지 로직.
- BE 클린: SQL 인젝션 없음(전 쿼리 bound param), `eval`/`exec`/`pickle` 없음, 지표 lookahead bias 없음, 라이브 경로 async I/O 경계 준수(17곳 to_thread — 잔여 구멍은 P2-01의 CPU-bound), TTLCache는 현재 이벤트 루프 단일 스레드 접근이라 락 불필요(TOCTOU만 P3-20), 13개 통화 환산 방향 전수 정확.
- FE 클린: 라이브 코드 FSD 준수, `eslint-disable`/`@ts-ignore`/`as any` 0건, strict tsconfig, 차트 memo/lazy/manualChunks 정석, Tailwind 4 규칙 준수, NaN 유입 차단.
- 문서 클린: 버전 표기 전면 최신(구버전 문자열 0건), Docker 온보딩 견실, CLAUDE.md 제약 검증표 Zustand 1건 제외 전부 VERIFIED(기준선 141/113 정적 재계산 일치).
- 이번 세션 추가 검증: lint 경고 정확히 3개 실측(컨테이너), `pool_config.py` 40+80 확인, `TICKER_POPULARITY_TOTAL.labels(ticker=…)` 확인, jsdom/patch-package 미사용 확인, 현금 이름 필드 검증 순서 버그 확인(Codex 옳음 — 이전 감사의 "현금 심볼 검증 면제" 서술은 필드 순서 때문에 실제로는 무효), `nginx.prod.conf` trailing slash·SPA fallback 확인.
- Codex 항목 중 미재현 잔여: BE 커버리지 42%(측정치 인용), 요청 한도 부재의 실부하 영향(P2-16), 캐시 DataFrame 공유 변경(P3-22), UI 숨김 옵션 payload 잔류(P2-13).
