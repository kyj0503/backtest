# 종합 분석: calculate_dca_portfolio_returns() 함수

## 개요

이 디렉토리에는 다음 위치의 `calculate_dca_portfolio_returns()` 함수에 대한 상세한 구조 분석이 포함되어 있습니다:

파일: `backtest_be_fast/app/services/portfolio_service.py`
라인: 86-709 (625줄)
함수 타입: DCA 및 리밸런싱을 포함한 포트폴리오 백테스팅용 비동기 메서드

## 분석 문서

### 1. REFACTORING_ANALYSIS.md (370줄)
다음을 다루는 종합 구조 분석:
- 7개 주요 논리 단계: Setup, initialization, main loop, result creation
- 루프 구조: 메인 날짜 루프 내 5개 중첩 루프
- 중첩 논리 블록: 복잡한 중첩 조건 식별
- 8개 추출 후보: 함수 명세, 입력, 출력, 라인 범위
- 시간 복잡도: O(n × m) (n = 거래일 수, m = 종목 수)

최적: 전체 구조 및 분해 전략 이해

---

### 2. EXTRACTION_CANDIDATES.md (379줄)
다음을 포함하는 8개 헬퍼 함수의 상세 명세:
- 추출 테이블: 8개 함수의 빠른 개요
- 상세 명세: 8개 헬퍼 각각에 대해:
  - 목적 및 책임
  - 타입이 포함된 입력 파라미터
  - 반환 타입 및 출력
  - 주요 구현 로직
  - 복잡도 분석
  - 의존성 및 부작용
- 주요 아키텍처 패턴: 가변 상태, 날짜 스케줄링, 폴백 로직
- 권장 추출 순서: 8단계 우선순위 계획

최적: 각 헬퍼 함수의 명세에 대한 심층 분석

---

### 3. FUNCTION_STRUCTURE_DIAGRAM.md (470줄)
다음을 포함하는 시각적 ASCII 표현:
- 전체 함수 플로우: 트리 구조를 가진 4단계 개요
- 메인 날짜 루프 분해: 일별 상세 7단계 처리
- 리밸런싱 로직: 가장 복잡한 블록의 6단계 상세 분해
- 루프 중첩 구조: 라인 번호가 포함된 완전한 중첩 분석
- 의존성 그래프: 어떤 헬퍼가 어떤 출력에 의존하는지
- 복잡도 비교: 리팩터링 전후 지표
- 주요 결정 지점: 실행 순서 제약 및 의존성

최적: 시각적 학습자 및 아키텍처 이해

---

### 4. EXTRACTION_QUICK_REFERENCE.txt (269줄)
다음을 포함하는 빠른 조회 가이드:
- 우선순위 순서의 8개 헬퍼: 각각의 한 줄 요약
- 7개 논리 단계: 상위 레벨 단계 개요
- 복잡도 지점: 어려운 부분의 위치
- 전후 비교: 품질 지표
- 실행 순서: 중요 의존성
- 다음 단계 체크리스트: 4단계 구현 계획

최적: 리팩터링 중 빠른 참조

---

## 빠른 요약

### 현재 상태
```
함수 크기:              625줄
순환 복잡도:            매우 높음 (10+)
최대 중첩 깊이:         4레벨
중첩 루프:              5개 루프 (O(n×m) 복잡도)
테스팅:                 통합 테스트만
재사용성:               없음
```

### 제안된 리팩터링
```
메인 함수:              약 150줄 (오케스트레이션만)
헬퍼 함수:              8개의 집중된 함수 (평균 53줄)
평균 복잡도:            3-4 (함수당)
최대 중첩 깊이:         2레벨
테스팅:                 8개 단위 테스트 + 1개 통합 테스트
재사용성:               각 헬퍼 독립적으로 테스트 가능
```

## 8개 헬퍼 함수

| # | 이름 | 줄 수 | 복잡도 | 추출 순서 |
|---|------|-------|--------|-----------|
| 1 | `initialize_portfolio_state()` | 23 | Low ✓ | 1번째 |
| 2 | `fetch_and_convert_prices()` | 47 | Medium | 3번째 |
| 3 | `detect_and_update_delisting()` | 38 | Medium | 6번째 |
| 4 | `calculate_adjusted_rebalance_weights()` | 31 | Low-Med ✓ | 2번째 |
| 5 | `execute_initial_purchases()` | 28 | Low-Med ✓ | 4번째 |
| 6 | `execute_periodic_dca_purchases()` | 62 | High | 7번째 |
| 7 | `execute_rebalancing_trades()` | 154 | Very High ⚠️ | 8번째 |
| 8 | `calculate_daily_metrics_and_history()` | 35 | Low-Med ✓ | 5번째 |

## 주요 발견 사항

### 주요 논리 단계
1. Setup & Initialization (76줄): 데이터 로드, 통화 준비
2. Variable Initialization (23줄): 추적 구조 초기화
3. Main Date Loop (470줄): 각 거래일에 대한 핵심 시뮬레이션
4. Result Creation (24줄): 출력 DataFrame 구축

### 가장 복잡한 블록
1. Rebalancing (154줄): 거래 실행, 수수료 적용, 이력 기록
2. Periodic DCA (62줄): Nth Weekday 로직을 사용한 스케줄 기반 매수
3. Price Conversion (47줄): 폴백을 포함한 다중 통화 변환

### 중요 의존성
- 가격 페칭은 모든 다른 일일 작업보다 먼저 실행되어야 함
- 상장폐지 감지는 가격 페칭에 의존
- 리밸런싱은 초기 및 정기 매수에 의존
- 일일 지표는 모든 이전 작업에 의존

