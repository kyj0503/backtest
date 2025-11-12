# 추출 요약 테이블: 8개 헬퍼 함수

주의: 이 문서는 리팩터링 전 분석 문서이며, 라인 번호는 과거의 625줄 함수 상태를 기준으로 합니다. 현재 코드는 이미 리팩터링되어 8개 헬퍼 함수로 분리되었습니다.

| # | 함수명 | 줄 수 (리팩터링 전) | 책임 | 입력 | 반환 타입 | 복잡도 |
|---|---|---|---|---|---|---|
| 1 | `initialize_portfolio_state()` | 191-213 (23) | 모든 추적 변수 및 상태 컨테이너 초기화 | `stock_amounts: Dict`, `cash_amount: float`, `amounts: Dict` | `Dict[str, Any]` | Low ✓ |
| 2 | `fetch_and_convert_prices()` | 222-268 (47) | 데이터에서 가격 추출 및 환율을 사용하여 USD로 변환 | `current_date`, `stock_amounts`, `portfolio_data`, `dca_info`, `ticker_currencies`, `exchange_rates_by_currency` | `Tuple[Dict[str, float], Dict[str, float]]` | Medium |
| 3 | `detect_and_update_delisting()` | 270-307 (38) | 상장폐지된 종목 감지 (30일 이상 가격 없음) 및 상태 업데이트 | `current_date`, `stock_amounts`, `current_prices`, `dca_info`, `delisted_stocks` (set), `last_valid_prices` (dict), `last_price_date` (dict) | `None` (부작용) | Medium |
| 4 | `calculate_adjusted_rebalance_weights()` | 428-458 (31) | 상장폐지된 종목에 대한 목표 비중 조정 (비례 재분배) | `target_weights: Dict`, `delisted_stocks: Set`, `dca_info: Dict` | `Dict[str, float]` | Low-Medium ✓ |
| 5 | `execute_initial_purchases()` | 310-337 (28) | 첫날 매수 실행 (lump_sum 또는 DCA 초기) | `current_date`, `stock_amounts`, `current_prices`, `dca_info`, `shares` (dict), `commission: float` | `Tuple[int, float]` (trades, cash_inflow) | Low-Medium ✓ |
| 6 | `execute_periodic_dca_purchases()` | 341-402 (62) | N번째 요일 스케줄에 따른 정기 DCA 매수 실행 | `current_date`, `prev_date`, `stock_amounts`, `current_prices`, `dca_info` (수정됨), `shares` (dict), `commission`, `start_date_obj` | `Tuple[int, float]` (trades, cash_inflow) | High |
| 7 | `execute_rebalancing_trades()` | 495-648 (154) | 리밸런싱 거래 실행, 수수료 적용, 이력 추적 | `current_date`, `adjusted_target_weights`, `shares` (수정됨), `current_prices`, `available_cash` (수정됨), `cash_holdings` (수정됨), `cash_amounts`, `commission`, `total_stock_value`, `dca_info`, `delisted_stocks` | `Dict[str, Any]` (trades, history, weights) | Very High ⚠️ |
| 8 | `calculate_daily_metrics_and_history()` | 650-684 (35) | 일일 포트폴리오 가치, 일일 수익률, 비중 이력 계산 | `current_date`, `shares`, `available_cash`, `current_prices`, `cash_holdings`, `prev_portfolio_value`, `daily_cash_inflow`, `total_amount`, `dca_info` | `Tuple[float, float, Dict]` (value, return, weights) | Low-Medium ✓ |

---

## 상세 명세

### 함수 1: initialize_portfolio_state()
```
목적: 모든 추적 변수 설정
라인: 191-213 (23줄)

입력:
  - stock_amounts: Dict[str, float]
  - cash_amount: float
  - amounts: Dict[str, float]

출력 Dict 포함:
  - shares: Dict[str, float] = {}
  - portfolio_values: List[float] = []
  - daily_returns: List[float] = []
  - prev_portfolio_value: float = 0
  - prev_date: Optional[pd.Timestamp] = None
  - is_first_day: bool = True
  - available_cash: float = cash_amount
  - cash_holdings: Dict[str, float]
  - total_trades: int = 0
  - rebalance_history: List[Dict] = []
  - weight_history: List[Dict] = []
  - last_rebalance_date: Optional[pd.Timestamp] = None
  - original_rebalance_nth: Optional[int] = None
  - last_valid_prices: Dict[str, float] = {}
  - last_price_date: Dict[str, date] = {}
  - delisted_stocks: Set[str] = set()

복잡도: O(m) (m = unique_keys 수)
테스팅: 단위 테스트 간단함 (부작용 없음)
```

---

