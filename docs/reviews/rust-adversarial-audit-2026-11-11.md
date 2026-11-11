# Rust 백테스트 독립 적대적 평가 — 2026-11-11

> 아래는 수정 전 이미지의 감사 기록이다. 후속 수정 및 재검증 결과는 [16개 결함 수정 검증](rust-correctness-fixes-2026-11-11.md)을 참조한다. 원래 반례와 당시 증거는 보존했다.

현재 구현은 계산 정확성 관점에서 승인하기 어렵다. 미래 신호의 과거 체결, 수수료 처리, 납입 시점, 입력 예산과 실제 투자액의 불일치를 재현했다. Python과 같은 결과를 내는지는 이번 금융 계산의 판정 기준으로 사용하지 않았다.

분류한 결함은 **16건(P1 5건, P2 10건, P3 1건)**이다. P1은 전략 성과·투자 원금·과거 시세를 크게 왜곡할 수 있어 먼저 수정해야 하는 항목이다. 같은 원인에서 나온 여러 검사 실패를 별도 결함으로 세지 않았다. 모델 정의에 따라 판단이 달라지는 항목은 아래 별도로 기록했다.

## 검토 대상과 증거

- 백엔드: `C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust`, `rust-migration`의 현재 작업 파일.
- 프론트엔드: `C:/Users/serial/source/개인프로젝트/backtest-console`, `rust-migration`의 현재 작업 파일.
- 실제 HTTP 검증 이미지: `sha256:bda62be9e3bcf9629170634bf5ada176124085ba589d7f363285f2e08c07edd1`.
- 엔진: **합성 시나리오 133개, 독립 검사 201개 중 123개 충족 / 78개 불일치**. 불일치 59개는 같은 부동소수점 분류 오류를 다른 금액·가격으로 재현한 것이다. 연율화 관례와 최초 비용의 낙폭 기준 같은 명시적 평가 기준도 검사에 포함되므로 78개의 서로 다른 버그라는 뜻이 아니다.
- HTTP: 분리된 합성 데이터 API에서 **19회** 요청. 금융 반례 9개는 모두 HTTP 200으로 반환됐고, 잘못된 입력 5개는 모두 422로 거부됐다. 시세·환율·벤치마크·뉴스 조회와 liveness도 확인했다.
- DB: 기존 비교 DB와 다른 **일회용 MySQL 8.4**에서 가격 정밀도와 혼합 조정 기준 캐시 2개 사례를 실행했다.
- FE: 실제 reducer·집계·보고서 함수를 Docker에서 실행했다. 매매 마커는 실제 컴포넌트의 `useMemo` 콜백과 보조 함수를 TypeScript AST로 추출해 실행했다. 화면 픽셀 검증을 했다는 뜻은 아니다.
- 운영 관련 기존 Rust 단위 검사: **14 통과, DB 통합 검사 1개 기본 제외**. 기존 검사에는 호환성 검사가 포함되어 있어 금융 정확성의 독립 증거로 취급하지 않았다.
- 감사용 복사본과 현재 Rust 원본의 바이트 일치를 확인했다. 원본 해시는 증거 JSON에 기록했다. 감사 중 서비스 계산 코드는 변경하지 않았다.

[검사 결과·소스 해시](C:/Users/serial/source/개인프로젝트/backtest/comparison/adversarial/evidence-2026-11-11.json), [재현 방법](C:/Users/serial/source/개인프로젝트/backtest/comparison/adversarial/README.md), [엔진 원시 출력](C:/Users/serial/source/개인프로젝트/backtest/.comparison/reports/adversarial-2026-11-11/engine-results.json), [실제 HTTP 출력](C:/Users/serial/source/개인프로젝트/backtest/.comparison/reports/adversarial-2026-11-11/http-results.json).

## 우선 수정할 결함

### F01 · P1 · 마지막 종가로 만든 신호가 같은 날 시가에 체결된다

EMA(5,10), 원금 $10,000, 수수료 0. 앞선 가격은 완만하게 하락하고 마지막 날만 시가 $100 → 종가 $200으로 설정했다. 마지막 종가를 본 뒤에 처음 매수 신호가 생기므로 그날 상승에는 참여할 수 없다. 정상 평가액은 **$10,000**이다.

