# backtest: Python FastAPI → Go(Chi) 백엔드 전환 계획 (`go-migration` 브랜치)

## Context

`backtest` 저장소의 백엔드 `backtest_be_fast/`는 FastAPI, pandas, backtesting.py 0.6.6, yfinance, SQLAlchemy(raw SQL), MySQL 8.4로 되어 있다. 이를 Go 단일 바이너리 백엔드로 바꾸려 한다.

이미 `rust-migration` 브랜치(커밋 `eef72a4`)에서 같은 작업을 Rust/Axum으로 진행했다. 그 과정에서 Python 동작 자체에 있던 회계 버그들(F01–F16, R01–R11, S01–S06, T01–T05)이 발견되어 고쳐졌다. 이번 Go 전환은 그 경험을 재사용한다.

결정 사항:
- **부모 브랜치**: `develop` (`b7a284f`). 새 브랜치 이름은 `go-migration`.
- **계산 기준**: 정합성 우선. develop의 Python 동작은 1차 회귀 기록으로만 쓰고, rust 브랜치에서 문서화된 수정을 모두 반영한다. 합격 기준은 Python 일치가 아니라 불변식(현금 보존, 인과성, 수수료/PnL 항등식)이다.
- **HTTP 프레임워크**: Chi v5 (표준 net/http).
- **Python 처리**: 완전 제거. Alembic도 Go 마이그레이션 도구(goose)로 옮긴다. 다만 Python 기준 픽스처는 제거하기 전에 먼저 추출해 둔다.

참고 자료는 `git show rust-migration:<path>`로 읽는다. 읽을 문서:
- `docs/rust-migration.md`
- `docs/reviews/rust-adversarial-audit-2026-11-11.md`
- `docs/reviews/rust-correctness-fixes-2026-11-11.md`
- `docs/reviews/rust-s01-s06-fixes-2026-11-11.md`
- `docs/reviews/rust-t01-t05-fixes-2026-11-11.md`
- `docs/reviews/rust-yahoo-client-2026-11-11.md`
- `backtest_be_rust/src/*.rs`: 수정이 실제로 어떻게 구현됐는지 확인하는 참고용. 그대로 번역하지 않는다.

## 0. 브랜치 준비

```bash
git switch -c go-migration develop
```

- 현재 체크아웃은 `rust-migration`이고 작업 트리는 깨끗하다.
- 커밋 작성자는 `kyj0503 <heroria0503@gmail.com>`, 형식은 `tag(scope): subject`. 커밋과 push는 사용자가 요청할 때만 한다.
- 모든 파일은 LF로 저장한다. `.gitattributes`에 `* text=auto eol=lf`가 이미 있다.
- **빌드·실행·테스트는 무조건 Docker로 한다** (사용자 규칙). 호스트에 Go 툴체인을 설치하거나 `go build/test/run`을 호스트에서 직접 실행하지 않는다. `go mod tidy`, `gofmt`, 픽스처 내보내기 같은 보조 작업도 `docker run`/`docker compose run`으로 실행한다. 단위 테스트는 `docker build --target test`, 개발 서버는 `compose.dev.yaml`, E2E는 `compose.go-test.yaml`로 한다.

## 0.5 로컬 검증용 DB: OCI 관리형 MySQL 일회성 복사본

원격 DB는 읽기만 하고, 이후 개발·검증은 로컬 복사본만 사용한다.

1. **덤프**: 관리형 MySQL은 프라이빗 서브넷이므로 DB에 닿는 OCI 앱 서버(또는 배스천)에서 실행한다.
   `mysqldump --single-transaction --routines=false --triggers --set-gtid-purged=OFF stock_data_cache | gzip > stock_data_cache-YYYYMMDD.sql.gz`
   (또는 `mysqlsh util.dumpSchemas`). 가능하면 읽기 전용 계정을 쓴다. 접속 정보는 사용자가 서버 환경에서 직접 넣는다.
