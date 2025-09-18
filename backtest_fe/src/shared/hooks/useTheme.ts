import { useState, useEffect, useCallback } from 'react';
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

export const useTheme = () => {
  const [currentTheme, setCurrentTheme] = useState<ThemeName>('claymorphism');
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);

  // Initialize theme from localStorage
  useEffect(() => {
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY) as ThemeName;
    const storedDarkMode = localStorage.getItem(DARK_MODE_STORAGE_KEY);
    
    if (storedTheme && themes[storedTheme]) {
      setCurrentTheme(storedTheme);
    }
    
    if (storedDarkMode !== null) {
      setIsDarkMode(storedDarkMode === 'true');
    } else {
      // Check system preference
      setIsDarkMode(window.matchMedia('(prefers-color-scheme: dark)').matches);
    }
  }, []);

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