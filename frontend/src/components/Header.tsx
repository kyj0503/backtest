import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine } from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';
import { Button } from './ui/button';

const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-blue-600 text-white sticky top-0 z-50 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="text-xl font-bold hover:text-blue-200 transition-colors flex items-center gap-2">
            <FaChartLine className="text-lg" />
            <span>라고할때살걸</span>
          </Link>
          
          {/* Navigation Links */}
          <div className="flex space-x-2 items-center">
            <Button asChild variant="ghost" className="text-white hover:bg-blue-700 hover:text-white">
              <Link to="/">홈</Link>
            </Button>
            <Button asChild variant="ghost" className="text-white hover:bg-blue-700 hover:text-white">
              <Link to="/backtest">백테스트</Link>
            </Button>
            <Button asChild variant="ghost" className="text-white hover:bg-blue-700 hover:text-white">
              <Link to="/community">커뮤니티</Link>
            </Button>
            <Button asChild variant="ghost" className="text-white hover:bg-blue-700 hover:text-white">
              <Link to="/chat">채팅</Link>
            </Button>
            {!user ? (
              <>
                <Button asChild variant="ghost" className="text-white hover:bg-blue-700 hover:text-white">
                  <Link to="/login">로그인</Link>
                </Button>
                <Button asChild variant="ghost" className="text-white hover:bg-blue-700 hover:text-white">
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
                  className="bg-blue-700 hover:bg-blue-800 text-white"
                >
                  로그아웃
                </Button>
              </>
            )}
            <Button asChild variant="ghost" className="text-white hover:bg-blue-700 hover:text-white">
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
    </nav>
  );
};

export default Header;