2. **전송·보관**: 덤프를 로컬로 가져와 저장소 밖(또는 gitignore된 `.local-db/`)에 둔다. 커밋하지 않는다.
3. **로컬 컨테이너**: `compose.devdb.yaml`에 `mysql:8.4` + 이름 있는 볼륨(`backtest-devdb`)을 정의하고, 포트는 `127.0.0.1`에만 연다. 덤프를 한 번 로드한다. 볼륨은 리셋하지 않는다(AGENTS 규칙).
4. **용도**
   - 운영 전환 리허설: 이 복사본에 `backtestctl migrate baseline` → `up`(00002 정밀도 변경 포함)을 먼저 적용해 운영 절차를 검증한다. 적용 전 볼륨 스냅샷(덤프 재로드 가능)을 확보한다.
   - 실데이터 검증: Go 서버를 이 DB에 붙여 실제 캐시 데이터로 backtest-console 시나리오를 돌린다.
   - 단위·E2E·CI 테스트는 계속 tmpfs MySQL + 합성 픽스처를 쓴다. 복사본은 수동 검증 전용이다.

## 1. 기준 픽스처 확보 (Python을 지우기 전에 먼저)

`backtest_be_go/testdata/`에 다음을 둔다.

1. **rust 브랜치 픽스처 재사용**
   - 복사 대상: `backtest_be_rust/tests/fixtures/{parity,histories,http-boundary,supplemental,yahoo-chart-regression,real-market-python,readversarial}.json`
   - 방법: `git show rust-migration:<path> > ...`
   - 입력, 합성 시세, Python HTTP 에러 응답, Yahoo 원본 응답이 들어 있다.
   - Python 출력값은 "역사적 기록"으로만 쓴다. Rust 출력으로 다시 만들지 않는다는 규칙을 Go에도 그대로 적용한다.
2. **develop 전용 자료 이관**
   - `tests/e2e/data/AAPL.csv`와 `expected_dca_output.json` (골든 마스터)
   - `tests/unit/fixtures/api-contract.json` (HTTP 형태 기준)
   - `tests/unit/data/portfolio_manager_response_snapshot.json`: buy&hold 시나리오 5개만 쓴다. strategy 시나리오는 결과가 mock이라 제외한다. 테스트 코드의 `_frame`/`_fx_rates` 합성 시세는 JSON으로 내보낸다.
3. **내보내기 스크립트**
   - 일회성 `scripts/export-python-reference.sh`를 만든다.
   - develop을 `git archive`한 뒤 `--network none` Python 컨테이너에서 실행해 픽스처를 생성한다.
   - 생성된 결과만 커밋하고, 스크립트는 Python 제거 커밋 이후 HISTORY에 절차로만 남긴다.

## 2. Go 프로젝트 구조 (`backtest_be_go/`)

```
backtest_be_go/
  go.mod                      # module github.com/kyj0503/backtest/backtest_be_go
  cmd/server/main.go          # HTTP 서버, graceful shutdown(SIGTERM)
  cmd/backtestctl/main.go     # 배치/운영: migrate, update-prices, sync-splits, check-orphans, backfill-listing-dates
  internal/config/            # env 파싱 (core/config.py 대응, DATABASE_URL의 mysql+pymysql:// 접두사 허용, OCI 관리형 MySQL용 TLS CA 설정 → mysql.RegisterTLSConfig)
  internal/api/               # chi 라우터, 핸들러, JSON 디코딩(DisallowUnknownFields), 에러 매핑
  internal/api/middleware/    # client IP(trusted_proxy_cidrs, IPv6 /64 그룹), turnstile, recover, 요청 로깅
  internal/admission/         # 전역/IP별 세마포어, 대기·실행 타임아웃, context 취소 (backtest_runner+file_slots+cancellation 대체)
  internal/apperr/            # ValidationError/DataNotFound/InvalidSymbol/RateLimited → 422/404/422/429 등
  internal/model/             # 요청·응답 구조체 (필드 순서 = JSON 키 순서)
  internal/validate/          # 요청 검증 규칙 (schemas.py의 validator 전부)
  internal/schedule/          # N번째 요일 스케줄, DCA/리밸런싱 날짜
  internal/marketdata/        # Yahoo chart 클라이언트, MySQL 캐시, 환율, 티커 정보
  internal/engine/            # buy&hold 일별 시뮬레이션, ledger, DCA, rebalancer
  internal/strategy/          # SMA/EMA/RSI/Bollinger/MACD 지표 + 바 단위 체결 엔진 (backtesting.py 대체)
  internal/stats/             # metrics_math, 포트폴리오 통계
  internal/supplemental/      # prices/exchange-rates/benchmarks/news, 15초 예산, 섹션별 상태
  internal/news/              # Naver OpenAPI + stock_news 3시간 캐시
  internal/monitoring/        # prometheus/client_golang 메트릭
  migrations/                 # goose SQL (embed.FS)
  testdata/
  Dockerfile
```

