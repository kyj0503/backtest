# 상태 관리 가이드

## 목적
백테스팅 프론트엔드에서 일관되고 예측 가능한 상태 관리를 구현하기 위한 설계 원칙과 패턴을 제시합니다.

## 대상
React + TypeScript 환경에서 폼/차트/데이터 페칭 상태를 구현·유지보수하는 프론트엔드 개발자.

## 상태 관리 철학

### 설계 원칙
1. **로컬 상태 우선**: 전역 상태는 꼭 필요한 경우에만 사용
2. **단방향 데이터 흐름**: Props down, Events up 패턴 준수
3. **상태 정규화**: 중복 데이터 방지, 단일 진실 공급원 유지
4. **타입 안전성**: TypeScript를 활용한 상태 타입 안전성 보장
5. **관심사 분리**: 각 훅은 특정 도메인의 상태만 관리
6. **재사용성**: 컴포넌트 독립적인 로직으로 설계

## 현재 구현된 상태 관리 시스템

### 1. 백테스트 폼 상태 (useReducer 기반)

```typescript
// types/backtest-form.ts
export interface BacktestFormState {
  portfolio: Stock[];
  dates: {
    startDate: string;
    endDate: string;
  };
  strategy: {
    selectedStrategy: string;
    strategyParams: Record<string, any>;
  };
  settings: {
    rebalanceFrequency: string;
    commission: number;
  };
  ui: {
    errors: string[];
    isLoading: boolean;
  };
}

// reducers/backtestFormReducer.ts
export function backtestFormReducer(
  state: BacktestFormState, 
  action: BacktestFormAction
): BacktestFormState {
  switch (action.type) {
    case 'UPDATE_STOCK':
      const { index, field, value } = action.payload;
      const updatedPortfolio = state.portfolio.map((stock, i) => 
        i === index ? { ...stock, [field]: value } : stock
      );
      return { ...state, portfolio: updatedPortfolio };
    
### 2. 새로 추가된 커스텀 훅들 (4.2 리팩토링 완료)

#### 2.1. useStockData (주가 데이터 페칭)
```typescript
// hooks/useStockData.ts
export const useStockData = ({ 
  symbols, 
  startDate, 
  endDate, 
  enabled = true 
}: UseStockDataParams): UseStockDataReturn => {
  // 주가 데이터 병렬 페칭
  // 캐싱 및 에러 처리
  // 자동 재시도 로직
}

// 사용법
const { stocksData, loading, error, refetch } = useStockData({
  symbols: ['AAPL', 'GOOGL'],
  startDate: '2023-01-01',
  endDate: '2023-12-31'
});
```

#### 2.2. useVolatilityNews (변동성 뉴스 관리)
```typescript
// hooks/useVolatilityNews.ts
export const useVolatilityNews = ({ 
  symbols, 
  startDate, 
  endDate, 
  enabled = true 
}: UseVolatilityNewsParams): UseVolatilityNewsReturn => {
  // 변동성 이벤트 조회
  // 종목 선택 상태 관리
  // 뉴스 모달 상태 제어
  // 뉴스 데이터 페칭
}

// 사용법
const {
  volatilityData,
  selectedStock,
  newsData,
  showNewsModal,
  loading,
  actions: { setSelectedStock, openNewsModal, closeNewsModal }
} = useVolatilityNews({ symbols, startDate, endDate });
```

#### 2.3. useModal (범용 모달 상태)
```typescript
// hooks/useModal.ts
export const useModal = (initialOpen = false): UseModalReturn => {
  // 모달 열기/닫기 상태
  // 모달 데이터 관리
  // 키보드 이벤트 처리
}

// 사용법
const { isOpen, data, open, close, toggle } = useModal();
```

### 3. 유틸리티 함수 분리

#### 3.1. numberUtils.ts
```typescript
export const formatCurrency = (value: number): string => { /* */ };
export const formatPercent = (value: number): string => { /* */ };
export const formatPrice = (value: number): string => { /* */ };
export const formatKoreanCurrency = (value: number): string => { /* */ };
```

#### 3.2. dateUtils.ts
```typescript
export const formatDate = (date: string | Date): string => { /* */ };
export const formatDateTime = (date: string | Date): string => { /* */ };
export const formatChartDate = (date: string | Date): string => { /* */ };
export const formatDateRange = (startDate: string, endDate: string): string => { /* */ };
export const isValidDateRange = (startDate: string, endDate: string): boolean => { /* */ };
```
    case 'SET_STRATEGY':
      return {
        ...state,
        strategy: { ...state.strategy, selectedStrategy: action.payload }
      };
    
    // 기타 액션들...
    default:
      return state;
  }
}
```

### 2. 커스텀 훅 시스템

