# Rust 후속 11개 결함 수정·독립 재검증 — 2026-11-11

[재적대 평가](rust-readversarial-audit-2026-11-11.md)의 **R01~R11을 모두 수정**했다. Python 출력은 정답으로 사용하지 않았다. 독립 자금·수량 원장, 실제 납입 달력, 청산 손익 및 화면/API 연결을 기준으로 재검증했다.

기존 133개 시나리오의 202개 검사와 후속 34개 검사가 모두 통과했다. 새 반례를 영구 회귀 테스트로 추가했고, 실제 런타임 HTTP 16개와 브라우저 4개 시나리오도 통과했다. 검증 범위에서 재현되는 11개 문제는 해결됐으며, 모든 시장·모든 입력에서 오류가 없다는 의미는 아니다.

## 수정과 재현 결과

| ID | 수정 | 독립 기대값 / 수정 후 결과 | 영구 회귀 테스트 |
|---|---|---|---|
| R01 | 휴장일 리밸런싱을 보류하고 다음 공동 거래일에 실행. 일부 시장만 열린 날의 부분 실행 방지 | 일요일 일정 5회 실행, 최종 $17,356.30580357143. 서로 다른 시장 휴장 조합은 1/11까지 이월 | Rust `r01_sunday_schedule…`, `r01_different_market_holidays…` |
| R02 | 거래 신호/체결과 달력 평가 분리. 매일 현지 종가·수량·그날 FX로 재평가 | USD 현금 597.014 + 96,938주 × KRW 97 / 2,000 = **$5,298.507**. 상세·개별·전체 평가액 및 연율화 기간 일치 | Rust `r02_closed_market…` |
| R03 | 캐시 메타데이터와 시세를 동일 REPEATABLE READ 읽기 트랜잭션으로 조회. 빈 캐시 결과 거부 | 실제 MySQL 8.4에서 500회 교체, 2,000회 읽기, 캐시 적중 959회 중 **불일치 0회**. 서버 기본 격리 수준 READ COMMITTED에서도 통과 | Rust DB `r03_concurrent_snapshot_reads…` |
| R04 | 종목 추가/삭제 시 재배분. 누락 비중 제출 차단, 제출 전 총예산 대사 | 추가 후 총액 $10,000 유지 및 미입력 오류. 5% 종목 삭제 후 남은 95% 종목에 $10,000 배정. DCA 총예산도 보존 | FE `readversarial.test.ts`의 R04 3개 |
| R05 | 상세/전체 Profit Factor를 청산 거래의 수수료 차감 USD 손익으로 통일 | +$3,540 / −$3,660 → **0.9672131147540983**, 최종 $9,880. 다종목·수수료 조합도 손익 합산으로 검증. 청산 원장이 없는 경로는 null | Rust `r05_profit_factor…` |
| R06 | 표시 심볼과 `asset_id` 분리. 구성·개별 결과·비중·리밸런싱·CSV 연결 통일 | 현금 50% / 주식 50% 실제 차트 영역 확인. 동명 CASH 주식, 복수 현금도 별도 자산으로 유지 | Rust `r06_r11_asset_ids…`, FE `WeightHistoryChart.test.tsx` |
| R07 | 미청산 포지션 진입을 실제 BUY 이벤트로 병합·중복 제거 | 1/5에 96주 × 97 매수, 현금 $688. 매수 1회·실제 SVG 마커 1개, 매도 0회. 가짜 청산 없음 | Rust `r07_open_position…`, FE R07 및 `OpenPositionChart.test.tsx` |
| R08 | 허용 비중 합계를 정규화하고 최대 나머지 방식으로 센트 배분. 동률 순서를 자산 기준으로 결정 | 95:10 → **$9,047.62 / $952.38**. 입력 순서 반전·95% 합계·센트 잔차 사례에서 자산별 금액과 총액 유지 | FE R08 4개 |
| R09 | 30일 월 근사 대신 실제 추가 DCA 납입일 존재 검사 | 1/30~3/29 격월: 1/30, 3/27 총 2회 및 $20,000 납입으로 HTTP 200. 3/26 종료는 추가 납입이 없어 거부 | Rust `r09_dca_validation…`, FE R09 |
| R10 | 유한성 검사와 명시적 오류 전달. 상세 통계 기간을 요청 달력과 일치 | 극단적 연율화는 panic/500 대신 422. 마지막 4일만 상장된 유한 입력은 **$96,000,688**, HTTP 200 | Rust `r10_finite_overflow…` |
| R11 | 임의 현금 이름도 자산 ID로 분리 | 현금 이름 `date` 및 중복 현금에서 날짜 문자열과 모든 자산 비중 보존. Buy & Hold/기술 전략 양쪽 검증 | Rust `r06_r11_asset_ids…` |

