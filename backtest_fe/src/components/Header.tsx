import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BarChart3, LogOut, User } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu';

const navigationItems = [
  { href: '/', label: '홈' },
  { href: '/backtest', label: '백테스트' },
  { href: '/community', label: '커뮤니티' },
  { href: '/chat', label: '채팅' },
];

const Header: React.FC = () => {
  const { user, logout, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('로그아웃되었습니다.');
      navigate('/');
    } catch (error) {
      toast.error('로그아웃 중 오류가 발생했습니다.');
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-background/90 backdrop-blur border-b border-border/80">
      <div className="mx-auto flex h-20 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl border border-border/60 bg-primary/10">
            <BarChart3 className="h-5 w-5 text-primary" />
          </span>
          <div className="flex flex-col leading-tight">
            <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Backtesting Studio</span>
            <span className="text-base font-semibold text-foreground">라고할때살걸</span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-4">
          {navigationItems.map((item) => (
            <Button key={item.href} asChild variant="ghost" className="rounded-full px-5 py-4">
              <Link to={item.href} className="text-sm font-semibold">
                {item.label}
              </Link>
            </Button>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          {!isLoading && (
            <>
              {user ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="rounded-full px-4 py-3 flex items-center gap-2">
                      <User className="h-4 w-4" />
                      <span>{user.username}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuLabel>내 계정</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link to="/profile" className="cursor-pointer">
                        <User className="mr-2 h-4 w-4" />
                        <span>프로필</span>
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-destructive">
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>로그아웃</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <>
                  <Button asChild variant="ghost" className="rounded-full px-4 py-3">
                    <Link to="/login">로그인</Link>
                  </Button>
                  <Button asChild className="rounded-full px-4 py-3">
                    <Link to="/signup">회원가입</Link>
                  </Button>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