#### useBacktestForm (통합 폼 관리)
```typescript
// hooks/useBacktestForm.ts
export const useBacktestForm = (initialState?: Partial<BacktestFormState>) => {
  const [state, dispatch] = useReducer(
    backtestFormReducer, 
    { ...initialBacktestFormState, ...initialState }
  );

  // 전략 변경 시 기본 파라미터 자동 설정
  useEffect(() => {
    const config = STRATEGY_CONFIGS[state.strategy.selectedStrategy];
    if (config && config.parameters) {
      const defaultParams = Object.entries(config.parameters).reduce((acc, [key, param]) => {
        acc[key] = (param as any).default;
        return acc;
      }, {} as Record<string, any>);
      dispatch({ type: 'SET_STRATEGY_PARAMS', payload: defaultParams });
    }
  }, [state.strategy.selectedStrategy]);

  const actions = {
    updateStock: (index: number, field: keyof Stock, value: string | number) => {
      dispatch({ type: 'UPDATE_STOCK', payload: { index, field, value } });
    },
    setSelectedStrategy: (strategy: string) => {
      dispatch({ type: 'SET_STRATEGY', payload: strategy });
    },
    // 기타 액션들...
  };

  const helpers = {
    getTotalAmount: () => state.portfolio.reduce((sum, stock) => sum + stock.amount, 0),
    validateForm: () => {
      // 폼 검증 로직
      return validationErrors;
    }
  };

  return { state, actions, helpers };
};
```

#### usePortfolio (포트폴리오 관리)
```typescript
// hooks/usePortfolio.ts
export const usePortfolio = (): UsePortfolioReturn => {
  const addStock = useCallback((): Stock => ({
    symbol: '',
    amount: 10000,
    investmentType: 'lump_sum',
    dcaPeriods: 12,
    assetType: ASSET_TYPES.STOCK
  }), []);

  const validatePortfolio = useCallback((stocks: Stock[]): string[] => {
    const errors: string[] = [];
    
    if (stocks.length === 0) {
      errors.push('최소 하나의 종목을 추가해야 합니다.');
    }

    // 중복 종목 검사 (현금 제외)
    const symbols = stocks
      .filter(stock => stock.assetType !== ASSET_TYPES.CASH)
      .map(stock => stock.symbol.toUpperCase());
    const duplicates = symbols.filter((symbol, index) => symbols.indexOf(symbol) !== index);
    
    if (duplicates.length > 0) {
      errors.push(`중복된 종목이 있습니다: ${[...new Set(duplicates)].join(', ')}`);
    }

    return errors;
  }, []);

  return {
    addStock,
    addCash,
    updateStock,
    removeStock,
    getTotalAmount,
    getPortfolioWeights,
    validatePortfolio
  };
};
```

#### useFormValidation (폼 검증)
```typescript
// hooks/useFormValidation.ts
export const useFormValidation = (): UseFormValidationReturn => {
  const [errors, setErrorsState] = useState<string[]>([]);

  const validateForm = useCallback((formState: BacktestFormState): boolean => {
    const newErrors: string[] = [];
    
    // 포트폴리오 검증
    formState.portfolio.forEach((stock, index) => {
      if (!stock.symbol.trim()) {
        newErrors.push(`${index + 1}번째 종목의 심볼을 입력해주세요.`);
      }
      if (stock.amount < 100) {
        newErrors.push(`${index + 1}번째 종목의 투자 금액은 최소 $100 이상이어야 합니다.`);
      }
    });
    
    // 날짜 검증
    if (formState.dates.startDate >= formState.dates.endDate) {
      newErrors.push('시작 날짜는 종료 날짜보다 이전이어야 합니다.');
    }

    setErrorsState(newErrors);
    return newErrors.length === 0;
  }, []);

  return {
    errors,
    isValid: errors.length === 0,
    validateForm,
    setErrors: setErrorsState
  };
};
```

#### useStrategyParams (전략 파라미터 관리)
```typescript
// hooks/useStrategyParams.ts
export const useStrategyParams = (): UseStrategyParamsReturn => {
  const getStrategyParams = useCallback((strategy: string, currentParams: Record<string, any>): StrategyParam[] => {
    const config = STRATEGY_CONFIGS[strategy as keyof typeof STRATEGY_CONFIGS];
    if (!config || !config.parameters) return [];

    return Object.entries(config.parameters).map(([key, paramConfig]) => {
      const param = paramConfig as any;
      return {
        key,
        label: getParamLabel(key),
        value: currentParams[key] !== undefined ? currentParams[key] : param.default,
        min: param.min,
        max: param.max,
        default: param.default
      };
    });
  }, []);

  const getParamLabel = useCallback((key: string): string => {
    const labelMap: Record<string, string> = {
      'short_window': '단기 이동평균 기간',
      'long_window': '장기 이동평균 기간',
      'rsi_period': 'RSI 기간',
      'rsi_oversold': 'RSI 과매도 기준',
      'rsi_overbought': 'RSI 과매수 기준'
    };
    return labelMap[key] || key;
  }, []);

  return {
    getStrategyConfig,
    getDefaultParams,
    getStrategyParams,
    updateParam,
    validateParams,
    getParamLabel
  };
};
```

### 4. 4.3 리팩터링으로 추가된 커스텀 훅들