R03의 959는 이번 스케줄링에서 관찰한 적중 수이며 보장된 적중률이 아니다. 종전 108개의 잘못된 적중과 같은 부하 형태에서 오류 수 0을 확인했다.

## 영구 테스트와 검증 층

- Rust: **일반 32개 + 격리 MySQL 3개 통과**. 이번 추가는 일반 8개, DB 1개다. `backtest_be_rust/tests/readversarial.rs`와 입력 전용 `tests/fixtures/readversarial.json`, `src/data_regression_tests.rs`에 보관한다.
- 프론트엔드: **42개 파일 / 382개 테스트 통과**, 이번 추가 11개. ESLint, 앱/테스트 TypeScript 검사도 통과했다. 실제 Recharts 렌더링으로 현금 영역의 높이와 미청산 BUY 마커를 검사한다.
- 별도 독립 검사: **기존 202 + 후속 34 = 236개 통과**. 기존 133개와 후속 16개 엔진 입력을 재사용했다. 이전 Python 출력 fixture 두 파일(`parity.json`, `real-market-python.json`)의 SHA-256은 변경하지 않았다.
- 운영 Rust 바이너리 HTTP: **16개 시나리오의 예상 상태·계산 결과 통과**. 극단적 입력과 비중 미입력 요청 2개는 의도된 422, 나머지 14개는 200이다.
- 실제 업데이트된 Rust 화면: AAPL Buy & Hold, 삼성전자 SMA, 월 DCA, 비중 DCA의 **4개 브라우저 시나리오** 통과. 각각 계산 POST와 독립 참고 GET 4개가 200이고 CSV 다운로드 및 브라우저 오류 0을 확인했다. 비중 DCA는 실제 폼→요청→결과에서 $10,000 총액을 대사했다.
- Docker Rust fmt/clippy/test, BE/FE 의존성 감사(예외 없음), BE/FE runtime 빌드 통과. 이번 수정에는 DB 스키마 변경이 없다.

`comparison/adversarial/second_correctness.py`는 고정된 반례를 준비·실행·대사하고, `second-correctness-evidence.py`는 결과와 소스 202개 파일의 해시를 보관한다. 기계 판독용 결과는 [second-corrected-evidence-2026-11-11.json](../../comparison/adversarial/second-corrected-evidence-2026-11-11.json)이다. 기존 감사와 원시 결과는 덮어쓰지 않았다.

## 시간·메모리 재측정

동일하게 보존된 시세 17종과 동일 API 요청 32종을 사용했다. 순차 각 10회(320건), 8년/5종목 요청 동시 2·8·16건(26건), **구현별 346건, 합계 692건 전부 HTTP 200**이다. 각 API는 새 프로세스 1개, 2 CPU, 2GiB 제한이며 Python과 Rust를 순서대로 측정했다. 외부 시세 API 및 DB 조회 지연은 제외하지만 HTTP 요청, 계산, JSON 응답 시간은 포함한다.

시세 SHA-256: `17f120ffbc9094301101a3c799df4b38e6321e9c5825342fbe0ee52977a9df96`. 직전 벤치마크와 같다. 계산 정의가 수정됐으므로 Python과 Rust의 금융 결과가 같다는 조건은 두지 않았다.

| 지표 | Python 이번 | Rust 이번 |
|---|---:|---:|
| 순차 요청 중앙값 | 107.86 ms | **4.94 ms** |
| 순차 요청 p95 | 268.90 ms | **8.44 ms** |
| 시작 유휴 컨테이너 메모리 | 162.75 MiB | 2.49 MiB |
| 순차 처리 중 관측 최대 | 189.21 MiB | 18.90 MiB |
| 전체 관측 최대 | 225.42 MiB | 72.57 MiB |
| 커널 기록 컨테이너 최대 (`memory.peak`) | 225.63 MiB | **74.31 MiB** |
| 프로세스 RSS high-water (`VmHWM`) | 252.09 MiB | 77.72 MiB |
| 종료 시 컨테이너 메모리 | 224.39 MiB | 61.00 MiB |
| OOM / swap | 0 / 0 | 0 / 0 |

