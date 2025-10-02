# 프론트엔드 테스트 가이드

## 개요

테스트는 수정에 대한 빠른 피드백을 제공하고 비즈니스 요구사항을 검증하는 안전망이다. React 기반 UI에서도 FAST 원칙과 가치 기반 전략을 적용해 필요한 곳에만 테스트를 집중해야 한다.

### 핵심 원칙
- **FIRST**: 빠르게 실행되고, 독립적이며, 반복 가능하며, 결과가 명확하고, 기능 작성 시점과 가까워야 한다.
- **가치 중심**: 단순 렌더링보다 포트폴리오 검증, 백테스트 실행 등 핵심 흐름을 우선한다.
- **행동 검증**: 내부 구현보다 사용자/서비스 관점의 결과를 확인한다.

## 테스트 전략

### 테스트 피라미드
```
        /\
       /  \
      / E2E \  (핵심 사용자 플로우만 실행)
     /______\
    /        \
   / 통합 테스트 \
  /______________\
 /                \
/   단위 테스트     \  (대부분의 검증)
```

### 현재 분포
- 공용 훅·유틸리티 단위 테스트: 33개 (`useAsync`, `useForm`, `shared/utils`)
- 서비스 레이어 단위 테스트: 10개 (`BacktestService`, Axios 목 사용)
- UI 컴포넌트 테스트: 16개 (`ThemeSelector`, `ErrorBoundary`)

향후에는 `useBacktest`, `BacktestForm`, `backtestFormReducer`처럼 도메인 로직이 많은 영역을 우선 보완해야 한다.

## 테스트 유형

### 단위 테스트
- 대상: 훅, 유틸리티, 서비스 함수
- 도구: Vitest, React Testing Library, `renderHook`
- 예: `useForm` 필드 업데이트, `debounce` 동작, Axios 요청 파라미터

### 통합 테스트
- 대상: 컨텍스트, 폼, 전략 시나리오 등 여러 모듈이 협력하는 부분
- 현재 상태: 컨텍스트·폼 통합 테스트가 부재. React Query나 폼 리듀서를 포함한 통합 검증이 필요함.

### E2E 테스트
- 아직 미구현. Playwright 또는 Cypress로 핵심 시나리오(로그인, 백테스트 실행, 결과 확인) 최소 1~2건을 목표로 한다.

## 작성 원칙

### AAA 패턴
```ts
it('다크 모드를 전환한다', async () => {
  const user = userEvent.setup()
  render(<ThemeSelector />)
  await user.click(screen.getByRole('button', { name: /라이트/i }))
  expect(toggleDarkMode).toHaveBeenCalledTimes(1)
})
```

### 명명 규칙
- `it('조건을 설명하면 결과가 어떻다')` 형식으로 상황과 기대값을 함께 표현한다.
- 한 테스트는 하나의 개념만 검증한다.

### 목킹 가이드
- 도메인 로직은 가능한 실제 객체로 검증하고, 외부 API·브라우저 전역에 한해 목킹을 사용한다.
- Axios 인스턴스를 직접 목킹할 경우 요청 경로와 페이로드만 검증하고 구현 세부사항에는 의존하지 않는다.

## 구현 현황

| 영역 | 대상 | 비고 |
|------|------|------|
| 훅 | `useAsync`, `useForm` | happy-dom 환경, 성공/실패/리셋 흐름 검증 |
| 서비스 | `BacktestService` | `apiClient` 목으로 요청 경로 검증, MSW는 아직 사용하지 않음 |
| 컴포넌트 | `ThemeSelector`, `ErrorBoundary` | 광범위한 목 데이터 사용, 구조 의존성 완화 필요 |
| 미작성 | `useBacktest`, `useBacktestForm`, `backtestFormReducer`, `BacktestForm`, `BacktestResults` | 포트폴리오 검증·전략 파라미터 변환 등 핵심 로직 |

### 플레키 테스트 주의
- `shared/utils/__tests__/index.test.ts`의 디바운스 테스트는 실제 타이머에 의존한다. 긴 지연 시간 또는 가짜 타이머 사용으로 안정화할 수 있다.

## 환경 설정

### Vitest 설정 요약 (`vitest.config.ts`)
- jsdom 환경, 전역 매처 등록
- `setupFiles: ['./src/test/setup.ts']`
- 커버리지: V8 provider, `src/**/*.{ts,tsx}` 포함 (테스트 폴더 제외)
- Docker에서 안정성을 높이기 위해 `pool: 'forks'`와 순차 실행을 사용

### 전역 설정 (`src/test/setup.ts`)
- Testing Library `expect` 확장
- MSW 서버 시작/리셋/종료 (향후 API 통합 테스트에 사용 가능)
- `matchMedia`, `IntersectionObserver`, `ResizeObserver` 전역 목킹

### 유틸리티
- `src/test/utils.tsx`: 공용 `render`, 픽스처 팩토리, 헬퍼 함수
- `src/test/fixtures.ts`: 백테스트, 전략, OHLC 데이터 팩토리
- `src/test/mocks`: MSW 핸들러와 서버 정의 (현재 대부분의 테스트에서는 사용하지 않음)

## 실행 방법

```bash
# 로컬
npm run test:run

# 단일 파일
npx vitest run src/shared/hooks/__tests__/useForm.test.ts

# Docker 컨테이너
export REDIS_PASSWORD=change-me-dev-redis-pass # 필요 시
cd /path/to/backtest
docker compose -f compose/compose.dev.yaml up -d backtest_fe
docker compose -f compose/compose.dev.yaml exec backtest_fe npm run test:run
docker compose -f compose/compose.dev.yaml down
```

## 개선 체크리스트

1. `useBacktest`의 성공/오류/포트폴리오 분기 테스트 추가 (`src/features/backtest/hooks/useBacktest.ts`)
2. `backtestFormReducer`와 `backtestFormHelpers`의 금액·비중 변환 로직 검증 (`src/features/backtest/model/backtestFormReducer.ts`)
3. `BacktestForm` 통합 테스트에서 폼 제출 흐름, 전략 파라미터 변환, 오류 표시 확인
4. MSW 핸들러를 활용한 서비스 테스트 작성 또는 기존 테스트를 MSW 기반으로 이전
5. Playwright/Cypress 기반 E2E 테스트로 백테스트 전체 흐름 검증

## 참고 자료
- Testing Library 문서: https://testing-library.com/
- Vitest 문서: https://vitest.dev/
- Toss Tech, MangKyu, BoostBrothers의 테스트 전략 글 (프로젝트 루트의 `(수정금지)테스트 코드 작성 요령.md` 참고)
