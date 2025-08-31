# 프론트엔드 컴포넌트 가이드

이 문서는 실제 코드(`frontend/src/components`)에 있는 컴포넌트들을 기준으로 각 컴포넌트의 파일 위치, 주요 props와 간단한 사용 예시를 정리합니다.

## 컴포넌트 개요

경로: `frontend/src/components`

### 주요 컴포넌트 목록

- `UnifiedBacktestForm.tsx` — 통합 백테스트 입력 폼 (포트폴리오 + 전략)
- `UnifiedBacktestResults.tsx` — 통합 백테스트 결과 표시
- `OHLCChart.tsx` — OHLC + 거래량 + 지표 + 거래 마커
- `EquityChart.tsx` — 자산(Equity) 곡선 + Drawdown
- `TradesChart.tsx` — 거래별 PnL 산점도
- `StatsSummary.tsx` — 카드형 성과 요약
- `CustomTooltip.tsx` — Recharts 툴팁 커스텀 렌더러
- `BacktestForm.tsx` — 단일 종목 백테스트 입력 폼 (레거시)
- `PortfolioForm.tsx` — 포트폴리오 입력 폼 (레거시)
- `PortfolioResults.tsx` — 포트폴리오 결과 표시 (레거시)

---

## UnifiedBacktestForm

- **파일**: `frontend/src/components/UnifiedBacktestForm.tsx`
- **설명**: 포트폴리오 구성부터 전략 선택까지 모든 백테스트 설정을 처리하는 통합 폼입니다.

### Props
```typescript
interface UnifiedBacktestFormProps {
  onSubmit: (request: UnifiedBacktestRequest) => Promise<void>;
  loading?: boolean;
}
```

### 주요 기능
- **포트폴리오 구성**: 다중 종목/자산 추가/제거
- **투자 방식 선택**: 일시투자 vs 분할매수(DCA)
- **전략 선택**: Buy & Hold, SMA, RSI, Bollinger Bands, MACD
- **동적 파라미터**: 전략별 파라미터 입력 폼 자동 생성
- **유효성 검증**: 포트폴리오 및 파라미터 유효성 검사

### 사용 예
```tsx
<UnifiedBacktestForm
  onSubmit={handleBacktestSubmit}
  loading={isLoading}
/>
```

---

## UnifiedBacktestResults

- **파일**: `frontend/src/components/UnifiedBacktestResults.tsx`
- **설명**: 포트폴리오 및 단일 종목 백테스트 결과를 통합 표시하는 컴포넌트입니다.

### Props
```typescript
interface UnifiedBacktestResultsProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}
```

### 주요 기능
- **자동 타입 감지**: 포트폴리오 vs 단일 종목 결과 자동 구분
- **성과 요약**: 총 수익률, 최대 낙폭, 샤프 비율 등
- **포트폴리오 구성 표시**: 종목별 비중과 개별 수익률
- **상세 통계**: 거래일수, 승률, 변동성 등

### 사용 예
```tsx
<UnifiedBacktestResults
  data={backtestResult}
  isPortfolio={portfolio.length > 1}
/>
```

---

## OHLCChart

- **파일**: `frontend/src/components/OHLCChart.tsx`
- **설명**: OHLC(종가 선으로 표현), 거래량 바, 여러 기술지표(선), 그리고 거래 마커(ReferenceLine)를 함께 그립니다.

### Props
```typescript
interface OHLCChartProps {
  data: Array<{
    date: string;
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    volume?: number;
  }>;
  indicators: Array<{
    name: string;
    color?: string;
    data?: Array<{ date: string; value: number }>;
  }>;
  trades: Array<{
    date: string;
    type: 'entry' | 'exit';
    side?: 'buy' | 'sell';
    price?: number;
    pnl_pct?: number;
  }>;
}
```

### 사용 예
```tsx
<OHLCChart
  data={chartData.ohlc_data}
  indicators={chartData.indicators}
  trades={chartData.trade_markers}
/>
```

---

## EquityChart

- **파일**: `frontend/src/components/EquityChart.tsx`
- **설명**: 백테스트 기간 동안의 equity(누적 자산) 변동을 선으로, drawdown을 영역(Area)으로 그립니다.

### Props
```typescript
interface EquityChartProps {
  data: Array<{
    date: string;
    equity?: number;
    return_pct?: number;
    drawdown_pct?: number;
  }>;
}
```

### 사용 예
```tsx
<EquityChart data={chartData.equity_data} />
```

