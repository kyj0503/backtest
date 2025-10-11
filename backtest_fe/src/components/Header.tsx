import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { TrendingUp, Moon, Sun, Palette } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { useTheme } from '@/shared/hooks/useTheme';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/shared/ui/dialog';
import ThemeSelector from './ThemeSelector';

const navigationItems = [
  { href: '/', label: '홈' },
  { href: '/backtest', label: '백테스트' },
];

const Header: React.FC = () => {
  const location = useLocation();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [themeDialogOpen, setThemeDialogOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/40">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-colors">
            <TrendingUp className="h-4 w-4 text-primary" />
          </div>
          <span className="text-lg font-bold bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
            라고할때살걸
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          {navigationItems.map((item) => (
            <Button
              key={item.href}
              asChild
              variant="ghost"
              className={`rounded-full px-4 ${location.pathname === item.href ? 'bg-accent' : ''}`}
            >
              <Link to={item.href} className="text-sm font-medium">
                {item.label}
              </Link>
            </Button>
          ))}
        </nav>

        <div className="flex items-center gap-1">
          <Dialog open={themeDialogOpen} onOpenChange={setThemeDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full" aria-label="테마 설정 열기">
                <Palette className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>테마 설정</DialogTitle>
                <DialogDescription>
                  원하는 디자인 테마와 다크 모드를 선택하세요
                </DialogDescription>
              </DialogHeader>
              <ThemeSelector />
            </DialogContent>
          </Dialog>

          <Button
            variant="ghost"
            size="icon"
            className="rounded-full"
            onClick={toggleDarkMode}
            aria-label={isDarkMode ? "라이트 모드로 전환" : "다크 모드로 전환"}
          >
            {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;