실제 결과는 **$14,700(+47%)**, 완료 거래는 0건이다. 종가 $200을 보고 계산한 47주를 이미 지나간 시가 $100에 사고 종가로 평가한다. 다음 날 가격 $200을 한 줄 추가하면 앞선 동일 날짜의 평가액이 $10,000으로 바뀐다. 수수료나 시장 관례로 설명할 수 없는 인과관계 위반이다.

원인: 마지막 바를 재처리하면서 대기 주문까지 같은 바의 시가로 체결한다. 보유 포지션도 종료 시점의 종가가 아닌 마지막 시가로 강제 청산한다. 다음 체결 가능 바가 없는 주문은 미체결로 남기고, 종료 평가·청산 정책을 명시해야 한다.

근거: [strategy.rs:225](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/strategy.rs:225). 사례 `last_close_future_buy`, `last_close_with_future_bar`; 실제 HTTP에서도 +47% 재현.

### F02 · P1 · 같은 수수료 입력이 전략마다 다른 비용으로 계산된다

화면은 매수·매도 수수료라고 설명한다. 기술 전략에서는 `commission`이 매수 가격 가산으로 쓰이고 매도에는 적용되지 않는다. 거래 로그의 `Commission`은 항상 0이다.

매수·매도 실제 시장 가격을 모두 $100으로 고정한 86주 왕복 거래, 수수료 1%에서 비용은 $86 + $86 = **$172**, 최종 자산은 **$9,828**이어야 한다. 실제는 **$9,914**, 로그 수수료는 **$0**이다. 주식 수를 실제 체결된 86주로 고정한 비교라 주문 수량 정책과 무관하다.

Buy & Hold도 현금 예산 A에 대해 `A×(1-c)`를 매수 대금으로 사용한다. 거래 대금에 수수료율 c를 부과한다면 `대금 + c×대금 = A`, 즉 `A/(1+c)`가 맞다. $10,000·1%·가격 불변에서 실제 $9,900, 이 정의의 기대값 $9,900.990099이다. 9% API 스트레스 입력에서는 $9,100 대 $9,174.311927로 차이가 커진다(화면 수수료 입력 상한은 5%).

수수료를 체결 가격과 분리한 원장 항목으로 두고 매수·매도·DCA·리밸런싱에 같은 정의를 적용해야 한다.

근거: [strategy.rs:187](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/strategy.rs:187), [engine.rs:251](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/engine.rs:251), [수수료 설명](C:/Users/serial/source/개인프로젝트/backtest-console/src/shared/components/tooltip/FinancialTermTooltip.tsx:63). 사례 `technical_roundtrip_fee`, `initial_fee_1pct`, `initial_fee_9pct`.

### F03 · P1 · 화면의 총 투자 예산이 실제 납입액으로 보존되지 않는다

비중 100%, 총액 **$10,000**, 월별 DCA, 2023-01-02~2023-10-31을 입력하면 FE는 30일 근사로 11회라고 계산하고 **회당 $909**를 요청에 넣는다. 실제 달력에는 초기 납입과 2~10월 첫 월요일, 총 10회가 있다. 실제 납입액은 **$9,090**, 입력보다 **$910(9.1%) 부족**하다.

단순한 미리보기 오차가 아니다. reducer가 근사 횟수로 실제 `amount`를 만들고 제출 함수가 그 값을 전송한다. 원래 예산·비중과 실제 납입 달력을 기준으로 금액을 배분하고 마지막 회차에서 잔여 센트를 정산해야 한다.

근거: [calculateDcaPeriods.ts:66](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/utils/calculateDcaPeriods.ts:66), [backtestFormReducer.ts:56](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/model/backtestFormReducer.ts:56), [PortfolioBacktestForm.tsx:59](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/components/PortfolioBacktestForm.tsx:59). 실제 FE 함수와 HTTP로 연결 확인.

### F04 · P1 · 현금 DCA의 미래 납입금을 시작일에 모두 보유한다

현금 자산에 주당 $500, 2023-01-02~2023-02-10을 요청하면 6회 합계 **$3,000이 첫날부터 존재**한다. 첫날 잔액은 $500이어야 한다. 주식 $1,000을 섞으면 첫날 $1,500 대신 $4,000으로 시작한다. 리밸런싱까지 켜면 아직 납입하지 않은 현금을 다른 자산에 배분할 수 있다.

