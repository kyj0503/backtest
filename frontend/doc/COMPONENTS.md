# 컴포넌트 아키텍처 가이드

React 백테스팅 시스템의 컴포넌트 구조와 설계 원칙을 설명합니다.

## 컴포넌트 계층 구조

### 최상위 컴포넌트
```
App.tsx (최상위 애플리케이션)
├── ErrorBoundary.tsx (전역 에러 처리)
├── ServerStatus.tsx (서버 연결 상태)
└── main content
    ├── UnifiedBacktestForm.tsx (백테스트 입력 폼)
    └── UnifiedBacktestResults.tsx (결과 표시)
```

### 폼 컴포넌트 구조
```
UnifiedBacktestForm.tsx
├── Portfolio Input Section
│   ├── Stock Input Fields
│   ├── Asset Type Selection (stock/cash)
│   └── Investment Type Selection (lump_sum/dca)
├── Date Range Section
├── Strategy Selection Section
└── Validation & Submission
```

### 결과 표시 컴포넌트 구조
```
UnifiedBacktestResults.tsx
├── StatsSummary.tsx (성과 요약)
├── Chart Components
│   ├── EquityChart.tsx (수익률 곡선)
│   ├── OHLCChart.tsx (캔들스틱 차트)
│   ├── StockPriceChart.tsx (개별 주가 차트)
│   ├── ExchangeRateChart.tsx (환율 차트)
│   └── TradesChart.tsx (거래 내역)
└── Additional Features
    └── StockVolatilityNews.tsx (뉴스 통합)
```

## 컴포넌트 설계 원칙

### 1. 단일 책임 원칙
각 컴포넌트는 하나의 명확한 기능만 담당합니다.

```typescript
// 좋은 예: 단일 책임
function StatsSummary({ stats }: StatsSummaryProps) {
  return (
    <Card>
      <Card.Header>성과 요약</Card.Header>
      <Card.Body>
        <StatsDisplay stats={stats} />
      </Card.Body>
    </Card>
  );
}

// 나쁜 예: 여러 책임
function StatsAndChartAndNews({ data }: ComplexProps) {
  // 통계 계산, 차트 렌더링, 뉴스 가져오기 모두 처리
}
```

### 2. Props 인터페이스 일관성
모든 컴포넌트는 명확한 Props 인터페이스를 가집니다.

```typescript
interface BaseComponentProps {
  className?: string;
  loading?: boolean;
  error?: string | null;
}

interface ChartComponentProps extends BaseComponentProps {
  data: ChartDataPoint[];
  height?: number;
  onInteraction?: (event: ChartEvent) => void;
}

interface FormComponentProps extends BaseComponentProps {
  onSubmit: (data: FormData) => void;
  initialValues?: Partial<FormData>;
  disabled?: boolean;
}
```

### 3. 컴포넌트 조합 패턴
복잡한 기능은 작은 컴포넌트들의 조합으로 구현합니다.

```typescript
// 큰 컴포넌트를 작은 조합으로 분해
function BacktestResults({ data, isPortfolio }: BacktestResultsProps) {
  return (
    <Container>
      <ResultsHeader data={data} />
      <StatsSummary stats={data.summary_stats} />
      
      {isPortfolio ? (
        <PortfolioCharts data={data as PortfolioData} />
      ) : (
        <SingleStockCharts data={data as ChartData} />
      )}
      
      <AdditionalFeatures data={data} />
    </Container>
  );
}
```

## 차트 컴포넌트 상세

### EquityChart.tsx
**목적**: 포트폴리오 또는 단일 종목의 자산 가치 변화 표시

```typescript
interface EquityChartProps {
  data: EquityPoint[];
  height?: number;
  showDrawdown?: boolean;
  className?: string;
}

// 핵심 기능
- 시간별 자산 가치 곡선
- 드로다운 영역 표시 (선택적)
- 반응형 디자인
- 확대/축소 상호작용
```

### OHLCChart.tsx
**목적**: 주식의 OHLC(시가/고가/저가/종가) 데이터와 기술적 지표 표시

```typescript
interface OHLCChartProps {
  data: OHLCDataPoint[];
  indicators?: IndicatorData[];
  trades?: TradeMarker[];
  height?: number;
}

// 핵심 기능
- 캔들스틱 차트
- 거래량 히스토그램
- 기술적 지표 오버레이 (이동평균, RSI 등)
- 거래 진입/청산 마커
```

### StockPriceChart.tsx
**목적**: 여러 종목의 주가를 비교할 수 있는 캐러셀 차트

```typescript
interface StockPriceChartProps {
  stocksData: Array<{
    symbol: string;
    data: Array<{
      date: string;
      price: number;
      volume?: number;
    }>;
  }>;
}

// 핵심 기능
- 종목별 탭 네비게이션
- 개별 주가 추이 라인 차트
- 종목 간 빠른 전환
- 가격 변화율 표시
```

### ExchangeRateChart.tsx
**목적**: USD/KRW 환율 정보 표시

```typescript
interface ExchangeRateChartProps {
  startDate: string;
  endDate: string;
  className?: string;
}

// 핵심 기능
- 기간별 환율 변화
- yfinance에서 KRW=X 데이터 자동 조회
- 환율 변동률 계산
- 투자 기간과 동일한 날짜 범위
```

### StockVolatilityNews.tsx
**목적**: 주가 급등/급락 시점의 뉴스 검색 및 표시

```typescript
interface StockVolatilityNewsProps {
  symbols: string[];
  startDate: string;
  endDate: string;
  className?: string;
}

// 핵심 기능
- 5% 이상 주가 변동일 감지
- 네이버 뉴스 API 연동
- 종목별 뉴스 필터링
- 모달 팝업으로 뉴스 상세 표시
```

