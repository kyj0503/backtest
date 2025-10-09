import React, { useState } from 'react';
import { AlertTriangle, TrendingUp, X, Loader2 } from 'lucide-react';
import SingleStockForm from '@/features/backtest/components/SingleStockForm';
import PortfolioBacktestForm from '@/features/backtest/components/PortfolioBacktestForm';
import BacktestResults from '@/features/backtest/components/BacktestResults';
import { useBacktest } from '@/features/backtest/hooks/useBacktest';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/shared/ui/alert';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';

const BacktestPage: React.FC = () => {
  const { result: results, isLoading: loading, error, isPortfolioBacktest: isPortfolio, runBacktest, reset: clearError } = useBacktest();
  const [activeTab, setActiveTab] = useState<string>('single');

  const getErrorTitle = (err: string | null) => {
    if (!err) return '오류가 발생했습니다';
    return '오류가 발생했습니다';
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="mx-auto px-4 sm:px-6 lg:px-8 w-full max-w-screen-2xl">
        {/* Page Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Badge variant="outline" className="mb-4">
              <TrendingUp className="w-4 h-4 mr-1" />
              투자 전략 백테스팅
            </Badge>
          </div>
          <h2 className="text-3xl font-bold text-primary mb-4">
            백테스트 실행
          </h2>
          <p className="text-muted-foreground">
            단일 종목 또는 포트폴리오 전략을 설정하고 백테스트를 실행해보세요
          </p>
        </div>

        {/* Backtest Form with Tabs */}
        <Card className="mb-8 shadow-sm">
          <CardHeader>
            <CardTitle>백테스트 설정</CardTitle>
            <CardDescription>
              단일 종목 또는 포트폴리오 백테스트를 선택하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto mb-8">
                <TabsTrigger value="single" className="text-sm sm:text-base">
                  단일 종목
                </TabsTrigger>
                <TabsTrigger value="portfolio" className="text-sm sm:text-base">
                  포트폴리오
                </TabsTrigger>
              </TabsList>

              <TabsContent value="single" className="mt-0">
                <div className="mb-4 p-4 bg-muted/50 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">
                    <strong>단일 종목 백테스트:</strong> 하나의 종목에 대한 투자 전략을 빠르게 테스트합니다.
                  </p>
                </div>
                <SingleStockForm onSubmit={runBacktest} loading={loading} />
              </TabsContent>

              <TabsContent value="portfolio" className="mt-0">
                <div className="mb-4 p-4 bg-muted/50 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">
                    <strong>포트폴리오 백테스트:</strong> 여러 종목으로 구성된 포트폴리오의 리밸런싱, 분산투자 전략을 테스트합니다.
                  </p>
                </div>
                <PortfolioBacktestForm onSubmit={runBacktest} loading={loading} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loading && (
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="text-center py-16">
              <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
              <CardTitle className="text-xl font-semibold mb-2">백테스트 실행 중...</CardTitle>
              <CardDescription>
                데이터를 분석하고 있습니다. 잠시만 기다려 주세요.
              </CardDescription>
            </CardContent>
          </Card>
        )}

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-8">
            <AlertTriangle className="h-4 w-4" />
            <div className="flex-1">
              <AlertTitle>
                {getErrorTitle(error)}
              </AlertTitle>
              <AlertDescription className="mt-1">
                {error}
              </AlertDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearError}
              className="ml-auto hover:bg-destructive/20"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">닫기</span>
            </Button>
          </Alert>
        )}

        {/* Results Display */}
        {results && !loading && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                백테스트 결과
                {isPortfolio && (
                  <Badge variant="secondary" className="ml-2">
                    포트폴리오
                  </Badge>
                )}
                {!isPortfolio && (
                  <Badge variant="secondary" className="ml-2">
                    단일 종목
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                설정하신 전략에 따른 백테스트 분석 결과입니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <BacktestResults
                data={results.data as any}
                isPortfolio={isPortfolio}
              />
            </CardContent>
          </Card>
        )}

        {/* Initial State Guide */}
        {!results && !loading && !error && (
          <Card className="border-dashed border-2 border-muted-foreground/25">
            <CardContent className="text-center py-16">
              <div className="w-16 h-16 mx-auto mb-6 flex items-center justify-center bg-primary/10 rounded-full">
                <TrendingUp className="text-primary h-8 w-8" />
              </div>
              <CardTitle className="text-xl font-semibold mb-4">
                백테스트 설정을 완료하고 실행 버튼을 눌러주세요
              </CardTitle>
              <CardDescription className="text-base">
                {activeTab === 'single' ? '종목 정보' : '포트폴리오 구성'}와 투자 전략, 백테스트 기간을 설정한 후<br />
                <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold mx-1">백테스트 실행</span>
                버튼을 클릭하면 결과를 확인할 수 있습니다.
              </CardDescription>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default BacktestPage;