#### 4.1. useExchangeRate (환율 데이터 페칭)
```typescript
// hooks/useExchangeRate.ts
export const useExchangeRate = ({ 
  startDate, 
  endDate, 
  enabled = true 
}: UseExchangeRateParams): UseExchangeRateReturn => {
  // USD/KRW 환율 데이터 페칭
  // 자동 재시도 및 에러 처리
  // 데이터 캐싱
}

// 사용법
const { exchangeData, loading, error, refetch } = useExchangeRate({
  startDate: '2023-01-01',
  endDate: '2023-12-31'
});
```

#### 4.2. useFormInput (범용 폼 입력 관리)
```typescript
// hooks/useFormInput.ts
export const useFormInput = ({
  initialValue = '',
  validate,
  transform
}: UseFormInputOptions = {}): UseFormInputReturn => {
  // 값 관리, 검증, 에러 처리 통합
  // 터치 상태 기반 검증
  // 변환 함수 지원
}

// 사용법
const symbolInput = useFormInput({
  initialValue: '',
  validate: (value) => value.trim() ? null : '종목 심볼을 입력해주세요',
  transform: (value) => value.toUpperCase()
});

const amountInput = useFormInput({
  initialValue: 10000,
  validate: (value) => Number(value) >= 100 ? null : '최소 $100 이상 입력해주세요',
  transform: (value) => Number(value)
});
```

#### 4.3. useDropdown (드롭다운 상태 관리)
```typescript
// hooks/useDropdown.ts
export const useDropdown = ({
  initialOpen = false,
  closeOnOutsideClick = true
}: UseDropdownOptions = {}): UseDropdownReturn => {
  // 열기/닫기 상태 관리
  // 외부 클릭 감지
  // 키보드 이벤트 처리 (ESC)
  // 포커스 관리
}

// 사용법
const strategyDropdown = useDropdown({
  closeOnOutsideClick: true
});

<div>
  <button 
    ref={strategyDropdown.triggerRef}
    onClick={strategyDropdown.toggle}
  >
    전략 선택 {strategyDropdown.isOpen ? '▲' : '▼'}
  </button>
  
  {strategyDropdown.isOpen && (
    <div ref={strategyDropdown.dropdownRef}>
      {/* 드롭다운 옵션들 */}
    </div>
  )}
</div>
```

#### 4.4. useTooltip (툴팁 상태 관리)
```typescript
// hooks/useTooltip.ts
export const useTooltip = ({
  delay = 300,
  offset = 8,
  placement = 'auto'
}: UseTooltipOptions = {}): UseTooltipReturn => {
  // 마우스 호버 감지
  // 자동 포지셔닝
  // 지연 표시 기능
  // 화면 경계 고려
}

// 사용법
const helpTooltip = useTooltip({
  delay: 500,
  placement: 'top'
});

<div>
  <span 
    ref={helpTooltip.targetRef}
    onMouseEnter={helpTooltip.show}
    onMouseLeave={helpTooltip.hide}
  >
    도움말
  </span>
  
  {helpTooltip.isVisible && (
    <div 
      ref={helpTooltip.tooltipRef}
      style={{
        position: 'fixed',
        left: helpTooltip.position.x,
        top: helpTooltip.position.y,
        zIndex: 1000
      }}
    >
      이것은 도움말입니다.
    </div>
  )}
</div>
```

### 5. 적용된 컴포넌트 리팩터링

#### 5.1. ExchangeRateChart 리팩터링
```typescript
// Before (174줄)
const ExchangeRateChart = ({ startDate, endDate, className }) => {
  const [exchangeData, setExchangeData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchExchangeRate = async () => {
      // 복잡한 API 호출 로직...
    };
    fetchExchangeRate();
  }, [startDate, endDate]);

  // 복잡한 렌더링 로직...
};

// After (훅 사용으로 80% 간소화)
const ExchangeRateChart = ({ startDate, endDate, className }) => {
  const { exchangeData, loading, error } = useExchangeRate({ startDate, endDate });

  // 포맷팅 함수들...
  // 깔끔한 렌더링 로직...
};
```

### 3. Context API 활용
#### 3.1. BacktestContext (전역 상태 관리)
export const BacktestProvider: React.FC<BacktestProviderProps> = ({ 
  children, 
  initialState 
}) => {
  const [state, dispatch] = useReducer(
    backtestFormReducer,
    { ...initialBacktestFormState, ...initialState }
  );

  const actions = {
    updateStock: (index: number, field: keyof Stock, value: string | number) => {
      dispatch({ type: 'UPDATE_STOCK', payload: { index, field, value } });
    },
    // 기타 액션들...
  };

  return (
    <BacktestContext.Provider value={{ state, actions }}>
      {children}
    </BacktestContext.Provider>
  );
};

