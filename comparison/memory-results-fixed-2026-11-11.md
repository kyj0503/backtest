# Python / Rust 수정 후 메모리 재측정 — 2026-11-11

최종 이미지의 전체 시험 최대 메모리는 Python **243.00 MiB**, Rust **45.85 MiB**로 Rust가 **81.1% 적었다**. cgroup v2 `memory.peak`의 컨테이너 수명 전체 최댓값이다.

## 조건

[최종 동작·성능 보고서](results-fixed-2026-11-11.md)의 이미지와 동일한 임시 API를 새로 시작했다. 각각 CPU 2개·메모리 2 GiB·프로세스 1개, 같은 비교 DB와 공개 시세 캐시를 사용했다. Python 소스는 변경하지 않았다. 정상 37개 입력에 각각 10회, 이후 서로 다른 클라이언트 2·8·16개 동시 요청을 실행했다. 구현당 396개, 총 **792개 모두 HTTP 200**이다.

시간 벤치마크가 끝난 뒤 별도로 측정했다. 관측기는 다른 cgroup에 있고 API의 메모리·PID 정보만 읽는다. `memory.current`는 파일 캐시·커널 메모리 등을 포함하고, 프로세스 RSS는 별도로 기록했다. 아래 값은 API 컨테이너만의 값이며 MySQL·프론트엔드·브라우저·호스트 전체 RAM은 포함하지 않는다. MiB는 1,048,576 bytes다.

Python 시작 시각(UTC): 2026-11-11T08:26:59.936122+00:00, Rust 시작 시각(UTC): 2026-11-11T08:28:27.950005+00:00.

각 시나리오 사이에 재시작하지 않아 앞선 요청의 캐시와 할당기 메모리가 다음 구간에 포함된다. 구간 최대는 약 1ms 간격의 관측 하한이다. 커널 전체 최대는 샘플 간격과 무관하지만 시작 과정과 healthcheck도 포함한다. 종료 후 값은 마지막 요청 뒤 1초 시점이다.

## 핵심 결과

| 항목 | Python | Rust | Rust 감소율 |
| --- | ---: | ---: | ---: |
| 준비 완료 후 요청 전 | 145.93 MiB | 3.14 MiB | 97.8% |
| 정상 37개 중 관측 최대 | 198.70 MiB | 24.01 MiB | 87.9% |
| 8개 동시 요청 관측 최대 | 226.80 MiB | 45.35 MiB | 80.0% |
| 16개 동시 요청 관측 최대 | 243.00 MiB | 45.29 MiB | 81.4% |
| 전체 시험 최대 — 커널 기록 | 243.00 MiB | 45.85 MiB | 81.1% |
| 종료 후 1초 | 239.80 MiB | 34.26 MiB | 85.7% |

| 프로세스 RSS | Python | Rust |
| --- | ---: | ---: |
| 요청 전 | 184.45 MiB | 10.06 MiB |
| 전체 관측 최대 | 286.40 MiB | 51.97 MiB |
| 종료 후 | 285.52 MiB | 41.89 MiB |

두 구현 모두 swap 사용과 OOM 발생은 0이었다. 요청 전후 메모리 차이는 누수의 증거가 아니며, 이 시험은 장기 누수 검증이 아니다.

- Python 실제 샘플 중앙 간격: 1.34~1.38ms, 가장 큰 공백 9.94ms.
- Rust 실제 샘플 중앙 간격: 1.35~1.57ms, 가장 큰 공백 8.57ms.

## 수정 전후 참고

수정 전 최대는 Python 237.31 / Rust 45.96 MiB, 이번에는 위 표와 같다. 실행 시점·시세 캐시·공유 페이지의 cgroup 청구 위치가 달라, 이 작은 차이를 수정 자체의 메모리 개선이나 악화로 단정하지 않는다.

## 구간별 관측 최대

각 행은 누적 실행 상태에서의 `memory.current` 관측 최대다.

