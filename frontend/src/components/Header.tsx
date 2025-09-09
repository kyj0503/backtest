import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine } from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';

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
          <div className="flex space-x-6 items-center">
            <Link 
              to="/" 
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              홈
            </Link>
            <Link 
              to="/backtest" 
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              백테스트
            </Link>
            <Link 
              to="/community" 
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              커뮤니티
            </Link>
            <Link 
              to="/chat" 
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              채팅
            </Link>
            {!user ? (
              <>
                <Link to="/login" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">로그인</Link>
                <Link to="/signup" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">회원가입</Link>
              </>
            ) : (
              <>
                <span className="text-sm">안녕하세요, <strong>{user.username}</strong>님</span>
                <button onClick={logout} className="px-3 py-1 rounded-md text-xs font-medium bg-blue-700 hover:bg-blue-800">로그아웃</button>
              </>
            )}
            <a 
              href="https://github.com/capstone-backtest/backtest" 
              target="_blank" 
              rel="noopener noreferrer"
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Header;
