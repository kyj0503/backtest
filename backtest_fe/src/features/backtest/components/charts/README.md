# Charts Components Directory

이 디렉토리는 차트 컴포넌트들을 도메인별로 분류하여 관리합니다.

## 디렉토리 구조

```
charts/
├── stock/          # 주가 관련 차트
│   ├── StockPriceChart.tsx
│   └── StockSymbolSelector.tsx
│
├── trades/         # 거래 관련 차트
│   ├── TradesChart.tsx
│   └── TradeSignalsChart.tsx
│
├── portfolio/      # 포트폴리오 관련 차트
│   ├── WeightHistoryChart.tsx
│   └── RebalanceHistoryTable.tsx
│
└── README.md       # 이 파일
```

## 마이그레이션 가이드

### 현재 상태
현재 차트 컴포넌트들은 `components/` 루트와 `components/results/`에 흩어져 있습니다.

### 향후 이동 계획
다음 차트 컴포넌트들을 점진적으로 도메인별 폴더로 이동할 수 있습니다:

#### stock/ 폴더로 이동 예정
- `StockPriceChart.tsx` ← `components/StockPriceChart.tsx`
- `StockSymbolSelector.tsx` ← `components/results/StockSymbolSelector.tsx`

#### trades/ 폴더로 이동 예정
- `TradesChart.tsx` ← `components/TradesChart.tsx`
- `TradeSignalsChart.tsx` ← `components/TradeSignalsChart.tsx`

#### portfolio/ 폴더로 이동 예정
- `WeightHistoryChart.tsx` ← `components/results/WeightHistoryChart.tsx`
- `RebalanceHistoryTable.tsx` ← `components/results/RebalanceHistoryTable.tsx`

### 이동 시 주의사항

1. **Import 경로 업데이트**: 컴포넌트를 이동하면 import 경로를 업데이트해야 합니다.
   ```tsx
   // Before
   import StockPriceChart from '../StockPriceChart';

   // After
   import StockPriceChart from '../charts/stock/StockPriceChart';
   ```

2. **상대 경로 수정**: 이동한 컴포넌트 내부의 import도 수정해야 합니다.

3. **테스트 파일**: 테스트 파일도 함께 이동하거나 경로를 업데이트합니다.

## 사용 예시

```tsx
// 주가 차트 사용
import { StockPriceChart } from '@/features/backtest/components/charts/stock';

// 거래 차트 사용
import { TradesChart, TradeSignalsChart } from '@/features/backtest/components/charts/trades';

// 포트폴리오 차트 사용
import { WeightHistoryChart } from '@/features/backtest/components/charts/portfolio';
```

## 장점

1. **명확한 분류**: 차트 컴포넌트가 도메인별로 명확하게 분류됩니다.
2. **쉬운 탐색**: 특정 도메인의 차트를 찾기 쉽습니다.
3. **재사용성**: 도메인별로 분리되어 다른 프로젝트에서도 재사용하기 쉽습니다.
4. **유지보수**: 관련 컴포넌트들이 모여 있어 유지보수가 용이합니다.