### 함수 2: fetch_and_convert_prices()
```
목적: portfolio_data에서 가격 추출 및 USD로 변환
라인: 222-268 (47줄)

입력:
  - current_date: pd.Timestamp
  - stock_amounts: Dict[str, float]
  - portfolio_data: Dict[str, pd.DataFrame]  (symbol -> OHLC)
  - dca_info: Dict[str, Dict]  (unique_key -> investment info)
  - ticker_currencies: Dict[str, str]  (unique_key -> currency code)
  - exchange_rates_by_currency: Dict[str, Dict[date, float]]

출력:
  - current_prices: Dict[str, float]  (unique_key -> USD price)
  - last_valid_exchange_rates: Dict[str, float]  (currency -> rate, 폴백용 캐시)

주요 로직:
  1. stock_amounts의 각 종목에 대해:
     - portfolio_data에서 current_date <= 가장 최근 가격 가져오기
     - currency == 'USD'인 경우: raw_price를 그대로 사용
     - 그 외: exchange_rate 조회, 누락 시 폴백 캐시 사용
     - currency_converter.get_conversion_multiplier() 적용
     - 환율 누락 처리 (종목 건너뛰기/계속)

복잡도: O(m) (m = 종목 수)
테스팅: exchange_rates 및 portfolio_data 모킹 가능
비동기: 아니오 (순수 계산 및 딕셔너리 조회)
```

---

### 함수 3: detect_and_update_delisting()
```
목적: 장기간 가격 부재 종목 추적 및 상장폐지로 표시
라인: 270-307 (38줄)

입력:
  - current_date: pd.Timestamp
  - stock_amounts: Dict[str, float]
  - current_prices: Dict[str, float]  (오늘 가격이 있는 종목)
  - dca_info: Dict[str, Dict]  (symbol 조회용)
  - delisted_stocks: Set[str]  (수정됨 - 상장폐지로 표시된 종목)
  - last_valid_prices: Dict[str, float]  (수정됨 - current_prices로부터 업데이트)
  - last_price_date: Dict[str, date]  (수정됨 - current_date로부터 업데이트)

출력: None (입력 컬렉션에 대한 부작용)

주요 로직:
  1. 오늘 가격이 있는 종목에 대해:
     - last_valid_prices, last_price_date 업데이트
     - 이전에 표시된 경우 delisted_stocks에서 제거
  2. 오늘 가격이 없는 종목에 대해:
     - days_without_price >= DELISTING_THRESHOLD_DAYS (30) 확인
     - 예인 경우 AND 이미 상장폐지되지 않음: delisted_stocks에 추가
  3. 루프 후: 평가를 위해 current_prices에서 상장폐지 가격 유지

복잡도: O(m) (m = 종목 수)
테스팅: current_prices 모킹, 날짜 조작 가능
부작용: 예 (sets/dicts를 제자리에서 수정)
```

---

### 함수 4: calculate_adjusted_rebalance_weights()
```
목적: 일부 종목이 상장폐지될 때 목표 비중 조정
라인: 428-458 (31줄)

입력:
  - target_weights: Dict[str, float]  (원래 계획된 배분)
  - delisted_stocks: Set[str]  (거래할 수 없는 종목)
  - dca_info: Dict[str, Dict]  (symbol 이름 로깅용)

출력:
  - adjusted_target_weights: Dict[str, float]

주요 로직:
  1. 상장폐지 종목이 없으면: target_weights 복사본 반환
  2. 그 외:
     - delisted_weight_sum = 상장폐지 종목 비중의 합 계산
     - tradeable_weight_sum = 1.0 - delisted_weight_sum 계산
     - scaling_factor = 1.0 / tradeable_weight_sum 계산
     - 각 종목에 대해:
       * 상장폐지된 경우: weight = 0.0
       * 그 외: weight *= scaling_factor  (비례 증가)
  3. 예제:
     * 원래: A=30%, B=30%, C=40%
     * C가 상장폐지된 경우: A'=30%/(30%+30%)=50%, B'=50%, C'=0%

복잡도: O(m) (m = 종목 수)
테스팅: 순수 함수, 예제로 테스트 쉬움
부작용: 없음 (새 dict 반환)
의존성: logging만
```

---

