# 코드베이스 구조

## 개요

본 프론트엔드 아키텍처는 **Feature-Sliced Design (FSD)** 방법론의 원칙을 기반으로 설계되었습니다. 이를 통해 코드의 응집도를 높이고 모듈 간의 결합도를 낮추어, 유지보수성과 확장성이 뛰어난 구조를 지향합니다.

## 디렉토리 구조

```
src/
├── App.tsx             # 애플리케이션 진입점, 라우팅 및 전역 레이아웃
├── main.tsx            # React DOM 렌더링 시작점
├── pages/              # 라우팅 단위의 페이지 컴포넌트
├── features/           # 애플리케이션의 주요 기능 모듈
└── shared/             # 여러 기능에서 공유되는 재사용 가능한 코드
```

### 1. `pages`

-   **역할**: 사용자가 특정 URL로 접근했을 때 보이는 전체 페이지를 구성합니다.
-   **규칙**: 페이지는 주로 여러 `features`와 `shared` 모듈을 조합하여 UI를 구성하며, 자체적으로 복잡한 비즈니스 로직을 포함하지 않습니다.
-   **예시**: `HomePage.tsx`, `PortfolioPage.tsx`

### 2. `features`

-   **역할**: 애플리케이션의 핵심 기능 덩어리입니다. 각 기능은 독립적으로 존재하며, 관련된 모든 코드(API, UI, 상태, 훅 등)를 포함합니다.
-   **구조**: `features/backtest` 디렉토리가 대표적인 예시입니다.
    ```
    features/backtest/
    ├── api/              # 백테스트 관련 API 호출 함수
    ├── components/       # 이 기능에서만 사용하는 UI 컴포넌트
    ├── hooks/            # 이 기능의 비즈니스 로직을 담은 커스텀 훅
    ├── model/            # 상태 관리(Zustand, Reducer), 타입, 상수
    └── services/         # API 응답을 가공하는 등의 서비스 로직
    ```
-   **장점**:
    -   **높은 응집도**: 백테스트와 관련된 모든 코드가 한곳에 모여 있어 파악이 쉽습니다.
    -   **낮은 결합도**: `backtest` 기능을 다른 프로젝트에 이식하거나 제거하기 용이합니다.

### 3. `shared`

-   **역할**: 특정 기능에 종속되지 않고, 여러 기능에서 공통으로 사용되는 코드를 모아놓은 곳입니다.
-   **규칙**: `shared` 모듈은 다른 `shared` 모듈에만 의존할 수 있으며, `features`나 `pages`에 의존해서는 안 됩니다.
-   **구조**:
    ```
    shared/
    ├── api/              # 공통 API 클라이언트 설정 (axios 인스턴스 등)
    ├── components/       # 여러 곳에서 재사용되는 범용 컴포넌트 (버튼, 폼, 레이아웃 등)
    ├── hooks/            # 범용 커스텀 훅 (useTheme, useLocalStorage 등)
    ├── lib/              # 외부 라이브러리 래퍼 또는 핵심 유틸리티 (shadcn의 cn 함수 등)
    ├── ui/               # shadcn/ui로 자동 생성된 원자적 UI 컴포넌트
    └── utils/            # 순수 함수 유틸리티 (날짜 포맷팅, 숫자 계산 등)
    ```

## 설계 원칙

### 1. 단방향 의존성

코드는 항상 **상위 레이어에서 하위 레이어로만** 의존해야 합니다.

`pages` → `features` → `shared`

-   `shared`는 그 어떤 것에도 의존하지 않습니다.
-   `features`는 `shared`에만 의존할 수 있습니다.
-   `pages`는 `features`와 `shared`에 의존할 수 있습니다.

이 규칙은 코드의 예측 가능성을 높이고 순환 의존성을 방지합니다.

### 2. 컴포넌트 분리 원칙

-   **`shared/ui`**: 가장 원자적인 단위의 UI 컴포넌트 (예: `<Button>`, `<Input>`). 스타일만 가집니다.
-   **`shared/components`**: `shared/ui` 컴포넌트를 조합하여 만든, 여러 곳에서 재사용 가능한 컴포넌트 (예: `PageHeader`, `FormField`). 약간의 로직을 포함할 수 있습니다.
-   **`features/*/components`**: 특정 기능을 위해 만들어진 컴포넌트. 해당 기능의 비즈니스 로직과 강하게 결합되어 있습니다. (예: `BacktestResultChart`)

## 주요 라이브러리 및 역할

-   **Vite**: 프론트엔드 빌드 도구 및 개발 서버
-   **React**: UI 라이브러리
-   **TypeScript**: 정적 타입 시스템
-   **React Router**: 클라이언트 사이드 라우팅
-   **Zustand**: 전역 상태 관리
-   **shadcn/ui & Tailwind CSS**: UI 컴포넌트 및 스타일링
-   **Recharts**: 데이터 시각화 및 차트 라이브러리
-   **Vitest & React Testing Library**: 단위 및 컴포넌트 테스트