export const useBacktestContext = (): BacktestContextType => {
  const context = useContext(BacktestContext);
  if (context === undefined) {
    throw new Error('useBacktestContext must be used within a BacktestProvider');
  }
  return context;
};
```

## 컴포넌트에서의 사용

### UnifiedBacktestForm 리팩터링 결과
```typescript
// components/UnifiedBacktestForm.tsx
const UnifiedBacktestForm: React.FC<UnifiedBacktestFormProps> = ({ onSubmit, loading = false }) => {
  const { state, actions, helpers } = useBacktestForm();
  const { errors, validateForm, setErrors } = useFormValidation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    actions.setLoading(true);
    
    const isFormValid = validateForm(state);
    if (!isFormValid) {
      actions.setLoading(false);
      return;
    }

    try {
      // 백엔드 API 호출 데이터 준비
      const portfolioData = state.portfolio.map(stock => ({
        symbol: stock.symbol.toUpperCase(),
        amount: stock.amount,
        investment_type: stock.investmentType,
        dca_periods: stock.dcaPeriods || 12,
        asset_type: stock.assetType || ASSET_TYPES.STOCK
      }));

      await onSubmit({
        portfolio: portfolioData,
        start_date: state.dates.startDate,
        end_date: state.dates.endDate,
        strategy: state.strategy.selectedStrategy,
        strategy_params: generateStrategyParams(),
        commission: state.settings.commission / 100,
        rebalance_frequency: state.settings.rebalanceFrequency
      });
    } catch (error) {
      setErrors([error.message]);
    } finally {
      actions.setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* 분리된 컴포넌트들에 state와 actions 전달 */}
      <PortfolioForm
        portfolio={state.portfolio}
        updateStock={actions.updateStock}
        addStock={actions.addStock}
        addCash={actions.addCash}
        removeStock={actions.removeStock}
        getTotalAmount={helpers.getTotalAmount}
      />
      
      <DateRangeForm
        startDate={state.dates.startDate}
        setStartDate={actions.setStartDate}
        endDate={state.dates.endDate}
        setEndDate={actions.setEndDate}
      />
      
      <StrategyForm
        selectedStrategy={state.strategy.selectedStrategy}
        setSelectedStrategy={actions.setSelectedStrategy}
        strategyParams={state.strategy.strategyParams}
        updateStrategyParam={actions.updateStrategyParam}
      />
      
      <CommissionForm
        rebalanceFrequency={state.settings.rebalanceFrequency}
        setRebalanceFrequency={actions.setRebalanceFrequency}
        commission={state.settings.commission}
        setCommission={actions.setCommission}
      />
      
      <button type="submit" disabled={loading || state.ui.isLoading}>
        백테스트 실행
      </button>
    </form>
  );
};
```

## 4.4 성능 최적화 구현 (2024-12-20 완료)

### 메모이제이션 적용

#### 차트 컴포넌트 최적화
```typescript
// hooks/useChartOptimization.ts (178줄)
export const useChartOptimization = () => {
  // 차트 색상 설정 메모이제이션
  const chartColors = useMemo(() => ({
    primary: '#0d6efd',
    success: '#198754',
    danger: '#dc3545',
    // ... 기타 색상들
  }), []);

  // 차트 기본 설정 메모이제이션
  const chartConfig = useMemo(() => ({
    margin: { top: 20, right: 30, left: 20, bottom: 5 },
    strokeWidth: { thin: 1, normal: 1.5, thick: 2, bold: 3 },
    opacity: { low: 0.1, medium: 0.3, high: 0.6, full: 1.0 },
    heights: { small: 200, medium: 300, large: 400, xlarge: 500 }
  }), []);

  // 데이터 변환 함수 메모이제이션
  const transformChartData = useCallback((data: any[], transformFn?: (item: any) => any) => {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map(item => {
      const baseItem = {
        ...item,
        // 숫자 데이터 안전성 보장
        ...(item.value !== undefined && { value: Number(item.value) || 0 }),
        ...(item.price !== undefined && { price: Number(item.price) || 0 })
      };
      return transformFn ? transformFn(baseItem) : baseItem;
    });
  }, []);

  return { chartColors, chartConfig, transformChartData, /* ... */ };
};
```

#### React.memo 적용 사례
```typescript
// components/EquityChart.tsx (최적화 후)
const EquityChart: React.FC<EquityChartProps> = memo(({ data }) => {
  // 데이터 안전성 검사 및 메모이제이션
  const safeData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map(item => ({
      ...item,
      return_pct: Number(item.return_pct) || 0,
      drawdown_pct: Number(item.drawdown_pct) || 0
    }));
  }, [data]);

  // 차트 설정 메모이제이션
  const chartConfig = useMemo(() => ({
    margin: { top: 20, right: 30, left: 20, bottom: 5 },
    strokeWidth: 2,
    fillOpacity: 0.3
  }), []);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={safeData} margin={chartConfig.margin}>
        {/* 차트 내용 */}
      </ComposedChart>
    </ResponsiveContainer>
  );
});

EquityChart.displayName = 'EquityChart';
```

### 코드 분할 (Code Splitting)

#### 지연 로딩 컴포넌트
```typescript
// components/lazy/LazyChartComponents.tsx
import { lazy } from 'react';