## 이 문서 사용 방법

### 리팩터링용
1. FUNCTION_STRUCTURE_DIAGRAM.md로 시작하여 큰 그림 이해
2. REFACTORING_ANALYSIS.md를 읽고 섹션별 상세 분해 파악
3. EXTRACTION_CANDIDATES.md를 구현 명세로 사용
4. 코딩 중 EXTRACTION_QUICK_REFERENCE.txt를 가까이 두기

### 코드 리뷰용
1. EXTRACTION_QUICK_REFERENCE.txt에서 단계별 접근 확인
2. EXTRACTION_CANDIDATES.md에서 함수 계약 참조
3. FUNCTION_STRUCTURE_DIAGRAM.md로 정확성 검증

### 테스팅용
1. EXTRACTION_CANDIDATES.md를 테스트 명세로 사용
2. FUNCTION_STRUCTURE_DIAGRAM.md에서 모킹 설정을 위한 의존성 참조
3. EXTRACTION_QUICK_REFERENCE.txt에서 실행 순서 확인

## 구현 단계

### 1단계: 준비
- [ ] 모든 분석 문서 검토
- [ ] 잠재적 통합 지점 식별
- [ ] 테스트 스캐폴딩 설정

### 2단계: 추출 (권장 순서대로)
- [ ] Helper 1: `initialize_portfolio_state()`
- [ ] Helper 4: `calculate_adjusted_rebalance_weights()`
- [ ] Helper 2: `fetch_and_convert_prices()`
- [ ] Helper 5: `execute_initial_purchases()`
- [ ] Helper 8: `calculate_daily_metrics_and_history()`
- [ ] Helper 3: `detect_and_update_delisting()`
- [ ] Helper 6: `execute_periodic_dca_purchases()`
- [ ] Helper 7: `execute_rebalancing_trades()`

### 3단계: 테스팅 및 검증
- [ ] 추출된 각 헬퍼 단위 테스트
- [ ] 리팩터링된 메인 함수 통합 테스트
- [ ] 출력 DataFrame이 원본과 일치하는지 검증
- [ ] 성능 비교 (동일한 O(n×m)이어야 함)
- [ ] 코드 리뷰 및 승인

### 4단계: 배포
- [ ] 사용하지 않는 코드 제거
- [ ] 문서 업데이트
- [ ] 전체 테스트 스위트 실행
- [ ] 스테이징/프로덕션에 배포

## 주요 지표

### 복잡도 감소
- 순환 복잡도: 10+ → 함수당 3-4
- 함수 크기: 625줄 → 평균 53줄 (12배 감소)
- 최대 중첩: 4레벨 → 2레벨
- 코드 중복: 도입되지 않음

### 테스트 가능성 개선
- 단위 테스트 커버리지: 새로 추가 (0% → 100%)
- 통합 테스트: 유지
- 테스트 격리: 높음 (각 헬퍼 독립적으로 테스트 가능)

### 유지보수성 개선
- 가독성: 7개 명확한 단계 → 8개 명명된 함수
- 디버깅: 전체 함수 → 격리된 헬퍼
- 변경: 어느 지점이든 → 격리된 함수
- 재사용성: 없음 → 각 헬퍼 재사용 가능

## 파일 구조

```
/home/user/backtest/
├── README_ANALYSIS.md (이 파일)
├── REFACTORING_ANALYSIS.md (메인 분석)
├── EXTRACTION_CANDIDATES.md (명세)
├── FUNCTION_STRUCTURE_DIAGRAM.md (시각적 가이드)
├── EXTRACTION_QUICK_REFERENCE.txt (빠른 참조)
└── backtest_be_fast/
    └── app/services/
        └── portfolio_service.py (리팩터링할 함수)
```

## 코드베이스의 관련 파일

- Strategy Implementation: `backtest_be_fast/app/strategies/strategies.py`
- Backtest Engine: `backtest_be_fast/app/services/backtest_engine.py`
- Currency Converter: `backtest_be_fast/app/utils/currency_converter.py`
- Rebalance Helper: `backtest_be_fast/app/services/rebalance_helper.py`
- DCA Calculator: `backtest_be_fast/app/services/dca_calculator.py`

## 참고 사항 및 경고

⚠️ 중요 의존성:
- Helper 2, 3, 5는 엄격한 순서로 실행되어야 함 (prices → delisting → purchases)
- Helper 7 (rebalancing)은 여러 상태 딕셔너리에 복잡한 부작용을 가짐
- Helper 6 (periodic DCA)는 날짜 스케줄링 로직에 의존

✓ 권장 사항:
1. 권장 순서대로 헬퍼 추출 (EXTRACTION_QUICK_REFERENCE.txt 참조)
2. 추출 직후 각 헬퍼에 대한 단위 테스트 작성
3. 부작용을 줄이기 위해 가능한 곳에서 불변 데이터 구조 사용
4. 성능을 위해 통화 변환 승수 메모이제이션 고려

📝 유지보수:
- 코드 레이아웃이 변경되면 분석 문서의 라인 번호 업데이트
- 단계 설명을 구현과 동기화 유지
- 새 헬퍼나 통합된 단계 문서화

---

함수 위치: backtest_be_fast/app/services/portfolio_service.py
총 페이지: 약 1500줄의 분석 문서

질문이나 설명이 필요한 경우 상세 문서 또는 함수 자체의 소스 코드 주석을 참조하십시오.