이번 측정에서 Rust의 순차 중앙값은 약 **21.8배 빠르고**, 컨테이너 최대 메모리는 **67.1% 적었다**. 메모리 관측기는 별도 cgroup에 있으며 요청 샘플 간격은 1ms, 실제 중앙 간격은 Python 1.33ms / Rust 1.40ms다. 짧은 피크는 관측에서 빠질 수 있으므로 전체 최대의 대표값은 커널 `memory.peak`를 사용했다. RSS와 cgroup 메모리는 공유 페이지·파일 캐시 등의 회계가 달라 서로 다른 지표다.

직전 Rust 결과와 비교하면 중앙값 **4.16→4.94ms(+18.6%)**, p95 **7.63→8.44ms(+10.7%)**, 커널 최대 **68.13→74.31MiB(+9.1%, +6.18MiB)**다. 달력 평가와 휴장일 처리가 늘어난 수정본에서 관찰된 변화이며, 한 번의 비교 실행만으로 코드 비용과 환경 변동의 기여를 분리할 수는 없다. 직전 Python 중앙값도 100.13→107.86ms로 변했다. 장기 메모리 누수 검사는 아니다.

### 시나리오별 측정

각 메모리 값은 해당 구간의 관측 최대이고 실행 순서에 따른 할당 유지 영향을 포함한다. 개별 시나리오의 순수 추가 메모리는 원시 JSON의 `additional_observed_peak`로 별도 보관한다. 동시 요청 중앙값은 대기 시간을 포함한 개별 HTTP 응답 시간이다.

| 시나리오 | 동시 요청 | Python 중앙값 ms | Rust 중앙값 ms | Python 관측 최대 MiB | Rust 관측 최대 MiB |
|---|---:|---:|---:|---:|---:|
| usd_single | 1 | 26.79 | 1.50 | 166.19 | 4.49 |
| usd_five_8years | 1 | 268.60 | 7.14 | 181.11 | 11.17 |
| mixed_us_kr_cash | 1 | 36.98 | 1.62 | 179.69 | 11.04 |
| crypto_7day | 1 | 44.18 | 1.75 | 179.87 | 11.21 |
| japan_europe_fx | 1 | 35.01 | 1.41 | 179.92 | 10.93 |
| cash_only | 1 | 6.72 | 1.30 | 179.75 | 10.94 |
| zero_weight | 1 | 35.14 | 1.64 | 179.82 | 11.17 |
| weights_cash | 1 | 38.26 | 1.92 | 179.75 | 10.88 |
| dca_weekly_1 | 1 | 131.89 | 4.25 | 179.79 | 10.97 |
| dca_weekly_2 | 1 | 121.44 | 5.22 | 179.62 | 11.85 |
| dca_monthly_1 | 1 | 115.83 | 4.09 | 180.05 | 11.60 |
| dca_monthly_2 | 1 | 113.30 | 4.69 | 179.54 | 11.68 |
| dca_monthly_3 | 1 | 107.94 | 3.25 | 179.86 | 11.43 |
| dca_monthly_6 | 1 | 107.12 | 3.93 | 179.80 | 11.52 |
| dca_monthly_12 | 1 | 107.94 | 3.61 | 179.79 | 11.44 |
| rebalance_weekly_1 | 1 | 309.31 | 8.07 | 180.32 | 13.55 |
| rebalance_monthly_1 | 1 | 177.90 | 5.55 | 180.18 | 18.90 |
| rebalance_monthly_12 | 1 | 139.46 | 5.83 | 180.21 | 13.38 |
| dca_with_rebalance | 1 | 196.29 | 6.76 | 180.41 | 12.95 |
| sma_default | 1 | 100.66 | 6.97 | 181.39 | 12.93 |
| sma_custom | 1 | 107.01 | 7.80 | 182.13 | 13.33 |
| ema_default | 1 | 108.40 | 7.46 | 189.21 | 13.40 |
| ema_custom | 1 | 112.18 | 7.74 | 183.50 | 13.95 |
| rsi_default | 1 | 88.51 | 5.98 | 183.50 | 13.97 |
| rsi_custom | 1 | 103.45 | 8.52 | 183.91 | 13.41 |
| bollinger_default | 1 | 106.98 | 6.79 | 183.87 | 13.40 |
| bollinger_custom | 1 | 110.80 | 6.97 | 184.03 | 13.78 |
| macd_default | 1 | 116.44 | 6.37 | 184.74 | 13.66 |
| macd_custom | 1 | 120.94 | 8.30 | 186.19 | 13.14 |
| small_cash_no_trades | 1 | 24.41 | 2.16 | 186.10 | 13.07 |
| crypto_sma | 1 | 27.55 | 1.99 | 186.21 | 13.32 |
| krw_sma | 1 | 30.91 | 2.01 | 186.41 | 13.00 |
| concurrent_2 | 2 | 713.56 | 12.04 | 188.96 | 18.73 |
| concurrent_8 | 8 | 3079.75 | 29.51 | 211.60 | 60.91 |
| concurrent_16 | 16 | 5157.57 | 43.54 | 225.42 | 72.57 |