// 차트 컴포넌트들의 지연 로딩
export const LazyEquityChart = lazy(() => import('../EquityChart'));
export const LazyOHLCChart = lazy(() => import('../OHLCChart'));
export const LazyTradesChart = lazy(() => import('../TradesChart'));
export const LazyStockPriceChart = lazy(() => import('../StockPriceChart'));

// 뉴스 관련 컴포넌트 지연 로딩
export const LazyStockVolatilityNews = lazy(() => import('../StockVolatilityNews'));
```

#### 로딩 상태 컴포넌트
```typescript
// components/common/ChartLoading.tsx
const ChartLoading: React.FC<ChartLoadingProps> = ({ 
  height = 320, 
  message = "차트를 로딩 중입니다..." 
}) => {
  return (
    <div 
      className="flex items-center justify-center bg-gray-50 rounded-lg border"
      style={{ height }}
    >
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
        <p className="text-gray-600 text-sm">{message}</p>
      </div>
    </div>
  );
};
```

### 성능 모니터링

#### 렌더링 성능 측정
```typescript
// components/common/PerformanceMonitor.tsx (140줄)
export const useRenderPerformance = (componentName: string) => {
  const renderStartTime = useRef<number>();
  const renderCount = useRef<number>(0);

  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      renderCount.current += 1;
      const renderEndTime = performance.now();
      const renderDuration = renderEndTime - (renderStartTime.current || renderEndTime);
      
      // 성능 측정 마크 생성
      performance.mark(`${componentName}-render-end`);
      
      console.log(`⏱️ [Render Performance] ${componentName}:`, {
        renderCount: renderCount.current,
        renderDuration: `${renderDuration.toFixed(2)}ms`,
        timestamp: new Date().toISOString()
      });
    }
  });
};

