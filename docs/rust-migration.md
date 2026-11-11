# Rust 백엔드 이전

작업 기준일: 2026-11-11. 백엔드 `backtest`와 프론트엔드 `backtest-console`의 `develop`에서 각각 `rust-migration` 브랜치를 만들었다. 백엔드 기준 커밋은 `b7a284f81283db1a537d15a5b49cc892f7f039d7`, 프론트엔드는 `40931a59703b768c13c37071d3f7e41797a21ae9`다.

현재 계산 기준은 아래 **정확성 수정 후 계산 계약**이다. 최초 마이그레이션의 Python 일치 결과는 역사적 기록이며, 수수료·종료 처리 등 잘못된 동작을 재현하는 승인 기준으로 사용하지 않는다. [최초 16개 결함 수정](reviews/rust-correctness-fixes-2026-11-11.md)에 이어 [후속 11개 결함 수정 검증](reviews/rust-second-correctness-fixes-2026-11-11.md)과 [S01~S06 수정](reviews/rust-s01-s06-fixes-2026-11-11.md)을 수행했다. 최신 독립 검증·성능·메모리 결과는 [T01~T05 수정·재검증](reviews/rust-t01-t05-fixes-2026-11-11.md)이다.

## T01~T05 계약 보완 (2026-11-11)

- 주식 수정종가가 누락되면 원종가를 섞지 않고 503으로 거절한다. 환산용 FX만 누락 시 항등 보정을 허용한다.
- 거래용 OHLC는 양수·유한 값과 고저가 범위를 검증한다. 부분 누락·모순·0은 오류이며, 전 OHLC 누락 봉만 건너뛴다. 환산용 FX는 일별 종가 point rate를 검증하고, FX 심볼 자체를 거래 자산으로 사용하면 전체 OHLC 검증을 요구한다.
- 가격 snapshot v4 이전 캐시는 재조회한다. 사용자 DB를 초기화하지 않으며, 새 버전 캐시도 손상된 OHLC가 있으면 적중으로 인정하지 않는다.
- 상장 전 납입금은 첫 거래일까지 현금으로 대기한다. DB 메타데이터나 캐시 유무에 따라 요청 허용 여부가 달라지지 않는다.
- 볼린저는 첫 완성된 기간의 봉부터 신호를 평가하고 다음 봉 시가에서 체결한다. 이전 지표도 필요한 교차 전략의 초기화와 구분한다.
- CSV 리밸런싱 수량·단가는 원장 숫자를 보존한다. 금액·수수료의 센트 반올림은 유지한다.

## S01~S06 계산·표시 계약 보완 (2026-11-11)

- 모든 주식 수량은 수정주가 기반 **소수 조정 단위**다. 당시의 실제 정수 주식 수·최소 주문 수량 모형은 아니다. 분할·배당 조정으로 가격 단위가 달라져도 동일 경제 경로의 자산 가치가 변하지 않도록 기술적 전략의 정수 내림을 제거했다.
- `calculation_assumptions`에 수량·가격·비중·회계 통화 기준을 반환하며 결과 화면과 CSV에도 표시한다.
- 최초 납입 후 매수 수수료를 첫 유효 `daily_returns`에 포함한다. 일간 수익률의 기하 연결이 요약 TWR과 일치하며, 일간 위험 지표에도 같은 관측값을 쓴다.
- 포트폴리오와 벤치마크 지수 차트는 주간·월간 첫 버킷까지 누적한다.
- 거래 원장의 `EntryPrice`/`ExitPrice`는 USD다. `EntryPriceNative`/`ExitPriceNative`는 해당 체결일 환율로 환산한 종목 통화의 조정 가격이다. `PriceCurrency`, `NativeCurrency`, `QuantityUnit`을 함께 제공한다. 거래 마커와 툴팁은 실제 체결일과 체결 가격을 유지하며, 시세 샘플링 날짜로 이동하지 않는다.
- `weight_history`는 종목별 보유자산과 매수 대기 현금을 합한 계정 비중이다. 첫 거래 전에도 납입금이 비중에서 빠지지 않는다. CSV 비중 열은 구성 자산과 전체 기간 키의 합집합이다.
- CSV 리밸런싱 수수료는 `trade.commission`만 사용한다. 누락은 `N/A`로 표시하고 이벤트 합계를 각 행에 중복 기록하지 않는다. 센트 표시는 행별 반올림 오차가 있다.
- 검증·성능·메모리: [S01~S06 수정 보고서](reviews/rust-s01-s06-fixes-2026-11-11.md).

