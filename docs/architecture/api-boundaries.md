# 계산 1개와 독립 조회 4개

2026-10-25. 계산 결과를 먼저 표시하고, 주가·환율·벤치마크·뉴스를 각각 조회·재시도한다.
한 조회의 지연·실패가 다른 조회의 표시나 이미 완료한 계산을 막지 않는다.
FastAPI 서버·DB는 그대로 사용하며 새 서비스나 영속 큐를 추가하지 않는다.

| API | 요청 | 반환하는 data 필드 |
|---|---|---|
| `POST /api/v1/backtest` | 기존 포트폴리오·기간·전략·수수료 | 계산 결과. 기존 include 옵션에 따른 통합 응답도 지원 |
| `GET /api/v1/prices` | symbols, start_date, end_date | ticker_info, stock_data, volatility_events |
| `GET /api/v1/exchange-rates` | start_date, end_date | exchange_rates, exchange_stats |
| `GET /api/v1/benchmarks` | start_date, end_date | sp500_benchmark, nasdaq_benchmark, sp500_total_return_pct |
| `GET /api/v1/news` | symbols, limit(선택) | latest_news |

## 요청·응답 계약

기존 계산 POST 본문·응답 필드와 다섯 `include_*` 기본값(true)은 유지한다. 콘솔은
다섯 옵션을 모두 false로 보내 계산만 받는다. 계산에 필요한 상장일 검사 등은 유지하고,
별도 참고 자료 수집은 생략한다. 참고 필드는 빈 값·기본 메타데이터, 상태는 skipped다.

네 GET 모두 `{status: "success", data: {...}}` 형태이며, 해당 자료에 속한
`supplemental_status`만 함께 반환한다. 상태는 ok/empty/skipped/timeout/error다.
뉴스가 실패한 사실을 다른 세 응답이 덮어쓸 수 없다. 계산 결과 필드는 GET에 없다.

```text
GET /api/v1/prices?symbols=AAPL&symbols=MSFT&start_date=2023-01-01&end_date=2023-12-31
GET /api/v1/exchange-rates?start_date=2023-01-01&end_date=2023-12-31
GET /api/v1/benchmarks?start_date=2023-01-01&end_date=2023-12-31
GET /api/v1/news?symbols=AAPL&symbols=MSFT&limit=15
```

prices/news의 symbols는 필수이며 반복 파라미터를 쓴다. 입력 최대 20개를 검증한 뒤
대문자화·중복 제거한다. 주식 입력과 같은 심볼 형식 제한을 적용한다.
기간 조회의 시작일·종료일은 필수이며 역전·미래 종료일·3,650일 초과를 거부한다.
뉴스는 백테스트 기간과 무관한 최신 뉴스다. 날짜 파라미터를 받지 않고 limit은
종목당 1~20개, 기본 15개다. 지원하지 않는 파라미터도 외부 I/O 전에 422로 거부한다.
환율·벤치마크는 symbols를 받지 않는다.

주가와 급등락 이벤트는 같은 시세를 한 번 조회해 공유한다. 환율·벤치마크·뉴스는
종목 메타데이터를 조회하지 않는다. 기존 캐시·수집·직렬화 코드를 재사용하며 계산식은
바꾸지 않는다. 벤치마크 자료가 부족하면 sp500_total_return_pct는 null이다.

## 실행 상한과 취소

- 계산: 기존 컨테이너 전체 8건, IP별 2건, 대기 30초 + 실행 60초.
- 조회: **네 API 합산** 전체 기본 4건, IP별 4건. 대기 2초 + 실행 20초.
  기본 수집 예산은 각 조회 15초다. 조회 종류마다 전체 풀을 새로 만들지 않는다.
- 전체 조회 상한은 `MAX_CONCURRENT_MARKET_DATA`, 대기·실행 시간은
  `MARKET_DATA_QUEUE_TIMEOUT_SECONDS`, `MARKET_DATA_TIMEOUT_SECONDS`로 조정한다.
  이전 환경 파일에 상한 2를 명시했다면 새 네 요청 흐름에 맞게 검토한다.
- IP 한도 초과 429, 전체 슬롯 대기 초과 503, 실행 초과 504는 detail과 Retry-After를 반환한다.
- 기존 파일 슬롯·협력적 취소 실행기를 재사용한다. 뉴스 루프는 취소 후 다음 종목을
  시작하거나 뒤늦게 캐시에 쓰지 않는다. 이미 진행 중인 동기 외부 호출은 라이브러리
  타임아웃까지 기다릴 수 있다.

콘솔은 요청별 AbortController를 사용한다. 특정 조회 재시도는 그 조회만 다시 실행하고,
새 계산·화면 이탈·초기화는 이전 계산과 모든 조회를 취소한다. 늦은 응답은 새 결과를
덮어쓸 수 없다. 조회별 로딩·오류·빈 결과 상태는 서로 독립적이다.

## 호환성과 배포

이 변경은 앞서 추가한 **GET /api/v1/market-data를 네 GET으로 대체**한다.
기존 계산 POST 호출자는 그대로 사용할 수 있지만 옛 콘솔의 통합 GET 호출은 호환되지 않는다.
운영 전환 시 두 저장소의 릴리스를 함께 계획해야 하며, 이전 탭은 새로고침해야 한다.
배포 중 옛 콘솔까지 계속 지원해야 한다면 운영 반영 전에 임시 호환 경로를 준비한다.
현재 프록시는 `/api/v1/` 전체를 전달하므로 경로별 Nginx 수정은 필요하지 않다.

## 검증

Docker 단위 검증은 기존 POST 스냅샷을 유지하면서 네 조회의 입력·응답 범위,
같은 IP의 네 동시 요청, 네 API의 공유 실행 상한, 뉴스 취소를 확인한다.
콘솔은 병렬 응답 병합·느린 뉴스 중 다른 자료 표시·각 API의 개별 재시도·잘못된
응답 형식·오래된 응답 차단·화면 이탈 취소·현금 포트폴리오의 불필요한 조회 생략을 검증한다.

실행 이미지 HTTP 검증 스크립트는 격리 MySQL에 미리 넣은 합성 AAPL 시세(2023년
200거래일 이상)와 현재 시각의 합성 뉴스 캐시를 사용한다. 운영 자격증명이나 실제 데이터는
필요하지 않다. DB에 시드하는 스크립트가 아니라 준비된 로컬 테스트 서버에 요청하는 검사다.

```bash
python backtest_be_fast/tests/integration/verify_reference_reads_http.py --base-url http://127.0.0.1:18080
```

브라우저에서는 네 조회만 503으로 실패시킨 뒤 하나씩 복구·재시도한다. 각 GET만 1회
늘고 계산 POST와 다른 GET의 호출 수가 같아야 한다. 자세한 콘솔 흐름은
[프론트엔드 문서](https://github.com/kyj0503/backtest-console/blob/dev/docs/api-data-flow.md)를 참조한다.

작업은 여전히 HTTP 연결에 묶여 있다. 작업 ID·영속 대기열·재시작 후 복구는 제공하지 않는다.
