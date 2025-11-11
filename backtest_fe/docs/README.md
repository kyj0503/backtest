# 프론트엔드 기술 문서

이 디렉토리에는 프론트엔드 시스템의 아키텍처, 상태 관리, 성능 최적화 전략에 대한 기술 문서가 포함되어 있습니다.

## 아키텍처

-   [**코드베이스 구조**](./architecture/codebase_structure.md)
    -   프로젝트의 디렉토리 구조와 각 모듈의 역할을 설명합니다.
    -   `Feature-Sliced Design`에 기반한 설계 원칙을 기술합니다.

-   [**상태 관리**](./architecture/state_management.md)
    -   `Zustand`를 이용한 전역 상태 관리와 `useReducer`를 활용한 복잡한 로컬 상태 관리 패턴을 설명합니다.

## 성능 최적화

-   [**차트 렌더링 최적화**](./optimization/chart_performance.md)
    -   `Recharts` 라이브러리 사용 시 발생하는 불필요한 리렌더링 문제와 해결 방법을 설명합니다.
    -   `memo`, `useMemo`, `useCallback`을 활용한 최적화 전략을 기술합니다.

-   [**데이터 샘플링 전략**](./optimization/data_sampling.md)
    -   장기 백테스트 데이터 시각화 시, 성능과 품질의 균형을 맞추기 위한 스마트 샘플링 전략을 설명합니다.
    -   일간, 주간, 월간 데이터 집계 방식을 기술합니다.

## 테스트

-   [**테스트 (`testing/`)**](./testing/README.md): Vitest와 React Testing Library를 사용한 테스트 전략 및 방법에 대해 설명합니다.
