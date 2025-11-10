# Chart Performance Optimization Checklist

## Critical Bottlenecks Found: 7 + 6 additional issues

---

## PHASE 1: Critical Fixes (7 Components - 30 minutes)

Add `memo()` wrapper to unmemoized components:

### [ ] 1. BenchmarkIndexChart
- **File**: `/backtest_fe/src/features/backtest/components/results/BenchmarkIndexChart.tsx`
- **Change**: Line 19
- **Current**: `const BenchmarkIndexChart: React.FC<BenchmarkIndexChartProps> = ({`
- **Fix**: `const BenchmarkIndexChart: React.FC<BenchmarkIndexChartProps> = memo(({`
- **And**: `});` → `}));\nBenchmarkIndexChart.displayName = 'BenchmarkIndexChart';`
- **Import**: Add `import { memo } from 'react';` if not present

### [ ] 2. BenchmarkReturnsChart  
- **File**: `/backtest_fe/src/features/backtest/components/results/BenchmarkReturnsChart.tsx`
- **Change**: Line 19
- **Current**: `const BenchmarkReturnsChart: React.FC<BenchmarkReturnsChartProps> = ({`
- **Fix**: Wrap with `memo()` and add displayName
- **Import**: Add `import { memo } from 'react';` if not present

### [ ] 3. WeightHistoryChart
- **File**: `/backtest_fe/src/features/backtest/components/results/WeightHistoryChart.tsx`
- **Change**: Line 34
- **Current**: `const WeightHistoryChart: React.FC<WeightHistoryChartProps> = ({`
- **Fix**: Wrap with `memo()` and add displayName
- **Import**: Add `import { memo } from 'react';` if not present

### [ ] 4. SupplementaryCharts
- **File**: `/backtest_fe/src/features/backtest/components/results/ChartsSection/SupplementaryCharts.tsx`
- **Change**: Line 41
- **Current**: `export const SupplementaryCharts: React.FC<SupplementaryChartsProps> = ({`
- **Fix**: Wrap with `memo()` 
- **Import**: Add `import { memo } from 'react';` if not present

### [ ] 5. PortfolioCharts
- **File**: `/backtest_fe/src/features/backtest/components/results/ChartsSection/PortfolioCharts.tsx`
- **Change**: Line 35
- **Current**: `export const PortfolioCharts: React.FC<PortfolioChartsProps> = ({`
- **Fix**: Wrap with `memo()`
- **Import**: Add `import { memo } from 'react';` if not present

### [ ] 6. SingleStockCharts
- **File**: `/backtest_fe/src/features/backtest/components/results/ChartsSection/SingleStockCharts.tsx`
- **Change**: Line 30
- **Current**: `export const SingleStockCharts: React.FC<SingleStockChartsProps> = ({`
- **Fix**: Wrap with `memo()`
- **Import**: Add `import { memo } from 'react';` if not present

### [ ] 7. BenchmarkSection
- **File**: `/backtest_fe/src/features/backtest/components/results/ChartsSection/BenchmarkSection.tsx`
- **Change**: Line 20
- **Current**: `export const BenchmarkSection: React.FC<BenchmarkSectionProps> = ({`
- **Fix**: Wrap with `memo()`
- **Import**: Add `import { memo } from 'react';` if not present

---

## PHASE 2: High-Impact Fixes (6 Issues - 45 minutes)

### [ ] 8. BenchmarkIndexChart - Add useCallback for Legend Click
- **File**: `/backtest_fe/src/features/backtest/components/results/BenchmarkIndexChart.tsx`
- **Lines**: 214-221 (Legend onClick)
- **Current**:
```typescript
<Legend
  onClick={(data) => {
    // ... logic
  }}
/>
```
- **Fix**: Extract to useCallback
```typescript
const handleLegendClick = useCallback((data: any) => {
  const dataKey = data.dataKey;
  if (dataKey && typeof dataKey === 'string') {
    setVisibleLines(prev => ({
      ...prev,
      [dataKey]: !prev[dataKey],
    }));
  }
}, []);

// Then in JSX:
<Legend onClick={handleLegendClick} />
```
- **Import**: Add `useCallback` to React import if not present

### [ ] 9. BenchmarkReturnsChart - Add useCallback for Legend Click
- **File**: `/backtest_fe/src/features/backtest/components/results/BenchmarkReturnsChart.tsx`
- **Lines**: 141-147 (Legend onClick)
- **Fix**: Same as issue #8
- **Import**: Add `useCallback` to React import if not present

### [ ] 10. WeightHistoryChart - Extract Gradient Definitions
- **File**: `/backtest_fe/src/features/backtest/components/results/WeightHistoryChart.tsx`
- **Lines**: 77-82
- **Current**:
```typescript
<defs>
  {symbols.map((symbol, index) => (
    <linearGradient key={symbol} id={`color${index}`} ...>
      {/* ... */}
    </linearGradient>
  ))}
</defs>
```
- **Fix**: Extract to useMemo
```typescript
const gradientDefs = useMemo(() => (
  symbols.map((symbol, index) => (
    <linearGradient key={symbol} id={`color${index}`} x1="0" y1="0" x2="0" y2="1">
      <stop offset="5%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0.8} />
      <stop offset="95%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0.1} />
    </linearGradient>
  ))
), [symbols]);

// In JSX:
<defs>{gradientDefs}</defs>
```
- **Import**: Ensure `useMemo` is imported

