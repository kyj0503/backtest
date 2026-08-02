# 테스트 환경 및 실행

이 문서는 프론트엔드 테스트를 위한 환경 설정과 Vitest를 사용한 테스트 실행 방법을 안내합니다.

## 테스트 스택

-   **테스트 러너 (Test Runner)**: **Vitest**
    -   Vite 기반으로 구축되어 설정이 매우 간단하고 실행 속도가 빠릅니다.
    -   Jest와 유사한 API를 제공하여 기존 Jest 사용자들이 쉽게 적응할 수 있습니다.
-   **테스팅 라이브러리**: **React Testing Library (RTL)**
    -   컴포넌트를 실제 사용자가 사용하는 방식과 유사하게 테스트하도록 돕는 라이브러리입니다.
    -   구현 세부 사항보다는 컴포넌트의 동작에 집중하여 리팩토링에 강건한 테스트를 작성하게 합니다.
-   **모킹 (Mocking)**: **Vitest 내장 `vi` 객체**
    -   API 요청, 타이머, 외부 모듈 등을 모킹하는 데 사용됩니다.
-   **E2E 테스트**: **Playwright**
    -   실제 브라우저 환경에서 사용자 시나리오를 테스트하기 위한 도구입니다.

## 설정 파일

-   **`vitest.config.ts`**: Vitest 설정은 `vite.config.ts`와 **분리된 별도 파일**에 있습니다.
    ```typescript
    // vitest.config.ts
    import { defineConfig } from 'vitest/config';

    export default defineConfig({
      // ... plugins, resolve.alias ...
      test: {
        globals: true,             // describe, it, expect 등을 전역으로 사용
        environment: 'happy-dom',  // 브라우저 환경 시뮬레이션
        setupFiles: ['./src/test/setup.ts'],
        css: true,
        pool: 'forks',
        maxWorkers: 1,
        isolate: true,             // 아래 주의 참고
        sequence: { concurrent: false },
      },
    });
    ```

    > **`isolate`를 `false`로 바꾸지 마십시오.** 모든 테스트 파일이 하나의 happy-dom 환경을 공유하게 되는데, vitest는 직전 실행의 파일별 소요시간을 캐시해 실행 순서를 조정하므로 순서가 매번 달라집니다. 그 결과 스위트가 flaky해집니다 — 실제로 같은 커밋에서 `113 passed`와 `3 failed`가 번갈아 나왔고, 깨끗한 도커 빌드에서는 최대 9건까지 실패했습니다.

-   **`src/test/setup.ts`**: 모든 테스트 실행 전 전역 설정을 담당합니다. MSW 서버 기동(`server.listen`), `@testing-library/jest-dom` 매처 등록, happy-dom이 구현하지 않는 `window.alert`/`confirm`/`prompt` 모킹 등이 여기에 있습니다.

-   **`tsconfig.test.json`**: 테스트 코드 전용 타입 체크 설정입니다. `tsconfig.build.json`이 테스트 파일을 제외하고 vitest는 타입 체크를 하지 않으므로, 이 설정이 없으면 삭제된 함수를 import해도 컴파일 단계에서 잡히지 않습니다(실제로 그런 테스트가 8개월간 방치된 적이 있습니다).

## 테스트 실행

`package.json`에 정의된 스크립트를 통해 테스트를 실행합니다.

-   **모든 단위/컴포넌트 테스트 실행 (Headless):**
    ```bash
    npm run test
    ```
    CI/CD 환경이나 터미널에서 모든 테스트를 실행하고 결과를 확인하는 데 사용됩니다.

-   **UI 모드로 테스트 실행:**
    ```bash
    npm run test:ui
    ```
    브라우저에서 테스트 결과, 코드 커버리지, 모듈 의존성 그래프 등을 시각적으로 확인하며 대화형으로 테스트를 실행할 수 있습니다. 개발 중에 특정 테스트만 골라 실행하거나 디버깅할 때 매우 유용합니다.

-   **1회 실행 (CI에서 쓰는 형태):**
    ```bash
    npm run test:run
    ```

-   **타입 체크:**
    ```bash
    npm run type-check       # 프로덕션 코드 (tsconfig.build.json)
    npm run type-check:test  # 테스트 코드 (tsconfig.test.json)
    ```
    테스트 코드는 `type-check`에 포함되지 않으므로 반드시 `type-check:test`를 함께 돌려야 합니다.

-   **E2E 테스트 실행:**
    ```bash
    npm run test:e2e
    ```
    Playwright를 사용하여 `e2e/` 디렉토리의 종단간 테스트를 실행합니다.

    > 개발 컨테이너에는 Playwright 브라우저가 설치되어 있지 않아 컨테이너 안에서는 실행되지 않습니다. 호스트에서 `npx playwright install` 후 실행하십시오.

## CI에서의 실행

`Jenkinsfile`의 `Quality Gate` 스테이지가 `docker build --target test ./backtest_fe`로 아래를 순서대로 실행합니다. 하나라도 실패하면 이미지 빌드와 배포에 도달하지 못합니다.

```
npm run lint → npm run type-check → npm run type-check:test → npm run test:run
```

로컬에서 CI와 동일한 조건으로 확인하려면 같은 명령을 그대로 쓰면 됩니다.

```bash
docker build --target test ./backtest_fe
```

E2E는 이 게이트에 포함되지 않습니다.

## 현재 기준선

테스트 파일 16개 / 테스트 113건, 전부 통과. 실패가 보이면 회귀입니다.

## 파일 구조

-   **테스트 파일 위치**: 테스트 대상 파일과 동일한 디렉토리에 `*.test.ts` 또는 `*.test.tsx` 형식으로 위치시키는 것을 권장합니다. (예: `Button.tsx`와 `Button.test.tsx`)
    -   **장점**: 테스트 파일과 실제 코드의 접근성이 좋아져 유지보수가 용이합니다.
-   **전역 설정**: `src/test/` 디렉토리에 테스트 관련 전역 설정 파일(`setup.ts`)이나 모킹 파일들을 위치시킵니다.
-   **E2E 테스트**: `e2e/` 최상위 디렉토리에 별도로 위치시킵니다.
