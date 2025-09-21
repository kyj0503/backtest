import React, { useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  Github,
  Loader2,
  LogOut,
  Menu,
  MessageSquareText,
  MoonStar,
  Palette,
  SunMedium,
  User,
} from 'lucide-react';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar';
import { useAuth } from '@/features/auth/hooks/useAuth';

const navigationItems = [
  { href: '/', label: '홈', description: '메인 대시보드로 이동' },
  { href: '/backtest', label: '백테스트', description: '투자 전략 백테스트 실행' },
  { href: '/community', label: '커뮤니티', description: '전략을 공유하고 토론' },
  { href: '/chat', label: '채팅', description: '실시간 커뮤니케이션' },
];

const Header: React.FC = () => {
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [themeDialogOpen, setThemeDialogOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isLoading, logout } = useAuth();

  const activeMap = useMemo(() => {
    const pathname = location.pathname;
    const map = new Map<string, boolean>();
    navigationItems.forEach((item) => {
      if (item.href === '/') {
        map.set(item.href, pathname === '/');
      } else {
        map.set(item.href, pathname.startsWith(item.href));
      }
    });
    return map;
  }, [location.pathname]);

  const ThemeControls = ({ compact = false }: { compact?: boolean }) => (
    <div className={cn('flex items-center', compact ? 'gap-1.5' : 'gap-2')}>
      <Button
        onClick={toggleDarkMode}
        variant="ghost"
        size="icon"
        className="rounded-full border border-transparent text-muted-foreground transition-transform hover:-translate-y-0.5 hover:border-border hover:bg-accent hover:text-foreground"
        aria-label={isDarkMode ? '라이트 모드로 변경' : '다크 모드로 변경'}
      >
        {isDarkMode ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      </Button>
      <Button
        onClick={() => setThemeDialogOpen(true)}
        variant="ghost"
        size="icon"
        className="rounded-full border border-transparent text-muted-foreground transition-transform hover:-translate-y-0.5 hover:border-border hover:bg-accent hover:text-foreground"
        aria-label="테마 선택"
      >
        <Palette className="h-4 w-4" />
      </Button>
    </div>
  );

  const AuthDesktopControls = () => {
    if (isLoading) {
      return (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">계정 정보를 불러오는 중...</span>
        </div>
      );
    }

    if (!user) {
      return (
        <div className="flex items-center gap-2">
          <Button variant="ghost" className="rounded-full" onClick={() => navigate('/login')}>
            로그인
          </Button>
          <Button className="rounded-full" onClick={() => navigate('/signup')}>
            회원가입
          </Button>
        </div>
      );
    }

    const fallback = user.username
      ? user.username.slice(0, 2).toUpperCase()
      : user.email.slice(0, 2).toUpperCase();

    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="flex items-center gap-2 rounded-full border border-transparent px-2 py-1 hover:border-border/70"
          >
            <Avatar className="h-9 w-9">
              <AvatarImage src={user.profileImage} alt={user.username} />
              <AvatarFallback>{fallback}</AvatarFallback>
            </Avatar>
            <div className="flex flex-col items-start">
              <span className="text-sm font-semibold text-foreground">{user.username}</span>
              <span className="text-xs text-muted-foreground">{user.email}</span>
            </div>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-60">
          <DropdownMenuLabel>계정</DropdownMenuLabel>
          <DropdownMenuItem onSelect={() => navigate('/community')}>
            <MessageSquareText className="mr-2 h-4 w-4" />
            커뮤니티로 이동
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => navigate('/chat')}>
            <User className="mr-2 h-4 w-4" />
            채팅 참여
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onSelect={() => {
              setMobileMenuOpen(false);
              void logout();
            }}
            className="text-destructive focus:text-destructive"
          >
            <LogOut className="mr-2 h-4 w-4" />
            로그아웃
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  };

  const DesktopNavigation = () => (
    <div className="hidden md:flex items-center gap-1">
      {navigationItems.map((item) => {
        const active = activeMap.get(item.href);
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
            <Badge
              variant="outline"
              className="ml-1 hidden sm:inline-flex rounded-full border-dashed border-primary/40 text-[10px] uppercase tracking-wide text-primary"
            >
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
                        const active = activeMap.get(item.href);
                        return (
                          <Button
                            key={item.href}
                            asChild
                            variant={active ? 'secondary' : 'ghost'}
                            className="w-full justify-start rounded-2xl px-4 py-3 text-left"
                            onClick={() => setMobileMenuOpen(false)}
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
                    {isLoading ? (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">계정 정보를 불러오는 중...</span>
                      </div>
                    ) : user ? (
                      <div className="space-y-3">
                        <div className="flex items-center gap-3 rounded-2xl border border-border/80 p-3">
                          <Avatar className="h-10 w-10">
                            <AvatarImage src={user.profileImage} alt={user.username} />
                            <AvatarFallback>
                              {(user.username ?? user.email).slice(0, 2).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex flex-col">
                            <span className="text-sm font-semibold text-foreground">{user.username}</span>
                            <span className="text-xs text-muted-foreground">{user.email}</span>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          className="w-full rounded-2xl"
                          onClick={() => {
                            setMobileMenuOpen(false);
                            void logout();
                          }}
                        >
                          <LogOut className="mr-2 h-4 w-4" />
                          로그아웃
                        </Button>
                      </div>
                    ) : (
                      <div className="grid gap-2">
                        <Button className="rounded-2xl" onClick={() => navigate('/login')}>
                          로그인
                        </Button>
                        <Button variant="outline" className="rounded-2xl" onClick={() => navigate('/signup')}>
                          회원가입
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

          <div className="hidden md:flex items-center gap-3">
            <ThemeControls />
            <AuthDesktopControls />
          </div>
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
