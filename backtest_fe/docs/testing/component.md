# 컴포넌트 테스트

컴포넌트 테스트는 사용자가 경험하게 될 UI가 의도대로 동작하는지를 검증하는 데 중점을 둡니다. React Testing Library(RTL)의 철학에 따라, 우리는 컴포넌트의 내부 구현보다는 외부에서 관찰 가능한 행동을 테스트합니다.

## 핵심 원칙

1.  **사용자처럼 테스트하라**: 테스트는 컴포넌트의 `props`나 `state`를 직접 확인하는 대신, 화면에 렌더링된 결과를 보고 상호작용하는 방식으로 작성되어야 합니다.
2.  **접근성을 고려한 쿼리 사용**: `getByRole`, `getByLabelText`, `getByText` 등 사용자가 UI를 식별하는 방식과 유사한 쿼리를 우선적으로 사용합니다. `data-testid`는 다른 방법으로 요소를 찾기 어려울 때 최후의 수단으로 사용합니다.
3.  **`act`와 비동기 처리**: 상태 업데이트나 비동기 작업 후의 UI 변경을 검증할 때는 `act` 유틸리티나 RTL의 비동기 API(`findBy*`, `waitFor`)를 사용하여 모든 업데이트가 완료된 후 단언(assertion)을 수행해야 합니다.

## 테스트 작성 패턴

컴포넌트 테스트는 일반적으로 "Arrange-Act-Assert" (AAA) 패턴을 따릅니다.

1.  **Arrange (준비)**: 테스트할 컴포넌트를 렌더링하고, 필요하다면 모의(mock) `props`나 초기 상태를 설정합니다.
2.  **Act (실행)**: 사용자의 행동을 시뮬레이션합니다. 예를 들어, 버튼을 클릭하거나(`fireEvent` 또는 `userEvent`), 입력 필드에 텍스트를 입력합니다.
3.  **Assert (단언)**: 실행의 결과로 화면에 나타난 변화를 확인합니다. 특정 텍스트가 보이는지, 특정 요소가 활성화되었는지 등을 `expect`를 사용하여 검증합니다.

### 예시: `Button` 컴포넌트 테스트

```tsx
// src/shared/ui/Button.test.tsx

import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { Button } from './Button';
import { vi } from 'vitest';

describe('Button', () => {
  it('should render with the correct text', () => {
    // Arrange
    render(<Button>Click Me</Button>);

    // Act (생략)

    // Assert
    // 'button' 역할을 가지며 'Click Me'라는 이름을 가진 요소를 찾습니다.
    const buttonElement = screen.getByRole('button', { name: /click me/i });
    expect(buttonElement).toBeInTheDocument();
  });

  it('should call the onClick handler when clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    const handleClick = vi.fn(); // 모의 함수 생성
    render(<Button onClick={handleClick}>Click Me</Button>);
    const buttonElement = screen.getByRole('button', { name: /click me/i });

    // Act
    await user.click(buttonElement); // 사용자가 버튼을 클릭하는 것을 시뮬레이션

    // Assert
    expect(handleClick).toHaveBeenCalledTimes(1); // 모의 함수가 1번 호출되었는지 확인
  });

  it('should be disabled when the disabled prop is true', () => {
    // Arrange
    render(<Button disabled>Click Me</Button>);
    const buttonElement = screen.getByRole('button', { name: /click me/i });

    // Assert
    expect(buttonElement).toBeDisabled();
  });
});
```

## 사용자 상호작용: `user-event`

`fireEvent`보다 `user-event` 라이브러리 사용을 권장합니다. `user-event`는 실제 사용자의 브라우저 상호작용을 더 정확하게 시뮬레이션합니다. 예를 들어, `user.click(button)`은 단순히 `click` 이벤트를 발생시키는 것을 넘어, 해당 요소에 포커스를 주고, 마우스를 올리는 등의 연관 이벤트를 함께 발생시킵니다.

## 비동기 작업 테스트

API 요청과 같이 비동기적으로 발생하는 UI 변경을 테스트할 때는 `findBy*` 쿼리나 `waitFor` 유틸리티를 사용합니다.

### 예시: 데이터 로딩 테스트

```tsx
// src/features/some-feature/components/DataDisplay.test.tsx

it('should display data after fetching', async () => {
  // Arrange: API 모킹
  vi.spyOn(api, 'fetchData').mockResolvedValue({ message: 'Hello World' });
  render(<DataDisplay />);

  // 로딩 상태 확인
  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  // Act & Assert
  // 'Hello World' 텍스트가 나타날 때까지 기다립니다. (기본 타임아웃: 1000ms)
  const dataElement = await screen.findByText(/hello world/i);
  expect(dataElement).toBeInTheDocument();

  // 로딩 상태가 사라졌는지 확인
  expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
});
```
- `findBy*`: Promise를 반환하며, 요소가 나타날 때까지 기다립니다.
- `queryBy*`: 요소를 찾지 못하면 `null`을 반환합니다. 요소가 화면에 없는지를 검증할 때 유용합니다.
- `waitFor`: 특정 단언이 통과될 때까지 일정 시간 동안 재시도합니다. 여러 개의 단언을 한 번에 기다려야 할 때 유용합니다.
