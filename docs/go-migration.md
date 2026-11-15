# Go 백엔드 전환

작업일: 2026-11-15. 브랜치 `go-migration`(부모 `develop` `b7a284f`). 계획: [go-migration-plan.md](go-migration-plan.md).

Python(FastAPI, pandas, backtesting.py 0.6.6, SQLAlchemy, Alembic) 백엔드를 Go 단일 바이너리로 바꿨다.
`backtest_be_fast/`는 삭제했고 git 이력에 남아 있다. 같은 시기 `rust-migration` 브랜치에서 Rust로 옮기며
찾은 회계 결함 수정(F01–F16, R01–R11, S01–S06, T01–T05)을 계산 계약으로 채택했다.

## 결정

| 항목 | 결정 |
|---|---|
| 계산 기준 | 정합성 우선. develop의 Python 출력은 회귀 기록이고 합격 기준은 불변식·독립 원장 테스트다 |
| HTTP | chi v5 + 표준 net/http. 요청 context로 취소를 전파한다 |
| DB | MySQL 유지(운영은 OCI 관리형 MySQL). database/sql + go-sql-driver/mysql, raw SQL |
| 마이그레이션 | Alembic → goose(SQL 파일을 바이너리에 내장). 자동 downgrade 없음 |
| Python | 완전 제거. 기준 자료는 삭제 전에 `backtest_be_go/testdata/`로 추출했다 |
| 빌드·테스트 | 모두 Docker. 런타임은 distroless static nonroot(서버·backtestctl 두 바이너리, curl 없음) |

## 구조

```
backtest_be_go/
  cmd/server        HTTP 서버, -healthcheck <path>
  cmd/backtestctl   migrate status|up|detect|baseline, check-orphans
  internal/config   환경 변수(Python 설정과 같은 이름·기본값), DB TLS
  internal/civil    시간대 없는 달력 날짜(일 수)
  internal/marketdata  Yahoo chart, MySQL 스냅샷 캐시, 메모리 캐시, 환율
  internal/engine   요청 모델·검증, buy&hold, 기술 전략 합산, 통계, 응답 타입
  internal/strategy 지표, 바 단위 체결 엔진(backtesting.py 대체)
  internal/api      라우터, 핸들러, pydantic 호환 422, 참고 조회, Turnstile, 클라이언트 IP
  internal/admission 실행 슬롯(전역·클라이언트별)
  internal/news     네이버 뉴스, 텍스트 정리, 3시간 캐시
  internal/monitoring Prometheus 지표(Python 이름·라벨·버킷 유지)
  migrations        goose SQL
  testdata          고정 기준 자료(Go 출력으로 재생성 금지)
```

## 계산 계약