### 함수 5: execute_initial_purchases()
```
목적: 첫날 종목 매수 실행 (lump_sum 또는 DCA 초기)
라인: 310-337 (28줄)

입력:
  - current_date: pd.Timestamp
  - stock_amounts: Dict[str, float]  (종목당 총 투자 금액)
  - current_prices: Dict[str, float]  (unique_key별 USD 가격)
  - dca_info: Dict[str, Dict]  (investment_type, monthly_amount 포함)
  - shares: Dict[str, float]  (수정됨 - 매수한 주식으로 업데이트)
  - commission: float  (예: 0.002 = 0.2%)

출력:
  - trades_executed: int
  - daily_cash_inflow: float

주요 로직:
  1. stock_amounts의 각 종목에 대해:
     - 가격을 사용할 수 없으면 건너뛰기
     - investment_type == 'lump_sum'인 경우:
       * invest_amount = amount * (1 - commission)
       * shares[unique_key] = invest_amount / price
     - 그 외 (DCA):
       * invest_amount = monthly_amount * (1 - commission)
       * shares[unique_key] = invest_amount / price
     - trades_executed 증가
     - daily_cash_inflow에 추가

복잡도: O(m) (m = 종목 수)
테스팅: current_prices, dca_info 모킹 가능
부작용: 예 (shares dict 수정)
```

---

### 함수 6: execute_periodic_dca_purchases()
```
목적: 스케줄에 따른 정기 DCA 투자 실행
라인: 341-402 (62줄)

입력:
  - current_date: pd.Timestamp
  - prev_date: pd.Timestamp
  - stock_amounts: Dict[str, float]
  - current_prices: Dict[str, float]
  - dca_info: Dict[str, Dict]  (수정됨 - executed_count, last_dca_date)
  - shares: Dict[str, float]  (수정됨 - 누적 주식)
  - commission: float
  - start_date_obj: datetime

출력:
  - trades_executed: int
  - daily_cash_inflow: float

주요 로직:
  1. investment_type == 'dca'인 각 종목에 대해:
     - 첫 실행 시 original_nth_weekday 초기화
     - get_next_nth_weekday()를 사용하여 next_dca_date 계산
     - 확인: current_date >= next_dca_date AND prev_date < next_dca_date?
       * 예 AND executed_count < dca_periods인 경우:
         * price = current_prices[symbol]
         * invest_amount = monthly_amount * (1 - commission)
         * shares[symbol] += invest_amount / price
         * dca_info[symbol] 업데이트:
           - executed_count += 1
           - last_dca_date = current_date
         * trades_executed 증가

복잡도: O(m) (m = 종목 수)
테스팅: 날짜 및 get_next_nth_weekday() 모킹 필요
부작용: 예 (dca_info, shares 수정)
의존성: get_next_nth_weekday(), get_weekday_occurrence(), FREQUENCY_MAP
```

---

### 함수 7: execute_rebalancing_trades()
```
목적: 리밸런싱 거래 실행 및 이력 기록
라인: 495-648 (154줄) [가장 크고 복잡함]

입력:
  - current_date: pd.Timestamp
  - adjusted_target_weights: Dict[str, float]
  - shares: Dict[str, float]  (수정됨)
  - current_prices: Dict[str, float]
  - available_cash: float  (수정됨)
  - cash_holdings: Dict[str, float]  (수정됨)
  - cash_amounts: Dict[str, float]  (참조용)
  - commission: float
  - total_stock_value: float  (사전 계산됨)
  - dca_info: Dict[str, Dict]  (asset_type, symbol 조회용)
  - delisted_stocks: Set[str]  (거래에서 이것들 건너뛰기)

출력 Dict:
  - trades_executed: int
  - rebalance_trades: List[Dict]  (이력용 거래 기록)
  - weights_before: Dict[str, float]  (리밸런싱 전 배분)
  - weights_after: Dict[str, float]  (리밸런싱 후 배분)
  - commission_cost: float  (총 비용)

주요 로직:
  1. 현재 주식 및 현금으로부터 weights_before 계산
  2. adjusted_target_weights의 각 (unique_key, target_weight)에 대해:
     - target_value = total_portfolio_value * target_weight
     - asset_type == 'cash'인 경우:
       * cash_holdings[unique_key]를 target_value로 조정
       * 차이가 임계값을 초과하면 거래 추적
     - 그 외:
       * 상장폐지된 경우: 건너뛰기 (현재 보유 유지)
       * 그 외:
         * 필요한 shares_diff 계산
         * BUY/SELL 거래 기록
         * 수수료 적용
  3. 모든 거래 후:
     - 수수료 스케일링 적용: shares *= (1 - total_commission_cost/total_value)
  4. weights_after 계산
  5. rebalance_history에 기록

복잡도: O(m²) 최악의 경우 (m 반복 × m 상장폐지 확인)
테스팅: 매우 어려움 - 많은 의존성, 부작용
부작용: 예 (shares, cash_holdings, available_cash, history lists 수정)
⚠️ 치명적: 이 함수는 가장 복잡한 로직 포함
```

---

