### 개발 환경 설정

```bash
# 프로젝트 클론 후
cd backtest_fe

# 의존성 설치
npm ci

# 환경 변수 설정
cp .env.example .env

# 개발 서버 실행
npm run dev
```

## 환경 설정

### 환경 변수

```bash
# .env.development (개발용)
VITE_API_URL=http://localhost:8080/api
VITE_ENVIRONMENT=development
VITE_DEBUG=true

# .env.production (배포용)  
VITE_API_URL=https://api.backtest.com/api
VITE_ENVIRONMENT=production
VITE_DEBUG=false
```

### API 프록시 설정

개발 중 CORS 문제 해결을 위한 프록시 설정:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET || 'http://localhost:8080',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
```

## 아키텍처 패턴

### 1. 폴더 구조

```
src/
├── shared/                 # 공통 인프라
│   ├── types/             # 글로벌 타입 정의
│   ├── config/            # 환경 설정
│   ├── hooks/             # 재사용 가능한 훅
│   │   ├── useAsync.ts    # 비동기 상태 관리
│   │   ├── useForm.ts     # 폼 상태 관리
│   │   └── useLocalStorage.ts
│   ├── utils/             # 유틸리티 함수들
│   └── components/        # 공통 UI 컴포넌트
├── features/              # 기능별 모듈
│   ├── backtest/         # 백테스트 기능
│   │   ├── components/   # 백테스트 전용 컴포넌트
│   │   ├── hooks/        # 백테스트 훅
│   │   ├── services/     # API 서비스
│   │   └── types/        # 백테스트 타입
│   └── portfolio/        # 포트폴리오 기능
├── pages/                # 페이지 컴포넌트
└── test/                 # 테스트 유틸리티
```

### 2. 커스텀 훅 패턴

#### useAsync - 비동기 상태 관리
```typescript
const { data, isLoading, error, execute } = useAsync<BacktestResult>();

// 사용 예시
const handleBacktest = async (params: BacktestRequest) => {
  await execute(() => BacktestService.execute(params));
};
```

#### useForm - 폼 상태 관리
```typescript
const { values, errors, handleChange, handleSubmit, isValid } = useForm({
  initialValues: { symbol: '', strategy: 'buy_and_hold' },
  validationSchema: backtestSchema,
  onSubmit: handleBacktestSubmit
});
```

### 3. 서비스 레이어 패턴

```typescript
// features/backtest/services/backtestService.ts
class BacktestService {
  private static instance: BacktestService;
  
  static getInstance(): BacktestService {
    if (!BacktestService.instance) {
      BacktestService.instance = new BacktestService();
    }
    return BacktestService.instance;
  }

  async execute(params: BacktestRequest): Promise<BacktestResult> {
    const response = await apiClient.post<BacktestResult>('/backtest', params);
    return response.data;
  }
}
```

## 테스트 전략

### 현재 테스트 현황 (59개 통과 ✅)

```
Test Files:  6 passed
Tests:       59 passed

📊 테스트 분포:
  - 단위 테스트: 33 tests (Hooks, Utils)
  - 통합 테스트: 10 tests (Services)
  - 컴포넌트 테스트: 16 tests (UI Components)
```

### 테스트 실행

```bash
# 전체 테스트 실행 (watch 모드)
npm test

# 단일 실행 (CI 모드)
npm test -- --run

# 특정 파일 테스트
npm test ErrorBoundary

# 커버리지 포함
npm test -- --coverage

# UI 모드
npm test -- --ui
```

### 테스트 인프라

**테스트 도구**:
- **Vitest**: 빠른 테스트 러너
- **Testing Library**: React 컴포넌트 테스팅
- **MSW**: API 모킹
- **jsdom**: 브라우저 환경 시뮬레이션

**테스트 유틸리티** (`src/test/`):
```
test/
├── setup.ts         # 전역 설정, MSW 라이프사이클
├── utils.tsx        # 커스텀 render, Testing Library re-export
├── fixtures.ts      # 테스트 데이터 팩토리
├── helpers.ts       # 테스트 헬퍼 함수들
└── mocks/
    ├── handlers.ts  # MSW API 핸들러
    └── server.ts    # MSW 서버 설정
