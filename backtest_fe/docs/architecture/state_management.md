# 상태 관리 전략

본 프로젝트는 두 가지 주요 상태 관리 패턴을 조합하여 사용합니다. 전역 상태 관리를 위한 **Zustand**와 복잡한 지역 상태 관리를 위한 **React의 `useReducer` 훅**입니다.

## 1. 전역 상태: Zustand

-   **역할**: 여러 컴포넌트나 페이지에 걸쳐 공유되어야 하는 상태를 관리합니다.
-   **사용 사례**:
    -   **UI 테마**: 사용자가 선택한 테마(예: dark, light)는 애플리케이션 전역에 영향을 미치므로 Zustand로 관리합니다. (`useThemeStore`)
    -   **인증 정보**: 사용자 로그인 상태나 토큰과 같은 정보는 모든 페이지에서 필요하므로 전역 상태로 관리하는 것이 적합합니다. (현재는 미구현)
    -   **백테스트 결과 데이터**: 백테스트 실행 후, 결과 데이터는 통계 테이블, 차트, 요약 정보 등 여러 컴포넌트에서 사용됩니다. 이 데이터를 전역 상태로 관리하면 props drilling 없이 필요한 컴포넌트에서 직접 접근할 수 있습니다. (`useBacktestResultStore`)

-   **Zustand를 선택한 이유**:
    -   **단순함**: Redux에 비해 보일러플레이트 코드가 거의 없습니다. 스토어를 정의하고 훅을 통해 바로 사용할 수 있습니다.
    -   **유연성**: Redux처럼 액션, 리듀서 등의 복잡한 개념 없이 상태를 직접 변경할 수 있습니다.
    -   **작은 번들 크기**: 매우 가벼운 라이브러리로, 애플리케이션 성능에 미치는 영향이 적습니다.

-   **구현 예시 (`useThemeStore.ts`)**:
    ```typescript
    import { create } from 'zustand';
    import { persist } from 'zustand/middleware';

    interface ThemeState {
      theme: string;
      setTheme: (theme: string) => void;
    }

    export const useThemeStore = create<ThemeState>()(
      persist(
        (set) => ({
          theme: 'dark', // 기본값
          setTheme: (theme) => set({ theme }),
        }),
        {
          name: 'theme-storage', // localStorage에 저장될 키
        }
      )
    );
    ```

## 2. 지역 상태: `useState` 와 `useReducer`

### `useState`

-   **역할**: 단일 컴포넌트 내에서만 사용되는 간단한 상태를 관리합니다.
-   **사용 사례**:
    -   모달의 열림/닫힘 상태
    -   입력 필드의 값
    -   토글 버튼의 활성화 여부

### `useReducer`

-   **역할**: 여러 개의 하위 값을 포함하거나, 상태 변경 로직이 복잡한 경우에 사용됩니다. 특히, 한 상태의 변경이 다른 상태에 영향을 미치는 경우 유용합니다.
-   **사용 사례**: **백테스트 설정 폼 (`BacktestForm`)**
    -   백테스트 폼은 종목, 전략, 시작/종료일, 초기 자본금, 포트폴리오 비중 등 매우 다양한 상태를 가집니다.
    -   하나의 상태 변경이 다른 상태에 영향을 미칩니다. 예를 들어, 포트폴리오 항목의 가중치(`weight`)를 변경하면 다른 항목들의 가중치도 자동으로 재계산되어야 합니다.
    -   이러한 복잡한 로직을 `useState`로 각각 관리하면 코드가 길어지고, 상태 업데이트 로직이 여러 곳에 흩어져 유지보수가 어려워집니다.

-   **`useReducer`를 사용한 이유**:
    -   **중앙화된 로직**: `reducer` 함수 내에 모든 상태 변경 로직이 모여 있어 코드를 이해하고 디버깅하기 쉽습니다.
    -   **예측 가능한 상태 변경**: `dispatch`에 `action`을 전달하는 방식으로만 상태를 변경할 수 있어, 상태 변화를 추적하기 용이합니다.
    -   **테스트 용이성**: `reducer`는 순수 함수이므로, 다양한 `action`에 대해 예상대로 상태를 변경하는지 독립적으로 테스트하기 매우 쉽습니다.

-   **구현 패턴 (`backtestFormReducer.ts`)**:
    ```typescript
    // Action 타입 정의
    type Action =
      | { type: 'SET_TICKER'; payload: { index: number; ticker: string } }
      | { type: 'UPDATE_WEIGHT'; payload: { index: number; weight: number } }
      | { type: 'REBALANCE_WEIGHTS' };

    // Reducer 함수
    function backtestFormReducer(state: FormState, action: Action): FormState {
      switch (action.type) {
        case 'SET_TICKER':
          // ... 로직 ...
          return newState;
        case 'UPDATE_WEIGHT':
          // ... 가중치 업데이트 및 다른 가중치 재계산 로직 ...
          return newState;
        // ... 다른 케이스들 ...
        default:
          return state;
      }
    }

    // 컴포넌트에서 사용
    const [formState, dispatch] = useReducer(backtestFormReducer, initialState);

    // 가중치 변경 시
    dispatch({ type: 'UPDATE_WEIGHT', payload: { index: 0, weight: 50 } });
    ```

## 결론

-   **Zustand**는 애플리케이션 전반에 걸쳐 필요한 **전역 상태**를 간결하게 관리합니다.
-   **`useReducer`**는 백테스트 폼과 같이 여러 입력과 복잡한 규칙이 얽혀 있는 **특정 기능의 지역 상태**를 중앙에서 관리하여 코드의 안정성과 유지보수성을 높입니다.
-   간단한 컴포넌트 내부 상태는 **`useState`**를 사용합니다.

이러한 조합을 통해 각 상태의 스코프(scope)에 맞는 최적의 도구를 사용하여 상태 관리의 복잡성을 효과적으로 제어합니다.
