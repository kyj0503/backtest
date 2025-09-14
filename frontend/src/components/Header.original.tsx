import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine, FaPalette } from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import { Button } from './ui/button';
import ThemeSelector from './ThemeSelector';

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [showThemeSelector, setShowThemeSelector] = useState(false);

  return (
    <nav className="bg-primary text-primary-foreground sticky top-0 z-50 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="text-xl font-bold hover:text-primary-foreground/80 transition-colors flex items-center gap-2">
            <FaChartLine className="text-lg" />
            <span>라고할때살걸</span>
          </Link>
          
          {/* Navigation Links */}
          <div className="flex space-x-2 items-center">
            <Button asChild variant="ghost" className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground">
              <Link to="/">홈</Link>
            </Button>
            <Button asChild variant="ghost" className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground">
              <Link to="/backtest">백테스트</Link>
            </Button>
            <Button asChild variant="ghost" className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground">
              <Link to="/community">커뮤니티</Link>
            </Button>
            <Button asChild variant="ghost" className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground">
              <Link to="/chat">채팅</Link>
            </Button>
            {!user ? (
              <>
                <Button asChild variant="ghost" className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground">
                  <Link to="/login">로그인</Link>
                </Button>
                <Button asChild variant="ghost" className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground">
                  <Link to="/signup">회원가입</Link>
                </Button>
              </>
            ) : (
              <>
                <span className="text-sm">안녕하세요, <strong>{user.username}</strong>님</span>
                <Button 
                  onClick={logout} 
                  variant="secondary" 
                  size="sm" 
                  className="bg-primary/80 hover:bg-primary/60 text-primary-foreground"
                >
                  로그아웃
                </Button>
              </>
            )}
            
            {/* Theme Controls */}
            <div className="flex items-center gap-1 ml-2">
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
            
            <Button asChild variant="ghost" className="text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground">
              <a 
                href="https://github.com/capstone-backtest/backtest" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                GitHub
              </a>
            </Button>
          </div>
        </div>
      </div>
      
      {/* Theme Selector Modal */}
      {showThemeSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="max-w-4xl w-full max-h-[90vh] overflow-auto">
            <ThemeSelector />
            <div className="mt-4 text-center">
              <Button 
                onClick={() => setShowThemeSelector(false)}
                variant="outline"
                className="bg-background text-foreground"
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Header;