### 함수 8: calculate_daily_metrics_and_history()
```
목적: 일일 포트폴리오 지표 및 이력 계산
라인: 650-684 (35줄)

입력:
  - current_date: pd.Timestamp
  - shares: Dict[str, float]  (현재 보유)
  - available_cash: float
  - current_prices: Dict[str, float]
  - cash_holdings: Dict[str, float]
  - prev_portfolio_value: float
  - daily_cash_inflow: float  (DCA + 리밸런싱 유입)
  - total_amount: float  (초기 투자)
  - dca_info: Dict[str, Dict]  (symbol 조회용)

출력 Tuple:
  - current_portfolio_value: float  (total_amount로 정규화됨)
  - daily_return: float  (백분율 변화)
  - current_weights: Dict[str, float]  (symbol별 배분)

주요 로직:
  1. current_portfolio_value 계산:
     - sum(shares[key] * current_prices[key]) + available_cash
  2. daily_return 계산:
     - prev_portfolio_value > 0인 경우:
       * net_change = current_value - prev_value - daily_cash_inflow
       * daily_return = net_change / prev_value
     - 그 외: daily_return = 0.0
  3. current_weights 계산:
     - 각 종목에 대해: weight = (shares * price) / current_portfolio_value
     - 각 현금에 대해: weight = amount / current_portfolio_value
     - 중복 symbol 처리 (비중 합산)
  4. 정규화된 portfolio_value 반환 (total_amount로 나누기)

복잡도: O(m) (m = 자산 수)
테스팅: 단위 테스트 간단함
부작용: 없음 (순수 계산)
의존성: symbol 조회를 위한 dca_info
```

---

## 주요 아키텍처 패턴

### 1. 가변 상태 패턴
여러 함수가 입력 딕셔너리/셋을 제자리에서 수정:
- `detect_and_update_delisting()`: delisted_stocks, last_valid_prices 수정
- `execute_initial_purchases()`: shares 수정
- `execute_periodic_dca_purchases()`: dca_info, shares 수정
- `execute_rebalancing_trades()`: shares, cash_holdings, available_cash 수정

권장 사항: 명확성을 위해 불변 데이터 구조 사용 또는 새 dict 반환 고려.

### 2. 날짜 기반 스케줄링
- `execute_periodic_dca_purchases()`는 N번째 요일 로직 사용
- `detect_and_update_delisting()`는 일수 계산 사용
- 의존성: `get_next_nth_weekday()`, `get_weekday_occurrence()`, `FREQUENCY_MAP`

### 3. 폴백 로직
- `fetch_and_convert_prices()`는 폴백 환율 캐시 보유
- `detect_and_update_delisting()`는 last_valid_prices를 폴백으로 사용

### 4. 임계값 기반 결정
- 상장폐지: 30일 이상 가격 없음 (DELISTING_THRESHOLD_DAYS)
- 리밸런싱 거래: 0.01% 이상 차이 (REBALANCING_THRESHOLD_PCT)

---

## 권장 추출 순서

최소 복잡도 및 최대 독립 테스트 가능성을 위해:

1. `initialize_portfolio_state()` ✓ 순수 설정, 의존성 없음
2. `calculate_adjusted_rebalance_weights()` ✓ 순수 함수, 단일 책임
3. `fetch_and_convert_prices()` 중간 복잡도, 의존성 적음
4. `execute_initial_purchases()` shares 수정하지만 간단한 로직
5. `calculate_daily_metrics_and_history()` 순수 계산, 안정적
6. `detect_and_update_delisting()` 부작용 있지만 격리된 로직
7. `execute_periodic_dca_purchases()` 높은 복잡도, 날짜 스케줄링
8. `execute_rebalancing_trades()` ⚠️ 마지막에 추출 (가장 복잡, 많은 의존성)

---

## 리팩터링 영향 분석

### 코드 품질 개선
- 순환 복잡도: 625줄 함수 → 8개 집중된 함수 (평균 78줄)
- 테스트 커버리지: 단일 통합 테스트 → 8개 단위 테스트 + 1개 통합 테스트
- 가독성: 높은 중첩 코드 → 명확한 함수명으로 의도 문서화
- 유지보수성: 단일 변경 지점 → 격리된 타겟 수정

### 성능 고려사항
- 변화 없음: 모든 연산은 O(n*m)으로 유지 (days × stocks)
- 잠재적 개선: 통화 변환 승수 메모이제이션
- 잠재적 개선: 비중 계산 벡터화

### 비동기/스레딩 고려사항
- 현재: `fetch_and_convert_prices()`는 동기 (순수 계산)
- 최적화: 종목별 통화 변환 병렬화 가능
- 위험: 정확성을 위해 원자적 트랜잭션 경계 유지 필요
