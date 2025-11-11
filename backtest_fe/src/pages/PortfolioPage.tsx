import React from 'react';
import { AlertTriangle, TrendingUp, X, Loader2, Briefcase } from 'lucide-react';
import PortfolioBacktestForm from '@/features/backtest/components/PortfolioBacktestForm';
import BacktestResults from '@/features/backtest/components/BacktestResults';
import { useBacktest } from '@/features/backtest/hooks/usePortfolioBacktest';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/shared/ui/alert';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';

const PortfolioPage: React.FC = () => {
  const { result: results, isLoading: loading, error, runBacktest, reset: clearError } = useBacktest();

  const getErrorTitle = (err: string | null) => {
    if (!err) return '오류가 발생했습니다';
    return '오류가 발생했습니다';
  };

  return (
    <div className="min-h-screen bg-background py-4 sm:py-8">
      <div className="mx-auto px-2 sm:px-4 md:px-6 lg:px-8 w-full lg:max-w-screen-2xl">
        {/* Page Header */}
        <div className="text-center mb-6 sm:mb-10">
          <div className="flex justify-center mb-3 sm:mb-5">
            <Badge variant="outline" className="mb-2">
              <TrendingUp className="w-4 h-4 mr-2" />
              투자 전략 백테스팅
            </Badge>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-primary mb-3 sm:mb-5 tracking-tight">
            백테스트
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto px-2">
            단일 종목 또는 여러 종목으로 구성된 포트폴리오의 투자 전략을 테스트합니다
          </p>
        </div>

        {/* Backtest Form */}
        <Card className="mb-6 sm:mb-10">
          <CardHeader>
            <CardTitle>백테스트 설정</CardTitle>
            <CardDescription className="text-sm sm:text-base">
              종목 구성, 투자 전략, 백테스트 기간을 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PortfolioBacktestForm onSubmit={runBacktest} loading={loading} />
          </CardContent>
        </Card>

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
                포트폴리오 데이터를 분석하고 있습니다. 잠시만 기다려 주세요.
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
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-2xl sm:text-3xl">
                <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 mr-2 sm:mr-3" />
                백테스트 결과
              </CardTitle>
              <CardDescription className="text-sm sm:text-base mt-2">
                설정하신 구성과 전략에 따른 백테스트 분석 결과입니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <BacktestResults
                data={results.data}
                isPortfolio={true}
              />
            </CardContent>
          </Card>
        )}

        {/* Initial State Guide */}
        {!results && !loading && !error && (
          <Card className="border-dashed border-2 border-muted-foreground/30 bg-muted/20 backdrop-blur-sm">
            <CardContent className="text-center py-12 sm:py-20 px-4">
              <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-6 sm:mb-8 flex items-center justify-center bg-primary/15 rounded-2xl shadow-sm">
                <Briefcase className="text-primary h-8 w-8 sm:h-10 sm:w-10" />
              </div>
              <CardTitle className="text-xl sm:text-2xl font-bold mb-3 sm:mb-5">
                백테스트 설정을 완료하고 실행하세요
              </CardTitle>
              <CardDescription className="text-sm sm:text-base leading-relaxed">
                종목 구성과 투자 전략, 백테스트 기간을 설정한 후<br />
                <span className="inline-flex items-center rounded-full border-2 px-3 py-1 text-xs font-bold mx-2 mt-2 bg-background">백테스트 실행</span>
                버튼을 클릭하면 결과를 확인할 수 있습니다.
              </CardDescription>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default PortfolioPage;