// 사용법
const StockPriceChart = memo(({ stocksData }) => {
  useRenderPerformance('StockPriceChart');
  // ... 컴포넌트 로직
});
```

#### 메모리 사용량 모니터링
```typescript
export const useMemoryMonitor = (componentName: string) => {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    const checkMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
  console.log(`[Memory] ${componentName}:`, {
          used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
          total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
          limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`
        });
      }
    };

    const interval = setInterval(checkMemory, 5000);
    return () => clearInterval(interval);
  }, [componentName]);
};
```

### 번들 최적화

#### Vite 설정 개선
```typescript
// vite.config.ts
export default defineConfig(({ mode }) => ({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React 관련 라이브러리 분리
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // 차트 라이브러리 분리
          'chart-vendor': ['recharts'],
          // 아이콘 라이브러리 분리
          'icon-vendor': ['react-icons'],
          // 유틸리티 라이브러리 분리
          'util-vendor': ['axios']
        }
      }
    },
    // 청크 크기 경고 임계값 설정 (1MB)
    chunkSizeWarningLimit: 1000,
    // 소스맵 생성 (개발 시에만)
    sourcemap: mode === 'development'
  }
}))
```

#### 번들 분석 스크립트
```json
// package.json
{
  "scripts": {
    "build:analyze": "tsc && vite build --mode analyze"
  }
}
```

### 성능 최적화 결과

#### 달성한 개선 사항
1. **메모리 사용량 감소**: React.memo와 useMemo로 불필요한 재렌더링 방지
2. **번들 크기 최적화**: 라이브러리별 청크 분리로 초기 로딩 속도 개선
3. **지연 로딩**: 차트 컴포넌트들의 조건부 로딩으로 초기 렌더링 속도 향상
4. **성능 모니터링**: 개발 환경에서 실시간 성능 추적 가능

#### 최적화 전후 비교
- **EquityChart**: 기본 컴포넌트 → memo + useMemo 적용
- **OHLCChart**: 복잡한 데이터 처리 → 데이터 변환 로직 메모이제이션
- **TradesChart**: 반복 렌더링 → useCallback으로 이벤트 핸들러 최적화
- **번들 크기**: 단일 청크 → 라이브러리별 분리로 캐싱 효율성 증대

## 리팩터링 결과

### Before (기존 구조)
```typescript
// 515줄의 거대한 컴포넌트
const UnifiedBacktestForm = () => {
  const [portfolio, setPortfolio] = useState([...]);
  const [startDate, setStartDate] = useState('...');
  const [endDate, setEndDate] = useState('...');
  const [selectedStrategy, setSelectedStrategy] = useState('...');
  const [strategyParams, setStrategyParams] = useState({});
  const [rebalanceFrequency, setRebalanceFrequency] = useState('...');
  const [commission, setCommission] = useState(0.2);
  const [errors, setErrors] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // 수십 개의 함수들...
  const addStock = () => { /* ... */ };
  const removeStock = () => { /* ... */ };
  const updateStock = () => { /* ... */ };
  const validatePortfolio = () => { /* ... */ };
  
  // 복잡한 JSX...
};
```

### After (리팩터링 후)
```typescript
// 166줄의 깔끔한 컴포넌트
const UnifiedBacktestForm = ({ onSubmit, loading = false }) => {
  const { state, actions, helpers } = useBacktestForm();
  const { errors, validateForm, setErrors } = useFormValidation();

  // 간단한 핸들러
  const handleSubmit = async (e) => { /* ... */ };

  // 분리된 컴포넌트들로 구성된 JSX
  return (
    <form onSubmit={handleSubmit}>
      <PortfolioForm {...portfolioProps} />
      <DateRangeForm {...dateProps} />
      <StrategyForm {...strategyProps} />
      <CommissionForm {...commissionProps} />
    </form>
  );
};
```

### 개선점

1. **코드 크기 축소**: 515줄 → 166줄 (68% 감소)
2. **관심사 분리**: 각 커스텀 훅이 특정 기능에 집중
3. **재사용성 향상**: 훅들을 다른 컴포넌트에서도 활용 가능
4. **타입 안전성**: 강타입 인터페이스로 버그 방지
5. **테스트 용이성**: 각 훅을 독립적으로 테스트 가능
6. **성능 최적화**: useCallback, useMemo로 불필요한 리렌더링 방지

## 성능 최적화 팁

### 상태 업데이트 최적화
```typescript
// 좋은 예: 함수형 업데이트
const updatePortfolioItem = useCallback((index: number, updates: Partial<Stock>) => {
  dispatch({ 
    type: 'UPDATE_STOCK', 
    payload: { index, field: 'amount', value: updates.amount } 
  });
}, []);

// 나쁜 예: 직접 상태 변경
const updatePortfolioItem = (index, updates) => {
  const newPortfolio = [...portfolio];
  newPortfolio[index] = { ...newPortfolio[index], ...updates };
  setPortfolio(newPortfolio);
};
```

### 메모이제이션 활용
```typescript
// 비싼 계산 메모이제이션
const totalAmount = useMemo(() => {
  return state.portfolio.reduce((sum, stock) => sum + stock.amount, 0);
}, [state.portfolio]);

// 이벤트 핸들러 메모이제이션
const handleStockUpdate = useCallback((index: number, field: keyof Stock, value: any) => {
  actions.updateStock(index, field, value);
}, [actions.updateStock]);
```

## 로컬 상태 관리

### useState 패턴
```typescript
// 단순 상태 관리
function StatsSummary({ initialStats }: StatsSummaryProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<string>('return');
  
  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);
  
  return (
    <Card>
      <Card.Header onClick={toggleExpanded}>
        성과 요약 {isExpanded ? '▲' : '▼'}
      </Card.Header>
      {isExpanded && (
        <Card.Body>
          <MetricSelector 
            selected={selectedMetric}
            onChange={setSelectedMetric}
          />
          <MetricDisplay metric={selectedMetric} stats={initialStats} />
        </Card.Body>
      )}
    </Card>
  );
}
```

### useReducer 패턴 (복잡한 상태)
```typescript
// 복잡한 폼 상태 관리
interface FormState {
  formData: BacktestFormData;
  errors: Record<string, string>;
  isSubmitting: boolean;
  touched: Record<string, boolean>;
}

type FormAction = 
  | { type: 'SET_FIELD'; field: string; value: any }
  | { type: 'SET_ERROR'; field: string; error: string }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'SET_SUBMITTING'; isSubmitting: boolean }
  | { type: 'SET_TOUCHED'; field: string };

function formReducer(state: FormState, action: FormAction): FormState {
  switch (action.type) {
    case 'SET_FIELD':
      return {
        ...state,
        formData: {
          ...state.formData,
          [action.field]: action.value
        },
        errors: {
          ...state.errors,
          [action.field]: '' // 필드 변경 시 에러 클리어
        }
      };
      
    case 'SET_ERROR':
      return {
        ...state,
        errors: {
          ...state.errors,
          [action.field]: action.error
        }
      };
      
    case 'CLEAR_ERRORS':
      return {
        ...state,
        errors: {}
      };
      
    case 'SET_SUBMITTING':
      return {
        ...state,
        isSubmitting: action.isSubmitting
      };
      
    case 'SET_TOUCHED':
      return {
        ...state,
        touched: {
          ...state.touched,
          [action.field]: true
        }
      };
      
    default:
      return state;
  }
}

function UnifiedBacktestForm({ onSubmit }: FormProps) {
  const [state, dispatch] = useReducer(formReducer, initialFormState);
  
  const setField = useCallback((field: string, value: any) => {
    dispatch({ type: 'SET_FIELD', field, value });
  }, []);
  
  const setError = useCallback((field: string, error: string) => {
    dispatch({ type: 'SET_ERROR', field, error });
  }, []);
  
  // 폼 검증 로직
  const validateForm = useCallback(() => {
    const errors = validateBacktestForm(state.formData);
    Object.entries(errors).forEach(([field, error]) => {
      setError(field, error);
    });
    return Object.keys(errors).length === 0;
  }, [state.formData, setError]);
  
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    dispatch({ type: 'SET_SUBMITTING', isSubmitting: true });
    
    try {
      await onSubmit(state.formData);
      dispatch({ type: 'CLEAR_ERRORS' });
    } catch (error) {
      setError('submit', error.message);
    } finally {
      dispatch({ type: 'SET_SUBMITTING', isSubmitting: false });
    }
  }, [state.formData, validateForm, onSubmit, setError]);
  
  return (
    <Form onSubmit={handleSubmit}>
      {/* 폼 필드들 */}
    </Form>
  );
}
```

## 전역 상태 관리 (Context API)

### App Context 설정
```typescript
interface AppContextType {
  // 테마 설정
  theme: 'light' | 'dark';
  updateTheme: (theme: 'light' | 'dark') => void;
  
  // API 설정
  apiBaseUrl: string;
  
  // 사용자 설정
  locale: string;
  currency: 'USD' | 'KRW';
  
  // 앱 상태
  isOnline: boolean;
  lastSyncTime: Date | null;
}

const AppContext = createContext<AppContextType | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [locale, setLocale] = useState('ko-KR');
  const [currency, setCurrency] = useState<'USD' | 'KRW'>('USD');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  
  // API Base URL 계산
  const apiBaseUrl = useMemo(() => {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      const protocol = window.location.protocol;
      
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return `${protocol}//backtest-be.yeonjae.kr`;
      }
    }
    return 'http://localhost:8001';
  }, []);
  
  // 온라인 상태 모니터링
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  // 테마 변경 함수
  const updateTheme = useCallback((newTheme: 'light' | 'dark') => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    
    // CSS 변수 업데이트
    document.documentElement.setAttribute('data-theme', newTheme);
  }, []);
  
  // 로컬 스토리지에서 설정 복원
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
    if (savedTheme) {
      updateTheme(savedTheme);
    }
    
    const savedLocale = localStorage.getItem('locale');
    if (savedLocale) {
      setLocale(savedLocale);
    }
    
    const savedCurrency = localStorage.getItem('currency') as 'USD' | 'KRW';
    if (savedCurrency) {
      setCurrency(savedCurrency);
    }
  }, [updateTheme]);
  
  const value = useMemo(() => ({
    theme,
    updateTheme,
    apiBaseUrl,
    locale,
    currency,
    isOnline,
    lastSyncTime
  }), [theme, updateTheme, apiBaseUrl, locale, currency, isOnline, lastSyncTime]);
  
  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// Context Hook
