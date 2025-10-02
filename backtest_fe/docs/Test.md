# 프론트엔드 테스트 개요

## 테스트 위치

- `src/components/__tests__`: 사용자 인터페이스 관련 컴포넌트 테스트 (예: `ThemeSelector`, `ErrorBoundary`)
- `src/shared/**/__tests__`: 공통 훅 및 유틸리티 테스트 (`useForm`, `useAsync`, 날짜/숫자 헬퍼, `debounce` 등)
- `src/features/backtest/hooks/__tests__`: 도메인 핵심 훅 테스트 (`useBacktest`, `useBacktestForm`)
- `src/features/backtest/model/__tests__`: 백테스트 폼 리듀서 및 헬퍼 테스트
- `src/features/backtest/services/__tests__/backtestService.integration.test.ts`: MSW를 사용한 API 연동(통합) 테스트

테스트 파일은 해당 코드와 함께 배치한다.

## 커버 항목

다음 영역을 중심으로 테스트가 작성되어 있습니다.

| 영역 | 주요 파일 | 목적 |
|------|-----------|------|
| 훅 (Hooks) | `useBacktest`, `useBacktestForm`, 공통 훅 | 상태 전이, 성공/오류 처리 검증 (AAA 패턴 권장) |
| 리듀서 | `backtestFormReducer`, 헬퍼 | 금액/비중 계산, 검증 메시지 등 로직 검증 |
| 서비스 | `BacktestService` 통합 테스트 | Axios 요청/응답 처리 및 에러 핸들링을 MSW로 검증 |
| 컴포넌트 | `ThemeSelector`, `ErrorBoundary` 등 | 사용자 상호작용, 접근성 관련 동작 검증 |
| 유틸리티 | `src/shared/utils` | 순수 함수 동작 검증, `debounce` 등 타이머 기반 로직 테스트 |

현재 E2E 테스트는 없다. 전체 플로우는 Playwright 또는 Cypress 도입을 검토한다.

## 실행 방법

로컬과 Docker에서 테스트를 실행하는 방법은 다음과 같다.

로컬 단회 실행:

```bash
# 모든 테스트 단회 실행(CI용)
npm run test:run
```

특정 파일만 실행:

```bash
npx vitest run src/features/backtest/hooks/__tests__/useBacktest.test.ts
```

Docker 워크플로우(Compose 사용):

```bash
# 필요 시 환경 변수 설정
export REDIS_PASSWORD=change-me-dev-redis-pass
cd /home/kyj/backtest
docker compose -f compose/compose.dev.yaml up -d backtest_fe
docker compose -f compose/compose.dev.yaml exec backtest_fe npm run test:run
docker compose -f compose/compose.dev.yaml down
```

Vitest는 `src/test/setup.ts`에서 Testing Library 매처를 등록하고 MSW 서버 시작/종료를 관리한다. 커버리지는 `npm run test:coverage`로 생성한다(결과는 `coverage/`).
