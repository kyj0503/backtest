# 상태 관리 가이드

React 백테스팅 시스템의 상태 관리 전략과 패턴을 설명합니다.

## 상태 관리 철학

### 설계 원칙
1. **로컬 상태 우선**: 전역 상태는 꼭 필요한 경우에만 사용
2. **단방향 데이터 흐름**: Props down, Events up 패턴 준수
3. **상태 정규화**: 중복 데이터 방지, 단일 진실 공급원 유지
4. **타입 안전성**: TypeScript를 활용한 상태 타입 안전성 보장

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

### 3. Context API 활용

#### BacktestContext (전역 상태 관리)
```typescript
// contexts/BacktestContext.tsx
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
// ✅ 좋은 예: 함수형 업데이트
const updatePortfolioItem = useCallback((index: number, updates: Partial<Stock>) => {
  dispatch({ 
    type: 'UPDATE_STOCK', 
    payload: { index, field: 'amount', value: updates.amount } 
  });
}, []);

// ❌ 나쁜 예: 직접 상태 변경
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