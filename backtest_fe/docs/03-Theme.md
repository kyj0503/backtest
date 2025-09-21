# 테마 시스템

## 🎨 개요

백테스트 플랫폼은 사용자 경험을 향상시키기 위해 다크/라이트 모드를 지원하는 테마 시스템을 제공합니다. Tailwind CSS와 CSS 변수를 활용하여 동적 테마 전환을 구현합니다.

## 🏗️ 아키텍처

### 핵심 구성 요소

```
src/
├── shared/
│   ├── types/theme.ts      # 테마 관련 타입 정의
│   └── hooks/useTheme.ts   # 테마 관리 훅
├── themes/                 # 테마 정의 파일
│   ├── default.json        # 기본 라이트 테마
│   └── dark.json          # 다크 테마  
└── index.css              # CSS 변수 정의
```

### 타입 정의

```typescript
// src/shared/types/theme.ts
export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeColors {
  background: string;
  foreground: string;
  primary: string;
  'primary-foreground': string;
  secondary: string;
  'secondary-foreground': string;
  accent: string;
  'accent-foreground': string;
  destructive: string;
  'destructive-foreground': string;
  muted: string;
  'muted-foreground': string;
  card: string;
  'card-foreground': string;
  border: string;
  input: string;
  ring: string;
}

export interface Theme {
  name: string;
  colors: ThemeColors;
}
```

## 🎯 사용 방법

### 기본 사용법

```tsx
import { useTheme } from '@/shared/hooks/useTheme';

const Header = () => {
  const { theme, setTheme, isDarkMode, toggleTheme } = useTheme();

  return (
    <header className="bg-background border-b">
      <div className="flex items-center justify-between p-4">
        <h1 className="text-foreground font-bold">Backtest Platform</h1>
        
        {/* 테마 토글 버튼 */}
        <Button 
          variant="ghost" 
          size="sm"
          onClick={toggleTheme}
        >
          {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
};
```

### 테마 선택기 컴포넌트

```tsx
import { useTheme } from '@/shared/hooks/useTheme';

const ThemeSelector = () => {
  const { theme, setTheme } = useTheme();

  return (
    <Select value={theme} onValueChange={setTheme}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="테마 선택" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="light">라이트 모드</SelectItem>
        <SelectItem value="dark">다크 모드</SelectItem>
        <SelectItem value="system">시스템 설정</SelectItem>
      </SelectContent>
    </Select>
  );
};
```

## 🛠️ 테마 커스터마이제이션

### 새 테마 추가

1. **테마 파일 생성**

```json
// src/themes/blue.json
{
  "name": "blue",
  "colors": {
    "background": "hsl(210, 100%, 98%)",
    "foreground": "hsl(210, 40%, 8%)",
    "primary": "hsl(210, 100%, 50%)",
    "primary-foreground": "hsl(0, 0%, 98%)",
    "secondary": "hsl(210, 40%, 96%)",
    "secondary-foreground": "hsl(210, 40%, 11%)",
    "accent": "hsl(210, 40%, 94%)",
    "accent-foreground": "hsl(210, 40%, 11%)",
    "destructive": "hsl(0, 84%, 60%)",
    "destructive-foreground": "hsl(0, 0%, 98%)",
    "muted": "hsl(210, 40%, 96%)",
    "muted-foreground": "hsl(210, 40%, 45%)",
    "card": "hsl(0, 0%, 100%)",
    "card-foreground": "hsl(210, 40%, 8%)",
    "border": "hsl(210, 40%, 90%)",
    "input": "hsl(210, 40%, 90%)",
    "ring": "hsl(210, 100%, 50%)"
  }
}
```

2. **훅에 테마 등록**

```typescript
// src/shared/hooks/useTheme.ts
import blueTheme from '@/themes/blue.json';

const themes = {
  light: defaultTheme,
  dark: darkTheme,
  blue: blueTheme  // 새 테마 추가
} as const;

export type ThemeMode = keyof typeof themes;
```

### 동적 색상 변경

```typescript
const CustomColorPicker = () => {
  const { updateThemeColor } = useTheme();

  const handleColorChange = (colorKey: keyof ThemeColors, newColor: string) => {
    updateThemeColor(colorKey, newColor);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <label>Primary Color:</label>
        <input
          type="color"
          onChange={(e) => handleColorChange('primary', e.target.value)}
        />
      </div>
      {/* 다른 색상들... */}
    </div>
  );
};
```

## 🎨 CSS 변수 시스템

### 기본 설정

```css
/* src/index.css */
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 240 5.9% 10%;
  --primary-foreground: 0 0% 98%;
  /* ... 기타 변수들 */
}

.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  --primary: 0 0% 98%;
  --primary-foreground: 240 5.9% 10%;
  /* ... 기타 변수들 */
}
```

### Tailwind CSS 설정

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        // ... 기타 색상들
      },
    },
  },
};
```

## 🔧 고급 기능

### 시스템 테마 감지

```typescript
// src/shared/hooks/useTheme.ts
const useSystemTheme = () => {
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };

    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return systemTheme;
};
```

### 테마 전환 애니메이션

```css
/* 부드러운 테마 전환 효과 */
* {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}

/* 특정 요소는 애니메이션 제외 */
.no-theme-transition {
  transition: none !important;
}
```

### 테마별 이미지 처리

```tsx
const ThemedImage = ({ lightSrc, darkSrc, alt, ...props }) => {
  const { isDarkMode } = useTheme();
  
  return (
    <img 
      src={isDarkMode ? darkSrc : lightSrc}
      alt={alt}
      {...props}
    />
  );
};

// 사용 예시
<ThemedImage
  lightSrc="/logo-light.png"
  darkSrc="/logo-dark.png"
  alt="Logo"
  className="h-8 w-auto"
/>
```

## 🧪 테스트

### 테마 관련 테스트

```typescript
// __tests__/useTheme.test.ts
describe('useTheme', () => {
  it('should toggle between light and dark themes', () => {
    const { result } = renderHook(() => useTheme());
    
    expect(result.current.theme).toBe('light');
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('dark');
  });

  it('should persist theme preference', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('dark');
    });
    
    expect(localStorage.getItem('theme')).toBe('dark');
  });
});
```

## 📱 접근성 고려사항

### 고대비 모드 지원

```css
@media (prefers-contrast: high) {
  :root {
    --background: 0 0% 100%;
    --foreground: 0 0% 0%;
    --primary: 240 100% 50%;
    --border: 0 0% 50%;
  }
  
  .dark {
    --background: 0 0% 0%;
    --foreground: 0 0% 100%;
  }
}
```

### 모션 감소 지원

```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
    animation: none !important;
  }
}
```

## 🎯 베스트 프랙티스

1. **색상 일관성**: semantic 색상 이름 사용 (primary, secondary 등)
2. **접근성**: 충분한 색상 대비 확보 (WCAG 2.1 AA 기준)
3. **성능**: CSS 변수 사용으로 런타임 계산 최소화
4. **사용자 경험**: 부드러운 전환 애니메이션
5. **상태 관리**: localStorage를 통한 테마 기본 설정 유지

이 테마 시스템을 통해 사용자 친화적이고 접근성이 높은 인터페이스를 제공할 수 있습니다.