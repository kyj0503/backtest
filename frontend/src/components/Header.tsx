import React, { useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  BarChart3,
  Github,
  LogOut,
  Menu,
  MoonStar,
  Palette,
  SunMedium,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Separator } from './ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import ThemeSelector from './ThemeSelector';
import { cn } from '../lib/utils';

const navigationItems = [
  { href: '/', label: '홈', description: '메인 대시보드로 이동' },
  { href: '/backtest', label: '백테스트', description: '투자 전략 백테스트 실행' },
  { href: '/community', label: '커뮤니티', description: '사용자 커뮤니티 및 토론' },
  { href: '/chat', label: '채팅', description: '실시간 채팅 및 질문' },
];

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [themeDialogOpen, setThemeDialogOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const initials = useMemo(() => user?.username?.charAt(0).toUpperCase() ?? 'U', [user?.username]);

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
      {user ? (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-full border border-border/50 bg-card/70 shadow-sm transition hover:-translate-y-0.5">
              <Avatar className="h-9 w-9 border border-border/40">
                <AvatarImage src={undefined} alt={user.username} />
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-60" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-semibold leading-tight">{user.username}</p>
                <p className="text-xs text-muted-foreground">{user.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="flex items-center gap-2">
              <LogOut className="h-4 w-4" />
              로그아웃
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ) : (
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm" className="rounded-full">
            <Link to="/login">로그인</Link>
          </Button>
          <Button asChild size="sm" className="rounded-full shadow-sm">
            <Link to="/signup">회원가입</Link>
          </Button>
        </div>
      )}
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
                    {user ? (
                      <div className="rounded-2xl border border-border/80 bg-card/60 p-4 shadow-sm">
                        <div className="flex items-center gap-3">
                          <Avatar className="h-10 w-10 border border-border/40">
                            <AvatarImage src={undefined} alt={user.username} />
                            <AvatarFallback>{initials}</AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-sm font-semibold">{user.username}</p>
                            <p className="text-xs text-muted-foreground">{user.email}</p>
                          </div>
                        </div>
                        <Button
                          onClick={() => {
                            logout();
                            setMobileMenuOpen(false);
                          }}
                          size="sm"
                          variant="outline"
                          className="mt-4 w-full rounded-full"
                        >
                          로그아웃
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Button asChild className="w-full rounded-full">
                          <Link to="/login" onClick={handleNavigate}>
                            로그인
                          </Link>
                        </Button>
                        <Button asChild variant="outline" className="w-full rounded-full">
                          <Link to="/signup" onClick={handleNavigate}>
                            회원가입
                          </Link>
                        </Button>
                      </div>
                    )}
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