---

## TradesChart

- **파일**: `frontend/src/components/TradesChart.tsx`
- **설명**: 종료(Exit) 거래들의 PnL(%)을 산점도로 표시합니다. 색상은 손익(양수: 녹색, 음수: 빨간색)으로 구분됩니다.

### Props
```typescript
interface TradesChartProps {
  trades: Array<{
    date: string;
    type: 'entry' | 'exit';
    pnl_pct?: number;
  }>;
}
```

### 사용 예
```tsx
<TradesChart trades={backtestResult.trades} />
```

---

## StatsSummary

- **파일**: `frontend/src/components/StatsSummary.tsx`
- **설명**: 백테스트의 요약 통계(총 수익률, 거래수, 승률, 최대 손실, 샤프, Profit Factor 등)를 카드 그리드로 렌더링합니다.

### Props
```typescript
interface StatsSummaryProps {
  stats: {
    total_return_pct: number;
    total_trades: number;
    win_rate_pct: number;
    max_drawdown_pct: number;
    sharpe_ratio: number;
    profit_factor: number;
    [key: string]: any;
  };
}
```

### 사용 예
```tsx
<StatsSummary stats={backtestResult.summary_stats} />
```

---

## CustomTooltip

- **파일**: `frontend/src/components/CustomTooltip.tsx`
- **설명**: Recharts의 툴팁(custom) 렌더러로, `active`, `payload`, `label`을 받아 내부적으로 포맷해 보여줍니다.

### Props
```typescript
interface CustomTooltipProps {
  active: boolean;
  payload: any[];
  label: string | number;
}
```

### 사용 예
```tsx
<RechartsTooltip content={<CustomTooltip />} />
```

---

## 레거시 컴포넌트들

### BacktestForm

- **파일**: `frontend/src/components/BacktestForm.tsx`
- **설명**: 단일 종목 백테스트용 간단한 폼 (현재는 `UnifiedBacktestForm` 사용 권장)

### PortfolioForm

- **파일**: `frontend/src/components/PortfolioForm.tsx`
- **설명**: 비중 기반 포트폴리오 폼 (현재는 `UnifiedBacktestForm` 사용 권장)

### PortfolioResults

- **파일**: `frontend/src/components/PortfolioResults.tsx`
- **설명**: 포트폴리오 결과 표시 (현재는 `UnifiedBacktestResults` 사용 권장)

---

## 컴포넌트 사용 패턴

### 1. 메인 애플리케이션 구조

```tsx
function App() {
  const [backtestResult, setBacktestResult] = useState(null);
  const [isPortfolio, setIsPortfolio] = useState(false);

  return (
    <Container>
      <UnifiedBacktestForm
        onSubmit={handleBacktest}
        loading={loading}
      />
      
      {backtestResult && (
        <UnifiedBacktestResults
          data={backtestResult}
          isPortfolio={isPortfolio}
        />
      )}
    </Container>
  );
}
```

### 2. 조건부 차트 렌더링

```tsx
// 단일 종목 결과의 경우
{!isPortfolio && chartData && (
  <>
    <OHLCChart
      data={chartData.ohlc_data}
      indicators={chartData.indicators}
      trades={chartData.trade_markers}
    />
    <EquityChart data={chartData.equity_data} />
    <TradesChart trades={chartData.trade_markers} />
    <StatsSummary stats={chartData.summary_stats} />
  </>
)}
```

### 3. 포트폴리오 결과의 경우

```tsx
// 포트폴리오 결과는 UnifiedBacktestResults에서 내부적으로 처리
{isPortfolio && portfolioData && (
  <UnifiedBacktestResults
    data={portfolioData}
    isPortfolio={true}
  />
)}
```

---

## 개발 참고사항

### 1. 타입 정의

모든 컴포넌트의 상세한 타입 정의는 `frontend/src/types/api.ts`에서 확인할 수 있습니다.

### 2. 스타일링

모든 컴포넌트는 React Bootstrap을 기반으로 하며, 추가적인 커스텀 스타일링은 `index.css`에서 관리됩니다.

### 3. 차트 라이브러리

차트 컴포넌트들은 `recharts` 라이브러리를 사용하며, 반응형 디자인을 위해 `ResponsiveContainer`로 감싸져 있습니다.

### 4. 에러 처리

모든 컴포넌트는 데이터가 없거나 잘못된 경우를 대비한 방어적 프로그래밍을 적용하고 있습니다.
