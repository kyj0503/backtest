import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useTheme } from '@/shared/hooks/useTheme';
import Header from '@/components/Header';
import HomePage from './pages/HomePage';
import SingleStockPage from './pages/SingleStockPage';
import PortfolioPage from './pages/PortfolioPage';
import ErrorBoundary from './components/ErrorBoundary';
import { Toaster } from '@/shared/ui/sonner';

function App() {
  // Initialize theme system
  const { currentTheme, isDarkMode } = useTheme();

  // Apply theme class to root element
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', currentTheme);
    
    if (isDarkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [currentTheme, isDarkMode]);

  return (
    <ErrorBoundary>
      <Router>
        <div className="App min-h-screen bg-background text-foreground theme-transition">
          <Header />
          <main>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/single-stock" element={<SingleStockPage />} />
              <Route path="/portfolio" element={<PortfolioPage />} />
              {/* Legacy route redirect */}
              <Route path="/backtest" element={<Navigate to="/single-stock" replace />} />
            </Routes>
          </main>
          <Toaster richColors position="top-right" closeButton />
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