export function useAppContext(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}
```

## 서버 상태 관리

### API 호출 커스텀 Hook
```typescript
interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

type ApiAction<T> = 
  | { type: 'LOADING' }
  | { type: 'SUCCESS'; data: T }
  | { type: 'ERROR'; error: string }
  | { type: 'RESET' };

function apiReducer<T>(state: ApiState<T>, action: ApiAction<T>): ApiState<T> {
  switch (action.type) {
    case 'LOADING':
      return { ...state, loading: true, error: null };
    case 'SUCCESS':
      return { data: action.data, loading: false, error: null };
    case 'ERROR':
      return { ...state, loading: false, error: action.error };
    case 'RESET':
      return { data: null, loading: false, error: null };
    default:
      return state;
  }
}

// 백테스트 API Hook
export function useBacktestApi() {
  const [state, dispatch] = useReducer(apiReducer<BacktestResult>, {
    data: null,
    loading: false,
    error: null
  });
  
  const { apiBaseUrl } = useAppContext();
  
  const executeBacktest = useCallback(async (request: BacktestRequest) => {
    dispatch({ type: 'LOADING' });
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/backtest/portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.status !== 'success') {
        throw new Error(result.message || '백테스트 실행 중 오류가 발생했습니다');
      }
      
      dispatch({ type: 'SUCCESS', data: result.data });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다';
      dispatch({ type: 'ERROR', error: errorMessage });
    }
  }, [apiBaseUrl]);
  
  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);
  
  return {
    ...state,
    executeBacktest,
    reset
  };
}

