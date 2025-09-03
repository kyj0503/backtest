# 상태 관리 가이드

React 백테스팅 시스템의 상태 관리 전략과 패턴을 설명합니다.

## 상태 관리 철학

### 설계 원칙
1. **로컬 상태 우선**: 전역 상태는 꼭 필요한 경우에만 사용
2. **단방향 데이터 흐름**: Props down, Events up 패턴 준수
3. **상태 정규화**: 중복 데이터 방지, 단일 진실 공급원 유지
4. **타입 안전성**: TypeScript를 활용한 상태 타입 안전성 보장

### 상태 분류
```typescript
// 로컬 상태: 컴포넌트 내부에서만 사용
const [isLoading, setIsLoading] = useState(false);
const [errors, setErrors] = useState<Record<string, string>>({});

// 공유 상태: 여러 컴포넌트 간 공유 (Context API 사용)
const { theme, apiBaseUrl, updateTheme } = useAppContext();

// 서버 상태: API에서 가져온 데이터 (커스텀 Hook 사용)
const { data, loading, error, refetch } = useBacktestApi();
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