### [ ] 11. PortfolioCharts - Extract Gradient Definitions
- **File**: `/backtest_fe/src/features/backtest/components/results/ChartsSection/PortfolioCharts.tsx`
- **Lines**: 69-74
- **Current**:
```typescript
<defs>
  <linearGradient id="portfolioValue" x1="0" y1="0" x2="0" y2="1">
    {/* ... */}
  </linearGradient>
</defs>
```
- **Fix**: Extract to const outside component render
```typescript
const PORTFOLIO_GRADIENT_DEF = (
  <linearGradient id="portfolioValue" x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
  </linearGradient>
);

// In component:
<defs>{PORTFOLIO_GRADIENT_DEF}</defs>
```

### [ ] 12. TradeSignalsChart - Extract CustomTooltip Component
- **File**: `/backtest_fe/src/features/backtest/components/TradeSignalsChart.tsx`
- **Lines**: 68-89 (CustomTooltip definition)
- **Current**:
```typescript
const CustomTooltip = ({ active, payload }: TooltipProps) => {
  // ... component definition inside render
};
```
- **Fix**: Extract before component
```typescript
interface TooltipProps {
  active?: boolean;
  payload?: Array<{ payload: { date: string; price: number; type: string; quantity: number; pnl_pct?: number } }>;
}

const CustomTooltip = memo(({ active, payload }: TooltipProps) => {
  if (!active || !payload || payload.length === 0) return null;
  // ... rest of component
});

// Then in TradeSignalsChart render:
<Tooltip content={<CustomTooltip />} />
```
- **Import**: Add `memo` to React import

### [ ] 13. SupplementaryCharts - Memoize Min/Max Calculations
- **File**: `/backtest_fe/src/features/backtest/components/results/ChartsSection/SupplementaryCharts.tsx`
- **Lines**: 73-75 (Exchange Rate YAxis domain)
- **Current**:
```typescript
<YAxis
  domain={[
    Math.min(...exchangeRates.map((d: any) => d.rate)),
    Math.max(...exchangeRates.map((d: any) => d.rate)),
  ]}
/>
```
- **Fix**: Extract to useMemo above JSX
```typescript
const exchangeRateDomain = useMemo(() => {
  if (exchangeRates.length === 0) return [0, 100];
  const rates = exchangeRates.map((d: any) => d.rate);
  return [Math.min(...rates), Math.max(...rates)];
}, [exchangeRates]);

// In YAxis:
<YAxis domain={exchangeRateDomain} />
```
- **Import**: Ensure `useMemo` is imported

---

## PHASE 3: Structural Improvements (Medium Priority)

### [ ] 14. useChartData Hook - Consider Splitting
- **File**: `/backtest_fe/src/features/backtest/hooks/charts/useChartData.ts`
- **Issue**: Returns 27 values, creates cascading dependencies
- **Recommendation**: Split into specialized hooks when time permits:
  - `usePortfolioChartData` for portfolio-specific values
  - `useSingleStockChartData` for single stock values
  - `useBenchmarkChartData` for benchmark values
  - `useSupplementaryChartData` for supplementary values

### [ ] 15. Add Performance Monitoring
- **Files**: All chart components
- **Current**: Only StockPriceChart has performance monitoring
- **Fix**: Add to all charts for visibility
```typescript
const useRenderPerformance = useRenderPerformance('ComponentName');
```

---

## Testing Checklist

After applying fixes, verify:

### [ ] Test 1: React DevTools Profiler
1. Open React DevTools Profiler
2. Run 10-year backtest
3. Confirm: Reduced render count on legend clicks and data updates
4. Expected: 90% reduction in re-renders

### [ ] Test 2: Manual Testing
1. [ ] Legend click on BenchmarkIndexChart - should only re-render that component
2. [ ] Legend click on BenchmarkReturnsChart - should only re-render that component
3. [ ] Verify all charts still display correctly
4. [ ] Verify interactive features (legend clicks, zooming) work

### [ ] Test 3: Performance Impact
1. [ ] Measure initial render time: should decrease by 20-30%
2. [ ] Measure legend click response: should be instant
3. [ ] Measure data update render: should decrease by 50%+

### [ ] Test 4: Visual Regression
1. [ ] Verify all charts render correctly
2. [ ] Verify gradient fills are present on weighted history chart
3. [ ] Verify tooltips display correctly
4. [ ] Verify responsive behavior on different screen sizes

---

## Summary

- **Total Issues Found**: 15 (7 critical + 6 high + 2 medium)
- **Estimated Fix Time**: 2-3 hours total
- **Expected Performance Gain**: 90% reduction in unnecessary re-renders
- **Effort Level**: Low complexity, high impact

---

## Notes

- All components already use Recharts optimization (`isAnimationActive={false}`, `debounce={300}`)
- `ChartsSection`, `StockPriceChart`, `EquityChart`, `OHLCChart`, `TradesChart`, `TradeSignalsChart` are already well-optimized
- No changes needed to data structure or API
- All fixes are component-level optimizations