HTTP는 이 요청을 허용한다. FE의 투자 방식 선택도 현금 행에 DCA를 허용한다. 현금만 있는 응답은 투자 방식을 `lump_sum`으로 바꾸어 반환하기까지 한다. 현금에도 실제 납입 스케줄을 적용하거나 이 조합을 입력 단계에서 거부해야 한다.

근거: [engine.rs:156](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/engine.rs:156), [현금도 선택 가능한 투자 방식](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/components/portfolio-form/PortfolioTable.tsx:174). 사례 `cash_dca`, `cash_dca_mixed`.

### F05 · P1 · 주식 분할·수정주가 기준이 다른 캐시를 합쳐도 성공으로 계산한다

캐시가 조회 시작·종료 날짜를 덮고 통화가 있으면 그대로 사용한다. 주식 캐시의 갱신 시각, 분할 정보, 조정 기준 버전, `data_quality`, 중간 날짜 누락은 이 판단에 사용되지 않는다. 새로 받은 시세를 요청 구간만 upsert하므로 기존 다른 구간의 조정 기준과 달라질 수 있다.

일회용 DB에 2:1 분할 정보를 기록하고, 과거 구간 $100 / 새 조정 기준 구간 $50인 혼합 캐시를 주입했다. 가격만 절반, 주식 수는 두 배가 되는 분할 자체로 경제적 손실은 없어야 한다. 실제 데이터 계층은 오래된 `suspicious` 두 행을 그대로 반환했고 엔진은 **$10,000 → $5,000**, 경고 `[]`를 반환했다.

이는 **혼합 캐시가 존재한다는 조건에서의 재현**이다. 실제 Yahoo에서 새 분할이 발생하는 과정을 이번에 재생한 것은 아니다. 소스상 부분 구간 갱신과 무기한 주식 캐시 재사용이 그 상태를 허용한다. 조정 기준 변경 시 전 구간을 동일 기준으로 원자적으로 갱신하고, 데이터 품질·세션 누락을 별도로 확인해야 한다.

근거: [data.rs:131](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/data.rs:131), [캐시 조회](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/data.rs:201), [구간 저장](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/data.rs:322). 증거 `database-results.json`의 `ZZSPLIT`.

## 그 외 재현된 결함

### F06 · P2 · 리밸런싱의 거래 수량·수수료·평가액이 같은 원장으로 맞지 않는다

주식과 현금을 각각 $1,000, 수수료 1%로 시작하고 첫 리밸런싱 날 주가를 $100→$200으로 만들었다. 이벤트에는 **2.45주 매도**, 실제 거래 로그에는 **2.46225주 매도**가 기록된다. 수수료는 $4.90이지만 실제 거래량에 1%를 적용하면 **$4.9245**다.

원인은 수수료 전 목표 차이로 비용·이벤트를 만든 다음 목표 자산을 비용만큼 축소해 실제 보유 수량을 따로 계산하는 것이다. 최초 매수 수수료 정의의 영향을 제외하고 실제 초기 체결 수량을 그대로 사용해도, 자금 보존과 50:50 배분을 함께 만족하는 최종 가치는 **$2,975.075377**, 실제는 **$2,975.10**이다. 실제 체결 원장 하나에서 모든 응답과 수수료를 파생시켜야 한다.

근거: [engine.rs:300](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/engine.rs:300), [engine.rs:319](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/engine.rs:319). 사례 `rebalance_fee`.

### F07 · P2 · 현금 합계가 `CASH`라는 주식의 결과를 덮어쓴다

현금 이름 `RESERVE` $1,000 + 주식 티커 `CASH` $2,000, 주식 가격 두 배. 전체 자산 **$5,000**은 맞지만 개별 결과는 현금 $1,000을 두 번 내보내 합계 **$2,000**이다. 주식 최종 $4,000이 사라진다. 현금 집계를 문자열 `CASH` 키에 덮어쓰는 것이 원인이다. 자산 유형과 식별자를 분리해야 한다. FE 참고 자료 조회에서도 이름만 `CASH`면 주식을 제외하는 경로가 있다.

근거: [engine.rs:446](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/engine.rs:446), [usePortfolioBacktest.ts:136](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/hooks/usePortfolioBacktest.ts:136). 사례 `cash_symbol_collision`.

### F08 · P2 · RSI 초기값이 표준 Wilder 초기화와 달라 잘못된 매수 신호가 생긴다