## 로컬 서비스 업데이트

- Python 화면: <http://localhost:5173/backtest>, API: <http://localhost:8000>
- 수정 Rust 화면: <http://localhost:5174/backtest>, API: <http://localhost:8001>
- Python 서비스는 보존하고 Rust API·콘솔만 재빌드·교체했다. 애플리케이션 4개와 DB 2개는 healthy이며 재시작 횟수 0이다. 기존 DB 볼륨은 유지했다.
- Rust API 이미지: `sha256:a37ccb58f50cebf992ce571cd6fe196f3c68351380c5ec7068839ee5ba1f23f0`.
- Rust 콘솔 이미지: `sha256:35673d12dbf27d7d2c4ea79bcf71780e1b7bd41afe50e2e0b800406cd1f5f23e`.
- 라이브 서비스·합성 HTTP 검사·벤치마크의 Rust 실행 파일 SHA-256은 모두 `8d9d6c0886c8c5c92727f11570d197a2b993b2c37d9ba342e0ec71d0f7d9c5ef`로 동일하다. Docker Compose의 provenance 때문에 이미지 식별자가 달라져도 실제 검증 바이너리가 같은지 따로 확인했다.
- 양쪽 저장소는 `rust-migration`이며 커밋·푸시·운영 배포는 하지 않았다.

## 재현과 증거 위치

원시 입력·엔진/HTTP/FE/DB 결과·빌드 로그·브라우저 CSV/스크린샷은 `.comparison/reports/second-corrected-2026-11-11/`, 시간·메모리 샘플은 `.comparison/reports/second-corrected-memory-2026-11-11/`에 있다.

```powershell
# 일반 테스트와 빌드: 각 저장소의 AGENTS.md 명령 사용
docker build --target test ./backtest_be_rust
# backtest-console에서
docker build --target test .

# backtest에서 기존 결과의 독립 산술 재검증
python comparison/adversarial/second_correctness.py evaluate
python comparison/adversarial/audit.py evaluate .comparison/reports/second-corrected-2026-11-11/baseline
python comparison/adversarial/second-correctness-evidence.py

# 성능 재실행은 새로운 디렉터리 이름 사용
./scripts/benchmark-frozen-memory.ps1 -OutputDirectory second-corrected-memory-rerun
```

새 엔진 결과를 만들 때는 `second_correctness.py prepare`가 준비한 `.comparison/second-correctness-crate`를 `/app`, 새 보고서 디렉터리를 `/reports`로 마운트한 Rust 도구 이미지에서 `cargo run --offline --example verify -- /reports`를 실행한다. `/reports/baseline`에도 같은 실행기를 사용한다. 같은 Cargo target을 여러 소스 사본이 공유할 때에는 mtime을 갱신해 재컴파일 여부를 확인한다.

DB 회귀 검사는 `database/schema.sql`을 적용한 **임시 MySQL만** 대상으로 `RUST_TEST_DATABASE=1`, 해당 `DATABASE_*`와 선택적인 `RUST_TEST_REPORT_DIR`를 주고 `cargo test --offline -- --ignored --nocapture`로 실행한다. 테스트는 `ZZRACE` 등을 쓰므로 사용자 DB를 지정하지 않는다.

정의·제한: USD 환산 가격에 의한 기술적 신호 정책을 유지했고, 이번 변경은 달력 평가를 교정했다. 현금 `asset_id`는 요청 내 연결 키로서 배열 순번을 포함한다. 캐시 스냅샷 검증은 제공업체 수정주가 자체의 경제적 정확성을 보증하지 않는다. 전체 기업행사·실제 시장별 시간대/장중 체결·운영 Turnstile 및 외부 인증 서비스·ARM64·장기간 누수는 이번 검증 범위 밖이다. 기존 TODO의 별도 미해결 지표 정의를 이번 11개 완료에 포함하지 않는다.