### 의존성
의존성은 최소로 두고, 버전은 고정한 뒤 `go.sum`을 커밋한다.
- `github.com/go-chi/chi/v5`
- `github.com/go-sql-driver/mysql` + `database/sql`: raw SQL만 쓰고 ORM은 쓰지 않는다.
- `github.com/pressly/goose/v3`
- `github.com/prometheus/client_golang`
- `golang.org/x/time/rate`: Yahoo 호출을 10 req/s로 공유 제한
- `golang.org/x/sync` (errgroup, semaphore)
- `github.com/go-playground/validator/v10`: 선택 사항. 규칙이 복잡하면 `internal/validate`에 직접 작성한다.
- 로깅: 표준 `log/slog`
- 시간대: 표준 `time.LoadLocation` + `time/tzdata` 임베드. 거래소 IANA 시간대를 날짜별 규칙으로 적용한다.
- Naver 뉴스: OpenAPI JSON 응답이므로 별도 HTML 파서가 필요 없다. HTML 엔티티는 `html.UnescapeString`으로 처리한다.

Go 버전은 작업 시점의 최신 안정 버전으로 하고, `go.mod`의 `toolchain`과 Dockerfile 이미지 태그를 고정한다.

### 설계 포인트

**JSON 형태**
- 응답 키 순서가 프론트 계약이다(statistics 키 순서). 그래서 응답은 map이 아니라 struct로 정의한다.
- 날짜를 키로 쓰는 맵(`equity_curve`, `daily_returns`)은 `map[string]float64`로 둔다. Go는 map 키를 정렬해서 출력하므로 날짜순이 된다.

**NaN/Inf**
- `encoding/json`은 NaN을 만나면 에러를 낸다.
- 계산할 수 없는 지표는 `*float64`(nil→null)로 표현한다. 이는 AGENTS 규칙 "계산 불가=None"과 같다.
- 엔진 출력에서 비유한 값이 나오면 422/500으로 처리한다(F15).

**동시성**
- Python은 uvicorn worker 17개와 fcntl 파일 슬롯을 썼지만, Go는 단일 프로세스와 인메모리 세마포어로 충분하다.
- 실행 흐름: `r.Context()` → 큐 대기(`queue_timeout`) → 실행(`context.WithTimeout`)
- 응답 코드:
  - 끊김은 499
  - 대기 초과는 503
  - 실행 초과는 504
  - IP당 초과는 429 + `Retry-After: 10`
- 엔진 루프는 날짜 N개마다 `ctx.Err()`를 확인해 협조적으로 취소한다.
- market-data용 러너는 별도 인스턴스로 둔다: 4/4, 2초, 20초.

**수치 처리**
- 계산은 `float64`로 한다.
- DB `DECIMAL(38,18)`은 문자열로 스캔한 뒤 `strconv.ParseFloat`로 변환한다.
- 저장 후에는 DB에서 다시 읽어 계산한다. 이렇게 해야 DECIMAL 반올림 차이가 생기지 않는다(rust 교훈).

## 3. 단계별 구현

각 단계는 테스트를 먼저 쓰는 TDD로 진행한다. 단계 하나를 독립된 커밋 한 개 이상으로 만든다.

### 3.1 골격
- config, slog, chi 라우터
- `/health`(DB 미접속)와 `/health/ready`(`SELECT 1`, 2초 타임아웃, 503)
- `/metrics`
- `GET /` → `/api/v1/docs` 리다이렉트
- 에러 응답 포맷 `{detail}`: Python과 같은 모양이고, `http-boundary.json`으로 검증한다.
- `/api/v1/openapi.json`: 수동으로 관리하는 정적 파일을 `embed`한다. `api-contract.json`과 동일한지 검사하는 테스트를 둔다.
- `/api/v1/docs`: 간단한 HTML 페이지.

### 3.2 마이그레이션 (Alembic → goose)
- `migrations/00001_baseline.sql`: develop의 Alembic head 스키마(`database/schema.sql`)와 동일하게 만든다.
- `migrations/00002_price_precision.sql`: `DECIMAL(38,18)` (F14, rust의 `6f903c2a711b` 대응).
- `backtestctl migrate`에 하위 명령을 둔다:
  - `up`
  - `status`
  - `baseline`: 기존 운영 DB에 00001을 "적용됨"으로만 기록. 반드시 백업 후 실행한다.
