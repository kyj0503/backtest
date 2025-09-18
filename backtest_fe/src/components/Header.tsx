import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, Github, Menu, MoonStar, Palette, SunMedium } from 'lucide-react';
import { useTheme } from '@/shared/hooks/useTheme';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/shared/ui/sheet';
// ... dropdown menu and avatar UI removed since auth is disabled
import { Separator } from '@/shared/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog';
import ThemeSelector from './ThemeSelector';
import { cn } from '@/shared/lib/core/utils';

const navigationItems = [
  { href: '/', label: '홈', description: '메인 대시보드로 이동' },
  { href: '/backtest', label: '백테스트', description: '투자 전략 백테스트 실행' },
];

const Header: React.FC = () => {
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [themeDialogOpen, setThemeDialogOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();


  const isActivePath = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const handleNavigate = () => {
    setMobileMenuOpen(false);
  };

  const ThemeControls = ({ compact = false }: { compact?: boolean }) => (
    <div className={cn('flex items-center', compact ? 'gap-1.5' : 'gap-2')}>
      <Button
        onClick={toggleDarkMode}
        variant="ghost"
        size="icon"
        className="rounded-full border border-transparent bg-transparent text-muted-foreground transition-transform hover:-translate-y-0.5 hover:border-border hover:bg-accent hover:text-foreground"
        aria-label={isDarkMode ? '라이트 모드로 변경' : '다크 모드로 변경'}
      >
        {isDarkMode ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      </Button>
      <Button
        onClick={() => setThemeDialogOpen(true)}
        variant="ghost"
        size="icon"
        className="rounded-full border border-transparent bg-transparent text-muted-foreground transition-transform hover:-translate-y-0.5 hover:border-border hover:bg-accent hover:text-foreground"
        aria-label="테마 선택"
      >
        <Palette className="h-4 w-4" />
      </Button>
    </div>
  );

  const DesktopNavigation = () => (
    <div className="hidden md:flex items-center gap-1">
      {navigationItems.map((item) => {
        const active = isActivePath(item.href);
        return (
          <Button
            key={item.href}
            asChild
            variant="ghost"
            size="sm"
            className={cn(
              'rounded-full px-4 py-2 text-left font-medium transition-all',
              'border border-transparent hover:border-border/60 hover:bg-accent/60 hover:text-foreground',
              active ? 'border-border/70 bg-accent/80 text-foreground shadow-sm' : 'text-muted-foreground'
            )}
          >
            <Link to={item.href} className="flex flex-col leading-tight">
              <span>{item.label}</span>
              <span className="text-xs font-normal text-muted-foreground/80">{item.description}</span>
            </Link>
          </Button>
        );
      })}
    </div>
  );

  const AuthControls = () => (
    <div className="hidden md:flex items-center gap-2">
      <ThemeControls />
      <div className="text-sm text-muted-foreground">계정 기능(로그인/회원가입)은 비활성화되어 있습니다.</div>
    </div>
  );

  return (
    <Dialog open={themeDialogOpen} onOpenChange={setThemeDialogOpen}>
      <nav className="sticky top-0 z-50 border-b border-border/80 bg-background/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link to="/" className="group flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl border border-border/60 bg-primary/10 shadow-sm transition-transform group-hover:-translate-y-0.5">
              <BarChart3 className="h-5 w-5 text-primary" />
            </span>
            <div className="flex flex-col">
              <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Backtesting Studio</span>
              <span className="text-base font-semibold text-foreground transition group-hover:text-primary">라고할때살걸</span>
            </div>
            <Badge variant="outline" className="ml-1 hidden sm:inline-flex rounded-full border-dashed border-primary/40 text-[10px] uppercase tracking-wide text-primary">
              Alpha
            </Badge>
          </Link>

          <DesktopNavigation />

          <div className="flex items-center gap-2 md:hidden">
            <ThemeControls compact />
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="rounded-full border border-transparent hover:border-border/60 hover:bg-accent/70"
                  aria-label="모바일 메뉴 열기"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent className="w-full max-w-sm border-border/80 bg-background/95 backdrop-blur-xl">
                <SheetHeader className="text-left">
                  <SheetTitle className="flex items-center gap-2 text-lg font-semibold">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-border/60 bg-primary/10">
                      <BarChart3 className="h-4 w-4 text-primary" />
                    </span>
                    <span>라고할때살걸</span>
                  </SheetTitle>
                </SheetHeader>

                <div className="mt-6 space-y-6">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">탐색</p>
                    <div className="space-y-1">
                      {navigationItems.map((item) => {
                        const active = isActivePath(item.href);
                        return (
                          <Button
                            key={item.href}
                            asChild
                            variant={active ? 'secondary' : 'ghost'}
                            className="w-full justify-start rounded-2xl px-4 py-3 text-left"
                            onClick={handleNavigate}
                          >
                            <Link to={item.href} className="flex flex-col gap-0.5">
                              <span className="text-sm font-medium">{item.label}</span>
                              <span className="text-xs text-muted-foreground">{item.description}</span>
                            </Link>
                          </Button>
                        );
                      })}
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">테마</p>
                    <div className="flex items-center justify-between rounded-2xl border border-border/80 px-4 py-3">
                      <div className="text-sm font-medium text-muted-foreground">다크 모드</div>
                      <Button onClick={toggleDarkMode} variant="outline" size="sm" className="rounded-full">
                        {isDarkMode ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
                      </Button>
                    </div>
                    <Button
                      onClick={() => {
                        setThemeDialogOpen(true);
                        setMobileMenuOpen(false);
                      }}
                      variant="outline"
                      className="w-full rounded-2xl"
                    >
                      <Palette className="mr-2 h-4 w-4" />
                      테마 커스터마이징 열기
                    </Button>
                  </div>

                  <Separator />

                                  <div className="space-y-3">
                                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">계정</p>
                                    <div className="text-sm text-muted-foreground">계정 기능(로그인/회원가입)은 비활성화되어 있습니다.</div>
                                  </div>

                  <Separator />

                  <Button
                    asChild
                    variant="ghost"
                    className="w-full justify-center rounded-full border border-border/60 hover:bg-accent/70"
                  >
                    <a
                      href="https://github.com/capstone-backtest/backtest"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <div className="flex items-center justify-center gap-2 text-sm font-medium">
                        <Github className="h-4 w-4" />
                        GitHub에서 보기
                      </div>
                    </a>
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
          </div>

          <AuthControls />
        </div>
      </nav>

      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>테마 커스터마이징</DialogTitle>
          <DialogDescription>
            선호하는 테마와 다크 모드 조합을 선택해 백테스트 스튜디오를 나만의 분위기로 꾸며보세요.
          </DialogDescription>
        </DialogHeader>
        <ThemeSelector />
        <DialogFooter>
          <Button variant="outline" onClick={() => setThemeDialogOpen(false)} className="ml-auto">
            닫기
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default Header;
