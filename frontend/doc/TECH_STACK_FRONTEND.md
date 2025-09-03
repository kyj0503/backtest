# 프론트엔드 기술 스택 가이드

React + TypeScript 기반 백테스팅 시스템 프론트엔드의 기술 선택과 구현 상세를 설명합니다.

## 목차
- [React 18 아키텍처](#react-18-아키텍처)
- [TypeScript 타입 시스템](#typescript-타입-시스템)
- [Vite 빌드 시스템](#vite-빌드-시스템)
- [UI 라이브러리 선택](#ui-라이브러리-선택)
- [차트 라이브러리 심화](#차트-라이브러리-심화)
- [상태 관리 전략](#상태-관리-전략)
- [성능 최적화](#성능-최적화)
- [테스팅 접근법](#테스팅-접근법)

## React 18 아키텍처

### 컴포넌트 설계 철학

#### 컴포넌트 계층 구조
```
App.tsx
├── UnifiedBacktestForm.tsx (폼 관리)
├── UnifiedBacktestResults.tsx (결과 표시)
│   ├── EquityChart.tsx (수익률 차트)
│   ├── OHLCChart.tsx (캔들스틱 차트)
│   ├── StockPriceChart.tsx (개별 주가 차트)
│   ├── ExchangeRateChart.tsx (환율 차트)
│   └── StockVolatilityNews.tsx (뉴스 컴포넌트)
└── components/
    ├── StatsSummary.tsx (성과 요약)
    ├── TradesChart.tsx (거래 내역)
    └── ErrorBoundary.tsx (에러 처리)
```

**설계 원칙**:
1. **단일 책임 원칙**: 각 컴포넌트는 하나의 명확한 기능
2. **컴포지션 우선**: 상속보다 컴포넌트 조합으로 기능 구성
3. **재사용성**: 범용적 컴포넌트와 도메인별 컴포넌트 분리
4. **테스트 가능성**: 각 컴포넌트 독립적 테스트 가능

#### 컴포넌트 인터페이스 설계
```typescript
interface ChartComponentProps {
  data: ChartDataPoint[];
  loading?: boolean;
  error?: string | null;
  onInteraction?: (event: ChartInteractionEvent) => void;
  className?: string;
  height?: number;
}

// 일관된 Props 패턴
interface BacktestResultsProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}
```

**인터페이스 원칙**:
- **선택적 속성**: 기본값으로 사용 편의성 제공
- **이벤트 핸들러**: 표준화된 이벤트 처리 패턴
- **스타일링 지원**: className으로 외부 스타일링 허용
- **타입 안전성**: 잘못된 데이터 전달 컴파일 타임 차단

### React 18 신기능 활용

#### Concurrent Features
```typescript
import { useDeferredValue, useTransition } from 'react';

function BacktestResults({ data }: BacktestResultsProps) {
  const [isPending, startTransition] = useTransition();
  const deferredData = useDeferredValue(data);
  
  const handleDataUpdate = (newData: BacktestData) => {
    startTransition(() => {
      setBacktestData(newData);
    });
  };
  
  return (
    <div>
      {isPending && <LoadingSpinner />}
      <Charts data={deferredData} />
    </div>
  );
}
```

**Concurrent Features 활용 이유**:
1. **사용자 경험 향상**: 대용량 차트 렌더링 시 UI 블로킹 방지
2. **우선순위 기반 렌더링**: 중요한 UI 업데이트 우선 처리
3. **부드러운 전환**: 데이터 변경 시 끊김 없는 애니메이션
4. **반응성 유지**: 사용자 입력에 즉각적 반응

#### Error Boundary 패턴
```typescript
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Chart rendering error:', error, errorInfo);
    // 에러 리포팅 서비스로 전송
  }

  render() {
    if (this.state.hasError) {
      return <ChartErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

**Error Boundary 필요성**:
- **차트 렌더링 안정성**: 복잡한 차트 렌더링 오류 격리
- **사용자 경험 보호**: 일부 오류가 전체 앱 크래시 방지
- **디버깅 지원**: 에러 정보 수집으로 문제 해결 지원

## TypeScript 타입 시스템

### 도메인 모델링

#### API 응답 타입 정의
```typescript
// 백엔드 응답과 정확히 매칭되는 타입
interface ChartDataResponse {
  ticker: string;
  strategy: string;
  start_date: string;
  end_date: string;
  ohlc_data: OHLCDataPoint[];
  equity_data: EquityPoint[];
  trade_markers: TradeMarker[];
  indicators: IndicatorData[];
  summary_stats: SummaryStats;
}

// 프론트엔드 전용 타입 확장
interface ChartDisplayData extends ChartDataResponse {
  displayOptions: ChartDisplayOptions;
  interactionState: ChartInteractionState;
}
```

**타입 설계 전략**:
1. **API 계약 준수**: 백엔드 응답 구조와 정확한 매칭
2. **확장성**: 프론트엔드 전용 속성 추가 가능
3. **재사용성**: 공통 타입 정의로 코드 중복 제거
4. **유지보수성**: 타입 변경 시 컴파일 타임 오류로 영향 범위 파악

#### 유니언 타입과 타입 가드
```typescript
type BacktestData = ChartData | PortfolioData;

function isPortfolioData(data: BacktestData): data is PortfolioData {
  return 'portfolio_statistics' in data;
}

function renderResults(data: BacktestData) {
  if (isPortfolioData(data)) {
    // TypeScript가 data를 PortfolioData로 추론
    return <PortfolioResults data={data} />;
  } else {
    // TypeScript가 data를 ChartData로 추론
    return <ChartResults data={data} />;
  }
}
```

**타입 가드 활용**:
- **런타임 타입 안전성**: 실행 시점 타입 검증
- **타입 좁히기**: 조건부 로직에서 정확한 타입 추론
- **가독성 향상**: 의도가 명확한 조건문 작성

### 제네릭과 유틸리티 타입

#### 재사용 가능한 제네릭 컴포넌트
```typescript
interface DataTableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  onRowClick?: (item: T) => void;
  loading?: boolean;
}

interface TableColumn<T> {
  key: keyof T;
  title: string;
  render?: (value: T[keyof T], item: T) => React.ReactNode;
  sortable?: boolean;
}

function DataTable<T>({ data, columns, onRowClick }: DataTableProps<T>) {
  // 제네릭을 활용한 타입 안전한 테이블 컴포넌트
}

// 사용 예시
<DataTable<TradeMarker>
  data={trades}
  columns={[
    { key: 'timestamp', title: '거래 시각' },
    { key: 'price', title: '가격', render: (price) => formatCurrency(price) },
    { key: 'type', title: '거래 유형' }
  ]}
/>
```

#### 유틸리티 타입 활용
```typescript
// Partial을 활용한 옵션 업데이트
type ChartOptions = {
  showGrid: boolean;
  showLegend: boolean;
  height: number;
  colors: string[];
};

function updateChartOptions(
  current: ChartOptions,
  updates: Partial<ChartOptions>
): ChartOptions {
  return { ...current, ...updates };
}

// Pick을 활용한 필수 속성 추출
type BacktestFormData = Pick<BacktestRequest, 'start_date' | 'end_date' | 'strategy'>;

// Omit을 활용한 속성 제외
type CreatePortfolioData = Omit<Portfolio, 'id' | 'created_at'>;
```

## Vite 빌드 시스템

### 개발 환경 최적화

#### HMR (Hot Module Replacement) 설정
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5174,
    hmr: {
      overlay: true, // 에러 오버레이 표시
    },
    watch: {
      usePolling: true, // Docker 환경에서 파일 변경 감지
    }
  },
  esbuild: {
    logOverride: { 'this-is-undefined-in-esm': 'silent' }
  }
});
```

**HMR 최적화 효과**:
- **개발 속도**: 파일 저장 후 0.1-0.5초 내 브라우저 반영
- **상태 보존**: 컴포넌트 상태 유지하며 코드 변경 반영
- **에러 처리**: 런타임 에러 즉시 화면 표시
- **Docker 호환**: 컨테이너 환경에서도 안정적 동작

#### 환경별 설정 분리
```typescript
// 개발 환경 설정
const development = {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true
      }
    }
  }
};

// 프로덕션 환경 설정
const production = {
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts'],
          ui: ['react-bootstrap']
        }
      }
    }
  }
};
```

### 빌드 최적화

#### 코드 스플리팅 전략
```typescript
// 라우트 기반 코드 스플리팅
const BacktestResults = lazy(() => import('./components/UnifiedBacktestResults'));
const NewsComponent = lazy(() => import('./components/StockVolatilityNews'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/results" element={<BacktestResults />} />
        <Route path="/news" element={<NewsComponent />} />
      </Routes>
    </Suspense>
  );
}
```

**번들 크기 최적화**:
- **라이브러리 분리**: vendor, charts, ui 청크 분리
- **동적 임포트**: 필요한 시점에 컴포넌트 로드
- **트리 셰이킹**: 사용하지 않는 코드 자동 제거
- **압축**: gzip 압축으로 전송 크기 감소

## UI 라이브러리 선택

### React Bootstrap 활용

#### 컴포넌트 커스터마이징
```typescript
// 테마 커스터마이징
const CustomCard: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <Card 
      className={`shadow-sm border-0 ${className || ''}`}
      {...props}
    >
      {children}
    </Card>
  );
};

// 스타일 확장
const StyledTable = styled(Table)`
  .table-success {
    --bs-table-accent-bg: #d1e7dd;
  }
  .table-danger {
    --bs-table-accent-bg: #f8d7da;
  }
`;
```

**커스터마이징 전략**:
1. **일관된 디자인**: 프로젝트 전체 일관성 유지
2. **확장성**: 기본 컴포넌트를 베이스로 기능 확장
3. **재사용성**: 커스텀 컴포넌트 라이브러리 구축
4. **유지보수성**: Bootstrap 업데이트 시 호환성 보장

#### 반응형 디자인 구현
```typescript
function ResponsiveLayout() {
  return (
    <Container fluid>
      <Row>
        <Col lg={8} md={12}>
          <ChartSection />
        </Col>
        <Col lg={4} md={12}>
          <StatsPanel />
        </Col>
      </Row>
      <Row className="mt-4">
        <Col xl={6} lg={12}>
          <NewsSection />
        </Col>
        <Col xl={6} lg={12}>
          <AnalysisSection />
        </Col>
      </Row>
    </Container>
  );
}
```

**반응형 원칙**:
- **모바일 우선**: 작은 화면부터 설계
- **브레이크포인트**: xl(1200px+), lg(992px+), md(768px+), sm(576px+)
- **콘텐츠 우선순위**: 중요한 정보 우선 배치
- **터치 친화적**: 모바일 터치 인터페이스 고려

### 스타일링 전략

#### CSS-in-JS vs CSS Modules
```typescript
// CSS-in-JS (styled-components)
const ChartContainer = styled.div`
  position: relative;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  
  .recharts-wrapper {
    font-family: 'Inter', sans-serif;
  }
`;

// CSS Modules
import styles from './Chart.module.css';

function Chart() {
  return (
    <div className={styles.chartContainer}>
      <ResponsiveContainer />
    </div>
  );
}
```

**스타일링 선택 기준**:
- **성능**: CSS Modules가 런타임 오버헤드 없음
- **동적 스타일**: CSS-in-JS가 props 기반 스타일링 유리
- **번들 크기**: CSS Modules가 더 작은 번들 크기
- **개발 경험**: CSS-in-JS가 타입 안전성 제공

## 차트 라이브러리 심화

### Recharts 아키텍처 이해

#### 컴포넌트 조합 패턴
```typescript
function OHLCChart({ data, indicators, trades }: OHLCChartProps) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        {/* 그리드와 축 */}
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={formatDateTick}
          interval="preserveStartEnd"
        />
        <YAxis domain={['dataMin - 5', 'dataMax + 5']} />
        
        {/* 캔들스틱 데이터 */}
        <Bar dataKey="candlestick" fill="#8884d8" />
        
        {/* 기술적 지표 */}
        {indicators.map((indicator, index) => (
          <Line
            key={indicator.name}
            type="monotone"
            dataKey={indicator.dataKey}
            stroke={indicator.color}
            strokeWidth={2}
            dot={false}
          />
        ))}
        
        {/* 거래 마커 */}
        <ReferenceLine 
          x={trades[0]?.timestamp} 
          stroke="red" 
          label="Buy"
        />
        
        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
```

#### 커스텀 컴포넌트 개발
```typescript
// 커스텀 캔들스틱 컴포넌트
const CustomCandlestick = ({ payload, x, y, width, height }: any) => {
  if (!payload) return null;
  
  const { open, high, low, close } = payload;
  const isGreen = close > open;
  const color = isGreen ? '#26a69a' : '#ef5350';
  
  return (
    <g>
      {/* 심지 */}
      <line
        x1={x + width / 2}
        y1={y}
        x2={x + width / 2}
        y2={y + height}
        stroke={color}
        strokeWidth={1}
      />
      {/* 몸통 */}
      <rect
        x={x + width * 0.25}
        y={isGreen ? y + (height * (high - close) / (high - low)) : y + (height * (high - open) / (high - low))}
        width={width * 0.5}
        height={Math.abs(height * (close - open) / (high - low))}
        fill={color}
      />
    </g>
  );
};
```

### 차트 성능 최적화

#### 데이터 포인트 최적화
```typescript
function optimizeChartData(data: ChartDataPoint[], maxPoints: number = 500): ChartDataPoint[] {
  if (data.length <= maxPoints) return data;
  
  // 시간 기반 샘플링
  const interval = Math.floor(data.length / maxPoints);
  const optimizedData: ChartDataPoint[] = [];
  
  for (let i = 0; i < data.length; i += interval) {
    optimizedData.push(data[i]);
  }
  
  // 마지막 데이터 포인트 반드시 포함
  if (optimizedData[optimizedData.length - 1] !== data[data.length - 1]) {
    optimizedData.push(data[data.length - 1]);
  }
  
  return optimizedData;
}

// 메모이제이션을 통한 렌더링 최적화
const MemoizedChart = React.memo(OHLCChart, (prevProps, nextProps) => {
  return (
    prevProps.data.length === nextProps.data.length &&
    prevProps.indicators.length === nextProps.indicators.length &&
    prevProps.trades.length === nextProps.trades.length
  );
});
```

**성능 최적화 기법**:
1. **데이터 샘플링**: 큰 데이터셋을 화면 해상도에 맞게 축소
2. **메모이제이션**: 불필요한 리렌더링 방지
3. **가상화**: 뷰포트 밖 요소는 렌더링하지 않음
4. **레이지 로딩**: 필요한 시점에 차트 컴포넌트 로드

## 상태 관리 전략

### 로컬 상태 vs 전역 상태

#### React Hook 기반 상태 관리
```typescript
// 로컬 상태 관리
function BacktestForm() {
  const [formData, setFormData] = useState<BacktestFormData>({
    startDate: '',
    endDate: '',
    strategy: 'buy_and_hold',
    portfolio: []
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleSubmit = useCallback(async (data: BacktestFormData) => {
    setIsSubmitting(true);
    try {
      const result = await submitBacktest(data);
      onSuccess(result);
    } catch (error) {
      setErrors(processApiErrors(error));
    } finally {
      setIsSubmitting(false);
    }
  }, [onSuccess]);
  
  return (
    <Form onSubmit={handleSubmit}>
      {/* 폼 컨트롤들 */}
    </Form>
  );
}
```

#### 커스텀 Hook 패턴
```typescript
// 재사용 가능한 API 호출 Hook
function useBacktestApi() {
  const [state, setState] = useState<ApiState<BacktestResult>>({
    data: null,
    loading: false,
    error: null
  });
  
  const executeBacktest = useCallback(async (request: BacktestRequest) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await backtestApiService.runBacktest(request);
      setState({ data: response.data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error.message });
    }
  }, []);
  
  return { ...state, executeBacktest };
}

// 사용 예시
function BacktestComponent() {
  const { data, loading, error, executeBacktest } = useBacktestApi();
  
  return (
    <div>
      {loading && <LoadingSpinner />}
      {error && <ErrorAlert message={error} />}
      {data && <BacktestResults data={data} />}
    </div>
  );
}
```

### 상태 동기화 전략

#### Context API 활용
```typescript
// 앱 전역 설정 컨텍스트
interface AppContextType {
  theme: 'light' | 'dark';
  locale: string;
  apiBaseUrl: string;
  updateTheme: (theme: 'light' | 'dark') => void;
}

const AppContext = createContext<AppContextType | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [locale, setLocale] = useState('ko-KR');
  
  const apiBaseUrl = useMemo(() => {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      return hostname === 'localhost' 
        ? 'http://localhost:8001' 
        : 'https://backtest-be.yeonjae.kr';
    }
    return 'http://localhost:8001';
  }, []);
  
  const value = useMemo(() => ({
    theme,
    locale,
    apiBaseUrl,
    updateTheme: setTheme
  }), [theme, locale, apiBaseUrl]);
  
  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}
```

## 성능 최적화

### 렌더링 최적화

#### React.memo와 useMemo 활용
```typescript
// 비싼 계산 메모이제이션
function StatsPanel({ data }: StatsPanelProps) {
  const statistics = useMemo(() => {
    return calculateAdvancedStatistics(data);
  }, [data]);
  
  const sortedTrades = useMemo(() => {
    return data.trades.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [data.trades]);
  
  return (
    <Panel>
      <StatsSummary stats={statistics} />
      <TradesList trades={sortedTrades} />
    </Panel>
  );
}

// 컴포넌트 메모이제이션
const ExpensiveChart = React.memo(({ data, options }: ChartProps) => {
  return <ComplexChart data={data} options={options} />;
}, (prevProps, nextProps) => {
  // 사용자 정의 비교 함수
  return (
    prevProps.data.length === nextProps.data.length &&
    JSON.stringify(prevProps.options) === JSON.stringify(nextProps.options)
  );
});
```

#### 가상화와 지연 로딩
```typescript
// 큰 리스트 가상화
import { FixedSizeList as List } from 'react-window';

function VirtualizedTradesList({ trades }: { trades: Trade[] }) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <TradeItem trade={trades[index]} />
    </div>
  );
  
  return (
    <List
      height={600}
      itemCount={trades.length}
      itemSize={60}
    >
      {Row}
    </List>
  );
}

// 이미지 지연 로딩
function LazyImage({ src, alt, ...props }: ImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );
    
    if (imgRef.current) {
      observer.observe(imgRef.current);
    }
    
    return () => observer.disconnect();
  }, []);
  
  return (
    <div ref={imgRef} {...props}>
      {isInView && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          style={{ opacity: isLoaded ? 1 : 0 }}
        />
      )}
    </div>
  );
}
```

## 테스팅 접근법

### Vitest 테스트 구조

#### 컴포넌트 테스트
```typescript
// components/__tests__/StatsSummary.test.tsx
import { render, screen } from '@testing-library/react';
import { StatsSummary } from '../StatsSummary';

describe('StatsSummary', () => {
  const mockStats = {
    total_return_pct: 15.5,
    total_trades: 25,
    win_rate_pct: 68.0,
    max_drawdown_pct: -12.3,
    sharpe_ratio: 1.45,
    profit_factor: 2.1
  };
  
  it('정확한 수익률을 표시해야 함', () => {
    render(<StatsSummary stats={mockStats} />);
    expect(screen.getByText('15.50%')).toBeInTheDocument();
  });
  
  it('음수 수치는 적색으로 표시해야 함', () => {
    render(<StatsSummary stats={mockStats} />);
    const drawdownElement = screen.getByText('-12.30%');
    expect(drawdownElement).toHaveClass('text-danger');
  });
});
```

#### Hook 테스트
```typescript
// hooks/__tests__/useBacktestApi.test.ts
import { renderHook, act } from '@testing-library/react';
import { useBacktestApi } from '../useBacktestApi';

describe('useBacktestApi', () => {
  it('초기 상태가 올바르게 설정되어야 함', () => {
    const { result } = renderHook(() => useBacktestApi());
    
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });
  
  it('백테스트 실행 시 로딩 상태가 변경되어야 함', async () => {
    const { result } = renderHook(() => useBacktestApi());
    
    act(() => {
      result.current.executeBacktest(mockRequest);
    });
    
    expect(result.current.loading).toBe(true);
  });
});
```

### E2E 테스트 전략

#### Playwright 통합
```typescript
// e2e/backtest-flow.spec.ts
import { test, expect } from '@playwright/test';

test('전체 백테스트 플로우', async ({ page }) => {
  // 1. 페이지 접속
  await page.goto('http://localhost:5174');
  
  // 2. 폼 입력
  await page.fill('[data-testid="start-date"]', '2023-01-01');
  await page.fill('[data-testid="end-date"]', '2023-12-31');
  await page.selectOption('[data-testid="strategy"]', 'buy_and_hold');
  
  // 3. 포트폴리오 추가
  await page.click('[data-testid="add-portfolio-item"]');
  await page.fill('[data-testid="symbol-input"]', 'AAPL');
  await page.fill('[data-testid="amount-input"]', '10000');
  
  // 4. 백테스트 실행
  await page.click('[data-testid="run-backtest"]');
  
  // 5. 결과 확인
  await expect(page.locator('[data-testid="results-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="equity-chart"]')).toBeVisible();
  await expect(page.locator('[data-testid="stats-summary"]')).toContainText('%');
});
```

이러한 체계적인 프론트엔드 기술 스택 선택과 구현을 통해 사용자 경험이 우수하고 유지보수가 용이한 백테스팅 시스템을 구축했습니다.