- 자동 downgrade는 넣지 않는다.
- `alembic_version` 테이블은 건드리지 않고 남겨 두며, 제거는 추후 별도로 한다.
- `scripts/check-schema-parity.sh`를 goose 기준으로 바꾼다. 빈 MySQL에 `goose up`을 돌린 결과와 `schema.sql`을 비교한다.

### 3.3 시장 데이터 (`internal/marketdata`)
- **Yahoo 클라이언트**: `query2.finance.yahoo.com/v8/finance/chart/{sym}`를 직접 호출한다. Go에는 유지보수되는 라이브러리가 없다. 처리 내용:
  - chart `meta`(currency, exchangeTimezoneName, firstTradeDate), `events.splits`, `adjclose`를 파싱한다.
  - 날짜별 시간대로 거래일을 산출한다. UTC 조회 구간은 넉넉히 잡은 뒤 요청 구간으로 걸러낸다.
  - adj/raw 비율은 OHLC에 한 번만 적용한다.
  - adjclose가 없는 주식은 503으로 처리하고, raw close로 대체하지 않는다(T01).
  - OHLC 정상성 검사를 한다.
  - 재시도는 2/4/6초 간격으로 3회. 빈 결과는 재시도 없이 404.
  - Yahoo 429는 `RateLimited`로 처리한다.
  - `yahoo-chart-regression.json`으로 파서 회귀 테스트를 한다.
- **MySQL 캐시**
  - 심볼 단위 스냅샷을 트랜잭션 안에서 원자적으로 교체한다(DELETE + INSERT … ON DUPLICATE KEY UPDATE).
  - 읽기는 `REPEATABLE READ READ ONLY` 트랜잭션에서 메타와 시세를 함께 읽는다(R 시리즈).
  - `info_json`에 스냅샷 버전 마커를 넣는다.
  - DB 1시간, 프로세스 내 5분 TTL.
  - 서로 다른 시점에 받은 adjusted 구간은 섞지 않는다(F05).
- **환율**
  - 통화 13종과 곱하기/나누기 규칙은 `constants/currencies.py`를 따른다.
  - 앞값 채우기(ffill)만 하고, 60일 lookback을 둔다.
  - 환율이 없으면 에러를 낸다.
- **티커 이름 매핑**: `constants/ticker_mapping.py`를 `embed`된 JSON으로 옮긴다.

### 3.4 엔진: buy&hold (`internal/engine`, `internal/schedule`)
develop의 `portfolio_simulation_engine.py`, `portfolio_dca_manager.py`, `portfolio_rebalancer.py`, `rebalance_helper.py`, `portfolio_asset_ledger.py`, `portfolio_metrics.py`의 흐름을 옮긴다. 옮기면서 아래 수정을 반영한다.
- **수수료**: 매수와 매도 모두에 적용한다(F02). 주식 수는 소수 단위로 계산한다(S01). 초기 수수료를 일 수익률에 반영한다(S02).
- **현금 DCA**: 미래 납입액을 첫날부터 보유하지 않게 한다(F04). 현금은 상장일 이후부터 시작한다(T04). `CASH` 티커와 현금 자산이 충돌하지 않게 `asset_id`로 분리한다(F07, R 시리즈).
- **리밸런싱**
  - 휴장일에는 대상 시장이 모두 열리는 다음 날로 미룬다.
  - 수수료가 ledger와 일치해야 한다(F06).
  - 보유 자산은 매일 그날 환율로 재평가한다(R).
- **수익률 분리**: TWR과 납입 기준 총수익률을 분리하고, 벤치마크 초과수익은 TWR끼리 비교한다(F11).
- **DCA 기간 계산**: 30일 근사를 쓰지 않고 실제 N번째 요일 스케줄로 계산한다(F03의 백엔드 측).
- **상장일 검증**: DB 캐시 상태에 의존하지 않게 한다(T04 교훈).

### 3.5 엔진: 전략 (`internal/strategy`)
backtesting.py 0.6.6을 대체하는 바 단위 엔진을 만든다.
- 신호는 t일 종가로 만들고, 체결은 t+1일 시가로 한다. 마지막 바의 신호는 체결하지 않는다(F01, look-ahead 제거).
- 매수 수량: `equity*0.95/price`. 정수 수량 규칙은 rust 문서의 최종 결정을 따른다.
- 수수료는 양방향 `notional*rate`. 거래 PnL = `size*(exit-entry) - fees`. 마지막 포지션은 finalize한다.
- 지표:
  - SMA/EMA: `adjust=False`
  - RSI: 첫 n개 변화의 평균으로 시작한 뒤 Wilder 평활(F08)
  - Bollinger: 첫 완전 구간부터 신호를 낸다(T)
  - MACD 12/26/9
