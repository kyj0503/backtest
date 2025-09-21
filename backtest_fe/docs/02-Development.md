# 개발 가이드 - 핵심 패턴

## 🚀 빠른 시작

### 요구 사항
- **Node.js 18+** (권장: 18.17.0 이상)
- **npm 8+** 또는 **yarn 3+**

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

## ⚙️ 환경 설정

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

## 🏗️ 아키텍처 패턴

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

## 🧪 테스트 전략

### 테스트 유형별 접근

```bash
# 단위 테스트 - 유틸리티, 훅, 서비스
npm run test:unit

# 컴포넌트 테스트 - UI 컴포넌트 
npm run test:components

# 통합 테스트 - 전체 플로우
npm run test:integration

# 모든 테스트 실행
npm run test:run
```

### 테스트 작성 패턴

```typescript
// 훅 테스트
describe('useBacktest', () => {
  it('should handle successful backtest execution', async () => {
    const { result } = renderHook(() => useBacktest());
    
    await act(async () => {
      await result.current.execute(mockRequest);
    });

    expect(result.current.data).toEqual(mockResult);
  });
});

// 컴포넌트 테스트
describe('BacktestForm', () => {
  it('should submit form with valid data', async () => {
    const mockOnSubmit = vi.fn();
    render(<BacktestForm onSubmit={mockOnSubmit} />);
    
    await userEvent.type(screen.getByLabelText('Symbol'), 'AAPL');
    await userEvent.click(screen.getByRole('button', { name: 'Execute' }));
    
    expect(mockOnSubmit).toHaveBeenCalledWith({ symbol: 'AAPL' });
  });
});
```

## 🎨 스타일링 패턴

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

## 🔧 개발 도구

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

## 🚀 빌드 & 배포

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

이 가이드를 통해 일관성 있고 확장 가능한 개발을 진행할 수 있습니다.