RSI(2), 가격 100→101→100 이후 계속 100, 과매도 기준 40. 최초 평균 상승·하락폭은 각각 0.5이므로 RSI는 **50**, 이후에도 50이다. 따라서 이 조건에서 매수는 없어야 한다. 실제는 0에서 재귀 평균을 시작하여 평균 상승 0.25 / 하락 0.5, **RSI 33.3333**을 만들고 1건 진입한다.

기존 Python 구현과 같은지는 이 정의 오류를 해소하지 않는다. Wilder RSI를 제공하려면 최초 n개 변화량의 단순 평균으로 초기화해야 한다. 변형 지표를 의도했다면 그 정의와 워밍업을 명시해야 한다. [StockCharts의 RSI 산식](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi)은 첫 평균을 단순 평균, 이후 값을 Wilder 평활로 정의한다.

근거: [strategy.rs:138](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/strategy.rs:138). 사례 `rsi_wilder_seed`; 실제 HTTP에서도 불필요한 거래 확인.

### F09 · P2 · 365일 시장에도 252일 연율화를 적용한다

주말을 포함한 매일의 수익률에 `√252`를 고정 적용한다. 365개 일간 변화(+2%, -1% 반복)에서 같은 표본·현재의 단순 연율화 관례를 유지하고 관측 빈도를 365로 맞추면 연 변동성은 **28.6618%**, 실제는 **23.8153%**다. 무위험 수익률 0 가정의 샤프도 **6.40216 대 5.31962**로 약 16.9% 작다. 이 비교는 첫날 0 수익률 포함 여부를 동일하게 유지했다.