## Yahoo 수집 라이브러리 전환 (2026-11-11)

Yahoo 일봉 요청과 응답 역직렬화는 `yahoo_finance_api = 5.0.0`의 비동기 `YahooConnector`를 사용한다. 공유 커넥터의 `governor` 기능으로 기본 초당 10회 요청 한도를 공유한다. `reqwest`는 라이브러리와 동일한 0.13 계열(잠금 버전 0.13.5)로 통일하고 뉴스 query/Turnstile form 기능을 명시적으로 유지한다. Chart 조회는 쿠키/crumb가 필요 없는 라이브러리 경로를 사용하며, 다른 엔드포인트의 인증 갱신 기능을 사용한다고 주장하지 않는다.

거래소 IANA 시간대·과거 DST, 조회 경계 패딩과 최종 날짜 필터, 수정종가/종가 비율을 OHLC에 한 번 적용하는 계약, 원래 통화 저장과 날짜 이전 환율 선택은 애플리케이션에서 유지한다. 라이브러리 `quotes()`가 누락된 수정종가를 0으로 바꾸므로 구조화 응답의 null을 보존한다. T01 이후 주식의 누락 수정종가는 오류이며, 환산용 FX만 원종가 사용을 허용한다. 실제 보정값 0, 시계열 길이 불일치, 보정 가격 범위 초과는 정상 시세로 반환하지 않는다.

회귀 자료는 `tests/fixtures/yahoo-chart-regression.json`의 실제 제공업체 7종·90개 일봉 및 `src/yahoo_regression_tests.rs`의 독립 계산 사례다. 상세 검증·로컬 이미지·재측정은 [Yahoo 라이브러리 전환 보고서](reviews/rust-yahoo-client-2026-11-11.md)를 참조한다. 당시 [3차 적대적 평가](reviews/rust-third-adversarial-audit-2026-11-11.md)의 S01~S06은 수집기 전환과 별도 미해결 사항이었다. 이후 [S01~S06 수정·재검증](reviews/rust-s01-s06-fixes-2026-11-11.md)에서 처리했다.

## 정확성 수정 후 계산 계약

- 기술 전략은 종가 신호를 다음 관측 봉 시가에만 체결한다. 다음 봉이 없으면 주문을 체결하지 않으며, 종료 시 보유 포지션은 마지막 종가로 평가한다. 미청산 포지션은 `strategy_details.*.open_positions`, 남은 현금은 `cash`에 제공한다. 거래 승률은 청산 거래 기준이다.
- `commission`은 매수·매도 각각의 체결 금액에 곱하는 수수료다. 매수 예산 B와 수수료율 c에서 매수 금액은 B/(1+c)다. 기술 전략 손익은 진입·청산 수수료를 모두 차감한다. 리밸런싱도 수수료 차감 후 자산 비중과 실제 체결 수량이 같은 원장으로 일치한다.
- DCA는 요청 시작일과 각 실제 예정일에만 납입한다. 현금도 동일하다. 월 단위 일정은 시작일의 N번째 요일을 유지하며 없는 경우 마지막 같은 요일로 조정한다. 휴장일 납입금은 현금으로 보관하다 다음 거래 가능일에 매수한다.
- `amount`는 금액 입력 모드의 회당 금액이다. 비중 입력 화면은 `amount`와 함께 정확한 종목별 총예산 `total_amount`를 전송한다. 센트 단위 기본 회차 금액과 마지막 회차 잔액을 합쳐 총예산을 보존한다. `total_amount`는 `weight`와 함께 사용할 수 없다. 요청 총 납입 예정액 상한은 1조 USD다.
- `Total_Return`은 최종 자산 / 실제 총 납입금 − 1이다. `Time_Weighted_Return`은 납입 전후 평가를 구분한 일간 수익률의 기하 연결이다. 벤치마크 초과수익은 TWR와 같은 기간 벤치마크 수익률의 차이다. CAPM 회귀 알파가 아니다.
- 요청 기간의 모든 달력 날짜에 평가한다. 휴장일은 직전 가격을 유지한다. 표본 표준편차와 평균으로 산출하는 위험 지표는 √365를 사용하고, `Return_Observation_Days_Per_Year=365`, `Annualization_Basis=calendar_daily`를 제공한다. 연복리 수익률은 기간 일수와 365.25일/년을 사용한다. `Total_Trading_Days`는 하위 호환 필드명이며 현재 의미는 달력 평가일 수다.
- 최초 매수 비용도 납입 전 원금 대비 낙폭에 포함한다. 부동소수점 오차로 발생하는 절대 일간 수익률 1e-11 이하만 0으로 정규화한다. 가격이 불변인 적립식 투자에서 가짜 상승·하락일을 세지 않는다.
- RSI는 최초 n개 가격 변화의 산술 평균으로 상승·하락 폭을 초기화한 다음 Wilder 평활을 적용한다. 상승·하락 폭이 모두 0인 완전 평탄 구간은 중립값 50으로 정의한다.
- DB 가격은 `DECIMAL(38,18)`이다. 한 종목의 캐시는 한 번의 제공업체 조회 구간으로 원자 교체한다. 다른 시점의 수정주가 구간을 합치지 않는다. 기존/불완전/품질 이상 캐시는 다시 조회하고 DB 스냅샷 유효기간은 1시간, 프로세스 캐시는 최대 5분이다. 재조회 실패 시 오래된 값을 정상 가격으로 조용히 대체하지 않는다.
- 프론트엔드 주간 수익률은 공통 월요일~일요일 경계로 복리 집계한다. 마지막 주는 공통 요청 종료일에서 자른다. 매수·매도 마커를 분리하고 CSV 셀의 쉼표·따옴표·개행을 인용 처리한다.

