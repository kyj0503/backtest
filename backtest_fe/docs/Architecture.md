# 프론트엔드 아키텍처 가이드

## 개요

이 문서는 백테스팅 프론트엔드 애플리케이션의 아키텍처 설계 원칙과 구조를 설명합니다.

## 아키텍처 원칙

### 1. 관심사의 분리 (Separation of Concerns)

- **Presentation Layer**: React 컴포넌트와 UI 로직
- **Business Logic Layer**: 커스텀 훅과 서비스 클래스
- **Data Access Layer**: API 클라이언트와 데이터 변환

### 2. 의존성 주입 (Dependency Injection)

- 컴포넌트는 필요한 의존성을 props나 Context를 통해 주입받음
- 테스트 시 쉬운 모킹 가능
- 결합도 감소

### 3. 타입 안전성 (Type Safety)

- TypeScript 엄격 모드 사용
- 모든 API 응답에 대한 타입 정의
- 런타임 에러 최소화

## 폴더 구조

### Feature-Based Architecture

```
src/
├── shared/                    # 공통 모듈
│   ├── api/                  # API 클라이언트
│   │   ├── client.ts         # Axios 설정 및 인터셉터
│   │   ├── auth-storage.ts   # 인증 토큰 관리
│   │   └── ws.ts            # WebSocket 유틸리티
│   ├── config/              # 환경 설정
│   │   └── index.ts         # 앱 설정 및 환경 변수
│   ├── hooks/               # 재사용 가능한 훅
│   │   ├── useAsync.ts      # 비동기 상태 관리
│   │   ├── useForm.ts       # 폼 상태 관리
│   │   └── useLocalStorage.ts # 로컬 스토리지 관리
│   ├── types/               # 전역 타입 정의
│   │   └── index.ts         # 공통 타입
│   ├── ui/                  # shadcn/ui 컴포넌트
│   ├── utils/               # 유틸리티 함수
│   │   └── index.ts         # 날짜, 숫자, 문자열 등 유틸리티
│   └── lib/                 # 라이브러리 설정
├── features/                # 기능별 모듈
│   ├── auth/                # 인증 기능
│   │   ├── components/      # 인증 관련 컴포넌트
│   │   ├── hooks/          # 인증 훅
│   │   ├── services/       # 인증 서비스
│   │   └── types.ts        # 인증 타입
│   ├── backtest/           # 백테스트 기능
│   │   ├── components/     # 백테스트 컴포넌트
│   │   ├── hooks/         # 백테스트 훅
│   │   ├── services/      # 백테스트 서비스
│   │   └── model/         # 데이터 모델 및 타입
│   └── chat/              # 채팅 기능
├── pages/                 # 페이지 컴포넌트
├── components/            # 공통 컴포넌트
├── test/                  # 테스트 유틸리티
└── App.tsx               # 루트 컴포넌트
```

## 상태 관리 전략

### 1. 로컬 상태 (Local State)

- `useState`, `useReducer` 사용
- 컴포넌트 내부에서만 사용되는 상태

### 2. 서버 상태 (Server State)

- `useAsync` 커스텀 훅 사용
- API 호출과 관련된 상태 (로딩, 에러, 데이터)

```typescript
const { data, isLoading, error, execute } = useAsync(
  () => BacktestService.getStrategies(),
  []
)
```

### 3. 전역 상태 (Global State)

- React Context 사용 (인증, 테마 등)
- 여러 컴포넌트에서 공유되는 상태

```typescript
// AuthContext 예시
const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  
  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}
```

### 4. 폼 상태 (Form State)

- `useForm` 커스텀 훅 사용
- 검증, 에러 처리, 제출 로직 포함

## 컴포넌트 설계 패턴

### 1. 컨테이너-프레젠테이션 패턴

```typescript
// Container Component (로직)
const BacktestContainer = () => {
  const { runBacktest, result, isLoading } = useBacktest()
  
  return (
    <BacktestPresentation
      onSubmit={runBacktest}
      result={result}
      isLoading={isLoading}
    />
  )
}

// Presentation Component (표시)
const BacktestPresentation = ({ onSubmit, result, isLoading }) => {
  return (
    <div>
      <form onSubmit={onSubmit}>
        {/* 폼 UI */}
      </form>
      {result && <Results data={result} />}
    </div>
  )
}
```

### 2. 합성 패턴 (Composition Pattern)