- 파라미터 오버라이드 범위는 `strategy_service.py`를 따른다.
- 포트폴리오 집계: 심볼별 equity를 ffill로 합산한 뒤 통계를 재계산한다.

### 3.6 통계 (`internal/stats`)
- 연환산: 달력일 기준 평가, √365 (F09).
- 일 수익률 절대값이 1e-11 이하이면 0으로 만든다(F10).
- 주간 버킷은 월~일, 첫 주간/월간 버킷도 포함한다(F12, S).
- 그 외 항목: Profit Factor(청산 거래의 순 USD PnL 기준, R), 일 기준 Win_Rate, Trade_Win_Rate, MDD(TWR 누적곱 기준).
- 정의 기준은 rust 문서의 최종 정의다. develop 정의와 다른 항목은 `docs/go-migration.md`에 표로 정리한다.

### 3.7 API
- `POST /api/v1/backtest`
  - 처리 순서: Turnstile → 디코딩/검증 → 30일 최소 기간·상장일 검사 → admission → 엔진 → supplemental 병합.
  - 검증 규칙은 `schemas.py`를 그대로 옮긴다:
    - 1–20개 종목
    - amount와 weight 혼용 금지
    - weight 합 95–105%
    - 종목 중복 금지
    - 비 buy&hold 전략에서는 DCA와 rebalance 금지
    - 10년 이하
    - 미래 날짜 금지
    - commission < 0.1
    - 범위와 유한성 검사(F15)
  - 에러 매핑은 `decorators.py`와 같다. 500 응답에는 `(오류 ID: uuid)`를 붙인다.
- `GET /api/v1/{prices,exchange-rates,benchmarks,news}`: 알 수 없는 쿼리 파라미터는 거부한다(`extra='forbid'` 대응). Turnstile은 적용하지 않는다.
- **Turnstile**
  - 헤더는 정확히 1개만 허용하고 2048자 이하.
  - Siteverify를 호출한 뒤 hostname과 action을 확인한다.
  - 거부는 403, 연결 실패는 503.
  - `TURNSTILE_ENABLED=false`면 건너뛴다.
- **메트릭**: Python의 이름과 라벨을 유지한다. 이렇게 하면 기존 대시보드를 그대로 쓸 수 있다(rust의 호환성 빈틈 해소). 대상: `backtest_execution_total`, `backtest_processing_seconds`(histogram), `backtest_stage_duration_seconds`, `ticker_popularity_total`(라벨 30개 상한), jobs running/waiting, `backtest_supplemental_outcome_total`.

### 3.8 배치 작업 (`cmd/backtestctl`)
`scripts/daily_price_update.py`, `manage_stock_splits.py`, `check_orphan_prices.py`(`--delete`, 종료코드 1), `update_ticker_listing_dates.py`를 하위 명령으로 옮긴다. `benchmark_performance.py`는 옮기지 않는다.

### 3.9 인프라
- **Dockerfile 스테이지**: `builder` → `test`(gofmt 검사, `go vet`, `staticcheck`, `go test -race ./...`) → `audit`(`govulncheck`) → `development` → `runtime`.
  - `runtime`은 distroless/static nonroot에 `CGO_ENABLED=0` 정적 바이너리를 넣고, server와 backtestctl을 함께 포함한다.
  - 헬스체크는 `server -healthcheck` 플래그로 한다. distroless에는 curl이 없기 때문이다.
- **compose 파일**
  - `compose.dev.yaml`: 서비스 `backtest-be`, `go run`(또는 air로 리로드), 포트는 `127.0.0.1`에만 바인딩.
  - `compose.dev-prod.yaml`: worker 17개 설정을 제거한다.
  - `compose.yaml`: 이미지와 네트워크는 기존과 같다.