### 후속 11개 수정의 계약 보완

- 리밸런싱 예정일이 휴장이면 보류하고, 대상 주식이 모두 거래 가능한 다음 공동 거래일에 실행한다. 일부 시장만 열린 날의 부분 리밸런싱은 하지 않으며 원래의 일정 간격을 유지한다.
- 기술적 전략의 신호와 체결은 거래일의 USD 환산 OHLC를 사용한다. 평가액은 별도로 모든 요청 달력일의 `USD 현금 + 수량 × 직전 현지 종가 × 그 평가일의 유효 환산율`이다. 휴장일 FX 변동을 반영하고 현금에는 환율을 다시 곱하지 않는다. 상세 지표와 포트폴리오의 평가 기간도 동일하다.
- `Profit_Factor`와 상세 `profit_factor`는 청산 거래의 수수료 차감 USD 이익 합계 / 손실 합계의 절댓값이다. 손실이 없거나 청산 손익 원장을 제공하지 않는 Buy & Hold/DCA 경로는 `null`이다. 일간 수익률 합계의 비율로 대체하지 않는다.
- 비중 입력은 허용된 합계 95~105를 전체 합계로 정규화한다. 센트 잔차는 최대 나머지와 자산 기준 동률 순서로 배분한다. 추가/삭제 시 총예산을 재계산하고 모든 종목의 양수 비중 입력과 제출 예산 일치를 검사한다.
- 실제 DCA 일정에 추가 납입일이 있는지 검증한다. 최소 요청 기간 30일과 별개이며 월을 30일로 근사하지 않는다.
- 모든 구성·개별 결과·비중 이력·리밸런싱 참조는 `asset_id`로 연결한다. 주식 ID는 정규화된 심볼이고 현금 ID는 `표시이름__cash_요청순번`이다. 현금 항목을 합쳐 버리지 않으며 `symbol`/`ticker`는 표시용으로 유지한다. ID는 한 응답 내부의 조인 키이며 요청 순서를 바꾸면 현금 ID가 달라질 수 있다. 화면과 CSV도 이 계약을 사용한다.
- 차트에는 `open_positions`의 진입을 BUY 이벤트로 병합한다. 매도와 청산 거래 수는 추가하지 않는다.
- 캐시 coverage 메타데이터와 시세 행은 동일한 REPEATABLE READ 읽기 트랜잭션으로 조회한다. 빈 결과는 캐시 적중으로 인정하지 않는다.
- 유한한 입력이라도 결과나 연율화가 표현 범위를 넘으면 명시적인 422를 반환한다. JSON null을 숫자로 unwrap해 500을 발생시키지 않는다.

