import React from 'react';
import { AlertTriangle, X, Loader2, Briefcase } from 'lucide-react';
import PortfolioBacktestForm from '@/features/backtest/components/PortfolioBacktestForm';
import BacktestResults from '@/features/backtest/components/BacktestResults';
import { useBacktest } from '@/features/backtest/hooks/usePortfolioBacktest';
import { Card, CardContent, CardDescription, CardTitle } from '@/shared/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/shared/ui/alert';
import { Button } from '@/shared/ui/button';

const PortfolioPage: React.FC = () => {
  const { result: results, isLoading: loading, error, runBacktest, reset: clearError } = useBacktest();

  const getErrorTitle = (err: string | null) => {
    if (!err) return '오류가 발생했습니다';
    return '오류가 발생했습니다';
  };

  return (
    <div className="min-h-screen bg-background py-4 sm:py-8">
      <div className="mx-auto px-2 sm:px-4 md:px-6 lg:px-8 w-full lg:max-w-screen-2xl">
        {/* Backtest Form */}
        <PortfolioBacktestForm onSubmit={runBacktest} loading={loading} />

        {/* Loading State */}
        {loading && (
          <Card className="border-primary/30 bg-primary/5 backdrop-blur-sm">
            <CardContent className="text-center py-12 sm:py-20">
              <div className="relative inline-block mb-4 sm:mb-6">
                <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl animate-pulse"></div>
                <Loader2 className="h-12 w-12 sm:h-16 sm:w-16 animate-spin text-primary relative" />
              </div>
              <CardTitle className="text-xl sm:text-2xl font-bold mb-2 sm:mb-3">백테스트 실행 중...</CardTitle>
              <CardDescription className="text-sm sm:text-base px-4">
                과거 데이터를 기반으로 전략을 시뮬레이션하고 있습니다. 잠시만 기다려 주세요.
              </CardDescription>
            </CardContent>
          </Card>
        )}

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6 sm:mb-10">
            <AlertTriangle className="h-5 w-5" />
            <div className="flex-1">
              <AlertTitle>
                {getErrorTitle(error)}
              </AlertTitle>
              <AlertDescription className="mt-2 text-sm">
                {error}
              </AlertDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={clearError}
              className="ml-auto hover:bg-destructive/20 rounded-lg"
            >
              <X className="h-5 w-5" />
              <span className="sr-only">닫기</span>
            </Button>
          </Alert>
        )}

        {/* Results Display */}
        {results && !loading && (
          <BacktestResults
            data={results.data}
            isPortfolio={true}
          />
        )}

        {/* Initial State Guide */}
        {!results && !loading && !error && (
          <Card className="border-dashed border-2 border-muted-foreground/30 bg-muted/20 backdrop-blur-sm">
            <CardContent className="text-center py-12 sm:py-20 px-4">
              <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-6 sm:mb-8 flex items-center justify-center bg-primary/15 rounded-2xl shadow-sm">
                <Briefcase className="text-primary h-8 w-8 sm:h-10 sm:w-10" />
              </div>
              <CardTitle className="text-xl sm:text-2xl font-bold mb-3 sm:mb-5">
                나만의 투자 전략을 검증해보세요
              </CardTitle>
              <CardDescription className="text-sm sm:text-base leading-relaxed">
                포트폴리오를 구성하고 투자 전략을 선택한 후, <br />
                <span className="inline-flex items-center rounded-full border-2 px-3 py-1 text-xs font-bold mx-2 mt-2 bg-background">백테스트 실행</span>
                버튼을 클릭하여 시뮬레이션 결과를 확인하세요.
              </CardDescription>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default PortfolioPage;
