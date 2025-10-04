# 개발 환경 가이드

## 환경 준비

```bash
cd backtest_fe
npm ci
cp .env.example .env # 필요한 경우
npm run dev
```

Vite 개발 서버는 포트 5173에서 실행되며 Docker 컨테이너에서도 동일한 포트를 노출한다.

## 환경 변수

주요 값은 프로젝트 루트의 `.env.local` 또는 `.env`에서 관리한다.

```bash
VITE_API_BASE_URL=/api
API_PROXY_TARGET=http://backtest_be_fast:8000
SPRING_PROXY_TARGET=http://host.docker.internal:8080
FASTAPI_PROXY_TARGET=http://backtest_be_fast:8000
VITE_APP_VERSION=1.0.0
REDIS_PASSWORD=change-me-dev-redis-pass
```

Compose는 `REDIS_PASSWORD`를 명령 치환에 사용하므로 필요하면 `export REDIS_PASSWORD=...`로 미리 등록한다.

## Vite 프록시 구성

`vite.config.ts`는 서비스별 타깃을 분리한다.

```ts
server: {
  proxy: {
    '/api/auth': { target: SPRING_TARGET, changeOrigin: true },
    '/api/users': { target: SPRING_TARGET, changeOrigin: true },
    '/api/chat': { target: SPRING_TARGET, changeOrigin: true },
    '/ws': { target: SPRING_TARGET, changeOrigin: true, ws: true },
    '/api/v1/backtest': { target: FASTAPI_TARGET, changeOrigin: true },
    '/api': { target: SPRING_TARGET, changeOrigin: true }
  }
}
```

`SPRING_TARGET`, `FASTAPI_TARGET`은 각각 `SPRING_PROXY_TARGET`, `FASTAPI_PROXY_TARGET` 환경 변수로 설정한다.

## 폴더 구조

```
src/
├── features/
│   ├── auth/
│   ├── backtest/
│   ├── chat/
│   └── community/
├── pages/
├── shared/
│   ├── api/
│   ├── components/
│   ├── config/
│   ├── hooks/
│   ├── types/
│   └── utils/
├── test/
└── themes/
```

- `features/backtest`는 폼 리듀서, 전략 설정, API 연동을 포함한다.
- `shared/hooks`에는 `useAsync`, `useForm`, `useTheme` 등 재사용 훅이 있다.
- `test/`에는 공용 테스트 설정, MSW 서버 구성, 픽스처가 있다.

## 커스텀 훅 패턴

### useAsync

```ts
const { data, isLoading, error, execute } = useAsync(fetcher, [], { immediate: false })
await execute()
```

비동기 호출 상태(isLoading, isSuccess, isError)를 관리한다.

### useForm

```ts
const { data, errors, handleSubmit } = useForm(initialValues, validators)
```

필드 업데이트, 폼 검증, 제출 핸들러를 제공한다.

### useTheme

```ts
const { currentTheme, isDarkMode, changeTheme, toggleDarkMode } = useTheme()
```

`themes/` 디렉터리에 정의된 테마를 적용하고 다크 모드를 토글한다.

## 서비스 레이어 패턴

`features/backtest/services/backtestService.ts`는 Axios 기반 API 호출을 서비스 클래스로 묶는다. 테스트는 Axios 인스턴스를 목킹해 요청 경로/페이로드를 검증한다.

```ts
const result = await BacktestService.executeBacktest(request)
expect(apiClient.post).toHaveBeenCalledWith('/v1/backtest/execute', request)
```

## 테스트 인프라

- 러너: Vitest (`vitest.config.ts`에서 jsdom 환경과 전역 설정 사용)
- 렌더링: React Testing Library + 커스텀 `render`
- API 모킹: MSW 서버 초기화(`src/test/setup.ts`), 서비스 테스트는 Axios 목을 사용
- 테스트 유틸리티: `src/test/fixtures.ts`, `src/test/helpers.ts`

실행 명령은 `npm run test:run`이며, 컨테이너에서는 `docker compose -f compose.dev.yaml exec backtest_fe npm run test:run`을 사용한다.
