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

-   **`vite.config.ts`**: Vitest는 Vite의 설정을 공유합니다. `test` 속성을 통해 Vitest 관련 설정을 추가합니다.
    ```typescript
    // vite.config.ts
    import { defineConfig } from 'vite';
    
    export default defineConfig({
      // ... 다른 설정 ...
      test: {
        globals: true, // describe, it, expect 등을 전역으로 사용
        environment: 'jsdom', // 브라우저 환경 시뮬레이션
        setupFiles: './src/test/setup.ts', // 각 테스트 파일 실행 전 설정 파일
        css: true, // CSS 파일 처리 활성화
      },
    });
    ```
-   **`src/test/setup.ts`**: 모든 테스트가 실행되기 전에 필요한 전역 설정을 담당합니다. 예를 들어, `vitest-localstorage-mock`을 설정하거나 `matchMedia`와 같은 브라우저 API를 모킹합니다.

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

-   **E2E 테스트 실행:**
    ```bash
    npm run test:e2e
    ```
    Playwright를 사용하여 `e2e/` 디렉토리의 종단간 테스트를 실행합니다.

## 파일 구조

-   **테스트 파일 위치**: 테스트 대상 파일과 동일한 디렉토리에 `*.test.ts` 또는 `*.test.tsx` 형식으로 위치시키는 것을 권장합니다. (예: `Button.tsx`와 `Button.test.tsx`)
    -   **장점**: 테스트 파일과 실제 코드의 접근성이 좋아져 유지보수가 용이합니다.
-   **전역 설정**: `src/test/` 디렉토리에 테스트 관련 전역 설정 파일(`setup.ts`)이나 모킹 파일들을 위치시킵니다.
-   **E2E 테스트**: `e2e/` 최상위 디렉토리에 별도로 위치시킵니다.
