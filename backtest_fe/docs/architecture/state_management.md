# 상태 관리 전략

본 프로젝트는 **전역 상태 관리 라이브러리를 쓰지 않습니다.** Zustand, Redux, Context 기반 전역 스토어 어느 것도 도입된 적이 없습니다 (`package.json`에 `zustand`가 의존성으로 들어간 적이 없고, 코드베이스에 `store` 파일이나 `createContext` 호출도 없습니다). 대신 두 가지 패턴을 조합합니다: 여러 컴포넌트가 함께 쓰는 상태는 **커스텀 훅(`useState` 기반) + localStorage**로, 복잡한 지역 상태는 **React의 `useReducer` 훅**으로 관리합니다.

## 1. 여러 컴포넌트가 공유하는 상태: 커스텀 훅 + localStorage

전역 스토어가 없으므로, "여러 곳에서 쓰이는 상태"는 상태를 소유하는 커스텀 훅을 각 컴포넌트가 개별적으로 호출하거나(테마), 상위 컴포넌트가 훅으로 상태를 만들어 props로 내려주는(백테스트 결과) 방식으로 처리됩니다. 둘 다 싱글턴 스토어가 아니라는 점에 유의하세요 — "전역"이라기보다는 "여러 곳에서 재사용되는 로컬 상태 패턴"에 가깝습니다.

-   **UI 테마 (`shared/hooks/useTheme.ts`)**:
    -   `useTheme()`은 내부적으로 `useState`(현재 테마, 다크모드 여부) + `useEffect`(DOM에 CSS 변수/`.dark` 클래스 적용, `localStorage`에 저장)로 구현된 평범한 커스텀 훅입니다. 스토어가 아니므로 **호출할 때마다 독립적인 state 인스턴스가 생깁니다.**
    -   현재 `App.tsx`, `Header.tsx`, `ThemeSelector.tsx`가 각자 `useTheme()`을 호출합니다. 세 인스턴스는 서로 다른 `useState`를 갖고, `localStorage`와 DOM(`document.documentElement`에 설정된 CSS 변수 및 `.dark` 클래스)을 통해서만 간접적으로 동기화됩니다. `App.tsx`의 인스턴스는 마운트 시 테마를 DOM에 적용하는 부수효과 실행용으로만 쓰이고, `Header.tsx`/`ThemeSelector.tsx`의 인스턴스가 실제 토글 UI를 담당합니다.
    -   **결과 코드 예시** (실제 `useTheme.ts`를 단순화):
        ```typescript
        export const useTheme = () => {
          const [currentTheme, setCurrentTheme] = useState<ThemeName>(() => {
            const stored = localStorage.getItem('selected-theme') as ThemeName;
            return stored && themes[stored] ? stored : 'claymorphism';
          });
          const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
            const stored = localStorage.getItem('dark-mode');
            return stored !== null ? stored === 'true' : window.matchMedia('(prefers-color-scheme: dark)').matches;
          });

          useEffect(() => {
            // document.documentElement에 CSS 변수 주입 + .dark 클래스 토글
            // + localStorage.setItem(...)으로 두 값을 모두 저장
          }, [currentTheme, isDarkMode]);

          return { currentTheme, isDarkMode, changeTheme, toggleDarkMode, /* ... */ };
        };
        ```
    -   **알려진 한계**: 진짜 전역 스토어가 아니므로, 한 인스턴스에서 `changeTheme`을 호출해도 다른 인스턴스의 `currentTheme` state는 리렌더링되기 전까지 갱신되지 않습니다(다음 렌더에서 `localStorage`를 다시 읽는 컴포넌트만 반영). 렌더 구조가 바뀌면 desync가 날 수 있는 구조적 리스크로 알려져 있습니다.

