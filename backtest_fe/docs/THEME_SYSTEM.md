# 03. 테마 시스템 — 구조와 사용법

프론트엔드는 JSON 기반 테마를 사용합니다. 테마 파일은 `src/themes/`에 있으며, `useTheme` 훅이 테마 적용과 다크 모드 전환, 로컬 저장을 담당합니다.

## 구성 파일
- 타입: `src/shared/types/theme.ts`
- 훅: `src/shared/hooks/useTheme.ts`
- 테마 JSON: `src/themes/*.json` (예: `amber-minimal.json`, `amethyst-haze.json`, `bubblegun.json`, `claymorphism.json`)

## 사용 가능한 테마 키
훅 내부 등록명(`ThemeName`):
- `amber-minimal`
- `amethyst-haze`
- `bubblegum`
- `claymorphism`

주의: 실제 파일명은 `bubblegun.json`이며 등록명은 `bubblegum`입니다. 훅에서 이미 매핑되어 있으므로 등록명을 기준으로 사용합니다.

## 런타임 동작
- 로컬 저장 키: `selected-theme`, `dark-mode`
- 다크 모드 적용 시 `document.documentElement.classList`에 `dark` 클래스를 토글합니다.
- CSS 변수는 `theme.cssVars.theme`와 `theme.cssVars.[light|dark]`를 루트에 바인딩합니다.

## 테마 변경/조회 API (`useTheme` 반환값)
- `currentTheme: ThemeName`
- `isDarkMode: boolean`
- `changeTheme(themeName: ThemeName)`
- `toggleDarkMode()`
- `getAvailableThemes()`
- `getCurrentThemeDefinition()`

## 새 테마 추가 절차
1) `src/themes/`에 JSON 파일 추가
2) `src/shared/hooks/useTheme.ts`에 import 및 `themes` 레코드 등록
3) 필요 시 `ThemeName` 타입(`src/shared/types/theme.ts`)에 이름 추가
4) UI에서 `getAvailableThemes()`를 사용해 선택지를 노출

## 예시 코드
```tsx
import { useTheme } from '@/shared/hooks/useTheme'

export function ThemeSelectorInline() {
  const { currentTheme, changeTheme, isDarkMode, toggleDarkMode, getAvailableThemes } = useTheme()
  const options = getAvailableThemes()

  return (
    <div className="flex items-center gap-2">
      <select value={currentTheme} onChange={(e) => changeTheme(e.target.value as any)}>
        {options.map(o => <option key={o.id} value={o.id}>{o.displayName}</option>)}
      </select>
      <button onClick={toggleDarkMode}>{isDarkMode ? '라이트' : '다크'}</button>
    </div>
  )
}
```
