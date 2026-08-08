import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@/shared/hooks/useTheme';
import { Header, Footer, ErrorBoundary } from '@/shared/components';
import { Toaster } from '@/shared/ui/sonner';
import { TooltipProvider } from '@/shared/ui/tooltip';

const HomePage = lazy(() => import('./pages/HomePage'));
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'));

function App() {
  return (
    // ThemeProvider가 테마 상태의 유일한 소스다 (P2-31) — 트리 전체(Header,
    // ThemeSelector 등)가 이 안에서 렌더링되므로 useTheme()을 호출하는 모든
    // 컴포넌트가 항상 같은 상태를 구독한다. DOM class/CSS 변수 적용 등
    // 부수효과는 ThemeProvider 내부에서 한 번만 실행된다.
    <ThemeProvider>
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
    </ThemeProvider>
  );
}

export default App;