- **CI**: `.github/workflows/cicd.yml`에서 `./backtest_be_fast`를 `./backtest_be_go`로 바꾼다. ARM64 publish와 deploy 흐름은 유지한다.
- **의존성 감사**: `scripts/audit-deps.sh`를 pip-audit에서 govulncheck로 바꾼다.
- **환경 변수 예시**: `.env.example`, `.env.production.example`을 정리한다. `PROMETHEUS_MULTIPROC_DIR`과 uvicorn 관련 항목을 제거한다.
- **배포**: `scripts/deploy.py` 흐름은 같다. 다만 배포 전에 `backtestctl migrate status`를 확인하는 절차를 README에 적는다.

### 3.10 Python 제거와 문서
- `backtest_be_fast/`를 삭제한다. 단, 1단계 픽스처와 Go 테스트가 모두 통과한 뒤에 한다.
- `AGENTS.md`
  - Python 규칙(asyncio.to_thread, backtesting.py 고정, requirements.lock)을 Go 규칙으로 바꾼다: 취소용 context 전파, 고루틴은 errgroup으로만 생성, `schema.sql`↔goose head 동기화.
  - 통합 브랜치 이름 `dev`를 실제 이름인 `develop`으로 고친다.
- `README.md`를 갱신한다.
- `docs/go-migration.md`: 결정 사항, develop 대비 지표 정의 변경표, 운영 DB 전환 절차(백업 → `migrate baseline` → `up`).
- `HISTORY.md`에 기록하고, `TODO.md`를 정리한다.

## 4. 범위 밖 (별도 작업)
- **프론트엔드 `backtest-console` 저장소**: rust에서 발견된 프론트 버그(F03의 30일 근사, F12 주간 버킷, F13 마커 뒤바뀜, F16 CSV 따옴표)와 proxy 환경변수 이름 변경. 백엔드 응답 정의가 바뀌는 항목(TWR 분리 등)은 Go 작업과 맞춰 처리해야 한다.
- `alembic_version` 테이블 삭제, 운영 DB 실제 전환.

## 5. 검증

1. **단위 테스트** (`go test -race ./...`)
   - 스케줄, 지표, 통계, 검증 규칙, admission(429/503/504/499), Turnstile, 에러 매핑.
   - develop 테스트 중 이름으로 고정된 동작은 Go 테스트로 옮긴다: `test_dca_schedule_alignment`, `test_nth_weekday*`, `test_metrics_definitions`, `test_flow_day_return`.
2. **불변식 테스트**: `parity.json`의 입력 64개, 스냅샷 5개, 골든 마스터 입력에 대해 다음을 확인한다(상대오차 1e-7).
   - 자산 합 = 총액
   - 수수료 = notional×rate
   - PnL 항등식
   - 체결 시점의 인과성
   - 현금 보존
3. **회귀 기록 비교**: Python 기대값과의 차이를 계산한다. 차이는 위 F/R/S/T 수정 목록으로 설명되어야 한다. 설명되지 않는 차이는 버그로 본다.
4. **HTTP 경계**: `http-boundary.json`의 23개 에러 응답, `api-contract.json`의 요청·응답 형태.
5. **E2E**: rust의 `compose.rust-test.yaml`과 같은 형태로 `compose.go-test.yaml`을 만든다.
   - 구성: tmpfs MySQL, `BACKTEST_FIXTURE_FILE=histories.json`, `../backtest-console`, Playwright 컨테이너.
   - 실행: `--exit-code-from e2e`.
6. **OCI MySQL TLS (배포 후, 운영 서버에서만)**: 로컬에서 원격 DB에 붙지 않는다. 로컬/CI 검증은 전부 compose의 MySQL 컨테이너로 한다. TLS 설정 코드는 로컬 MySQL 컨테이너에 자체 서명 CA를 걸어 테스트하고, 실제 OCI 관리형 MySQL 접속은 배포 파이프라인의 기존 `/health/ready` 확인 단계로 검증한다 (rust 브랜치에서 미검증으로 남았던 항목). DB는 MySQL을 유지한다(사용자 결정).
7. **실데이터 확인**: 0.5의 로컬 OCI 복사본 DB(마이그레이션 리허설 적용 후)에 Go 서버를 붙여 `compose.dev.yaml`로 띄운 뒤 backtest-console에서 buy&hold(DCA, 리밸런싱, KRW/EUR)와 전략 5종을 직접 실행해 본다. `/health/ready`와 `/metrics`도 확인한다.
8. **Docker**: `docker build --target test`, `--target audit`, `scripts/check-schema-parity.sh`를 실행한다. 모두 CI `verify` 잡과 같은 명령이다.
