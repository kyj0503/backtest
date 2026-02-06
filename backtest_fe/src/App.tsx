import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useTheme } from '@/shared/hooks/useTheme';
import { Header, Footer, ErrorBoundary } from '@/shared/components';
import { Toaster } from '@/shared/ui/sonner';
import { TooltipProvider } from '@/shared/ui/tooltip';

const HomePage = lazy(() => import('./pages/HomePage'));
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'));

function App() {
  // Initialize theme system — useTheme hook handles all DOM updates (dark class, CSS variables)
  useTheme();

  return (
    <ErrorBoundary>
      <TooltipProvider delayDuration={200}>
        <Router>
          <div className="App min-h-screen bg-background text-foreground theme-transition">
            <Header />
            <main>
              <Suspense fallback={<div className="flex items-center justify-center min-h-[60vh]" />}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/backtest" element={<PortfolioPage />} />
                  {/* Legacy route redirects */}
                  <Route path="/single-stock" element={<Navigate to="/backtest" replace />} />
                  <Route path="/portfolio" element={<Navigate to="/backtest" replace />} />
                </Routes>
              </Suspense>
            </main>
            <Footer />
            <Toaster richColors position="top-right" closeButton />
          </div>
        </Router>
      </TooltipProvider>
    </ErrorBoundary>
  );
}

export default App;