| 시나리오 | Python MiB | Rust MiB |
| --- | ---: | ---: |
| usd_single | 149.19 | 4.52 |
| usd_five_8years | 169.92 | 19.95 |
| mixed_us_kr_cash | 169.43 | 14.94 |
| crypto_7day | 169.12 | 14.80 |
| japan_europe_fx | 188.50 | 14.81 |
| cash_only | 187.74 | 14.81 |
| zero_weight | 187.71 | 14.80 |
| weights_cash | 183.28 | 14.78 |
| dca_weekly_1 | 183.21 | 16.46 |
| dca_weekly_2 | 183.89 | 16.73 |
| dca_monthly_1 | 184.10 | 16.40 |
| dca_monthly_2 | 184.55 | 16.29 |
| dca_monthly_3 | 190.17 | 16.27 |
| dca_monthly_6 | 184.50 | 15.62 |
| dca_monthly_12 | 184.57 | 15.55 |
| rebalance_weekly_1 | 185.82 | 24.01 |
| rebalance_monthly_1 | 185.49 | 21.49 |
| rebalance_monthly_12 | 185.20 | 21.48 |
| dca_with_rebalance | 185.48 | 21.56 |
| sma_default | 185.58 | 21.32 |
| sma_custom | 185.94 | 21.06 |
| ema_default | 187.02 | 21.20 |
| ema_custom | 187.91 | 21.11 |
| rsi_default | 189.57 | 21.14 |
| rsi_custom | 190.35 | 21.36 |
| bollinger_default | 191.39 | 21.04 |
| bollinger_custom | 192.91 | 21.29 |
| macd_default | 198.70 | 21.38 |
| macd_custom | 192.77 | 21.10 |
| small_cash_no_trades | 192.84 | 20.62 |
| crypto_sma | 192.82 | 20.87 |
| krw_sma | 193.29 | 20.86 |
| post_all_supplemental | 193.40 | 21.62 |
| get_prices | 193.80 | 21.54 |
| get_exchange | 193.96 | 21.32 |
| get_benchmarks | 193.54 | 21.56 |
| get_news | 189.25 | 21.27 |
| concurrent_2 | 193.68 | 21.41 |
| concurrent_8 | 226.80 | 45.35 |
| concurrent_16 | 243.00 | 45.29 |

## 원본과 재현

- `.comparison/reports/memory-fixed/python.json`, `rust.json`: 요청 전·후·관측 최대·커널 최대·RSS·응답 상태·OOM 이벤트.
- 같은 폴더의 `*-samples.json`: 시간별 원본 메모리 샘플.
- 입력: `.comparison/reports/scenarios-final/normal/*/input.json`.
- 실행: `./scripts/benchmark-local-memory.ps1 -SamplesDirectory scenarios-final`. 기존 디렉터리를 덮어쓰지 않도록 출력은 매번 새 이름이다.
- 임시 메모리 API는 측정 후 제거했으며 원래 비교용 앱 4개와 DB 2개는 유지했다.

## 계속 실행 중인 비교 스택의 참고 스냅샷

17:30:57 KST의 `docker stats --no-stream` 근사 작업 집합이다. 새 프로세스의 위 피크 실험과 다르며, 장시간 실행한 컨테이너의 한 시점 관측이다. Docker가 반올림해 표시한 값이다.

| 구성 | Python 측 MiB | Rust 측 MiB |
| --- | ---: | ---: |
| API | 290.00 | 26.04 |
| React/Vite 프론트엔드 | 910.80 | 918.00 |
| MySQL | 468.40 | 506.00 |
| 합계 | 1,669.20 | 1,450.04 |

API 피크의 81.1% 감소를 전체 스택 RAM 감소율로 적용할 수 없다. 이 스냅샷의 전체 차이는 약 13.1%이며 양쪽 프론트엔드는 여전히 같은 React/Vite 구성이다. 원본 요약은 `.comparison/reports/memory-fixed/stack-snapshot.json`이다.
