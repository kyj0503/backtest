# 테마 시스템

## 구조

```
src/themes/              # 테마 JSON 파일
src/shared/hooks/useTheme.ts  # 테마 관리 훅
src/shared/types/theme.ts     # 테마 타입 정의
```

## 테마 JSON 형식

```json
{
  "cssVars": {
    "theme": {
      "font-sans": "sans-serif",
      "radius": "0.5rem"
    },
    "light": {
      "background": "0 0% 100%",
      "foreground": "222.2 84% 4.9%",
      "primary": "221.2 83.2% 53.3%"
    },
    "dark": {
      "background": "222.2 84% 4.9%",
      "foreground": "210 40% 98%",
      "primary": "217.2 91.2% 59.8%"
    }
  }
}
```

## 테마 사용

```typescript
const { currentTheme, changeTheme, isDarkMode, toggleDarkMode } = useTheme()

// 테마 변경
changeTheme('amber-minimal')

// 다크 모드 토글
toggleDarkMode()
```

## 테마 추가

1. `src/themes/`에 JSON 파일 추가
2. `src/shared/hooks/useTheme.ts`에 import 및 등록
3. `src/shared/types/theme.ts`의 `ThemeName` 타입 업데이트
