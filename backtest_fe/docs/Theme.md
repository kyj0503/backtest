# 테마 시스템

## 구조

```
src/
├── shared/
│   └── hooks/
│       └── useTheme.ts
├── shared/
│   └── types/theme.ts
└── themes/
    ├── amber-minimal.json
    ├── amethyst-haze.json
    ├── bubblegun.json
    └── claymorphism.json
```

- JSON 파일은 라이트/다크 팔레트와 폰트, 곡률 등 CSS 변수를 제공한다.
- `useTheme` 훅이 JSON을 로드해 `document.documentElement`에 CSS 변수를 주입한다.

## 타입 정의

```ts
export interface ThemeDefinition {
  cssVars: {
    theme: { 'font-sans': string; radius: string; [key: string]: string }
    light: ThemeColors
    dark: ThemeColors
  }
}

export type ThemeName = 'amber-minimal' | 'amethyst-haze' | 'bubblegum' | 'claymorphism'
```

`ThemeColors`는 버튼, 카드, 차트, 사이드바 색상을 포함하며 필요한 키를 확장할 수 있다.

## useTheme 사용법

```ts
import { useTheme } from '@/shared/hooks/useTheme'

const ThemeSelector = () => {
  const { currentTheme, changeTheme, isDarkMode, toggleDarkMode, getAvailableThemes } = useTheme()
  // ...
}
```

- `changeTheme(themeName)`는 선택한 테마를 적용하고 로컬 스토리지에 저장한다.
- `toggleDarkMode()`는 다크 모드 CSS 클래스와 저장 값을 동기화한다.
- `getAvailableThemes()`는 테마 리스트와 표시명을 반환한다.

## 새 테마 추가

1. `themes` 디렉터리에 JSON 파일을 추가한다.
2. `useTheme.ts`에서 해당 JSON을 import하고 `themes` 맵에 등록한다.
3. 필요하면 `ThemeName` 유니언 타입을 업데이트한다.

## CSS 적용 방식

`useTheme` 훅은 아래 순서로 스타일을 적용한다.

1. 다크 모드 여부에 따라 `html` 요소에 `dark` 클래스를 추가 또는 제거한다.
2. 테마 메타 변수(`font-sans`, `radius` 등)를 `--font-sans` 형태로 등록한다.
3. 현재 모드(light/dark)에 맞는 색상을 CSS 변수(`--background`, `--primary` 등)로 주입한다.

이 구조로 Tailwind CSS가 `var(--background)` 등의 토큰을 활용해 UI 색상을 제어한다.