기존 DB는 백업 후 `alembic upgrade head`로 `6f903c2a711b`까지 확장한다. 이전 스키마를 initdb로 만들었고 Alembic 이력이 없는 DB는 실제 스키마가 `1f574a9ba22e`와 같은지 확인한 뒤 해당 리비전으로 stamp하고 upgrade한다. 새 스키마로 생성한 DB만 head로 stamp한다. 정밀도 축소 downgrade는 자동 실행하지 않는다.

## 구현 범위

실행 경로는 `backtest_be_rust`의 Axum/Tokio 서버다. 기존 React/TypeScript 콘솔의 화면과 API 모델은 유지하고 Vite가 `/api/v1` 전체를 Rust 서버에 전달하도록 수정했다. 이전에는 계산 경로만 개발 프록시에 등록되어 있었다.

Rust 서버가 다음 기능을 직접 수행한다.

- Buy & Hold, SMA, EMA, RSI, Bollinger, MACD와 기존 전략 파라미터 검증.
- 일시 투자·적립식 투자, 현금, 리밸런싱, USD 환산 및 거래 내역.
- 실제 납입액 기준 총수익률, 납입 흐름을 제거한 일별 수익률·연환산 수익률·낙폭, 일별 승률과 거래 승률의 구분.
- `POST /api/v1/backtest` 및 `/api/v1/prices`, `/exchange-rates`, `/benchmarks`, `/news`의 독립 GET. POST의 기존 `include_*` 기본값도 유지한다.
- Yahoo chart의 수정 OHLC 조회, MySQL 캐시, 네이버 뉴스 검색·회사명 매핑·텍스트 정리·관련성 필터.
- Turnstile 검증, 신뢰 프록시를 통한 클라이언트 구분, IPv6 /64 단위 한도, 대기·실행 시간 제한과 협력적 계산 취소.
- `/health`, 별도 DB 연결을 이용하는 `/health/ready`, OpenAPI 스키마와 기본 Prometheus 실행 지표.

운영 이미지는 비루트 사용자로 Rust 바이너리 하나를 실행한다. Python·Node 실행 환경을 포함하지 않는다. 기존 `backtest_be_fast`는 비교 기준과 Alembic 관리용으로 보존했으며 Rust 요청 처리에서는 호출하지 않는다. 기존 테이블과 물리 FK 정책을 유지하고, 가격 정밀도 확장을 위한 Alembic 리비전 `6f903c2a711b`를 추가했다.

## 로컬 실행

두 저장소가 같은 상위 디렉터리에 있다고 가정한다. 백엔드에서 기존 `.env`를 검토하거나 파일이 없는 경우 `.env.example`을 복사한다. Compose가 환경변수를 주입하며 바이너리가 `.env`를 자동으로 읽지는 않는다.

```sh
# backtest 저장소
docker compose -f compose.dev.yaml up -d --build
# Rust 소스 변경 후 재컴파일
docker compose -f compose.dev.yaml restart backtest-be

# backtest-console 저장소
docker compose -f compose.dev.yaml up -d --build
```

콘솔은 `http://localhost:5173`, API는 `http://localhost:8000`이다. 프론트엔드 `VITE_API_BASE_URL`은 빈 값이며, 개발 프록시는 `BACKTEST_PROXY_TARGET`을 읽고 이전 `FASTAPI_PROXY_TARGET`도 대체값으로 지원한다.

릴리스 이미지를 로컬에서 시험하려면 개발 API만 중지한 뒤 `compose.dev-prod.yaml`을 사용한다. 기존 개발 MySQL과 `backtest-network`를 사용한다. 보관할 DB에 `down -v`를 실행하지 않는다.

## 설정과 실행 모델

`HOST`, `PORT`, `LOG_LEVEL`과 `RUST_LOG`를 지원한다. `RUST_LOG`가 우선한다. `DATABASE_URL`은 개별 `DATABASE_*`보다 우선하며 이전 `mysql+pymysql://` 접두사도 받아들인다. URL의 `ssl_ca`, `ssl_check_hostname=false`를 기존 관리형 MySQL CA 검증 방식에 대응시킨다. `DATABASE_SSL_CA`는 CA와 호스트 이름을 모두 검증한다.