이는 관측 빈도 불일치의 검증이다. `√N` 방식 자체도 자기상관 등 가정에 의존하므로 이를 실제 미래 위험의 정확한 예측이라고 해석해서는 안 된다. [Sharpe의 원 논문](https://web.stanford.edu/~wfsharpe/art/sr/sr.htm)은 측정 기간과 연율화 가정을 구분한다. 주식·가상자산·혼합 포트폴리오에 일관된 평가 달력과 산식을 정해야 한다.

근거: [metrics.rs:23](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/metrics.rs:23), [metrics.rs:69](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/metrics.rs:69). 사례 `crypto_daily_annualization`. 현재 세부 전략 통계에는 별도의 365/252 추정도 있어 지표 체계가 일관되지 않다.

### F10 · P2 · 가격 불변인데 상승·하락일과 프로핏 팩터가 생긴다

수수료 0, 모든 가격 $7, 주당 $999.99 납입, 100개 일봉에서 경제적 수익은 0이다. 실제는 **상승 4일, 하락 27일, 7일 연속 하락, 승률 4%, 프로핏 팩터 0.290104754**다. 금액·가격을 바꾼 63개 평탄 시세 사례 중 59개에서 발생했다.

정규화 후 원래 단위로 되돌리는 부동소수점 왕복과 현금흐름 연산의 미세 오차를 엄격한 `>0` / `<0`로 분류한다. 최대 낙폭·변동성에는 임계값을 쓰면서 승률·연속 일수·손익 비율에는 적용하지 않는다. 경제적으로 0인 수익률의 분류 정책을 일관되게 적용해야 한다.

근거: [engine.rs:396](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/engine.rs:396), [metrics.rs:68](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/metrics.rs:68). 사례 `flat_dca_999.99_7` 및 63개 격자 검사.

### F11 · P2 · DCA 수익률과 일시불 벤치마크를 빼서 초과수익으로 표시한다

포트폴리오와 지수의 가격 흐름을 똑같이 100→200으로 만들었다. 최초 $1,000, 가격이 두 배가 된 시점에 $1,000을 더 납입하면 최종 $3,000, 총 납입 $2,000, 납입액 대비 수익률은 50%다. 시간가중 수익률은 100%, 지수도 100%다. 같은 흐름의 초과성과는 0%p이어야 하지만 실제 API는 **`alpha_vs_sp500_pct: -50`**을 반환했다.

FE의 별도 벤치마크 로딩 경로에도 같은 뺄셈이 있다. 동일 현금흐름의 벤치마크를 만들거나 포트폴리오와 벤치마크를 둘 다 TWR로 비교해야 한다. 이 차이를 CAPM의 알파로 부르는 것도 별도 정의가 필요하다. 외부 납입의 영향을 분리하는 원리는 [GIPS Handbook의 수익률 계산 설명](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/)을 참고했다. GIPS 준수 의무가 있다고 판단한 것은 아니다.

근거: [api.rs:452](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/api.rs:452), [usePortfolioBacktest.ts:50](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/hooks/usePortfolioBacktest.ts:50). HTTP 사례 `dca_growth`.

### F12 · P2 · ‘주간’ 비교 차트가 서로 다른 기간을 겹쳐 그린다

주간 집계가 달력 7일이 아니라 **관측치 7개**다. 주식은 거래일만, 벤치마크는 주말 0%까지 포함한다. 같은 평일 +1% 흐름에서 주식의 첫 점은 **1월 10일 +7.2135%**, 지수는 **1월 8일 +5.1010%**가 된다. 이후 버킷도 계속 어긋난다. 전체 기간의 복리 합계가 같아도 기간별 비교는 틀리다.

공통 달력 경계를 먼저 만들고 모든 계열을 같은 구간으로 집계해야 한다. 현재 주석이 ‘근사’라고 인정하는 것만으로 비교 차트의 의미가 맞아지는 것은 아니다.

근거: [returnAggregation.ts:48](C:/Users/serial/source/개인프로젝트/backtest-console/src/shared/utils/dataSampling/returnAggregation.ts:48). 증거 `frontend-results.json.weekly`.

### F13 · P2 · 기술 전략의 매도 마커가 매수 마커로 표시된다

`Type` 없이 `EntryTime`과 `ExitTime`을 함께 가진 기술 전략 거래 로그에서 양쪽 날짜를 순회하면서 항상 `EntryTime` 존재 조건이 먼저 참이 된다. 1월 3일 매수 / 1월 4일 매도 한 건을 실제 변환 콜백에 넣으면 **두 날짜 모두 `buySignal`**, `sellSignal`은 없다. 차트의 매매 횟수는 별도 로직이라 매도 1회라고 표시될 수 있다.

날짜만 모으지 말고 진입·청산 이벤트의 유형을 보존한 뒤 표시해야 한다. 이 검사는 원화/USD 변환 오류와는 별개다. 현 차트 마커는 원래 거래 가격 대신 해당 날짜의 시세 위에 놓도록 구현되어 있다.

근거: [StockPriceChart.tsx:172](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/components/StockPriceChart.tsx:172). 증거 `frontend-results.json.signals`.

### F14 · P2 · 소수점 네 자리보다 작은 시세가 DB에서 0이 된다

가격 $0.00001→$0.00003의 수익률은 +200%이고, $10,000의 종료 가치는 **$30,000**이다. 직접 엔진 입력은 이 값을 계산한다. 그러나 실제 스키마 `DECIMAL(19,4)`에 저장하면 두 가격 모두 0이다. 일회용 MySQL에서 저장·Rust 데이터 조회·엔진 실행까지 연결했을 때 **422 ‘기간 내에 실행된 투자가 없습니다’**가 된다. 저장 가능한 0.00006도 0.0001로 반올림되어 상대오차가 크다.

직접 입력 가능한 저가 자산과 아주 오래된 조정 주가에서 문제가 된다. 자산 가격에 맞는 정밀도를 보존하고, 반올림으로 유효한 가격이 0이 될 때는 조용히 캐시 성공으로 처리하지 않아야 한다. 스키마 변경 시 기존 Alembic 정책을 따라야 한다.

근거: [schema.sql:87](C:/Users/serial/source/개인프로젝트/backtest/database/schema.sql:87), [data.rs:144](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/data.rs:144). 사례 `small_price_unrounded`, DB `ZZTINY`.

### F15 · P3 · 유한 입력을 합산한 오버플로가 성공 응답으로 나간다

두 자산 각각 `1e308`은 개별 유한성 검증을 통과하지만 총합은 무한대다. 실제 HTTP는 **200 success, `Initial_Value: null`, `Final_Value: null`, `Annual_Return: -100`**을 반환한다. 이 응답을 실제 텍스트 보고서 함수에 넣으면 `null.toLocaleString` 예외가 발생한다.

현실적인 투자금 범위를 크게 벗어난 입력이므로 우선순위는 낮다. 다만 명시적 상한·합산 후 유한성·계산 결과 불변식 검증이 필요하다. 잘못된 결과를 정상 금융 결과로 직렬화해서는 안 된다.

근거: [validation.rs:237](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/validation.rs:237), [metrics.rs:71](C:/Users/serial/source/개인프로젝트/backtest/backtest_be_rust/src/metrics.rs:71). 사례 `finite_input_overflow`.

### F16 · P2 · CSV 금액의 천 단위 쉼표가 열 구분자로 해석된다

최종 자산 $3,000을 내보내면 실제 행이 **`최종 자산가치,$3,000`**이다. 열은 `항목,값` 두 개여야 하는데 세 개로 분리된다. 숫자에 `toLocaleString()`을 적용하고 CSV 셀을 따옴표로 감싸지 않기 때문이다. 금액이 큰 정상 결과에서도 발생한다.

CSV에는 지역화하지 않은 숫자를 사용하거나 모든 셀에 표준 escaping을 적용해야 한다. 이번 검사는 다운로드 클릭이 아니라 실제 보고서 생성 함수의 반환 문자열을 검사했다.

근거: [reportGenerator.ts:226](C:/Users/serial/source/개인프로젝트/backtest-console/src/features/backtest/services/reportGenerator.ts:226). 증거 `frontend-results.json.exportResults`.

## 오류와 구분해서 확정해야 할 계산 규칙

| 항목 | 확인한 동작과 판단 |
|---|---|
| 최초 수수료와 MDD | 가격 불변·9% 수수료에서 총 수익률 -9%, MDD 0%. 최초 납입 전 자본부터 위험을 측정한다면 MDD -9%여야 한다. 매수 후 NAV를 시작점으로 정의할 수도 있으므로 별도 결함 수에 넣지 않았다. 화면에서 비용 포함 수익과 비용 제외 위험 시작점의 차이를 설명해야 한다. |
| SMA/EMA/MACD 교차의 동률 | `이전 단기 < 장기`를 요구하므로 동일값에서 위로 갈라지는 신호는 제외된다. 평탄 가격 이후 상승하는 SMA 사례에서 거래 0건 확인. 교차 정의를 `<=`까지 포함할지 명세·테스트로 확정해야 한다. |
| 워밍업·지표 변형 | 시작일 이전 주식 데이터 없이 지표를 초기화한다. EMA는 첫 값 시작, MACD는 보정 가중 EMA, Bollinger는 표본 표준편차를 쓴다. 각각을 모두 오류라고 단정하지 않았지만 일반 차트와 신호가 달라질 수 있다. RSI의 표준 초기화 불일치는 F08로 별도 분류했다. |
| 환율의 시점 | 과거 날짜에 미래 날짜의 환율을 역으로 채우지는 않는다. 다만 기술 전략의 시가에도 해당 일봉 종가 환율을 곱하므로 실제 장 시작 시점에 알 수 있는 환율인지까지 보장하지 않는다. 거래소별 시간대·FX fixing 시점을 명시해야 한다. |
| 조정 주가·현금흐름 | 배당·분할이 조정된 OHLC를 사용하며 실제 배당 현금, 세금, 환전 비용, 슬리피지, 주문 유동성은 따로 모델링하지 않는다. 조정 주가 기반 성과 모형으로 설명해야 한다. 정수 주식 주문과 미래 조정 기준 변경을 결합하면 과거 주문 수량의 재현성도 점검해야 한다. |
| 가격 지수 벤치마크 | `^GSPC`/`^IXIC` 종가 계열과 배당 조정 자산을 비교한다. 투자수익 전체를 비교하려면 가격 지수인지 총수익 지수인지, 배당 처리 기준을 맞춰야 한다. |
| 미정의 지표 | 기술 전략에서 거래가 없거나 downside가 없을 때 일부 지표를 0으로 표시하는 문제가 남아 있다. 기존 TODO A-21과 관련 있으며 ‘위험이 없음’과 ‘계산 불가’를 구분해야 한다. |

## 기능별 검토 범위

| 기능 | 수행한 검증 | 평가 |
|---|---|---|
| Buy & Hold, 현금, 다종목 | 달러 가격 두 배·가격 불변, 10개 규모의 자산 배분과 입력 순서 반전, 개별/전체 합계 | 기본 무수수료 잔액 계산은 통과. F02/F04/F07/F10 영향 |
| SMA/EMA/MACD/RSI/Bollinger | 모든 전략의 평탄 시세, 공통 주문 엔진 소스, EMA 실제 왕복·종료 반례, RSI 초기값, SMA 동률 | F01/F02/F08. 모든 파라미터 조합과 모든 비평탄 경로의 지표 동등성을 증명한 것은 아님 |
| DCA | 외부 납입 중립성, 가격 2배/절반 시 TWR·MDD, 7개 주기의 실제 납입 합계 | 기본 TWR·MDD와 7개 스케줄 합계는 통과. F03/F04/F10 |
| 리밸런싱 | 무수수료 가치 보존, 유수수료 체결 원장·비중·수수료의 동시 대사 | 무수수료 통과. F06. 여러 거래소 휴장 시 일부 자산만 재배분하는 정책은 명세 필요 |
| 통화 변환 | USD 및 지원하는 12개 비USD 통화의 환율 방향, 첫 유효 환율 이전 거래 거부, 기존 IANA DST 회귀 검사 | 이 날짜·방향 검사 통과. 장중 FX 시점은 별도 모델 과제 |
| 수익·위험 지표 | 단순 잔액 산술, 현금흐름 조정, -50% 낙폭·회복, 365일 연율화, 평탄 시세 손익 분류 | 기본 수익·현금흐름 조정 통과. F09/F10/F11 및 최초 비용 기준 |
| 시세·기업행위·캐시 | 실제 MySQL 저장 정밀도, 캐시 반환 조건, 조정 OHLC·DST 기존 검사 | F05/F14. 실시간 제공업체의 완전성·수정 내역은 별도 검증 필요 |
| 차트·매매 표시 | 실제 주간 집계, 벤치마크 날짜 병합 소스, 마커 콜백 실행 | F12/F13. 기존 TODO A-30의 장기 공백·휴장일 샘플링 문제도 남아 있음 |
| 입력·참고 자료 API | 금융 반례 9개, 거부 사례 5개, 4개 GET, 유효성 검증 소스 | 기본 거부·독립 조회 동작 확인. F15. 현금 DCA와 결과 불변식 검증 보강 필요 |
| CSV·텍스트 보고서 | 정상 결과 실제 생성, 금액 열 구조, null 결과 전달 | 정상 텍스트의 값 표기 확인. F16, 오버플로 결과의 다운로드 예외 |
| 뉴스 | 텍스트 정규화·필터 코드, 기존 단위 검사, 합성 환경 empty 응답, React 텍스트 렌더링 | 뉴스는 최신 자료로 계산과 분리됨. 실제 Naver 계정 응답·종목별 검색 관련성은 이번에 검증하지 않음 |
| 동시성·취소·인증·헬스 | admission 수명, 취소, trusted proxy, fail-closed 인증 기존 검사, liveness HTTP | 검사 통과. 운영 Turnstile 왕복·운영 네트워크 설정·공격 부하를 전면 보증하는 감사는 아님 |

## 수정 순서와 완료 기준

1. **F01/F02/F06:** 주문 시각과 체결·수수료 원장을 먼저 고친다. 다음 바가 없는 주문 미체결, 매수·매도 양쪽 비용, `현금 + 보유가치 = 전체 자산` 및 이벤트와 실제 체결 수량 일치를 독립 검사로 고정한다.
2. **F03/F04/F07:** 납입 달력·예산·자산 식별자를 바로잡는다. 입력 총액과 실제 납입액, 각 날짜까지 실제 유입된 현금, 개별 잔액 합계가 맞아야 한다.
3. **F05/F14:** 시세 정밀도와 수정주가 캐시의 일관성을 보장한다. 분할·배당으로 조정 기준이 바뀐 뒤 전체 재실행 결과가 과거 요청 구간 조합에 의존하지 않아야 한다.
4. **F08~F13/F16:** 지표 정의, 벤치마크 비교, 차트 버킷·매매 마커, 내보내기를 일치시킨다. F15의 합산·결과 유한성 방어도 추가한다.
5. 위 독립 정확성 기준을 충족한 버전에서 성능·메모리를 다시 측정한다. 계산 규칙이 달라지므로 예전 Python 결과를 무조건 기대값으로 유지하면 안 된다.

검토 종료 시 기존 Python/Rust 프론트엔드·백엔드 4개 비교 서비스는 계속 실행 중이다. 감사용 HTTP·DB 컨테이너는 종료했고 기존 DB의 내용·스키마·볼륨은 변경하지 않았다. 이번 추가 산출물은 감사 보고서, 재현 스크립트, 검증 증거다.