// 뉴스 API Hook
export function useNewsApi(ticker?: string, date?: string) {
  const [state, dispatch] = useReducer(apiReducer<NewsItem[]>, {
    data: null,
    loading: false,
    error: null
  });
  
  const { apiBaseUrl } = useAppContext();
  
  const fetchNews = useCallback(async (searchTicker: string, searchDate?: string) => {
    dispatch({ type: 'LOADING' });
    
    try {
      const url = searchDate
        ? `${apiBaseUrl}/api/v1/naver-news/date/${searchTicker}/${searchDate}`
        : `${apiBaseUrl}/api/v1/naver-news/ticker/${searchTicker}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`뉴스 조회 실패: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.status === 'success') {
        dispatch({ type: 'SUCCESS', data: result.data.news_list || [] });
      } else {
        throw new Error(result.message || '뉴스 조회 중 오류가 발생했습니다');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다';
      dispatch({ type: 'ERROR', error: errorMessage });
    }
  }, [apiBaseUrl]);
  
  // 자동 호출 (선택적)
  useEffect(() => {
    if (ticker) {
      fetchNews(ticker, date);
    }
  }, [ticker, date, fetchNews]);
  
  return {
    ...state,
    fetchNews
  };
}
```

## 상태 동기화 패턴

### 부모-자식 컴포넌트 간 상태 동기화
```typescript
// 부모 컴포넌트: 상태 소유 및 관리
function BacktestContainer() {
  const [backtestData, setBacktestData] = useState<BacktestResult | null>(null);
  const [formData, setFormData] = useState<BacktestFormData>(initialFormData);
  const { executeBacktest, loading, error } = useBacktestApi();
  
  const handleFormSubmit = useCallback(async (data: BacktestFormData) => {
    setFormData(data);
    const result = await executeBacktest(data);
    if (result) {
      setBacktestData(result);
    }
  }, [executeBacktest]);
  
  const handleFormChange = useCallback((newFormData: BacktestFormData) => {
    setFormData(newFormData);
    // 폼 변경 시 기존 결과 클리어
    setBacktestData(null);
  }, []);
  
  return (
    <Container>
      <UnifiedBacktestForm
        initialData={formData}
        onSubmit={handleFormSubmit}
        onChange={handleFormChange}
        loading={loading}
        error={error}
      />
      
      {backtestData && (
        <UnifiedBacktestResults
          data={backtestData}
          formData={formData}
        />
      )}
    </Container>
  );
}

// 자식 컴포넌트: Props를 통한 상태 수신
function UnifiedBacktestForm({ 
  initialData, 
  onSubmit, 
  onChange, 
  loading, 
  error 
}: FormProps) {
  const [localFormData, setLocalFormData] = useState(initialData);
  
  // 부모의 initialData 변경 시 동기화
  useEffect(() => {
    setLocalFormData(initialData);
  }, [initialData]);
  
  // 로컬 상태 변경 시 부모에게 알림
  const handleFieldChange = useCallback((field: string, value: any) => {
    const newFormData = {
      ...localFormData,
      [field]: value
    };
    setLocalFormData(newFormData);
    onChange?.(newFormData);
  }, [localFormData, onChange]);
  
  return (
    <Form onSubmit={(e) => {
      e.preventDefault();
      onSubmit(localFormData);
    }}>
      {/* 폼 필드들 */}
    </Form>
  );
}
```

### 형제 컴포넌트 간 상태 공유
```typescript
// 공통 부모를 통한 상태 공유
function ChartsContainer({ backtestData }: ChartsContainerProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>('all');
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['sma20']);
  
  // 시간 범위에 따른 데이터 필터링
  const filteredData = useMemo(() => {
    return filterDataByTimeRange(backtestData, selectedTimeRange);
  }, [backtestData, selectedTimeRange]);
  
  return (
    <Row>
      <Col lg={8}>
        <OHLCChart
          data={filteredData.ohlcData}
          indicators={selectedIndicators}
        />
        <EquityChart
          data={filteredData.equityData}
        />
      </Col>
      <Col lg={4}>
        <ChartControls
          timeRange={selectedTimeRange}
          onTimeRangeChange={setSelectedTimeRange}
          indicators={selectedIndicators}
          onIndicatorsChange={setSelectedIndicators}
        />
        <StatsSummary
          stats={filteredData.stats}
        />
      </Col>
    </Row>
  );
}
```

## 성능 최적화

### 상태 업데이트 최적화
```typescript
// 객체 상태 업데이트 최적화
const updatePortfolioItem = useCallback((index: number, updates: Partial<PortfolioStock>) => {
  setPortfolio(prevPortfolio => 
    prevPortfolio.map((item, i) => 
      i === index ? { ...item, ...updates } : item
    )
  );
}, []);

// 배열 상태 업데이트 최적화
const addPortfolioItem = useCallback((newItem: PortfolioStock) => {
  setPortfolio(prevPortfolio => [...prevPortfolio, newItem]);
}, []);

const removePortfolioItem = useCallback((index: number) => {
  setPortfolio(prevPortfolio => 
    prevPortfolio.filter((_, i) => i !== index)
  );
}, []);
```

### 메모이제이션을 통한 리렌더링 방지
```typescript
// 비싼 계산 메모이제이션
const processedData = useMemo(() => {
  return backtestData?.ohlc_data?.map(point => ({
    ...point,
    formattedDate: formatDate(point.timestamp),
    priceChange: calculatePriceChange(point),
    volume: formatVolume(point.volume)
  })) || [];
}, [backtestData?.ohlc_data]);

// 이벤트 핸들러 메모이제이션
const handleChartInteraction = useCallback((event: ChartEvent) => {
  if (event.type === 'zoom') {
    setZoomLevel(event.zoomLevel);
  } else if (event.type === 'pan') {
    setViewport(event.viewport);
  }
}, []);
```