| 설정 | 기본값 |
| --- | --- |
| `MAX_CONCURRENT_BACKTESTS` | 8 |
| `MAX_CONCURRENT_BACKTESTS_PER_CLIENT` | 2 |
| `BACKTEST_QUEUE_TIMEOUT_SECONDS` | 30 |
| `BACKTEST_TIMEOUT_SECONDS` | 60 |
| `SUPPLEMENTAL_DATA_TIMEOUT_SECONDS` | 15 |
| `MAX_CONCURRENT_MARKET_DATA` | 4 |
| `MARKET_DATA_QUEUE_TIMEOUT_SECONDS` | 2 |
| `MARKET_DATA_TIMEOUT_SECONDS` | 20 |
| `READINESS_DB_TIMEOUT_SECONDS` | 2 |
| `MIN_BACKTEST_PERIOD_DAYS` | 30 |
| `VOLATILITY_THRESHOLD_PCT` | 5 |

컨테이너마다 서버 프로세스 하나를 실행해야 한다. 계산과 네 참고 조회는 각각 공유된 실행 제한을 사용한다. CPU 계산이 취소 토큰을 확인하고 종료할 때까지 슬롯을 보유한다. 인증의 기본값은 `TURNSTILE_ENABLED=true`이며 설정이 불완전하면 503, 토큰이 없거나 유효하지 않으면 403으로 계산을 거부한다. 로컬 Compose만 기본적으로 인증을 끈다. 운영 설정은 `.env.production.example`을 따른다.

과거 Uvicorn worker 수·파일 슬롯·Prometheus multiprocess 환경변수는 Rust에 적용되지 않는다. 이전 Python 전용 설정을 그대로 넣어도 동작한다고 가정하지 말고 현재 예제와 위 설정을 사용한다. 기본 최대 기간은 3,650일, 종목 수는 20개다.

## 재현 가능한 검증

```sh
# backtest
docker build --target test ./backtest_be_rust
sh scripts/audit-deps.sh be
sh scripts/check-schema-parity.sh
docker build --target runtime -t backtest-rust:runtime ./backtest_be_rust

# backtest-console
docker build --target test .
sh scripts/audit-deps.sh
docker build --target runtime .
```

실제 브라우저와 Vite 프록시를 통과하는 합성 시세 통합 검증은 백엔드 저장소에서 실행한다. 임시 DB는 메모리에 저장되고 호스트 포트를 열지 않는다. 브라우저는 API에 실제 HTTP 요청을 보낸다. 이 검증 환경의 API는 `DEBUG=true` 합성 시세를 사용하고 Turnstile을 끈다.

```sh
docker compose -f compose.rust-test.yaml up --build --abort-on-container-exit --exit-code-from e2e
docker compose -f compose.rust-test.yaml down
```

Rust의 별도 MySQL 통합 테스트는 빈 검증 DB에 `database/schema.sql`을 적용한 뒤 `RUST_TEST_DATABASE=1` 및 해당 DB의 `DATABASE_*`를 주입하여 `cargo test --locked mysql_cache_roundtrip -- --ignored`로 실행한다. 이 테스트는 `ZZRUST`, `ZZFAIL` 데이터를 사용하므로 개발·운영 DB를 지정하지 않는다.

### 기준 결과의 출처

`tests/fixtures/parity.json`의 64개 사례는 보존한 Python 구현과 잠긴 `backtesting.py 0.6.6`을 실행해 생성했다. 현금·USD/KRW 혼합·비중·6종 적립 및 리밸런싱 주기·휴장일·중복 현금·5개 기술 전략의 기본/사용자 파라미터·마지막 봉 청산/신규 매수를 포함한다. Rust 계산 결과로 기대값을 갱신하지 않는다.

현재 테스트는 보존된 64개 사례와 실데이터 6개의 **입력**을 재사용하되, 합산 자산·총 납입 수익률·수수료·청산 손익·체결 시각의 독립 불변식을 검사한다. Python 금융 출력은 수정하거나 승인 기준으로 사용하지 않는다. 시세·환율·벤치마크·뉴스 텍스트의 기존 변환 회귀 검사는 별도로 유지한다.

기준값을 의도적으로 갱신할 때만 다음을 실행한다. `/app/app`에는 해당 기준 커밋의 Python 소스가 있어야 한다. Rust 운영 환경에는 이 절차가 필요 없다.

