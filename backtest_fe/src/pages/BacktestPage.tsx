import React from 'react';
import { AlertTriangle, TrendingUp, X, Loader2 } from 'lucide-react';
import BacktestForm from '@/features/backtest/components/BacktestForm';
import BacktestResults from '@/features/backtest/components/BacktestResults';
import { useBacktest } from '@/features/backtest/hooks/useBacktest';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/shared/ui/alert';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';

const BacktestPage: React.FC = () => {
  const { results, loading, error, errorType, errorId, isPortfolio, runBacktest, clearError } = useBacktest();

  const getErrorTitle = (type: string) => {
    switch (type) {
      case 'network': return '네트워크 오류';
      case 'data_not_found': return '데이터 없음';
      case 'validation': return '입력값 오류';
      case 'rate_limit': return '요청 제한 초과';
      default: return '오류가 발생했습니다';
    }
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-6 max-w-[1400px]">
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
            투자 전략을 설정하고 백테스트를 실행해보세요
          </p>
        </div>

        {/* Backtest Form */}
        <Card className="mb-8 shadow-sm">
          <CardHeader>
            <CardTitle>백테스트 설정</CardTitle>
            <CardDescription>
              포트폴리오 구성, 투자 전략, 백테스트 기간을 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <BacktestForm 
              onSubmit={runBacktest} 
              loading={loading} 
            />
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
                {getErrorTitle(errorType || 'unknown')}
              </AlertTitle>
              <AlertDescription className="mt-1">
                {error}
                {errorId && (
                  <div className="text-xs mt-2 font-mono">
                    오류 ID: {errorId}
                  </div>
                )}
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
              </CardTitle>
              <CardDescription>
                설정하신 전략에 따른 백테스트 분석 결과입니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <BacktestResults 
                data={results} 
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
                포트폴리오 구성, 투자 전략, 백테스트 기간을 설정한 후<br />
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
