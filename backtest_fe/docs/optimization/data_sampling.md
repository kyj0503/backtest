# 스마트 데이터 샘플링 전략

## 정의

스마트 데이터 샘플링은 백테스트의 전체 기간에 따라 차트에 표시할 데이터의 집계 단위를 동적으로 조절하는 전략입니다. 기간이 짧을 때는 상세한 데이터를 보여주고, 기간이 길어질수록 데이터를 더 큰 시간 단위(주별, 월별)로 집계하여 렌더링할 데이터 포인트의 수를 최적의 범위 내로 유지합니다.

## 목적

-   **성능 향상**: 장기간(예: 5년, 10년)의 백테스트 결과는 수천 개의 데이터 포인트를 포함합니다. 이 모든 데이터를 한 번에 렌더링하면 브라우저에 심각한 성능 부하를 유발합니다. 데이터 샘플링은 렌더링할 데이터의 양을 줄여 차트의 초기 로딩 속도와 상호작용 반응성을 크게 향상시킵니다.
-   **시각적 명료성**: 너무 많은 데이터 포인트는 차트를 알아보기 어렵게 만듭니다. 10년치 데이터를 일별로 표시하면 그래프가 빽빽하게 뭉쳐져 추세를 파악하기 어렵습니다. 주별 또는 월별 데이터로 집계하면 장기적인 추세를 더 명확하게 파악할 수 있습니다.

## 샘플링 규칙

데이터 집계 단위는 백테스트 기간(시작일과 종료일 사이의 총 일수)을 기준으로 다음과 같이 결정됩니다.

| 기간 (총 일수) | 집계 단위 | 예상 데이터 포인트 수 (최대) | 설명 |
| :--- | :--- | :--- | :--- |
| 1일 ~ 730일 (약 2년) | **일별 (Daily)** | ~500 | 단기 분석에 필요한 모든 상세 데이터를 표시합니다. |
| 731일 ~ 1825일 (약 5년) | **주별 (Weekly)** | ~260 | 중기 추세 파악에 적합합니다. |
| 1826일 이상 (5년 초과) | **월별 (Monthly)** | 기간에 따라 변동 | 장기적인 자산 변화 추세를 명확하게 보여줍니다. |

-   **주별 데이터 집계 방식**:
    -   해당 주의 마지막 날짜(보통 금요일)의 데이터를 해당 주를 대표하는 데이터 포인트로 사용합니다.
    -   시가(Open)는 주의 첫날 시가, 고가(High)는 주간 최고가, 저가(Low)는 주간 최저가, 종가(Close)는 주의 마지막 날 종가를 사용합니다.
-   **월별 데이터 집계 방식**:
    -   해당 월의 마지막 날 데이터를 해당 월을 대표하는 데이터 포인트로 사용합니다.
    -   시/고/저/종가 집계 방식은 주별과 동일한 원리를 따릅니다.

## 구현

샘플링 로직은 프론트엔드에서 백엔드로부터 원본 데이터를 수신한 후, 차트 렌더링 직전에 `useMemo` 훅 내부에서 수행됩니다.

```typescript
// /src/features/backtest/hooks/useBacktestResult.ts

const useBacktestResult = () => {
  const { backtestResult } = useBacktestResultStore();

  const sampledData = useMemo(() => {
    if (!backtestResult?._equity_curve) return [];

    const equityData = backtestResult._equity_curve.Equity;
    const dates = backtestResult._equity_curve.index;

    const totalDays = calculateDaysBetween(dates[0], dates[dates.length - 1]);

    let samplingUnit: 'daily' | 'weekly' | 'monthly' = 'daily';
    if (totalDays > 1825) {
      samplingUnit = 'monthly';
    } else if (totalDays > 730) {
      samplingUnit = 'weekly';
    }

    switch (samplingUnit) {
      case 'weekly':
        return aggregateToWeekly(dates, equityData);
      case 'monthly':
        return aggregateToMonthly(dates, equityData);
      default:
        // 일별 데이터는 그대로 반환
        return dates.map((date, i) => ({ date, value: equityData[i] }));
    }
  }, [backtestResult]); // backtestResult가 변경될 때만 재계산

  return { sampledData };
};
```

-   `calculateDaysBetween`: 두 날짜 사이의 총 일수를 계산하는 유틸리티 함수입니다.
-   `aggregateToWeekly` / `aggregateToMonthly`: 일별 데이터를 각각 주별, 월별 데이터로 집계하는 순수 함수입니다. 이 함수들은 데이터 배열을 순회하며 각 기간의 마지막 데이터를 선택하여 새로운 배열을 만듭니다.

## 장점 및 효과

-   **일관된 성능**: 백테스트 기간에 상관없이 차트에 렌더링되는 데이터 포인트의 수가 500개 내외로 유지되어 일관된 사용자 경험을 제공합니다.
-   **자동 최적화**: 사용자는 별도의 조작 없이 최적화된 차트를 보게 됩니다. 시스템이 기간에 따라 자동으로 최적의 집계 단위를 선택해 줍니다.
-   **코드 분리**: 샘플링 로직은 데이터 처리 단계에 캡슐화되어 있어, 차트 렌더링 컴포넌트는 샘플링 여부를 신경 쓸 필요 없이 전달된 데이터를 그리기만 하면 됩니다.

이 스마트 샘플링 전략은 장기 백테스트의 사용성을 저해하는 핵심적인 성능 병목 현상을 해결하고, 동시에 데이터의 시각적 분석 효율을 높이는 중요한 최적화 기법입니다.
