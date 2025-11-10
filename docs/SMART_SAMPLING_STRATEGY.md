# 스마트 샘플링 전략 (Smart Sampling Strategy)

## 개요

백테스트 기간에 따라 적절한 시간 단위로 차트 데이터를 집계하여, 성능과 시각적 품질의 균형을 맞춥니다.

## 전략

| 백테스트 기간 | 데이터 집계 | 설명 |
|--------------|------------|------|
| **1일 미만** | 오류 | 최소 2일 이상 필요 |
| **2일 ~ 2년** | 일간 (Daily) | 원본 데이터 그대로 표시 |
| **2년 초과 ~ 5년** | 주간 (Weekly) | 매주 마지막 거래일 데이터 |
| **5년 초과 ~ 10년** | 월간 (Monthly) | 매월 마지막 거래일 데이터 |
| **10년 초과** | 월간 (Monthly) + 경고 | 10년 초과 시 경고 메시지 표시 |

## 구현 위치

### 백엔드
- **전략**: 일간 데이터를 정확하게 계산하여 전달
- **이유**: 백테스트 엔진은 정확한 계산이 우선
- **파일**: `app/services/portfolio_service.py`, `app/services/backtest_engine.py`

### 프론트엔드
- **전략**: 받은 일간 데이터를 기간에 따라 주간/월간으로 집계
- **이유**: 시각화 유연성, 캐싱 재사용 가능
- **파일**: 
  - 샘플링 로직: `backtest_fe/src/shared/utils/dataSampling.ts`
  - 데이터 변환: `backtest_fe/src/features/backtest/hooks/charts/useChartData.ts`
  - UI 표시: `backtest_fe/src/features/backtest/components/results/ChartsSection/index.tsx`

## 주요 함수

### `smartSampleByPeriod(data, startDate, endDate)`

백테스트 기간을 계산하여 자동으로 적절한 집계 전략 적용:

```typescript
const { data, aggregationType, warning } = smartSampleByPeriod(
  equityData,
  '2020-01-01',
  '2023-12-31'
);

// aggregationType: 'daily' | 'weekly' | 'monthly'
// warning: 10년 초과 시 경고 메시지
```

### `aggregateReturns(dailyReturns, aggregationType)`

일일 수익률을 주간/월간 수익률로 복리 계산:

```typescript
const weeklyReturns = aggregateReturns(dailyReturns, 'weekly');
const monthlyReturns = aggregateReturns(dailyReturns, 'monthly');
```

## 적용된 차트

다음 차트들이 자동으로 기간에 따라 집계됩니다:

1. **누적 자산 가치** (Equity Curve)
2. **일일/주간/월간 수익률** (Returns)
3. **개별 자산 주가** (Stock Prices)
4. **벤치마크 비교** (Benchmark Comparison)
   - S&P 500
   - NASDAQ
5. **환율 추이** (Exchange Rates)
6. **포트폴리오 비중 변화** (Weight History)

## 성능 이점

| 백테스트 기간 | 원본 데이터 포인트 | 집계 후 포인트 | 감소율 |
|--------------|-------------------|---------------|--------|
| 2년 | ~500 | ~500 | 0% |
| 5년 | ~1,250 | ~260 (주간) | ~79% |
| 10년 | ~2,500 | ~120 (월간) | ~95% |

## 주의사항

### 복리 계산
주간/월간 수익률은 일일 수익률을 복리로 계산합니다:

```
주간 수익률 = (1 + r1) × (1 + r2) × ... × (1 + r7) - 1
```

### 리밸런싱 마커
- 주간/월간 집계 시에도 리밸런싱 이벤트는 원본 날짜 유지
- 화면에 최대 20개 마커만 표시 (성능 최적화)

## 향후 개선 사항

1. **사용자 설정**: 집계 단위 수동 선택 옵션 (일간/주간/월간)
2. **적응형 샘플링**: 변화 큰 구간은 더 많은 포인트 유지
3. **다운로드 옵션**: 원본 일간 데이터 CSV 다운로드
