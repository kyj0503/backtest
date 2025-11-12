# 중복 데이터 로딩 함수 분석 - 전체 보고서

## 개요

이 디렉토리는 Phase 2.2 리팩터링 중 백엔드 코드베이스에서 발견된 6개 중복/중첩 데이터 로딩 함수에 대한 종합 분석을 포함합니다.

## 주요 발견사항

요약:
- DB 우선, yfinance 폴백 패턴을 가진 6개 함수
- 약 360줄의 데이터 로딩 코드
- 약 189줄 (52%)의 중복 코드
- ChartDataService._get_price_data()에서 1개 치명적 버그 발견
- 통합 시 40-50% 코드 감소 가능

---

## 6개 중복 함수

| # | 함수 | 파일 | 라인 | 타입 | 상태 |
|---|----------|------|-------|------|--------|
| 1 | `DataService.get_ticker_data()` | data_service.py | 57-100 | Async | #2와 중복 |
| 2 | `DataService.get_ticker_data_sync()` | data_service.py | 102-135 | Sync | #1과 중복 |
| 3 | `BacktestEngine._get_price_data()` | backtest_engine.py | 169-187 | Async | #4와 유사 ✓ |
| 4 | `ChartDataService._get_price_data()` | chart_data_service.py | 200-214 | Async | 🔴 치명적 버그 |
| 5 | `YFinanceDataRepository.get_stock_data()` | data_repository.py | 106-151 | Async | 가장 정교함 |
| 6 | `yfinance_db._load_ticker_data_internal()` | yfinance_db.py | 767-813 | Sync | 핵심 구현 |

---

## 발견된 치명적 버그

함수 4: ChartDataService._get_price_data() (Line 205)

문제: async 컨텍스트에서 동기 I/O 호출에 대한 `asyncio.to_thread()` 래퍼 누락

영향: 첫 차트 생성 시 레이스 컨디션 및 데이터 손상 유발 가능

심각도: 🔴 치명적

수정: 동기 호출을 `asyncio.to_thread()`로 래핑하는 코드 1줄 추가

수정 소요 시간: 5분

---

## 권장 조치사항

### Priority 1: 치명적 (즉시)
- 수정: ChartDataService._get_price_data() async/sync 경계 버그
- 파일: app/services/chart_data_service.py, Line 205
- 시간: 5분
- 영향: 레이스 컨디션 방지

### Priority 2: 높음 (Phase 2.8)
- 통합: DataService.get_ticker_data() 및 get_ticker_data_sync()
- 감소: 76줄에서 약 40줄로 (47% 감소)
- 시간: 1일
- 영향: async/sync 중복 제거

### Priority 3: 중간 (Phase 2.9)
- 리팩터링: BacktestEngine 및 ChartDataService가 통합 서비스 사용
- 통합: YFinanceDataRepository를 캐시 레이어로 사용
- 시간: 2-3일
- 영향: 모든 데이터 로딩 로직 통합, 총 40-50% 감소

### Priority 4: 낮음 (장기 정리)
- 폐기: 구형 함수
- 문서화: 마이그레이션 가이드
- 일정: 1-2 릴리스 사이클

---

## 코드 지표

### 중복 분석

| 카테고리 | 줄 수 | 발생 횟수 | 총합 |
|----------|-------|-------------|-------|
| DB 우선 전략 | ~25 | 4x | 100 |
| yfinance 폴백 | ~15 | 3x | 45 |
| 에러 핸들링 | ~8 | 3x | 24 |
| 날짜 정규화 | ~10 | 2x | 20 |
| 총 중복 | | | 189 |

### 고유 코드 (중복되지 않음)

| 기능 | 줄 수 | 위치 |
|---------|-------|----------|
| 3계층 캐싱 | ~40 | YFinanceDataRepository |
| 재시도 로직 | ~50 | yfinance_db.load_ticker_data() |
| 연결 관리 | ~30 | yfinance_db helpers |
| 총 고유 | | 120 |

### 총계
- 총 데이터 로딩 코드: 약 360줄
- 중복: 52%
- 고유: 48%
- 잠재적 절감: 140-180줄 (40-50%)

---

## 영향받는 파일

| 파일 | 함수 | 조치 |
|------|-----------|--------|
| app/services/data_service.py | #1, #2 | 통합 (P1) |
| app/services/backtest_engine.py | #3 사용 | 리팩터링 (P3) |
| app/services/chart_data_service.py | #4 사용 | 버그 수정 (P0) + 리팩터링 (P3) |
| app/repositories/data_repository.py | #5 | 통합 (P3) |
| app/services/yfinance_db.py | #6 | 핵심 유지 (P3) |
| app/services/unified_data_service.py | 호출자 | 업데이트 (P3) |

---

## 통합 전략

### 옵션 1: 공격적 (최대 감소)
- 단일 통합 DataLoadingService 생성
- 6개 함수 모두 병합
- 약 180줄 감소 (50%)
- 위험: 중간 | 시간: 3-5일

### 옵션 2: 중간 (권장)
- DataService async/sync 버전 통합
- ChartDataService 버그 수정
- Repository를 캐시 레이어로 유지
- 약 90줄 감소 (25-30%)
- 위험: 낮음 | 시간: 1-2일

### 옵션 3: 최소 (빠른 수정)
- ChartDataService 버그만 수정
- 나머지 모두 유지
- 감소: 0줄 (버그 수정만)
- 위험: 최소 | 시간: 1일 미만

권장사항: 옵션 2 (중간 통합)

---

## 수정 후 테스팅

1. 각 데이터 로딩 함수에 대한 단위 테스트
2. 백테스트 실행에 대한 통합 테스트
3. 차트 생성 테스트 (특히 버그 수정용)
4. 여러 종목이 있는 포트폴리오 백테스트 테스트
5. 캐시 히트/미스 시나리오 테스트
6. 네트워크 장애가 있는 재시도 로직
7. async/sync 경계 준수 검증
8. 연결 풀링에 대한 동시 로드 테스트

---

## 관련 문서

- CLAUDE.md: 치명적 async/sync 경계 관리 규칙
- backtest_be_fast/docs/troubleshooting/race_condition.md: 레이스 컨디션 분석
- Phase 2.x 커밋 메시지: 과거 리팩터링 컨텍스트
