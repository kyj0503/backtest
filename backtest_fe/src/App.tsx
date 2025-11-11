import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useTheme } from '@/shared/hooks/useTheme';
import { Header, ErrorBoundary } from '@/shared/components';
import HomePage from './pages/HomePage';
import PortfolioPage from './pages/PortfolioPage';
import { Toaster } from '@/shared/ui/sonner';
import { TooltipProvider } from '@/shared/ui/tooltip';

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
      <TooltipProvider delayDuration={200}>
        <Router>
          <div className="App min-h-screen bg-background text-foreground theme-transition">
            <Header />
            <main>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/backtest" element={<PortfolioPage />} />
                {/* Legacy route redirects */}
                <Route path="/single-stock" element={<Navigate to="/backtest" replace />} />
                <Route path="/portfolio" element={<Navigate to="/backtest" replace />} />
              </Routes>
            </main>
            <Toaster richColors position="top-right" closeButton />
          </div>
        </Router>
      </TooltipProvider>
    </ErrorBoundary>
  );
}

export default App;
