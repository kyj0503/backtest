import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaChartLine, FaPalette, FaBars } from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet';
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from './ui/navigation-menu';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Separator } from './ui/separator';
import ThemeSelector from './ThemeSelector';
import { cn } from '../lib/utils';

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [showThemeSelector, setShowThemeSelector] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActivePath = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const navigationItems = [
    { href: '/', label: '홈', description: '메인 대시보드로 이동' },
    { href: '/backtest', label: '백테스트', description: '투자 전략 백테스트 실행' },
    { href: '/community', label: '커뮤니티', description: '사용자 커뮤니티 및 토론' },
    { href: '/chat', label: '채팅', description: '실시간 채팅 및 질문' },
  ];

  const UserMenu = () => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage src={undefined} alt={user?.username || '사용자'} />
            <AvatarFallback>
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user?.username}</p>
            <p className="text-xs leading-none text-muted-foreground">
              {user?.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout}>
          로그아웃
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  const ThemeControls = () => (
    <div className="flex items-center gap-1">
      <Button
        onClick={toggleDarkMode}
        variant="ghost"
        size="sm"
        className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground p-2"
        title={isDarkMode ? '라이트 모드로 변경' : '다크 모드로 변경'}
      >
        {isDarkMode ? '☀️' : '🌙'}
      </Button>
      <Button
        onClick={() => setShowThemeSelector(!showThemeSelector)}
        variant="ghost"
        size="sm"
        className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground p-2"
        title="테마 설정"
      >
        <FaPalette className="text-sm" />
      </Button>
    </div>
  );

  return (
    <>
      <nav className="bg-primary text-primary-foreground sticky top-0 z-50 shadow-lg border-b border-primary/20">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Brand */}
            <Link 
              to="/" 
              className="text-xl font-bold hover:text-primary-foreground/80 transition-colors flex items-center gap-2"
            >
              <div className="w-8 h-8 bg-primary-foreground/10 rounded-lg flex items-center justify-center">
                <FaChartLine className="text-primary-foreground" />
              </div>
              <span className="hidden sm:block">라고할때살걸</span>
            </Link>
            
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-1">
              <NavigationMenu>
                <NavigationMenuList>
                  {navigationItems.map((item) => (
                    <NavigationMenuItem key={item.href}>
                      <NavigationMenuLink asChild>
                        <Link
                          to={item.href}
                          className={cn(
                            "group inline-flex h-9 w-max items-center justify-center rounded-md bg-transparent px-4 py-2 text-sm font-medium transition-colors hover:bg-primary/80 hover:text-primary-foreground focus:bg-primary/80 focus:text-primary-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50",
                            isActivePath(item.href) && "bg-primary/80"
                          )}
                        >
                          {item.label}
                          {item.href === '/backtest' && (
                            <Badge variant="secondary" className="ml-2 text-xs">
                              New
                            </Badge>
                          )}
                        </Link>
                      </NavigationMenuLink>
                    </NavigationMenuItem>
                  ))}
                </NavigationMenuList>
              </NavigationMenu>
            </div>

            {/* Desktop Right Side */}
            <div className="hidden md:flex items-center space-x-2">
              {!user ? (
                <div className="flex items-center space-x-1">
                  <Button asChild variant="ghost" size="sm" className="text-primary-foreground hover:bg-primary/80">
                    <Link to="/login">로그인</Link>
                  </Button>
                  <Button asChild variant="secondary" size="sm">
                    <Link to="/signup">회원가입</Link>
                  </Button>
                </div>
              ) : (
                <UserMenu />
              )}
              
              <Separator orientation="vertical" className="h-6 bg-primary-foreground/20" />
              <ThemeControls />
              
              <Button 
                asChild 
                variant="ghost" 
                size="sm"
                className="text-primary-foreground hover:bg-primary/80"
              >
                <a 
                  href="https://github.com/capstone-backtest/backtest" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-1"
                >
                  <span className="text-sm">GitHub</span>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
                  </svg>
                </a>
              </Button>
            </div>

            {/* Mobile Menu Button */}
            <div className="md:hidden">
              <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="sm" className="text-primary-foreground">
                    <FaBars />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[300px] sm:w-[400px]">
                  <SheetHeader>
                    <SheetTitle className="flex items-center gap-2">
                      <FaChartLine className="text-primary" />
                      라고할때살걸
                    </SheetTitle>
                    <SheetDescription>
                      백테스팅 및 투자 분석 플랫폼
                    </SheetDescription>
                  </SheetHeader>
                  
                  <div className="mt-6 space-y-4">
                    {/* User Section */}
                    {user ? (
                      <div className="p-4 bg-muted rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <Avatar className="h-10 w-10">
                            <AvatarImage src={undefined} alt={user?.username || '사용자'} />
                            <AvatarFallback>
                              {user?.username?.charAt(0).toUpperCase() || 'U'}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{user.username}</p>
                            <p className="text-sm text-muted-foreground">{user.email}</p>
                          </div>
                        </div>
                        <Button onClick={logout} size="sm" variant="outline" className="w-full">
                          로그아웃
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Button asChild className="w-full">
                          <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                            로그인
                          </Link>
                        </Button>
                        <Button asChild variant="outline" className="w-full">
                          <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                            회원가입
                          </Link>
                        </Button>
                      </div>
                    )}

                    <Separator />

                    {/* Navigation Links */}
                    <div className="space-y-1">
                      {navigationItems.map((item) => (
                        <Button
                          key={item.href}
                          asChild
                          variant={isActivePath(item.href) ? "secondary" : "ghost"}
                          className="w-full justify-start"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          <Link to={item.href} className="flex flex-col items-start">
                            <span className="font-medium">{item.label}</span>
                            <span className="text-xs text-muted-foreground">{item.description}</span>
                          </Link>
                        </Button>
                      ))}
                    </div>

                    <Separator />

                    {/* Theme Controls */}
                    <div className="space-y-2">
                      <p className="text-sm font-medium">테마 설정</p>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">다크 모드</span>
                        <Button
                          onClick={toggleDarkMode}
                          variant="outline"
                          size="sm"
                        >
                          {isDarkMode ? '☀️' : '🌙'}
                        </Button>
                      </div>
                      <Button
                        onClick={() => {
                          setShowThemeSelector(true);
                          setMobileMenuOpen(false);
                        }}
                        variant="outline"
                        className="w-full"
                      >
                        <FaPalette className="mr-2" />
                        테마 커스터마이징
                      </Button>
                    </div>

                    <Separator />

                    {/* External Links */}
                    <Button 
                      asChild 
                      variant="outline"
                      className="w-full"
                    >
                      <a 
                        href="https://github.com/capstone-backtest/backtest" 
                        target="_blank" 
                        rel="noopener noreferrer"
                      >
                        GitHub에서 보기
                      </a>
                    </Button>
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Theme Selector Modal */}
      {showThemeSelector && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="max-w-4xl w-full max-h-[90vh] overflow-auto bg-background rounded-lg shadow-xl">
            <div className="p-6">
              <ThemeSelector />
              <div className="mt-4 text-center">
                <Button 
                  onClick={() => setShowThemeSelector(false)}
                  variant="outline"
                >
                  닫기
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Header;