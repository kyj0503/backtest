import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine } from 'react-icons/fa';

const Header: React.FC = () => {
  return (
    <nav className="bg-blue-600 text-white sticky top-0 z-50 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="text-xl font-bold hover:text-blue-200 transition-colors flex items-center gap-2">
            <FaChartLine className="text-lg" />
            <span>백테스팅 플랫폼</span>
          </Link>
          
          {/* Navigation Links */}
          <div className="flex space-x-6">
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
