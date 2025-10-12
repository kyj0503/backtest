# 프론트엔드 개발 가이드

## 환경 준비

```bash
cd backtest_fe
npm ci
npm run dev
```

Vite 개발 서버: http://localhost:5173

## 디렉터리 구조

```
src/
├── features/           # 기능별 모듈
│   └── backtest/      # 백테스트 기능
│       ├── components/# UI 컴포넌트
│       ├── hooks/     # 비즈니스 로직 훅
│       ├── api/       # API 클라이언트
│       └── model/     # 타입 정의
├── shared/            # 공통 리소스
│   ├── api/          # 공통 API 설정
│   ├── components/   # 공통 UI 컴포넌트
│   ├── hooks/        # 공통 훅 (useAsync, useForm, useTheme)
│   ├── types/        # 공통 타입
│   └── utils/        # 유틸리티 함수
├── pages/            # 라우트 페이지
├── themes/           # 테마 정의 (JSON)
└── test/             # 테스트 설정
```

## 주요 훅

**useAsync**: 비동기 상태 관리
```typescript
const { data, isLoading, error, execute } = useAsync(fetcher)
```

**useForm**: 폼 상태 및 검증
```typescript
const { data, errors, handleSubmit } = useForm(initialValues, validators)
```

**useTheme**: 테마 관리
```typescript
const { currentTheme, isDarkMode, changeTheme, toggleDarkMode } = useTheme()
```

## API 프록시

`vite.config.ts`에서 백엔드 API 프록시 설정:
```typescript
proxy: {
  '/api/v1/backtest': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```