-   **백테스트 결과 데이터**: 전역 스토어로 관리되지 않습니다. `features/backtest/hooks/usePortfolioBacktest.ts`가 `useState`로 `result`/`isLoading`/`error`를 소유하고, 페이지 컴포넌트(`pages/PortfolioPage.tsx`)가 이 훅을 호출해 얻은 값을 `BacktestResults` 등 하위 컴포넌트에 **props로 전달**합니다. 즉 흔한 "훅으로 상태를 끌어올리고 props로 내려주는(lift state up)" 패턴이며, `useBacktestResultStore` 같은 전역 스토어는 존재하지 않습니다.

-   **인증 정보**: 로그인/토큰 상태는 현재 미구현입니다.

## 2. 지역 상태: `useState` 와 `useReducer`

### `useState`

-   **역할**: 단일 컴포넌트 내에서만 사용되는 간단한 상태를 관리합니다.
-   **사용 사례**:
    -   모달의 열림/닫힘 상태
    -   입력 필드의 값
    -   토글 버튼의 활성화 여부

### `useReducer`

-   **역할**: 여러 개의 하위 값을 포함하거나, 상태 변경 로직이 복잡한 경우에 사용됩니다. 특히, 한 상태의 변경이 다른 상태에 영향을 미치는 경우 유용합니다.
-   **사용 사례**: **백테스트 설정 폼 (`PortfolioBacktestForm`)**
    -   백테스트 폼은 종목, 전략, 시작/종료일, 초기 자본금, 포트폴리오 비중 등 매우 다양한 상태를 가집니다.
    -   하나의 상태 변경이 다른 상태에 영향을 미칩니다. 예를 들어, 포트폴리오 항목의 가중치(`weight`)를 변경하면 다른 항목들의 가중치도 자동으로 재계산되어야 합니다.
    -   이러한 복잡한 로직을 `useState`로 각각 관리하면 코드가 길어지고, 상태 업데이트 로직이 여러 곳에 흩어져 유지보수가 어려워집니다.

-   **`useReducer`를 사용한 이유**:
    -   **중앙화된 로직**: `reducer` 함수 내에 모든 상태 변경 로직이 모여 있어 코드를 이해하고 디버깅하기 쉽습니다.
    -   **예측 가능한 상태 변경**: `dispatch`에 `action`을 전달하는 방식으로만 상태를 변경할 수 있어, 상태 변화를 추적하기 용이합니다.
    -   **테스트 용이성**: `reducer`는 순수 함수이므로, 다양한 `action`에 대해 예상대로 상태를 변경하는지 독립적으로 테스트하기 매우 쉽습니다.

-   **구현 패턴 (`backtestFormReducer.ts`)**:
    ```typescript
    // Action 타입 정의 (실제 타입명은 BacktestFormAction/BacktestFormState)
    type Action =
      | { type: 'SET_TICKER'; payload: { index: number; ticker: string } }
      | { type: 'UPDATE_WEIGHT'; payload: { index: number; weight: number } }
      | { type: 'REBALANCE_WEIGHTS' };

    // Reducer 함수
    function backtestFormReducer(state: BacktestFormState, action: BacktestFormAction): BacktestFormState {
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

-   전역 상태 관리 라이브러리는 쓰지 않습니다. 여러 컴포넌트가 공유하는 상태(테마)는 **커스텀 훅 + localStorage**로, 백테스트 결과처럼 한 화면 트리 안에서만 공유되면 되는 상태는 **훅으로 끌어올려 props로 전달**하는 방식으로 처리합니다.
-   `useReducer`는 백테스트 폼과 같이 여러 입력과 복잡한 규칙이 얽혀 있는 **특정 기능의 지역 상태**를 중앙에서 관리하여 코드의 안정성과 유지보수성을 높입니다.
-   간단한 컴포넌트 내부 상태는 `useState`를 사용합니다.

이러한 조합으로 대부분의 화면을 충분히 커버하지만, `useTheme`처럼 여러 컴포넌트가 각자 훅을 호출하는 패턴은 진짜 전역 상태가 아니라는 한계가 있습니다 — 인스턴스 간 동기화가 필요해지면 Context나 상태 관리 라이브러리 도입이 검토 대상입니다 (`TODO.md`의 관련 항목 참고).
