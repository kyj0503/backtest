# 동적 테마 시스템 가이드

이 문서는 프론트엔드 테마 변경 기능의 구조를 현재 코드 기준으로 설명합니다. 모든 내용은 `frontend/src` 디렉터리와 동기화되어 있습니다.

## 구성 요소 개요

- **테마 정의 파일**: `frontend/src/themes/*.json`
- **타입 정의**: `frontend/src/types/theme.ts`
- **상태 훅**: `frontend/src/hooks/useTheme.ts`
- **선택 UI**: `frontend/src/components/ThemeSelector.tsx`
- **헤더 연동**: `frontend/src/components/Header.tsx`

## 테마 정의(JSON)

현재 저장소에는 다음 네 가지 테마가 포함되어 있습니다.

| 파일명 | 설명 |
| --- | --- |
| `amber-minimal.json` | 고채도 앰버 포커스 테마 |
| `amethyst-haze.json` | 저채도 보라 계열 테마 |
| `bubblegun.json` | 채도가 높은 활기 있는 테마 |
| `claymorphism.json` | 기본 테마, 부드러운 중간 톤 |

각 JSON은 shadcn/ui 스키마를 따르며 `cssVars.theme`(폰트, radius 등)와 `cssVars.light`/`cssVars.dark`(색상 팔레트)를 제공합니다. 값은 OKLCH 색상과 일반 CSS 변수를 혼합해 정의됩니다.

## 타입과 유틸리티

`frontend/src/types/theme.ts`에서 `ThemeDefinition`과 `ThemeName`을 정의합니다. `ThemeName`은 위 JSON 파일명을 기반으로 한 문자열 리터럴 유니언입니다. 새 테마를 추가할 때는 이 파일에 타입을 확장해야 합니다.

## `useTheme` 훅 동작

`frontend/src/hooks/useTheme.ts`는 테마 상태를 관리합니다.

- 초기 상태는 `currentTheme = 'claymorphism'`, `isDarkMode = false`.
- `themes` 객체에 각 JSON을 직접 import하여 매핑합니다.
- `selected-theme`, `dark-mode` 키로 localStorage에 상태를 저장합니다.
- `applyTheme` 함수가 CSS 변수와 `.dark` 클래스를 루트 요소에 적용합니다.
- `changeTheme`, `toggleDarkMode`, `getAvailableThemes`, `getCurrentThemeDefinition` 헬퍼를 제공합니다.

## UI 통합

- `ThemeSelector.tsx`는 모든 테마를 카드 형태로 보여주고 `useTheme` 훅을 사용해 변경합니다.
- `Header.tsx`는 팔레트 버튼으로 ThemeSelector를 토글하고, 해/달 아이콘으로 다크 모드를 전환합니다.
- 라우트 수준 외에도 카드/차트 등 공통 컴포넌트는 `var(--color-*)` 변수 값을 사용합니다.

## 새 테마 추가 절차

1. `frontend/src/themes/`에 JSON 파일을 추가합니다.
2. `frontend/src/types/theme.ts`의 `ThemeName` 유니언과 필요한 타입을 업데이트합니다.
3. `useTheme.ts`의 `themes` 객체에 새 JSON import와 매핑을 추가합니다.
4. 필요 시 `ThemeSelector` 카드 설명을 보강합니다.
5. `npm run lint`와 `npm run test`로 타입과 컴포넌트 테스트를 확인합니다.

## localStorage 키

- `selected-theme`: 현재 선택된 테마 (`ThemeName` 값)
- `dark-mode`: 문자열 `'true'` 또는 `'false'`

## CSS 변수와 Tailwind 연동

`frontend/src/index.css`는 shadcn/ui 테마 구조를 따르며 Tailwind와 함께 사용할 수 있도록 CSS 변수를 선언합니다. 테마 JSON의 `cssVars.theme`/`light`/`dark` 항목이 런타임에 루트 요소에 주입되고, Tailwind 프리셋은 해당 변수를 참조합니다.

## 문제 해결 체크

- 테마가 적용되지 않으면 개발자 도구에서 `document.documentElement`의 스타일과 `localStorage` 값을 확인합니다.
- 다크 모드가 토글되지 않으면 `.dark` 클래스가 루트에 추가되는지 확인합니다.
- 새 테마가 보이지 않으면 타입 정의와 `themes` 매핑이 최신인지 검토합니다.

문서 이력은 실제 구현 변경 시 함께 업데이트해야 합니다.
