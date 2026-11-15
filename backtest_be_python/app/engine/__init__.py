"""포트폴리오 백테스트 계산 엔진 (Go 백엔드 backtest_be_go/internal/engine 이식).

계산 계약(rust-migration 정합성 수정 F01–F16, R01–R11, S01–S06, T01–T05)과 응답 스키마·키 순서는
운영 기준인 Go 구현과 같다. docs/go-migration.md "계산 계약" 참고.

구성:
- civil: 시간대 없는 달력 날짜(proleptic ordinal 정수)
- schedule: 적립·리밸런싱 예정일(N번째 요일)
- marketdata: 일봉·시세 묶음, 환율(RateOn), OHLC 검사, 고정 시세(fixture)
- request: 요청 모델과 업무 규칙 검증
- strategy: 기술 지표와 바 단위 체결 엔진
- buyhold / technical / stats: 계산
- response: 응답 dict(키 순서 포함)
- source: 시세 조회(메모리 캐시 → 고정 시세 또는 DB·Yahoo)
- supplemental: POST include_* 부가 데이터
- service: POST /api/v1/backtest 진입점
"""
