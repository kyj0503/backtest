# 프론트엔드 테스트 전략 가이드

## 목차

1. [테스트 전략 개요](#테스트-전략-개요)
2. [테스트 피라미드](#테스트-피라미드)
3. [테스트 유형별 전략](#테스트-유형별-전략)
4. [좋은 테스트 코드 작성 원칙](#좋은-테스트-코드-작성-원칙)
5. [테스트 작성 가이드](#테스트-작성-가이드)
6. [테스트 환경 설정](#테스트-환경-설정)
7. [유지보수 가능한 테스트](#유지보수-가능한-테스트)

---

## 테스트 전략 개요

### 왜 테스트가 필요한가?

#### 수동 테스트의 한계
- 사람은 실수를 하며 편협된 시각을 가질 수 있음
- 모든 케이스를 커버하지 못할 수 있음
- 늦은 피드백, 유지보수 난이도 상승, 신뢰성 하락으로 이어짐

#### 테스트 코드의 가치
1. **빠른 피드백**: 코드 작성 후 즉각적인 검증
2. **자동화**: 반복적인 테스트를 자동으로 수행
3. **안정성**: 변경사항이 기존 기능을 망가뜨리지 않는지 확인
4. **문서화**: 코드의 의도와 사용법을 명확히 전달
5. **리팩터링 안전망**: 안심하고 코드 개선 가능

### 테스트의 핵심 가치

> "테스트 코드를 작성하지 않으면, 변화가 생기는 매순간마다 발생할 수 있는 모든 Case를 고려해야 하고, 
> 변화가 생기는 매순간마다 모든 팀원이 동일한 고민을 해야 하며, 빠르게 변화하는 소프트웨어의 안정성을 보장할 수 없다."

---

## 테스트 피라미드

```
        /\
       /  \
      / E2E \ ← 적은 수, 느림, 비용 높음
     /______\
    /        \
   / 통합테스트  \ ← 중간 수준
  /____________\
 /              \
/  단위 테스트     \ ← 많은 수, 빠름, 비용 낮음
/________________\
```

### 계층별 특징

| 테스트 유형 | 범위 | 속도 | 비용 | 안정성 | 비율 |
|------------|------|------|------|--------|------|
| 단위 테스트 | 개별 함수/컴포넌트 | 매우 빠름 | 낮음 | 높음 | 70% |
| 통합 테스트 | 여러 모듈 조합 | 중간 | 중간 | 중간 | 20% |
| E2E 테스트 | 전체 시스템 | 느림 | 높음 | 낮음 | 10% |

### 실용적 접근

- **핵심 비즈니스 로직**: 단위 테스트로 철저히 검증
- **주요 사용자 플로우**: 통합 테스트로 검증
- **크리티컬 시나리오**: E2E 테스트로 최소한만 검증

> 가치 있는 20%의 테스트로 80% 이상의 신뢰성을 얻을 수 있습니다.

---

## 테스트 유형별 전략

### 1. 단위 테스트 (Unit Test)

#### 목적
- 개별 함수, 컴포넌트, 훅의 독립적인 동작 검증
- 비즈니스 로직의 정확성 확인

#### 특징
- ✅ 빠른 실행 속도
- ✅ 명확한 실패 원인 파악
- ✅ 외부 의존성으로부터 격리
- ⚠️ 실제 통합 환경과 차이 있을 수 있음

#### 무엇을 테스트할 것인가?

**테스트해야 할 것:**
- 순수 함수 (Pure Functions)
- 유틸리티 함수
- 비즈니스 로직 (계산, 검증, 변환)
- Custom Hooks
- 복잡한 상태 로직

**테스트하지 말아야 할 것:**
- 외부 라이브러리의 기본 동작
- 단순 Getter/Setter
- 프레임워크가 보장하는 기능

#### 작성 전략

```typescript
// ✅ Good: 순수 함수 테스트
describe('calculateBacktestMetrics', () => {
  it('수익률을 올바르게 계산한다', () => {
    const trades = [
      { profit: 100, loss: 0 },
      { profit: 50, loss: 0 }
    ];
    
    expect(calculateBacktestMetrics(trades)).toEqual({
      totalProfit: 150,
      winRate: 100
    });
  });

  it('손실이 있는 경우를 올바르게 처리한다', () => {
    const trades = [
      { profit: 100, loss: 0 },
      { profit: 0, loss: 50 }
    ];
    
    expect(calculateBacktestMetrics(trades).winRate).toBe(50);
  });
});
```

### 2. 통합 테스트 (Integration Test)

#### 목적
- 여러 모듈 간의 상호작용 검증
- API 통신, 상태 관리, 라우팅 등의 통합 동작 확인

#### 특징
- 실제 환경과 유사한 테스트
- 모듈 간 인터페이스 검증
- API 호출, 데이터 흐름 확인

#### 작성 전략

```typescript
// ✅ Good: 컴포넌트와 API 통합 테스트
describe('BacktestResult Component', () => {
  it('백테스트 실행 후 결과를 표시한다', async () => {
    // Mock API 응답 설정
    server.use(
      http.post('/api/v1/backtest/run', () => {
        return HttpResponse.json({
          profit: 1000,
          winRate: 65.5
        });
      })
    );

    render(<BacktestResult />);
    
    // 백테스트 실행
    await userEvent.click(screen.getByRole('button', { name: '실행' }));
    
    // 결과 확인
    await waitFor(() => {
      expect(screen.getByText('수익: 1000')).toBeInTheDocument();
      expect(screen.getByText('승률: 65.5%')).toBeInTheDocument();
    });
  });
});
```

### 3. E2E 테스트 (End-to-End Test)

#### 목적
- 사용자 관점에서 전체 플로우 검증
- 실제 프로덕션 환경과 유사한 시나리오 테스트

#### 특징
- 전체 시스템 동작 확인
- 실제 브라우저 환경에서 실행
- 느리고 유지보수 비용이 높음

#### 작성 전략
- **핵심 사용자 여정만 테스트**
- 회원가입 → 로그인 → 핵심 기능 사용
- 결제, 중요한 비즈니스 프로세스

```typescript
// Playwright 예시
test('사용자가 백테스트를 실행하고 결과를 확인할 수 있다', async ({ page }) => {
  // 로그인
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');
  
  // 백테스트 설정
  await page.goto('/backtest');
  await page.selectOption('[name="strategy"]', 'RSI');
  await page.fill('[name="capital"]', '1000000');
  
  // 실행
  await page.click('button:has-text("백테스트 실행")');
  
  // 결과 확인
  await expect(page.locator('.result-profit')).toBeVisible();
});
```

---

## 좋은 테스트 코드 작성 원칙

### FIRST 원칙

1. **Fast (빠르게)**: 테스트는 빠르게 실행되어야 함
2. **Independent (독립적으로)**: 각 테스트는 독립적이며 서로 의존하지 않음
3. **Repeatable (반복 가능하게)**: 어느 환경에서도 동일한 결과
4. **Self-Validating (자가 검증)**: 성공/실패가 명확함
5. **Timely (적시에)**: 테스트 코드를 먼저 작성

### AAA (Arrange-Act-Assert) 패턴

```typescript
describe('useBacktest hook', () => {
  it('백테스트 실행 시 로딩 상태를 관리한다', async () => {
    // Arrange: 테스트 준비
    const { result } = renderHook(() => useBacktest());
    
    // Act: 테스트 실행
    act(() => {
      result.current.runBacktest({ strategy: 'RSI' });
    });
    
    // Assert: 결과 검증
    expect(result.current.isLoading).toBe(true);
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });
});
```

### 단일 책임 원칙

❌ **Bad: 하나의 테스트에서 여러 개념 검증**
```typescript
it('백테스트 기능이 동작한다', () => {
  // 여러 검증이 섞여 있음
  expect(calculateProfit()).toBe(100);
  expect(validateStrategy()).toBe(true);
  expect(formatDate()).toBe('2024-01-01');
});
```

✅ **Good: 하나의 테스트는 하나의 개념만**
```typescript
it('수익을 올바르게 계산한다', () => {
  expect(calculateProfit(trades)).toBe(100);
});

it('전략 유효성을 검증한다', () => {
  expect(validateStrategy(strategy)).toBe(true);
});

it('날짜를 올바른 형식으로 변환한다', () => {
  expect(formatDate(date)).toBe('2024-01-01');
});
```

### 명확한 테스트 이름

❌ **Bad:**
```typescript
it('테스트1', () => { ... });
it('작동 확인', () => { ... });
```

✅ **Good:**
```typescript
it('백테스트 실행 시 수익률을 계산한다', () => { ... });
it('잘못된 전략이 입력되면 에러를 반환한다', () => { ... });
it('초기 자본금이 0 이하면 백테스트를 실행하지 않는다', () => { ... });
```

**네이밍 가이드:**
1. 명사 나열 대신 문장으로 작성
2. 테스트 행위와 결과를 명확히 기술
3. 도메인 용어 사용
4. "~하면 ~한다" 형식 권장

---

## 테스트 작성 가이드

### 1. 컴포넌트 테스트

#### 테스트 대상
- 사용자 인터랙션
- 조건부 렌더링
- Props 변경에 따른 UI 업데이트
- 이벤트 핸들러 호출

#### 예시

```typescript
// BacktestForm.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BacktestForm } from './BacktestForm';

describe('BacktestForm', () => {
  it('사용자가 폼을 제출하면 onSubmit이 호출된다', async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();
    
    render(<BacktestForm onSubmit={mockOnSubmit} />);
    
    // 폼 입력
    await user.type(screen.getByLabelText('초기 자본금'), '1000000');
    await user.selectOptions(screen.getByLabelText('전략'), 'RSI');
    
    // 제출
    await user.click(screen.getByRole('button', { name: '실행' }));
    
    // 검증
    expect(mockOnSubmit).toHaveBeenCalledWith({
      capital: 1000000,
      strategy: 'RSI'
    });
  });

  it('초기 자본금이 비어있으면 에러 메시지를 표시한다', async () => {
    const user = userEvent.setup();
    
    render(<BacktestForm onSubmit={vi.fn()} />);
    
    await user.click(screen.getByRole('button', { name: '실행' }));
    
    expect(screen.getByText('초기 자본금을 입력하세요')).toBeInTheDocument();
  });
});
```

### 2. Custom Hook 테스트

```typescript
// useBacktest.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useBacktest } from './useBacktest';

describe('useBacktest', () => {
  it('초기 상태가 올바르게 설정된다', () => {
    const { result } = renderHook(() => useBacktest());
    
    expect(result.current.isLoading).toBe(false);
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('백테스트 실행 중 로딩 상태가 true가 된다', async () => {
    const { result } = renderHook(() => useBacktest());
    
    act(() => {
      result.current.runBacktest({ strategy: 'RSI' });
    });
    
    expect(result.current.isLoading).toBe(true);
  });
});
```

### 3. 유틸리티 함수 테스트

```typescript
// formatters.test.ts
describe('formatCurrency', () => {
  it('숫자를 통화 형식으로 변환한다', () => {
    expect(formatCurrency(1000000)).toBe('₩1,000,000');
  });

  it('음수를 올바르게 처리한다', () => {
    expect(formatCurrency(-1000)).toBe('-₩1,000');
  });

  it('소수점을 반올림한다', () => {
    expect(formatCurrency(1234.56)).toBe('₩1,235');
  });
});
```

### 4. API 통신 테스트

```typescript
// MSW를 사용한 API 모킹
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.post('/api/v1/backtest/run', () => {
    return HttpResponse.json({
      profit: 1000,
      winRate: 65.5
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('runBacktest API', () => {
  it('백테스트 결과를 반환한다', async () => {
    const result = await runBacktest({ strategy: 'RSI' });
    
    expect(result).toEqual({
      profit: 1000,
      winRate: 65.5
    });
  });

  it('에러 발생 시 에러를 throw한다', async () => {
    server.use(
      http.post('/api/v1/backtest/run', () => {
        return HttpResponse.json(
          { message: 'Internal Server Error' },
          { status: 500 }
        );
      })
    );

    await expect(runBacktest({ strategy: 'RSI' }))
      .rejects
      .toThrow('Internal Server Error');
  });
});
```

### 5. 상태 관리 테스트

```typescript
// Zustand store 테스트
import { renderHook, act } from '@testing-library/react';
import { useBacktestStore } from './backtestStore';

describe('useBacktestStore', () => {
  it('결과를 저장하고 조회할 수 있다', () => {
    const { result } = renderHook(() => useBacktestStore());
    
    act(() => {
      result.current.setResult({
        profit: 1000,
        winRate: 65.5
      });
    });
    
    expect(result.current.result).toEqual({
      profit: 1000,
      winRate: 65.5
    });
  });

  it('결과를 초기화할 수 있다', () => {
    const { result } = renderHook(() => useBacktestStore());
    
    act(() => {
      result.current.setResult({ profit: 1000, winRate: 65.5 });
      result.current.reset();
    });
    
    expect(result.current.result).toBeNull();
  });
});
```

---

## 테스트 환경 설정

### Vitest 설정

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/*',
        'src/main.tsx',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 테스트 설정 파일

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// 각 테스트 후 정리
afterEach(() => {
  cleanup();
});

// MSW 서버 설정
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// 전역 모킹
global.matchMedia = vi.fn().mockImplementation(query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));
```

### MSW 핸들러 설정

```typescript
// src/test/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('/api/v1/backtest/run', () => {
    return HttpResponse.json({
      profit: 1000,
      winRate: 65.5,
      trades: []
    });
  }),

  http.get('/api/v1/backtest/history', () => {
    return HttpResponse.json([
      { id: 1, strategy: 'RSI', profit: 1000 },
      { id: 2, strategy: 'SMA', profit: -500 }
    ]);
  }),
];
```

### 테스트 유틸리티

```typescript
// src/test/utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

interface AllProvidersProps {
  children: React.ReactNode;
}

const AllProviders = ({ children }: AllProvidersProps) => {
  const queryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

---

## 유지보수 가능한 테스트

### 테스트 코드 냄새 (Test Smells)

#### 1. 과도한 Setup/Teardown
❌ **Bad:**
```typescript
beforeEach(() => {
  // 모든 테스트에 필요하지 않은 복잡한 설정
  setupComplexDatabase();
  initializeAllModules();
  configureAllSettings();
});
```

✅ **Good:**
```typescript
// 필요한 테스트에서만 설정
it('특정 기능 테스트', () => {
  const data = createMinimalTestData();
  // 테스트...
});
```

#### 2. 테스트 간 의존성
❌ **Bad:**
```typescript
let sharedState;

it('테스트 1', () => {
  sharedState = { value: 100 };
});

it('테스트 2', () => {
  expect(sharedState.value).toBe(100); // 테스트 1에 의존
});
```

✅ **Good:**
```typescript
it('테스트 1', () => {
  const state = { value: 100 };
  // 독립적인 테스트
});

it('테스트 2', () => {
  const state = { value: 100 };
  // 독립적인 테스트
});
```

#### 3. 과도한 Mocking
❌ **Bad:**
```typescript
it('테스트', () => {
  vi.mock('./module1');
  vi.mock('./module2');
  vi.mock('./module3');
  vi.mock('./module4');
  // 너무 많은 모듈을 모킹
});
```

✅ **Good:**
```typescript
// 테스트하기 어려운 부분만 격리
it('테스트', () => {
  const externalApi = createMockApi();
  // 필요한 부분만 모킹
});
```

### 테스트 데이터 관리

```typescript
// src/test/fixtures/backtest.ts
export const createMockBacktest = (overrides = {}) => ({
  id: 1,
  strategy: 'RSI',
  capital: 1000000,
  profit: 1000,
  winRate: 65.5,
  ...overrides
});

export const createMockTrade = (overrides = {}) => ({
  id: 1,
  symbol: 'BTC',
  type: 'BUY',
  price: 50000,
  quantity: 0.1,
  ...overrides
});

// 사용
it('테스트', () => {
  const backtest = createMockBacktest({ profit: 2000 });
  // ...
});
```

### 공통 테스트 유틸리티

```typescript
// src/test/helpers.ts
export const waitForLoadingToFinish = () => 
  waitFor(() => {
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

export const fillBacktestForm = async (user: UserEvent, data: BacktestFormData) => {
  await user.type(screen.getByLabelText('초기 자본금'), data.capital.toString());
  await user.selectOptions(screen.getByLabelText('전략'), data.strategy);
};
```

---

## 테스트 실행 및 CI/CD

### 로컬 실행

```bash
# 모든 테스트 실행
npm run test

# Watch 모드
npm run test:watch

# UI 모드
npm run test:ui

# 커버리지 확인
npm run test:coverage
```

### CI에서 테스트

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
        working-directory: ./backtest_fe
      
      - name: Run tests
        run: npm run test:run
        working-directory: ./backtest_fe
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backtest_fe/coverage/coverage-final.json
```

---

## 테스트 커버리지 목표

### 커버리지 기준

| 카테고리 | 목표 커버리지 | 우선순위 |
|---------|-------------|---------|
| 비즈니스 로직 | 80% 이상 | 높음 |
| 유틸리티 함수 | 90% 이상 | 높음 |
| 컴포넌트 | 70% 이상 | 중간 |
| API 클라이언트 | 80% 이상 | 높음 |
| 타입 정의 | 테스트 불필요 | - |

### 커버리지는 절대적 지표가 아님

> 100% 커버리지가 버그 없음을 보장하지 않습니다.
> 중요한 것은 의미 있는 테스트를 작성하는 것입니다.

**테스트 작성 우선순위:**
1. 핵심 비즈니스 로직
2. 버그가 자주 발생하는 부분
3. 복잡도가 높은 코드
4. 자주 변경되는 코드

---

## 실전 예시: 백테스트 기능 테스트

### 시나리오
사용자가 백테스트를 실행하고 결과를 확인하는 전체 플로우를 테스트

```typescript
// BacktestPage.test.tsx
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { BacktestPage } from './BacktestPage';

describe('BacktestPage - 전체 플로우', () => {
  it('사용자가 백테스트를 실행하고 결과를 확인할 수 있다', async () => {
    const user = userEvent.setup();
    
    // 1. 페이지 렌더링
    render(<BacktestPage />);
    
    // 2. 전략 선택
    const strategySelect = screen.getByLabelText('전략 선택');
    await user.selectOptions(strategySelect, 'RSI');
    
    // 3. 초기 자본금 입력
    const capitalInput = screen.getByLabelText('초기 자본금');
    await user.clear(capitalInput);
    await user.type(capitalInput, '1000000');
    
    // 4. 기간 선택
    await user.click(screen.getByLabelText('시작일'));
    await user.click(screen.getByText('2024-01-01'));
    
    await user.click(screen.getByLabelText('종료일'));
    await user.click(screen.getByText('2024-12-31'));
    
    // 5. 백테스트 실행
    const runButton = screen.getByRole('button', { name: '백테스트 실행' });
    await user.click(runButton);
    
    // 6. 로딩 표시 확인
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    // 7. 결과 표시 대기 및 확인
    await waitFor(() => {
      expect(screen.getByText('백테스트 결과')).toBeInTheDocument();
    });
    
    expect(screen.getByText('총 수익:')).toBeInTheDocument();
    expect(screen.getByText('승률:')).toBeInTheDocument();
    expect(screen.getByText('65.5%')).toBeInTheDocument();
    
    // 8. 차트 렌더링 확인
    expect(screen.getByRole('img', { name: '수익률 차트' })).toBeInTheDocument();
  });

  it('입력값이 유효하지 않으면 에러 메시지를 표시한다', async () => {
    const user = userEvent.setup();
    
    render(<BacktestPage />);
    
    // 빈 상태로 실행 시도
    await user.click(screen.getByRole('button', { name: '백테스트 실행' }));
    
    // 에러 메시지 확인
    expect(screen.getByText('전략을 선택하세요')).toBeInTheDocument();
    expect(screen.getByText('초기 자본금을 입력하세요')).toBeInTheDocument();
  });

  it('API 에러 발생 시 에러 메시지를 표시한다', async () => {
    const user = userEvent.setup();
    
    // API 에러 응답 설정
    server.use(
      http.post('/api/v1/backtest/run', () => {
        return HttpResponse.json(
          { message: '서버 오류가 발생했습니다' },
          { status: 500 }
        );
      })
    );
    
    render(<BacktestPage />);
    
    // 폼 작성 및 실행
    await user.selectOptions(screen.getByLabelText('전략 선택'), 'RSI');
    await user.type(screen.getByLabelText('초기 자본금'), '1000000');
    await user.click(screen.getByRole('button', { name: '백테스트 실행' }));
    
    // 에러 메시지 확인
    await waitFor(() => {
      expect(screen.getByText('서버 오류가 발생했습니다')).toBeInTheDocument();
    });
  });
});
```

---

## 결론

### 핵심 원칙 요약

1. **가치 있는 테스트 작성**: 모든 코드가 아닌, 중요한 부분을 테스트
2. **빠른 피드백 사이클**: 단위 테스트를 주로 작성하고 자주 실행
3. **독립성 유지**: 각 테스트는 독립적으로 실행 가능해야 함
4. **명확한 의도**: 테스트 이름과 구조로 의도를 명확히 전달
5. **유지보수성**: 테스트 코드도 프로덕션 코드만큼 중요하게 관리

### 테스트 작성 체크리스트

- [ ] 테스트 이름이 명확한가?
- [ ] 하나의 테스트가 하나의 개념만 검증하는가?
- [ ] AAA 패턴을 따르는가?
- [ ] 테스트가 독립적으로 실행되는가?
- [ ] 실패 시 원인을 쉽게 파악할 수 있는가?
- [ ] 불필요한 모킹을 하지 않았는가?
- [ ] 테스트 코드가 읽기 쉬운가?

### 참고 자료

- [Testing Library 공식 문서](https://testing-library.com/)
- [Vitest 공식 문서](https://vitest.dev/)
- [MSW 공식 문서](https://mswjs.io/)
- [Kent C. Dodds - Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

## 구현 현황

### 테스트 인프라 (완료 ✅)

#### 1. 테스트 환경 설정
- **Vitest**: 테스트 러너 (v3.2.4)
- **Testing Library**: React 컴포넌트 테스팅 (@testing-library/react v16.3.0)
- **MSW (Mock Service Worker)**: API 모킹 (v2.x)
- **jsdom**: 브라우저 환경 시뮬레이션

#### 2. 테스트 유틸리티 파일 구조
```
src/test/
├── setup.ts              # 전역 테스트 설정, MSW 라이프사이클
├── utils.tsx             # 커스텀 render, Testing Library re-export
├── fixtures.ts           # 테스트 데이터 생성 함수들
├── helpers.ts            # 테스트 헬퍼 함수들
└── mocks/
    ├── handlers.ts       # MSW API 핸들러
    └── server.ts         # MSW 서버 설정
```

#### 3. 구현된 테스트 유형

**단위 테스트 (Unit Tests)**
- ✅ `useAsync` Hook (6 tests) - 비동기 상태 관리
- ✅ `useForm` Hook (10 tests) - 폼 상태 관리 및 검증
- ✅ `utils` 함수들 (17 tests) - 유틸리티 함수 검증

**통합 테스트 (Integration Tests)**
- ✅ `backtestService` (10 tests) - API 서비스 계층 (MSW 사용)

**컴포넌트 테스트 (Component Tests)**
- ✅ `ThemeSelector` (7 tests) - 테마 선택 UI 컴포넌트
- ✅ `ErrorBoundary` (9 tests) - 에러 경계 컴포넌트

### 테스트 통계

```
Test Files:  6 passed (6)
Tests:       59 passed (59)
Duration:    ~7-8 seconds
```

#### 테스트 커버리지 구성

**포함 대상**:
- `src/**/*.{ts,tsx}`

**제외 대상**:
- `src/test/` - 테스트 유틸리티
- `**/__tests__/**` - 테스트 파일 자체
- `**/*.d.ts` - 타입 정의 파일
- `src/main.tsx` - 앱 진입점
- 설정 파일들

### 구현된 테스트 헬퍼들

#### Fixtures (src/test/fixtures.ts)
```typescript
- createMockBacktest()
- createMockTrade()
- createMockOHLC()
- createMockEquity()
- createMockStrategy()
- createMockBacktestRequest()
- createMockBacktestResult()
```

#### Helpers (src/test/helpers.ts)
```typescript
- waitForLoadingToFinish()
- fillBacktestForm()
- clickRunBacktest()
- loginUser()
- expectErrorMessage()
- mockApiError()
- sleep()
```

#### MSW Handlers (src/test/mocks/handlers.ts)
```typescript
- POST /api/v1/backtest/run
- GET /api/v1/backtest/history
- GET /api/v1/backtest/strategies
- GET /health
- GET /api/v1/backtest/volatility
- POST /api/v1/backtest/optimize
```

### 실행 명령어

```bash
# 전체 테스트 실행
npm test

# 단일 실행 모드 (CI용)
npm test -- --run

# 특정 파일만 테스트
npm test -- ErrorBoundary

# 커버리지 포함 실행
npm test -- --coverage

# UI 모드로 실행
npm test -- --ui
```

### 개선 계획

#### 단기 계획 (1-2주)
- [ ] 추가 컴포넌트 테스트 작성 (Header, 백테스트 폼 등)
- [ ] E2E 테스트 도입 (Playwright)
- [ ] 코드 커버리지 측정 및 목표 설정 (목표: 80%+)

#### 중기 계획 (1개월)
- [ ] 시각적 회귀 테스트 (Chromatic or Percy)
- [ ] 접근성 테스트 (axe-core)
- [ ] 성능 테스트 기준 수립

#### 장기 계획 (3개월+)
- [ ] CI/CD 파이프라인에 자동 테스트 통합
- [ ] 테스트 커버리지 리포트 자동 생성
- [ ] 테스트 메트릭 모니터링

### 팀 가이드라인

1. **새 기능 추가 시**: 반드시 테스트 먼저 작성 (TDD 권장)
2. **버그 수정 시**: 버그를 재현하는 테스트 작성 후 수정
3. **리팩터링 시**: 기존 테스트가 모두 통과하는지 확인
4. **PR 제출 전**: `npm test -- --run`으로 전체 테스트 확인

---

**작성일**: 2025-02-10  
**최종 업데이트**: 2025-02-10  
**버전**: 1.1.0  
**작성자**: Backtest Team
