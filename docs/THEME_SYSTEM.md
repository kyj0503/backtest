# 동적 테마 시스템 가이드

## 개요

투자 백테스팅 시스템에 동적 테마 시스템이 구현되었습니다. 사용자가 웹페이지에서 실시간으로 디자인 테마를 변경할 수 있으며, 선택한 테마는 localStorage에 저장되어 다음 방문 시에도 유지됩니다.

## 구성 요소

### 1. 테마 파일들 (`frontend/src/themes/*.json`)

다음 테마들이 제공됩니다:
- `amber-minimal.json`: 앰버 색상의 미니멀 테마
- `amethyst-haze.json`: 자수정 색상의 몽환적인 테마 
- `bubblegun.json`: 생동감 있는 버블검 테마
- `claymorphism.json`: 클레이모피즘 스타일 테마

각 테마 파일은 다음 구조를 가집니다:

```json
{
  "name": "테마 이름",
  "description": "테마 설명",
  "colors": {
    "primary": "#색상코드",
    "secondary": "#색상코드",
    "accent": "#색상코드",
    // ... 기타 색상들
  }
}
```

### 2. TypeScript 타입 정의 (`frontend/src/types/theme.ts`)

테마 시스템의 타입 안전성을 보장합니다:

```typescript
interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  // ... 기타 색상 속성들
}

interface Theme {
  name: string;
  description: string;
  colors: ThemeColors;
}
```

### 3. 테마 훅 (`frontend/src/hooks/useTheme.ts`)

테마 관리의 핵심 로직을 담당합니다:

```typescript
const useTheme = () => {
  const [currentTheme, setCurrentTheme] = useState<string>('amber-minimal');
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);
  
  // 테마 변경, 다크모드 토글, CSS 변수 적용 등의 기능 제공
};
```

주요 기능:
- 테마 변경 (`changeTheme`)
- 다크모드 토글 (`toggleDarkMode`)
- 자동 CSS 변수 적용
- localStorage 연동

### 4. 테마 선택기 컴포넌트 (`frontend/src/components/ThemeSelector.tsx`)

사용자가 테마를 선택할 수 있는 UI를 제공합니다:

```tsx
const ThemeSelector = () => {
  // 모든 사용 가능한 테마를 카드 형태로 표시
  // 각 테마의 색상 팔레트 미리보기
  // 현재 선택된 테마 표시
};
```

### 5. 헤더 통합 (`frontend/src/components/Header.tsx`)

네비게이션 헤더에 테마 제어 기능이 통합되었습니다:
- 다크모드 토글 버튼 (달/해 아이콘)
- 테마 선택 버튼 (팔레트 아이콘)
- 모달 형태의 테마 선택기

## 사용 방법

### 개발자용

#### 새로운 테마 추가

1. `frontend/src/themes/` 폴더에 새 JSON 파일 생성
2. 테마 구조에 맞게 색상 정의
3. `useTheme.ts`의 `THEME_FILES` 배열에 파일명 추가

#### 테마 색상 사용

CSS에서 CSS 변수로 테마 색상을 사용할 수 있습니다:

```css
.my-component {
  background-color: var(--color-primary);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
```

#### 컴포넌트에서 테마 정보 접근

```tsx
import { useTheme } from '../hooks/useTheme';

const MyComponent = () => {
  const { currentTheme, isDarkMode, changeTheme, toggleDarkMode } = useTheme();
  
  // 테마 정보 활용
};
```

### 사용자용

1. **테마 변경**: 헤더의 팔레트 아이콘을 클릭하여 테마 선택기 열기
2. **다크모드**: 헤더의 달/해 아이콘을 클릭하여 다크모드 토글
3. **설정 유지**: 선택한 테마와 다크모드 설정은 자동으로 저장되어 다음 방문 시 유지됨

## 기술적 세부사항

### CSS 변수 시스템

테마 시스템은 CSS 커스텀 속성(변수)을 활용하여 동적으로 색상을 변경합니다:

```css
:root {
  --color-primary: #f59e0b; /* 기본값 */
  --color-secondary: #6b7280;
  /* ... */
}

/* 다크모드일 때 */
.dark {
  --color-background: #1f2937;
  --color-text: #f9fafb;
  /* ... */
}
```

### localStorage 저장

사용자 설정은 다음 키로 저장됩니다:
- `selectedTheme`: 선택된 테마 이름
- `isDarkMode`: 다크모드 활성화 여부

### Tailwind CSS 통합

`index.css`에서 Tailwind의 `@theme` 디렉티브를 사용하여 CSS 변수를 Tailwind 색상으로 통합:

```css
@theme {
  --color-primary: var(--color-primary);
  --color-secondary: var(--color-secondary);
  /* ... */
}
```

## 성능 고려사항

- 테마 파일들은 번들링 시점에 동적 import로 로드
- CSS 변수 변경은 리플로우를 최소화
- localStorage 접근은 debounce 처리로 최적화

## 호환성

- 모던 브라우저의 CSS 커스텀 속성 지원 필요
- localStorage 지원 브라우저 필요
- React 18+ 호환

## 문제 해결

### 테마가 적용되지 않을 때

1. 브라우저의 개발자 도구에서 CSS 변수가 올바르게 설정되었는지 확인
2. localStorage의 `selectedTheme` 값 확인
3. 콘솔 에러 메시지 확인

### 새 테마 추가가 인식되지 않을 때

1. JSON 파일 형식이 올바른지 확인
2. `THEME_FILES` 배열에 파일명이 포함되었는지 확인
3. 개발 서버 재시작

## 향후 개선사항

- [ ] 테마 미리보기 개선
- [ ] 커스텀 테마 생성 기능
- [ ] 시스템 다크모드 감지
- [ ] 애니메이션 효과 개선
- [ ] 접근성 향상 (고대비 모드 등)