```typescript
// 복합 컴포넌트
const Card = ({ children, className, ...props }) => (
  <div className={cn("rounded-lg border bg-card", className)} {...props}>
    {children}
  </div>
)

const CardHeader = ({ children, className, ...props }) => (
  <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props}>
    {children}
  </div>
)

// 사용
<Card>
  <CardHeader>
    <CardTitle>백테스트 결과</CardTitle>
  </CardHeader>
  <CardContent>
    {/* 내용 */}
  </CardContent>
</Card>
```

### 3. 렌더 프롭 패턴

```typescript
const DataFetcher = ({ children, url }) => {
  const { data, isLoading, error } = useAsync(() => fetch(url))
  
  return children({ data, isLoading, error })
}

// 사용
<DataFetcher url="/api/strategies">
  {({ data, isLoading, error }) => (
    <div>
      {isLoading && <Spinner />}
      {error && <Error message={error} />}
      {data && <StrategyList strategies={data} />}
    </div>
  )}
</DataFetcher>
```

## 에러 처리 전략

### 1. Error Boundary

```typescript
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />
    }

    return this.props.children
  }
}
```

### 2. API 에러 처리

```typescript
// API 클라이언트에서 중앙 집중식 에러 처리
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = extractErrorMessage(error)
    
    if (error.response?.status === 401) {
      // 인증 에러 처리
      redirectToLogin()
    }
    
    return Promise.reject(new Error(message))
  }
)
```

### 3. 비동기 에러 처리

```typescript
const { data, error, isLoading } = useAsync(
  () => BacktestService.executeBacktest(request),
  [request],
  {
    onError: (error) => {
      toast.error(error.message)
    }
  }
)
```

## 성능 최적화

### 1. 코드 분할 (Code Splitting)

```typescript
// 레이지 로딩
const BacktestPage = lazy(() => import('./pages/BacktestPage'))

// 동적 임포트
const loadChartLibrary = () => import('./components/Chart')
```

### 2. 메모이제이션

```typescript
// 컴포넌트 메모이제이션
const ExpensiveComponent = memo(({ data }) => {
  return <div>{/* 복잡한 렌더링 */}</div>
})

// 값 메모이제이션
const processedData = useMemo(() => {
  return expensiveCalculation(rawData)
}, [rawData])

// 콜백 메모이제이션
const handleClick = useCallback((id) => {
  onItemClick(id)
}, [onItemClick])
```

### 3. 가상화 (Virtualization)

```typescript
// 대용량 리스트 처리
import { FixedSizeList as List } from 'react-window'

const VirtualizedList = ({ items }) => (
  <List
    height={600}
    itemCount={items.length}
    itemSize={50}
    itemData={items}
  >
    {Row}
  </List>
)
```

## 테스트 전략

### 1. 단위 테스트

- 유틸리티 함수
- 커스텀 훅
- 서비스 클래스

### 2. 통합 테스트

- API 연동
- 사용자 플로우
- 컴포넌트 상호작용

### 3. E2E 테스트

- 핵심 사용자 시나리오
- 크로스 브라우저 테스트

## 보안 고려사항

### 1. XSS 방지

- React의 기본 이스케이핑 활용
- `dangerouslySetInnerHTML` 사용 시 주의
- 사용자 입력 검증

### 2. 인증 토큰 관리

- HttpOnly 쿠키 사용 고려
- 토큰 만료 처리
- 리프레시 토큰 관리

### 3. CSRF 방지

- CSRF 토큰 사용
- SameSite 쿠키 속성 설정

## 접근성 (Accessibility)

### 1. 시맨틱 HTML

```typescript
// 적절한 HTML 요소 사용
<main>
  <section>
    <h1>백테스트 결과</h1>
    <article>
      {/* 내용 */}
    </article>
  </section>
</main>
```

### 2. ARIA 속성

```typescript
<button
  aria-label="백테스트 실행"
  aria-disabled={isLoading}
  onClick={handleSubmit}
>
  {isLoading ? <Spinner aria-hidden="true" /> : '실행'}
</button>
```

### 3. 키보드 내비게이션

```typescript
const handleKeyDown = (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    handleClick()
  }
}
```

## 국제화 (i18n)

### 1. 다국어 지원 준비

```typescript
// 문자열 상수화
const MESSAGES = {
  BACKTEST_RUNNING: '백테스트 실행 중...',
  BACKTEST_COMPLETE: '백테스트 완료',
  ERROR_OCCURRED: '오류가 발생했습니다'
}
```

### 2. 날짜/숫자 포맷

```typescript
// 로케일 고려한 포맷팅
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW'
  }).format(amount)
}
```

이 아키텍처 가이드를 따라 일관성 있고 유지보수 가능한 코드를 작성할 수 있습니다.