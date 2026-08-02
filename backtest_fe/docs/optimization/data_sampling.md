# 스마트 데이터 샘플링 전략

## 정의

스마트 데이터 샘플링은 백테스트의 전체 기간에 따라 차트에 표시할 데이터의 집계 단위를 동적으로 조절하는 전략입니다. 기간이 짧을 때는 상세한 데이터를 보여주고, 기간이 길어질수록 데이터를 더 큰 시간 단위(주별, 월별)로 집계하여 렌더링할 데이터 포인트의 수를 최적의 범위 내로 유지합니다.

## 목적

-   **성능 향상**: 장기간(예: 5년, 10년)의 백테스트 결과는 수천 개의 데이터 포인트를 포함합니다. 이 모든 데이터를 한 번에 렌더링하면 브라우저에 심각한 성능 부하를 유발합니다. 데이터 샘플링은 렌더링할 데이터의 양을 줄여 차트의 초기 로딩 속도와 상호작용 반응성을 크게 향상시킵니다.
-   **시각적 명료성**: 너무 많은 데이터 포인트는 차트를 알아보기 어렵게 만듭니다. 10년치 데이터를 일별로 표시하면 그래프가 빽빽하게 뭉쳐져 추세를 파악하기 어렵습니다. 주별 또는 월별 데이터로 집계하면 장기적인 추세를 더 명확하게 파악할 수 있습니다.

## 샘플링 규칙

실제 구현(`shared/utils/dataSampling.ts`의 `smartSampleByPeriod`)은 총 일수가 아니라 **기간을 연 단위로 환산한 값**(`(종료일 - 시작일) / 1000 / 60 / 60 / 24 / 365.25`)을 기준으로 판단합니다. 아래 "총 일수" 열은 참고용 근사치입니다(2년 ≈ 730일, 5년 ≈ 1825일).

| 기간 (연 단위) | 집계 단위 | 설명 |
| :--- | :--- | :--- |
| 2일 미만 | 원본 그대로 + 경고 | "백테스트 기간은 최소 2일 이상이어야 합니다." 경고와 함께 원본 데이터를 그대로 반환합니다. |
| 2일 ~ 2년 | **일별 (Daily)** | 원본 데이터를 그대로 사용합니다. |
| 2년 초과 ~ 5년 | **주별 (Weekly)** | 배열 인덱스 기준 매 7번째 데이터 포인트를 선택하는 단순 샘플링입니다 (실제 달력 주와 일치하지 않을 수 있습니다). |
| 5년 초과 | **월별 (Monthly)** | 실제 달력 월(月) 기준으로 집계합니다. 10년을 초과하면 "10년 초과 백테스트는 월간 데이터로 표시됩니다." 경고가 추가됩니다. |

-   **가격/자산가치(equity) 데이터**: 위 표의 규칙을 그대로 따르는 `smartSampleByPeriod()`가 처리합니다. 주별 집계는 매 7번째 항목을 선택하는 단순 샘플링이고, 월별 집계는 실제 달력 월의 마지막 데이터를 선택합니다.
-   **수익률(%, `return_pct`) 데이터**: 위와 다른 함수인 `aggregateReturns()`를 사용합니다. 일별 수익률을 단순히 마지막 값만 취하면 틀린 결과가 나오므로(예: +5%, -5%가 반복되면 마지막 값만으로는 누적 효과가 사라짐), 구간 내 일별 수익률을 **복리로 합성**해 주간/월간 수익률을 계산합니다.

## 구현

샘플링 로직은 프론트엔드에서 백엔드로부터 원본 데이터를 수신한 후, 차트 렌더링 직전에 `features/backtest/hooks/charts/useChartData.ts` 훅 내부의 `useMemo`에서 수행됩니다. (`useBacktestResult`라는 이름의 훅이나 `useBacktestResultStore`라는 전역 스토어는 존재하지 않습니다 — 이 코드베이스에 전역 상태 스토어 자체가 없습니다.)

```typescript
// src/features/backtest/hooks/charts/useChartData.ts (구조를 단순화한 예시)
import { smartSampleByPeriod, aggregateReturns } from '@/shared/utils/dataSampling';

export const useChartData = (/* backtestResult, startDate, endDate, ... */): UseChartDataReturn => {
  // 가격/자산가치 데이터: smartSampleByPeriod가 기간에 따라 daily/weekly/monthly 자동 선택
  const sampledEquity = useMemo(() => {
    const { data, aggregationType, warning } = smartSampleByPeriod(
      equityPoints, startDate, endDate
    );
    return { data, aggregationType, warning };
  }, [equityPoints, startDate, endDate]);

  // 수익률(%) 데이터: 복리 집계가 필요하므로 별도 함수 사용
  const sampledReturns = useMemo(
    () => aggregateReturns(dailyReturnPoints, sampledEquity.aggregationType),
    [dailyReturnPoints, sampledEquity.aggregationType]
  );

  // ... 이하 트레이드 마커, OHLC 등 다른 변환 로직과 함께 반환
}
```

-   `smartSampleByPeriod(data, startDate, endDate)`: 가격/자산가치 계열 데이터를 기간에 따라 자동으로 daily/weekly/monthly로 집계하고, 실제 적용된 `aggregationType`과 (필요 시) 경고 메시지를 함께 반환합니다.
-   `aggregateReturns(data, aggregationType)`: 수익률(%) 계열 데이터를 복리로 집계합니다. 내부적으로 주간은 `aggregateWeeklyReturns`, 월간은 `aggregateMonthlyReturns`를 호출합니다.

## 장점 및 효과

-   **일관된 성능**: 백테스트 기간에 상관없이 차트에 렌더링되는 데이터 포인트의 수가 500개 내외로 유지되어 일관된 사용자 경험을 제공합니다.
-   **자동 최적화**: 사용자는 별도의 조작 없이 최적화된 차트를 보게 됩니다. 시스템이 기간에 따라 자동으로 최적의 집계 단위를 선택해 줍니다.
-   **코드 분리**: 샘플링 로직은 데이터 처리 단계에 캡슐화되어 있어, 차트 렌더링 컴포넌트는 샘플링 여부를 신경 쓸 필요 없이 전달된 데이터를 그리기만 하면 됩니다.

이 스마트 샘플링 전략은 장기 백테스트의 사용성을 저해하는 핵심적인 성능 병목 현상을 해결하고, 동시에 데이터의 시각적 분석 효율을 높이는 중요한 최적화 기법입니다.