```

### 테스트 작성 예시

#### 1. 훅 테스트
```typescript
import { describe, it, expect } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useAsync } from '../useAsync'

describe('useAsync', () => {
  it('데이터 로딩에 성공한다', async () => {
    const { result } = renderHook(() => useAsync<string>())
    
    await result.current.execute(async () => 'success')

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
      expect(result.current.data).toBe('success')
    })
  })
})
```

#### 2. 컴포넌트 테스트
```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import ThemeSelector from '../ThemeSelector'

describe('ThemeSelector', () => {
  it('테마 변경이 정상 작동한다', async () => {
    const user = userEvent.setup()
    render(<ThemeSelector />)
    
    const blueTheme = screen.getByText(/^Blue$/i)
    await user.click(blueTheme)
    
    // 테마 변경 확인 로직
  })
})
```

#### 3. 서비스 통합 테스트 (MSW 사용)
```typescript
import { describe, it, expect } from 'vitest'
import { BacktestService } from '../backtestService'
import { createMockBacktestRequest } from '@/test/fixtures'

describe('backtestService', () => {
  it('백테스트 실행 API를 호출한다', async () => {
    const request = createMockBacktestRequest()
    const result = await BacktestService.executeBacktest(request)
    
    expect(result.success).toBe(true)
    expect(result.data).toBeDefined()
  })
})
```

### 테스트 가이드라인

#### FIRST 원칙
- **Fast**: 빠른 실행
- **Independent**: 독립적 실행
- **Repeatable**: 재현 가능
- **Self-validating**: 자동 검증
- **Timely**: 적시 작성

#### AAA 패턴
```typescript
it('예시 테스트', () => {
  // Arrange: 테스트 준비
  const data = createMockData()
  
  // Act: 동작 실행
  const result = someFunction(data)
  
  // Assert: 결과 검증
  expect(result).toBe(expected)
})
```

더 자세한 내용은 [📖 테스트 전략 가이드](./04-Test-Strategy.md)를 참고하세요.

## 스타일링 패턴

### Tailwind CSS 조합

```typescript
import { cn } from '@/shared/utils';

// 조건부 스타일링
const Button = ({ variant, size, disabled, className, ...props }) => (
  <button
    className={cn(
      // 기본 스타일
      'inline-flex items-center justify-center rounded-md font-medium transition-colors',
      // 변형별 스타일
      {
        'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
        'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
      },
      // 크기별 스타일  
      {
        'h-10 px-4 py-2': size === 'default',
        'h-9 px-3': size === 'sm',
        'h-11 px-8': size === 'lg',
      },
      // 상태별 스타일
      disabled && 'opacity-50 cursor-not-allowed',
      className
    )}
    disabled={disabled}
    {...props}
  />
);
```

### shadcn/ui 컴포넌트 활용

```typescript
// 기본 컴포넌트 확장
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const CustomForm = () => (
  <form className="space-y-4">
    <Input 
      placeholder="Symbol" 
      value={symbol}
      onChange={(e) => setSymbol(e.target.value)}
    />
    <Button type="submit" disabled={isLoading}>
      {isLoading ? 'Executing...' : 'Execute Backtest'}
    </Button>
  </form>
);
```

## 개발 도구

### VS Code 확장 프로그램

```json
// .vscode/extensions.json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode", 
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

### ESLint 설정

```json
// .eslintrc.json
{
  "extends": [
    "@typescript-eslint/recommended",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

## 빌드 & 배포

### 빌드 최적화

```bash
# 타입 검사
npm run type-check

# 린팅
npm run lint

# 테스트
npm run test:run

# 프로덕션 빌드
npm run build

# 빌드 크기 분석
npm run build:analyze
```

### Docker 개발 환경

```dockerfile
# Dockerfile.dev
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```