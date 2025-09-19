# 03. 테마 시스템 — 프론트엔드

구성 요소
- 타입: `src/shared/types/theme.ts`
- 훅: `src/shared/hooks/useTheme.ts`
- 테마 파일: `src/themes/*.json`

사용법
```tsx
import { useTheme } from '@/shared/hooks/useTheme'

const { currentTheme, changeTheme, isDarkMode, toggleDarkMode } = useTheme()
```

테마 추가 요약
1. `src/themes/`에 JSON 파일 추가
2. `useTheme.ts`에 import/등록
3. `ThemeName` 타입에 필요시 추가