rust-migration의 [`docs/rust-migration.md`](https://github.com/kyj0503/backtest/blob/rust-migration/docs/rust-migration.md)
"정확성 수정 후 계산 계약"과 같다. 요점:

- **체결**: 기술 전략은 종가 신호를 다음 봉 시가에 체결한다. 마지막 봉 신호는 체결하지 않고, 남은
  포지션은 마지막 종가로 평가한다(`open_positions`, `cash`). (F01)
- **수수료**: 매수·매도 각각 체결 금액 × 수수료율. 예산 B로 사는 금액은 B/(1+c). 리밸런싱 수수료는 실제
  회전 금액 기준이며 원장과 같다. (F02, F06)
- **수량**: 수정 주가 기준 소수 단위. 가격 단위를 바꿔도 같은 경제 경로의 자산 가치가 같다. (S01)
- **적립**: 시작일과 실제 예정일에만 납입한다. 월 주기는 시작일의 N번째 요일, 없으면 마지막 같은 요일.
  30일 근사 없음. 휴장일·상장 전 납입금은 현금으로 기다렸다 다음 거래 가능일에 산다. `total_amount`는 센트
  단위 기본 회차 + 마지막 회차 잔액으로 총예산을 보존한다. (F03, F04, T04)
- **평가**: 요청 기간의 모든 달력일. 휴장일은 직전 현지 종가를 유지하고 그날 환율로 다시 평가한다. 현금에는
  환율을 곱하지 않는다. (R)
- **리밸런싱**: 예정일이 휴장이면 보류하고 자금이 있는 모든 주식이 거래 가능한 다음 날 실행한다. 부분
  리밸런싱 없음. 첫날에는 하지 않는다. (R)
- **수익률**: `Total_Return` = 최종 / 실제 총 납입 − 1. `Time_Weighted_Return` = 납입 전후를 나눈 일간
  수익률의 기하 연결. 최초 매수 수수료도 첫 일간 수익률에 들어간다. 벤치마크 초과수익
  (`alpha_vs_sp500_pct`)은 TWR − S&P 500 기간 수익률이다(CAPM 알파 아님). (F11, S02)
- **위험 지표**: 달력일 일간 수익률, 표본 표준편차, √365. `Annual_Return`은 TWR을 기간 일수와 365.25일로
  연복리화. |r| ≤ 1e-11은 0. 낙폭은 TWR 지수 기준이고 최초 매수 비용을 포함한다. (F09, F10)
- **Profit_Factor**: 청산 거래의 수수료 차감 USD 이익 합 / 손실 합. 손실이 없거나 buy&hold면 `null`. (R)
- **RSI**: 첫 n개 변화의 평균으로 시작한 Wilder 평활, 완전 평탄 구간은 50. 볼린저는 첫 완성 창부터. (F08, T03)
- **식별자**: 모든 구성·결과·비중·리밸런싱은 `asset_id`(주식은 심볼, 현금은 `이름__cash_요청순번`)로 잇는다.
  `CASH` 티커와 현금 항목이 충돌하지 않는다. (F07)
- **시세**: 주식은 수정종가 비율을 OHLC에 한 번만 곱한다. 주식의 수정종가가 없으면 503(T01). 부분 누락·0·
  음수·크게 모순된 봉은 503, 전부 비어 있는 봉만 건너뛴다(T02). 한 종목의 캐시는 한 번의 제공업체 응답으로
  통째로 교체하고 1시간 뒤 다시 받는다(F05). 가격 정밀도 `DECIMAL(38,18)`(F14).
- **표현 범위**: 결과·연환산이 유한수가 아니면 422(F15).

### Go에서 더한 보완

- **G01 — 작은 OHLC 범위 오류 보정.** 실제 Yahoo 일봉에 종가가 저가보다 조금 낮은 봉이 있다
  (005930.KS 2024-10-14: 시가 59,500 고가 61,200 저가 59,400 종가 59,300). T02대로 거부하면 그 기간의
  삼성전자 계산이 전부 503이 된다. 고가·저가가 시가·종가를 **1% 이내**로 벗어나면 범위만 넓혀 받고
  (시가·종가는 그대로) 경고 로그를 남긴다. 그보다 크면 계속 503이다. (`marketdata.repairRange`)
- **미래 종료일 기준은 한국 날짜.** Python·rust는 서버(UTC) 날짜를 써서 KST 00~09시에 오늘 종료일이
  거부됐다. Go는 Asia/Seoul 날짜를 쓴다.
- **POST `ticker_info`는 계산에 쓴 시세의 메타데이터**(통화·이름·거래소·상장일)다. rust는 prices 섹션을 끄면
  자리표시값(`currency: USD`)을 돌려줬다.
- **응답 키 순서**는 Python 순서를 따르고 새 필드는 가까운 자리에 둔다(rust는 serde 기본값이라 알파벳순).
  `portfolio_statistics`: … `Annual_Return`, `Time_Weighted_Return`, `Annual_Volatility`,
  `Return_Observation_Days_Per_Year`, `Annualization_Basis`, `Sharpe_Ratio` … `Trade_Win_Rate`(전략 경로만),
  `Profit_Factor`, `sp500_total_return_pct`, `alpha_vs_sp500_pct`(벤치마크가 있을 때만).

## Python(develop) 대비 바뀐 값

같은 입력에서 Python 기록과 다른 값과 그 이유다(`go test -v -run Record ./internal/engine`이 비교를 출력한다).

| 항목 | Python | Go | 근거 |
|---|---|---|---|
| 수수료 반영 | 매수만, B×(1−c) | 매수·매도, B/(1+c) | F02 |
| 기술 전략 체결 | 신호 봉 종가/시가(마지막 봉 포함) | 다음 봉 시가 | F01 |
| 기술 전략 수량 | 정수 내림 | 소수 단위 | S01 |
| 평가 달력 | 거래일 | 모든 달력일 | F09, R |
| 연환산 | √252 | √365(달력일) | F09 |
| Win_Rate | 거래일 중 상승일 비율 | 달력일 중 상승일 비율(휴장일 0) | F09 |
| 수익률 | Total_Return만 | Total_Return + Time_Weighted_Return | F11 |
| 벤치마크 알파 | 총수익률 − S&P | TWR − S&P | F11 |
| Profit_Factor | 일간 수익 합 비율(buy&hold 포함) | 청산 거래 순손익 비율, buy&hold는 null | R |
| RSI 초기값 | pandas EWM | 첫 n개 평균 + Wilder | F08 |
| 리밸런싱 휴장일 | 그날 가능한 종목만 | 모두 가능한 다음 날 | R |
| 응답 필드 | — | `asset_id`, `calculation_assumptions`, `open_positions`, `cash`, `*PriceNative`, `total_amount` 입력 | R, S04 |

수수료·리밸런싱·적립이 없는 일시 투자는 최종 평가액·총수익률·연수익률·MDD가 Python과 정확히 같다
(스냅샷 `buy_hold_failed_symbol`, `buy_hold_cash_only`). 변동성·샤프·승률은 달력일 기준이라 다르다.

## API·운영 호환성

- 경로·요청 본문·`include_*` 기본값·오류 본문 형태는 같다. 422 목록은 Python이 실제로 돌려준 23개 사례와
  같다(`TestHTTPBoundaryMatchesPython`). 500은 `(오류 ID: uuid)`만 준다.
- 콘솔은 rust 계약을 반영한 `backtest-console` rust-migration 브랜치를 쓴다(브라우저 E2E 통과). develop
  콘솔은 `asset_id` 등 새 필드를 모른다.
- `/metrics`: Python의 HTTP 지표(instrumentator 이름·라벨·버킷)와 업무 지표(`backtest_execution_total`,
  `backtest_processing_seconds`, `backtest_stage_duration_seconds`, `ticker_popularity_total`,
  `backtest_jobs_running/waiting`, `market_data_jobs_running/waiting`, `backtest_supplemental_outcome_total`)를
  같은 이름으로 낸다. 기존 대시보드를 그대로 쓴다. Go 런타임 지표(`go_*`, `process_*`)가 더해진다.
- `/api/v1/docs`·`/redoc`: FastAPI와 같은 Swagger UI·ReDoc(CDN). `openapi.json`은 FastAPI가 만든 문서를
  내장한 정적 파일이며 계약 스냅샷 테스트로 고정한다.
- 헬스체크: 이미지에 curl이 없다. `/app/server -healthcheck /health`(Docker), `/health/ready`(배포 스크립트).
- 동시성: 컨테이너당 프로세스 하나. uvicorn 워커 수·파일 슬롯·`PROMETHEUS_MULTIPROC_DIR`은 쓰지 않는다.
  `MAX_CONCURRENT_BACKTESTS` 등 한도 이름·기본값은 같다. DB 풀은 `DATABASE_MAX_OPEN_CONNS`(16).
- DB TLS: `DATABASE_URL`의 `ssl_ca`/`ssl_check_hostname`(SQLAlchemy 형식 그대로) 또는 `DATABASE_SSL_CA`/
  `DATABASE_SSL_CHECK_HOSTNAME`. 호스트명 검사를 꺼도 CA 체인은 검증한다. 모르는 URL 파라미터는 기동 오류다.
- 배치: `check_orphan_prices.py` → `backtestctl check-orphans`. `daily_price_update.py`,
  `manage_stock_splits.py`, `update_ticker_listing_dates.py`는 옮기지 않았다. 스냅샷이 1시간마다 통째로
  교체되어 분할·배당이 자동 반영되고 상장일은 시세 응답에서 온다.
- 기존 캐시 행(Python·Rust가 쓴 것)에는 스냅샷 표식이 없어 첫 조회 때 다시 받는다. DB를 비울 필요는 없다.

## 운영 전환 절차

1. **리허설**: OCI 서버에서 덤프를 떠(`scripts/load-devdb.sh` 머리말) 로컬 복사본에 적재하고
   `detect → baseline 1 → up`과 실데이터 계산을 확인한다. 00002 ALTER 소요 시간을 잰다.
2. **백업**: 운영 DB 논리 백업(`mysqldump --single-transaction`). 정밀도 확장은 되돌릴 수 없다.
3. **이미지 배포 전 마이그레이션**: Python 컨테이너가 도는 동안 실행해도 된다(00002는 열 형식만 넓힌다).
   다만 DECIMAL 정밀도 변경은 테이블 복사(ALGORITHM=COPY)라 그동안 `daily_prices` 쓰기가 막힌다. 리허설에서
   잰 시간을 보고 사용량이 적은 시간에 한다. 새 이미지를 서버에 받은 뒤 일회성 컨테이너로 실행한다:
   `docker run --rm --network backend-net --env-file /opt/backtest/production/.env -v /opt/backtest/production/tls:/app/tls:ro --entrypoint /app/backtestctl <image> migrate detect`
   → `baseline 1` → `up` → `status`.
4. **배포**: main 병합 후 Actions가 digest로 배포하고 `/health/ready`를 확인한다. 실패하면 이전 릴리스로
   복원된다(DB는 DECIMAL(38,18)이어도 Python이 읽을 수 있다).
5. **콘솔**: backtest-console의 rust-migration 계약 변경을 같은 시점에 배포한다.
6. **확인**: `/metrics`의 `backtest_execution_total{status="error"}`, `backtest_supplemental_outcome_total`,
   G01 경고 로그.

## 검증 결과 (2026-11-15, 로컬 Docker)

| 검사 | 결과 |
|---|---|
| `docker build --target test` (gofmt, vet, staticcheck, `go test -race`) | 11개 패키지 통과 |
| MySQL 통합 테스트 | migrate 2건, 시세 캐시 7건(정밀도 왕복, 부분 갱신 비병합, 의심 행, 만료, 롤백, 동시 교체·읽기, 고아 행) |
| 독립 원장 사례 | F01, F02, F04, F06, F07, F08, F10, F11, S01, S02, S04, S05, T02, T03, R 등 rust 검증 사례 전부 이식·통과 |
| 불변식 | parity 64개(6개 전략, 적립 6종, 리밸런싱, 휴장일, KRW) + 실데이터 6개: 자산 합 = 총액, 수수료 = 체결액 × 수수료율, PnL 항등식, 체결 인과성, 일간 수익률 곱 = TWR |
| rust 차등 비교 | 64개 전부 모든 필드 상대 오차 ≤ ~1e-13(`scripts/diff-rust-reference.sh`) |
| Python 기록 | 골든 마스터 납입 회차·총액 동일, 차이는 위 표로 설명됨 |
| HTTP 경계 | Python 422 본문 23개 일치. 참고 조회 변환(주가·급등락·환율·통계·벤치마크) Python 값과 일치 |
| Yahoo | 실제 응답 7종·90개 일봉 회귀(1e-12) 통과, 실조회 AAPL·005930.KS·KRW=X·EURUSD=X·BTC-USD 통과 |
| 스키마 | schema.sql = goose head(COMMENT 포함), 로컬 dev DB와 합성 Python 덤프로 baseline·up 리허설 |
| E2E | compose.go-test.yaml: 브라우저 → 콘솔 → Go API 계산 + 참고 조회 4개 통과 |
| 감사 | govulncheck 통과 |

## 아직 확인하지 않은 것

- 실제 운영 덤프로의 리허설(덤프는 OCI 서버에서만 뜰 수 있다).
- OCI 관리형 MySQL TLS 실접속(로컬은 자체 서명 CA 단위 테스트), 운영 Turnstile 실토큰, 유효한 네이버 키
  (개발 `.env` 키는 401을 받아 news 섹션이 `error`였다), ARM64 이미지 실행(CI가 arm64 러너에서 빌드한다).
- 장시간 메모리·부하 측정.
