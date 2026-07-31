import React from 'react';
import { useTheme } from '@/shared/hooks/useTheme';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';
import { ThemeName } from '@/shared/types/theme';

interface ThemePreviewProps {
  themeName: ThemeName;
  isActive: boolean;
  onClick: () => void;
  theme: any;
}

const ThemePreview: React.FC<ThemePreviewProps> = ({ isActive, onClick, theme }) => {
  if (!theme) return null;

  const lightColors = theme.cssVars.light;
  
  return (
    <Card 
      role="button"
      tabIndex={0}
      aria-pressed={isActive}
      className={`cursor-pointer transition-all duration-200 hover:scale-105 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-2 ${
        isActive ? 'ring-2 ring-primary shadow-lg' : 'hover:shadow-md'
      }`}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onClick()
        }
      }}
    >
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center justify-between">
          {theme.name.split('-').map((word: string) => 
            word.charAt(0).toUpperCase() + word.slice(1)
          ).join(' ')}
          {isActive && <Badge variant="default" className="ml-2">활성</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Color Preview */}
        <div className="grid grid-cols-6 gap-1 mb-3">
          <div 
            className="w-6 h-6 rounded-sm border"
            style={{ backgroundColor: lightColors.primary }}
            title="Primary"
          />
          <div 
            className="w-6 h-6 rounded-sm border"
            style={{ backgroundColor: lightColors.secondary }}
            title="Secondary"
          />
          <div 
            className="w-6 h-6 rounded-sm border"
            style={{ backgroundColor: lightColors.accent }}
            title="Accent"
          />
          <div 
            className="w-6 h-6 rounded-sm border"
            style={{ backgroundColor: lightColors.card }}
            title="Card"
          />
          <div 
            className="w-6 h-6 rounded-sm border"
            style={{ backgroundColor: lightColors.background }}
            title="Background"
          />
          <div 
            className="w-6 h-6 rounded-sm border"
            style={{ backgroundColor: lightColors.muted }}
            title="Muted"
          />
        </div>
        
        {/* Font Preview */}
        <div className="text-xs text-muted-foreground">
          <div>폰트: {theme.cssVars.theme['font-sans'].split(',')[0]}</div>
          <div>반지름: {theme.cssVars.theme.radius}</div>
        </div>
      </CardContent>
    </Card>
  );
};

interface ThemeSelectorProps {
  className?: string;
  showDarkModeToggle?: boolean;
}

const ThemeSelector: React.FC<ThemeSelectorProps> = ({ className = "", showDarkModeToggle = false }) => {
  const { 
    currentTheme, 
    isDarkMode, 
    changeTheme, 
    toggleDarkMode, 
    getAvailableThemes,
    themes
  } = useTheme();

  const availableThemes = getAvailableThemes();

  return (
    <div className={className}>
      <div className="mb-6 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          테마는 자동으로 저장됩니다
        </div>
        {showDarkModeToggle && (
          <Button
            variant={isDarkMode ? "default" : "outline"}
            size="sm"
            onClick={toggleDarkMode}
          >
            {isDarkMode ? '🌙 다크' : '☀️ 라이트'}
          </Button>
        )}
      </div>
      <div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {availableThemes.map((themeInfo) => (
            <ThemePreview
              key={themeInfo.id}
              themeName={themeInfo.id}
              isActive={currentTheme === themeInfo.id}
              onClick={() => changeTheme(themeInfo.id)}
              theme={themes[themeInfo.id]}
            />
          ))}
        </div>
        
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <div className="text-sm font-medium mb-2">현재 테마 정보</div>
          <div className="text-xs text-muted-foreground space-y-1">
            <div>선택된 테마: <span className="font-medium">{availableThemes.find(t => t.id === currentTheme)?.displayName}</span></div>
            <div>다크 모드: <span className="font-medium">{isDarkMode ? '활성' : '비활성'}</span></div>
            <div>저장 위치: 브라우저 로컬 스토리지</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeSelector;
