import { createContext, createElement, useState, useEffect, useCallback, useContext } from 'react';
import type { ReactNode } from 'react';
import { ThemeDefinition, ThemeName } from '../types/theme';

// Theme imports
import amberMinimal from '../../themes/amber-minimal.json';
import amethystHaze from '../../themes/amethyst-haze.json';
import bubblegum from '../../themes/bubblegun.json';
import claymorphism from '../../themes/claymorphism.json';

const themes: Record<ThemeName, ThemeDefinition> = {
  'amber-minimal': amberMinimal as ThemeDefinition,
  'amethyst-haze': amethystHaze as ThemeDefinition,
  'bubblegum': bubblegum as ThemeDefinition,
  'claymorphism': claymorphism as ThemeDefinition,
};

const THEME_STORAGE_KEY = 'selected-theme';
const DARK_MODE_STORAGE_KEY = 'dark-mode';

export interface ThemeContextValue {
  currentTheme: ThemeName;
  isDarkMode: boolean;
  changeTheme: (themeName: ThemeName) => void;
  toggleDarkMode: () => void;
  getAvailableThemes: () => Array<{ id: ThemeName; name: string; displayName: string }>;
  getCurrentThemeDefinition: () => ThemeDefinition;
  themes: Record<ThemeName, ThemeDefinition>;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

/**
 * 실제 테마 상태/부수효과 로직 — ThemeProvider 안에서 한 번만 호출되는, 진짜
 * 전역 상태의 유일한 소스다 (P2-31).
 *
 * 예전에는 이 로직 전체가 `useTheme`이라는 이름의 훅이었고, App.tsx/
 * Header.tsx/ThemeSelector.tsx가 각자 호출해 서로 다른 useState 인스턴스
 * 3벌을 만들었다. DOM class·CSS 변수·localStorage 같은 부수효과로만
 * "동기화된 것처럼" 보였을 뿐이라, 렌더 구조가 바뀌면(ThemeSelector를 상시
 * 렌더링하거나 showDarkModeToggle을 여러 곳에서 켜면) desync가 났다.
 */
const useThemeState = (): ThemeContextValue => {
  const [currentTheme, setCurrentTheme] = useState<ThemeName>(() => {
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY) as ThemeName;
    return (storedTheme && themes[storedTheme]) ? storedTheme : 'claymorphism';
  });
  
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    const storedDarkMode = localStorage.getItem(DARK_MODE_STORAGE_KEY);
    if (storedDarkMode !== null) {
      return storedDarkMode === 'true';
    }
    // Check system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Apply theme variables to CSS
  const applyTheme = useCallback((themeName: ThemeName, darkMode: boolean) => {
    const theme = themes[themeName];
    if (!theme) return;

    const root = document.documentElement;
    const colorMode = darkMode ? 'dark' : 'light';
    const colors = theme.cssVars[colorMode];
    const themeVars = theme.cssVars.theme;

    // Apply dark mode class first
    if (darkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Apply theme variables (fonts, radius, etc.)
    Object.entries(themeVars).forEach(([key, value]) => {
      root.style.setProperty(`--${key}`, value);
    });

    // Apply color variables - these override the CSS defaults
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--${key}`, value);
    });

    // Store preferences
    localStorage.setItem(THEME_STORAGE_KEY, themeName);
    localStorage.setItem(DARK_MODE_STORAGE_KEY, darkMode.toString());
  }, []);

  // Apply theme when current theme or dark mode changes
  useEffect(() => {
    applyTheme(currentTheme, isDarkMode);
  }, [currentTheme, isDarkMode, applyTheme]);

  const changeTheme = useCallback((themeName: ThemeName) => {
    setCurrentTheme(themeName);
  }, []);

  const toggleDarkMode = useCallback(() => {
    setIsDarkMode(prev => !prev);
  }, []);

  const getAvailableThemes = useCallback(() => {
    return Object.entries(themes).map(([key, theme]) => ({
      id: key as ThemeName,
      name: theme.name,
      displayName: theme.name.split('-').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }));
  }, []);

  const getCurrentThemeDefinition = useCallback(() => {
    return themes[currentTheme];
  }, [currentTheme]);

  return {
    currentTheme,
    isDarkMode,
    changeTheme,
    toggleDarkMode,
    getAvailableThemes,
    getCurrentThemeDefinition,
    themes,
  };
};

/**
 * 앱 루트(App.tsx)에서 한 번만 렌더링해야 하는 테마 상태의 유일한 소스.
 * 이 안에서 렌더링되는 모든 컴포넌트는 useTheme()으로 같은 상태를 구독한다.
 *
 * createElement를 쓰는 이유: 이 파일은 `.ts`라 JSX 구문을 쓸 수 없다(파일
 * 확장자를 바꾸지 않기 위함 — 다른 파일들이 `@/shared/hooks/useTheme`
 * 경로로 그대로 import한다).
 */
export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const value = useThemeState();
  return createElement(ThemeContext.Provider, { value }, children);
};

/**
 * ThemeProvider가 제공하는 테마 상태를 구독한다. App.tsx가 트리 최상단을
 * ThemeProvider로 감싸므로, 실제 사용처(Header, ThemeSelector)는 항상 그
 * 안에서 렌더링된다 — Provider 밖에서 호출되면 설정 실수를 조용히 넘어가지
 * 않고 바로 에러를 던진다.
 */
export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};