# 커스텀 훅 및 리듀서 테스트

React 애플리케이션에서 복잡한 비즈니스 로직은 종종 UI 컴포넌트에서 분리되어 커스텀 훅(Custom Hooks)이나 리듀서(Reducer) 함수에 위치합니다. 이러한 로직을 테스트하는 것은 애플리케이션의 안정성을 보장하는 데 매우 중요합니다.

## 1. 리듀서(Reducer) 테스트

`useReducer`에 사용되는 리듀서 함수는 **순수 함수**입니다. 즉, 동일한 `state`와 `action`에 대해 항상 동일한 `newState`를 반환하며, 외부 상태에 의존하거나 부수 효과(side effects)를 일으키지 않습니다. 이러한 특성 덕분에 리듀서는 UI 렌더링 없이 매우 간단하고 빠르게 테스트할 수 있습니다.

### 테스트 전략

-   **도구**: `Vitest`
-   **방법**: 리듀서 함수를 직접 가져와서(import), 다양한 초기 상태와 액션을 인자로 전달하고, 반환된 새로운 상태가 예상과 일치하는지 검증합니다.

### 예시: `backtestFormReducer` 테스트

`backtestFormReducer`는 포트폴리오 자산의 가중치를 조절하는 복잡한 로직을 포함하고 있습니다.

```ts
// __tests__/recalcAmountsByWeight.test.ts

import { backtestFormReducer, initialState } from '@/features/backtest/model/backtestFormReducer';

describe('backtestFormReducer - Weight and Amount Recalculation', () => {
  it('should recalculate amounts of other assets when one asset weight is changed', () => {
    // Arrange: 초기 상태 설정
    const stateWithTwoAssets = {
      ...initialState,
      portfolio: {
        ...initialState.portfolio,
        assets: [
          { ticker: 'AAPL', weight: 50, amount: 5000 },
          { ticker: 'GOOG', weight: 50, amount: 5000 },
        ],
      },
    };

    // Act: 첫 번째 자산(AAPL)의 가중치를 20으로 변경하는 액션 전달
    const action = {
      type: 'RECALC_AMOUNTS_BY_WEIGHT' as const,
      payload: {
        assetIndex: 0, // AAPL
        newWeight: 20,
      },
    };
    const newState = backtestFormReducer(stateWithTwoAssets, action);

    // Assert: 상태 변화 검증
    const newAssets = newState.portfolio.assets;
    // 1. 변경된 자산(AAPL)의 가중치와 금액 확인
    expect(newAssets[0].weight).toBe(20);
    expect(newAssets[0].amount).toBe(2000); // 10000 * 0.2

    // 2. 나머지 자산(GOOG)의 가중치와 금액이 자동으로 재조정되었는지 확인
    expect(newAssets[1].weight).toBe(80); // 100 - 20
    expect(newAssets[1].amount).toBe(8000); // 10000 * 0.8
  });
});
```

## 2. 커스텀 훅(Custom Hook) 테스트

커스텀 훅은 내부적으로 `useState`, `useEffect` 등 다른 React 훅을 사용하므로, 일반 함수처럼 테스트할 수 없습니다. 훅을 테스트하려면 실제 React 컴포넌트 환경 내에서 실행해야 합니다. `React Testing Library`는 이를 위한 `renderHook`이라는 유틸리티를 제공합니다.

### 테스트 전략

-   **도구**: `Vitest` + `@testing-library/react`의 `renderHook`
-   **방법**:
    1.  `renderHook`을 사용하여 테스트할 훅을 렌더링합니다.
    2.  `renderHook`이 반환하는 `result` 객체를 통해 훅의 현재 반환값(`result.current`)에 접근합니다.
    3.  훅이 반환하는 함수를 실행해야 할 경우, `act`로 감싸서 실행하여 상태 업데이트가 DOM에 반영되도록 합니다.
    4.  상태 변경 후 `result.current`의 값이 예상대로 바뀌었는지 검증합니다.

### 예시: `useCounter` 훅 테스트

```tsx
// src/shared/hooks/useCounter.test.ts

import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('should initialize with the initial value', () => {
    // Arrange & Act
    const { result } = renderHook(() => useCounter(10));

    // Assert
    expect(result.current.count).toBe(10);
  });

  it('should increment the count', () => {
    // Arrange
    const { result } = renderHook(() => useCounter(0));

    // Act: 훅이 반환한 함수를 act로 감싸서 실행
    act(() => {
      result.current.increment();
    });

    // Assert
    expect(result.current.count).toBe(1);
  });

  it('should decrement the count', () => {
    // Arrange
    const { result } = renderHook(() => useCounter(5));

    // Act
    act(() => {
      result.current.decrement();
    });

    // Assert
    expect(result.current.count).toBe(4);
  });
});
```

`renderHook`을 사용하면 UI 컴포넌트를 직접 렌더링하지 않고도 훅의 로직 자체에만 집중하여 테스트할 수 있어, 복잡한 비즈니스 로직을 검증하는 데 매우 효과적입니다.
