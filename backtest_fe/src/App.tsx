import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useTheme } from '@/shared/hooks/useTheme';
import Header from '@/components/Header';
import { AuthProvider } from '@/features/auth/hooks/useAuth';
import HomePage from './pages/HomePage';
import BacktestPage from './pages/BacktestPage';
import ErrorBoundary from './components/ErrorBoundary';

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
      <AuthProvider>
        <Router>
          <div className="App min-h-screen bg-background text-foreground theme-transition">
            <Header />
            <main>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/backtest" element={<BacktestPage />} />
                {/* Community, chat, and auth routes are temporarily disabled */}
              </Routes>
            </main>
          </div>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