## 폼 컴포넌트 상세

### UnifiedBacktestForm.tsx
**목적**: 백테스트 파라미터 입력 및 검증

```typescript
interface BacktestFormData {
  portfolio: PortfolioStock[];
  startDate: string;
  endDate: string;
  strategy: string;
  strategyParams: Record<string, any>;
  commission: number;
  rebalanceFrequency: string;
}

// 상태 관리 구조
const [formData, setFormData] = useState<BacktestFormData>(initialFormData);
const [errors, setErrors] = useState<Record<string, string>>({});
const [isSubmitting, setIsSubmitting] = useState(false);
```

#### 폼 검증 로직
```typescript
const validateForm = (data: BacktestFormData): Record<string, string> => {
  const errors: Record<string, string> = {};
  
  // 날짜 검증
  if (new Date(data.endDate) <= new Date(data.startDate)) {
    errors.dateRange = '종료일은 시작일보다 늦어야 합니다';
  }
  
  // 포트폴리오 검증
  if (data.portfolio.length === 0) {
    errors.portfolio = '최소 하나의 자산을 추가해야 합니다';
  }
  
  // 투자 금액 검증
  data.portfolio.forEach((item, index) => {
    if (item.amount <= 0) {
      errors[`portfolio.${index}.amount`] = '투자 금액은 0보다 커야 합니다';
    }
  });
  
  return errors;
};
```

## 에러 처리 전략

### ErrorBoundary.tsx
React 컴포넌트 트리에서 발생하는 JavaScript 에러를 포착하고 대체 UI를 표시합니다.

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
    // 에러 로깅
    console.error('Component Error:', error, errorInfo);
    
    // 프로덕션에서는 에러 리포팅 서비스로 전송
    if (process.env.NODE_ENV === 'production') {
      // reportError(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

### 에러 표시 컴포넌트
```typescript
function ErrorFallback({ error }: { error: Error | null }) {
  return (
    <Alert variant="danger" className="m-3">
      <Alert.Heading>문제가 발생했습니다</Alert.Heading>
      <p>
        차트를 표시하는 중 오류가 발생했습니다. 
        페이지를 새로고침하거나 다른 설정으로 다시 시도해보세요.
      </p>
      {error && (
        <details className="mt-2">
          <summary>기술적 세부사항</summary>
          <pre className="mt-2 text-small">{error.message}</pre>
        </details>
      )}
      <hr />
      <Button variant="outline-danger" onClick={() => window.location.reload()}>
        페이지 새로고침
      </Button>
    </Alert>
  );
}
```

## 성능 최적화 패턴

### React.memo 활용
```typescript
// 비싼 차트 컴포넌트 메모이제이션
const ExpensiveChart = React.memo(({ data, options }: ChartProps) => {
  return <ComplexChart data={data} options={options} />;
}, (prevProps, nextProps) => {
  // 커스텀 비교 함수
  return (
    prevProps.data.length === nextProps.data.length &&
    JSON.stringify(prevProps.options) === JSON.stringify(nextProps.options)
  );
});

// 단순 Props 비교
const SimpleComponent = React.memo(({ title, value }: SimpleProps) => {
  return <div>{title}: {value}</div>;
});
```

### useMemo와 useCallback 활용
```typescript
function DataTable({ data, filters }: DataTableProps) {
  // 비싼 계산 메모이제이션
  const filteredData = useMemo(() => {
    return data.filter(item => matchesFilters(item, filters));
  }, [data, filters]);
  
  // 이벤트 핸들러 메모이제이션
  const handleRowClick = useCallback((item: DataItem) => {
    onRowSelect(item);
  }, [onRowSelect]);
  
  return (
    <Table>
      {filteredData.map(item => (
        <TableRow 
          key={item.id} 
          data={item} 
          onClick={handleRowClick}
        />
      ))}
    </Table>
  );
}
```

## 컴포넌트 테스트 가이드

### 단위 테스트 예시
```typescript
describe('StatsSummary', () => {
  const mockStats = {
    total_return_pct: 15.5,
    max_drawdown_pct: -8.2,
    sharpe_ratio: 1.3
  };
  
  it('수익률을 올바르게 표시해야 함', () => {
    render(<StatsSummary stats={mockStats} />);
    expect(screen.getByText('15.50%')).toBeInTheDocument();
  });
  
  it('음수 드로다운을 빨간색으로 표시해야 함', () => {
    render(<StatsSummary stats={mockStats} />);
    const drawdown = screen.getByText('-8.20%');
    expect(drawdown).toHaveClass('text-danger');
  });
});
```

### 통합 테스트 예시
```typescript
describe('BacktestForm Integration', () => {
  it('폼 제출 시 올바른 API 호출이 이루어져야 함', async () => {
    const mockApiCall = jest.fn();
    render(<UnifiedBacktestForm onSubmit={mockApiCall} />);
    
    // 폼 입력
    fireEvent.change(screen.getByLabelText('시작일'), {
      target: { value: '2023-01-01' }
    });
    fireEvent.change(screen.getByLabelText('종료일'), {
      target: { value: '2023-12-31' }
    });
    
    // 포트폴리오 항목 추가
    fireEvent.click(screen.getByText('자산 추가'));
    fireEvent.change(screen.getByLabelText('종목 코드'), {
      target: { value: 'AAPL' }
    });
    
    // 제출
    fireEvent.click(screen.getByText('백테스트 실행'));
    
    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith(
        expect.objectContaining({
          start_date: '2023-01-01',
          end_date: '2023-12-31',
          portfolio: expect.arrayContaining([
            expect.objectContaining({ symbol: 'AAPL' })
          ])
        })
      );
    });
  });
});
```