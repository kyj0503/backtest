# Nth Weekday 엣지 케이스 분석 및 해결 방안

## 문제 상황

### 케이스 1: N번째 요일이 존재하지 않는 경우

**시나리오:**
- 사용자가 "매월 5번째 금요일에 투자"를 선택
- 하지만 어떤 달은 5번째 금요일이 없음 (예: 2024년 2월)

**현재 동작:**
```python
# 2024년 2월에 5번째 금요일 요청
day = get_nth_weekday_of_month(2024, 2, 4, 5)
# 결과: 23 (4번째 금요일)

# 다음 달 계산 시 "몇 번째 주" 재계산
week_of_month = (23 - 1) // 7 + 1  # = 4
# 이제 4번째 금요일로 고정됨!
```

**문제점:**
- 원래 5번째 금요일로 시작했지만, 없는 달을 거치면서 4번째로 영구 변경됨
- 일관성 없음: 사용자가 선택한 "5번째"가 "4번째"로 바뀜

### 케이스 2: "몇 번째 주" 계산의 모호성

**현재 계산 방식:**
```python
week_of_month = (day_of_month - 1) // 7 + 1

# 예시:
# 1~7일: 1번째 주
# 8~14일: 2번째 주
# 15~21일: 3번째 주
# 22~28일: 4번째 주
# 29~31일: 5번째 주
```

**문제점:**
- 1월 26일: 4번째 금요일이지만 계산상 4번째 주
- 하지만 실제로는 1월 26일이 1월의 **마지막** 금요일일 수 있음
- 5번째 주로 계산될 수도 있음 (29~31일 범위)

## 해결 방안

### 방안 1: 원본 N 값 유지 (권장 ⭐)

**개념:**
- 시작 날짜의 "몇 번째 요일"을 기억하고 계속 사용
- 없는 달에서는 해당 월의 마지막 해당 요일 사용
- 다음 달에 다시 있으면 원래 N으로 복귀

**장점:**
- 일관성: 사용자가 선택한 N번째 유지
- 예측 가능: 5번째로 시작하면 계속 5번째 시도
- 금융권 표준과 일치

**단점:**
- 구현 복잡도 약간 증가 (N 값 추적 필요)

**구현 방법:**

```python
def get_next_nth_weekday(
    current_date: datetime, 
    period_type: str, 
    interval: int,
    original_nth: int = None  # 원본 N 값
) -> datetime:
    """
    다음 Nth Weekday 날짜 계산 (원본 N 값 유지)
    """
    if period_type == 'weekly':
        return current_date + timedelta(weeks=interval)
    
    elif period_type == 'monthly':
        weekday = current_date.weekday()
        
        # 원본 N 값이 없으면 현재 날짜에서 계산
        if original_nth is None:
            original_nth = get_weekday_occurrence(current_date)
        
        # interval개월 후 계산
        target_year = current_date.year
        target_month = current_date.month + interval
        
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # 원본 N번째 요일 시도
        target_day = get_nth_weekday_of_month(
            target_year, target_month, weekday, original_nth
        )
        
        return datetime(target_year, target_month, target_day)


def get_weekday_occurrence(date: datetime) -> int:
    """
    날짜가 해당 월의 몇 번째 요일인지 정확히 계산
    
    Returns:
        1-5: 몇 번째 해당 요일인지
    """
    weekday = date.weekday()
    year, month = date.year, date.month
    
    occurrence = 0
    for day in range(1, date.day + 1):
        if datetime(year, month, day).weekday() == weekday:
            occurrence += 1
    
    return occurrence
```

**DCA 정보 구조 변경:**

```python
dca_info[symbol] = {
    'symbol': symbol,
    'investment_type': investment_type,
    'dca_frequency': dca_frequency,
    'dca_periods': dca_periods,
    'monthly_amount': per_period_amount,
    'asset_type': asset_type,
    'executed_count': 0,
    'last_dca_date': None,
    'original_nth_weekday': None  # ✨ 추가: 원본 N번째 값 추적
}
```

### 방안 2: 월말 기준 사용 (대안)

**개념:**
- "마지막 금요일", "마지막에서 2번째 수요일" 같은 월말 기준 사용
- 모든 달에 항상 존재

**장점:**
- 항상 일관성 있음
- "5번째 금요일" 대신 "마지막 금요일" 사용

**단점:**
- UI 변경 필요
- 기존 "1번째, 2번째, 3번째" 개념과 다름

### 방안 3: 없는 달 건너뛰기

**개념:**
- 5번째 금요일이 없으면 해당 월 건너뛰고 다음 달로

**장점:**
- 완벽한 일관성

**단점:**
- DCA 주기가 불규칙해짐
- 투자 기회 손실

## 권장 사항

### DCA (분할 매수)

**권장: 방안 1 (원본 N 값 유지)**

이유:
- ✅ 사용자가 선택한 주기 존중
- ✅ 모든 월에 투자 (건너뛰지 않음)
- ✅ 없는 달에서는 마지막 해당 요일 사용 (월말 효과 최소화)
- ✅ 다시 존재하는 달에서 원래대로 복귀

예시:
```
설정: 매월 5번째 금요일 DCA
1월: 31일 (5번째 금요일) ✅
2월: 23일 (4번째 금요일, 5번째 없음) ⚠️ 폴백
3월: 29일 (5번째 금요일) ✅ 복귀
4월: 26일 (4번째 금요일, 5번째 없음) ⚠️ 폴백
5월: 31일 (5번째 금요일) ✅ 복귀
```

### 리밸런싱

**권장: 동일 (방안 1)**

이유:
- ✅ 리밸런싱도 일관된 주기 필요
- ✅ "분기 말 리밸런싱" 같은 패턴 지원

## 구현 우선순위

### Phase 1: 현재 버전 (긴급)

**현재 상태 문서화:**
- ⚠️ 현재는 N이 변경될 수 있음을 명시
- 사용자에게 1~4번째 요일 사용 권장

### Phase 2: 개선 버전 (다음 릴리스)

**방안 1 구현:**
1. `get_weekday_occurrence()` 함수 추가
2. `get_next_nth_weekday()` 함수에 `original_nth` 파라미터 추가
3. `dca_info`에 `original_nth_weekday` 필드 추가
4. 테스트 케이스 추가

### Phase 3: UI 개선 (선택)

**프론트엔드 경고:**
- 5번째 요일 선택 시 경고 표시
- "일부 달에는 5번째 X요일이 없어 마지막 X요일로 대체됩니다" 메시지

## 테스트 시나리오

### 필수 테스트

```python
def test_fifth_weekday_consistency():
    """5번째 요일 일관성 테스트"""
    start = datetime(2024, 1, 31)  # 5번째 수요일
    
    dates = []
    current = start
    
    for _ in range(12):
        dates.append(current)
        current = get_next_nth_weekday(current, 'monthly', 1, original_nth=5)
    
    # 모든 날짜가 5번째 또는 마지막 해당 요일인지 확인
    for date in dates:
        occurrence = get_weekday_occurrence(date)
        last_occurrence = get_last_weekday_occurrence(date)
        
        # 5번째이거나 마지막이어야 함
        assert occurrence == 5 or occurrence == last_occurrence
```

## 결론

**현재 버전:** 방안 1의 일부만 구현됨 (폴백은 되지만 N 복귀 안 됨)

**권장 조치:**
1. 짧은 기간: 현재 버전 문서화, 1~4번째 권장
2. 중기: 방안 1 완전 구현 (`original_nth` 추적)
3. 장기: UI 경고 및 "월말 기준" 옵션 추가
