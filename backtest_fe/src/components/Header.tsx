import React from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, Github } from 'lucide-react';
import { Button } from '@/shared/ui/button';

const navigationItems = [
  { href: '/', label: '홈' },
  { href: '/backtest', label: '백테스트' },
  { href: '/community', label: '커뮤니티' },
  { href: '/chat', label: '채팅' },
];

const Header: React.FC = () => {
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
          <Button variant="ghost" className="rounded-full px-4 py-3">로그인</Button>
          <Button className="rounded-full px-4 py-3">회원가입</Button>
        </div>
      </div>
    </header>
  );
};

export default Header;