```sh
docker build --target test -t backtest-python-reference ./backtest_be_fast
docker run --rm --network none -e PYTHONPATH=/app \
  --mount type=bind,source="$PWD/backtest_be_fast/app",target=/app/app,readonly \
  --mount type=bind,source="$PWD/backtest_be_rust",target=/rust \
  backtest-python-reference python /rust/tests/export_reference.py
docker run --rm --network none -e PYTHONPATH=/app \
  --mount type=bind,source="$PWD/backtest_be_fast/app",target=/app/app,readonly \
  --mount type=bind,source="$PWD/backtest_be_rust",target=/rust \
  backtest-python-reference python /rust/tests/export_supplemental.py
```

### 최초 마이그레이션 시점의 확인 결과

- Rust: 64개 Python 계산 비교 사례와 실데이터 회귀 6개, 14개 API·취소·입력 검증·데이터 변환 테스트 통과. 거래 로그의 보유기간·지표 진단 컬럼과 결과 목록도 비교한다.
- 별도 MySQL 8.4: 캐시 저장·조회·실패 시 부모/자식 트랜잭션 롤백 통과.
- MySQL 26.10: `schema.sql`과 Alembic head의 3개 테이블 및 COMMENT 정합성 통과.
- 프론트엔드: ESLint, 앱/테스트 TypeScript 검사, Vitest 367개 통과.
- Chromium: 실제 계산 POST, 네 참고 GET, 결과와 CSV 버튼 표시 통과.
- 최종 운영 Nginx를 통한 계산 POST와 네 참고 GET 통과. `tests/verify_runtime.py`로 재현 가능.
- 실제 외부 Yahoo AAPL·삼성전자·환율을 사용한 혼합 포트폴리오 계산, 주가·환율·벤치마크 조회와 DB readiness 확인. 뉴스는 인증 없이 빈 결과 경로만 확인했다.
- Rust와 프론트엔드 운영 이미지 빌드 통과. Rust 컨테이너 비루트 UID와 Python·Node 실행 파일 부재 확인.
- 의존성 감사: RustSec 예외 없음, npm high 이상 예외 없음으로 통과. MySQL 전용 SQLx 의존성을 사용하고 프론트엔드 `follow-redirects`를 1.16.3으로 갱신했다.

## 호환성 경계와 배포 전 확인

2026-11-11 [수정 후 재검증](../comparison/results-fixed-2026-11-11.md)에서 과거 서머타임 환율 날짜·요청 기간 필터·DB 시세 정밀도·DCA 0 근처 수익률·입력/응답 차이를 수정했다. 동일 시세의 실데이터 32개 계산은 전체 비교 필드가 허용 오차 안에서 일치했다. 정상 HTTP 37개는 성과 지표가 일치했고 경계 35개도 통과했다. 비교용 Rust DB는 백업 후 Python의 공개 시세로 한 번 맞췄으며, Yahoo 재조회가 있는 일본·유럽 사례의 일별 평가액에는 1센트 미만 차이가 남는다.

위 결과는 모든 가능한 시세·전략 조합의 동일성을 증명하지 않는다. `Entry_*`/`Exit_*` 거래 진단 컬럼은 구현하고 검증했으며, 실행 시각·소요 시간 등 비결정적 메타데이터는 제외한다. Yahoo의 실시간 응답 및 수정 주가는 제공업체 변경에 영향을 받는다. 구버전 환율 캐시는 `info_json.rust_chart_date_version` 표식으로 판별해 해당 환율만 원자적으로 복구한다.

`/api/v1/docs`는 OpenAPI 링크를 제공하는 간단한 문서 페이지이며 이전 Swagger/Redoc UI와 다르다. `/metrics`는 실행·대기 gauge와 성공/오류 counter를 제공한다. Python의 전략별·단계별 histogram, 티커 인기 및 HTTP 계측 지표 전체를 재현하지 않으므로 기존 대시보드·알림은 전환 전에 맞춰야 한다.

실제 운영 Turnstile 성공 토큰, 네이버 인증을 사용한 뉴스 조회, OCI 관리형 MySQL CA/TLS 및 ARM64 실행은 이 로컬 검증에 포함되지 않는다. 이번 작업은 코드와 Docker·CI 구성 변경이며 커밋·푸시·운영 배포는 수행하지 않았다. 운영 전환은 기존 main 수동 병합·digest 배포·readiness 확인·이전 이미지 복원 절차를 따른다.
