import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Separator } from '../components/ui/separator';
import BacktestForm from '../components/BacktestForm';
import BacktestResults from '../components/BacktestResults';
import { useBacktest } from '../hooks/useBacktest';
import { AlertCircle, TrendingUp, PlayCircle } from 'lucide-react';

const BacktestPage: React.FC = () => {
  const { results, loading, error, errorType, errorId, isPortfolio, runBacktest, clearError } = useBacktest();

  const getErrorIcon = () => {
    switch (errorType) {
      case 'network': return '🌐';
      case 'data_not_found': return '📊';
      case 'validation': return '⚠️';
      case 'rate_limit': return '⏱️';
      default: return '❗';
    }
  };

  const getErrorTitle = () => {
    switch (errorType) {
      case 'network': return '네트워크 오류';
      case 'data_not_found': return '데이터 없음';
      case 'validation': return '입력값 오류';
      case 'rate_limit': return '요청 제한 초과';
      default: return '오류 발생';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* 페이지 헤더 */}
        <div className="text-center mb-8 space-y-4">
          <div className="flex justify-center items-center gap-2">
            <TrendingUp className="h-8 w-8 text-primary" />
            <h1 className="text-4xl font-bold text-foreground">백테스트 실행</h1>
          </div>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            투자 전략을 설정하고 과거 데이터를 기반으로 성과를 분석해보세요
          </p>
          <div className="flex justify-center gap-2">
            <Badge variant="secondary" className="flex items-center gap-1">
              <PlayCircle className="h-3 w-3" />
              실시간 데이터 연동
            </Badge>
            <Badge variant="outline">다중 전략 지원</Badge>
            <Badge variant="outline">위험 분석 포함</Badge>
          </div>
        </div>

        {/* 백테스트 폼 */}
        <div className="mb-8">
          <Card className="border-2 border-dashed border-primary/20 hover:border-primary/40 transition-colors">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-primary font-bold">1</span>
                </div>
                백테스트 설정
              </CardTitle>
              <CardDescription>
                투자 전략의 매개변수를 설정하고 백테스트를 실행하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <BacktestForm 
                onSubmit={runBacktest} 
                loading={loading} 
              />
            </CardContent>
          </Card>
        </div>

        {/* 로딩 상태 */}
        {loading && (
          <Card className="mb-8 border-blue-200 bg-blue-50/50 dark:bg-blue-950/20">
            <CardContent className="py-12">
              <div className="text-center space-y-6">
                <div className="flex justify-center">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-pulse"></div>
                    <div className="absolute top-0 left-0 w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold text-blue-900 dark:text-blue-100">
                    백테스트 실행 중...
                  </h3>
                  <p className="text-blue-700 dark:text-blue-300">
                    데이터를 분석하고 성과를 계산하고 있습니다
                  </p>
                </div>

                <div className="space-y-2 max-w-md mx-auto">
                  <div className="flex justify-between text-sm text-blue-600 dark:text-blue-400">
                    <span>진행률</span>
                    <span>분석 중...</span>
                  </div>
                  <div className="space-y-1">
                    <Skeleton className="h-2 w-full bg-blue-200" />
                    <Skeleton className="h-2 w-3/4 bg-blue-100" />
                    <Skeleton className="h-2 w-1/2 bg-blue-100" />
                  </div>
                </div>

                <Button
                  variant="outline"
                  onClick={() => {/* TODO: Implement abort */}}
                  className="border-blue-200 text-blue-700 hover:bg-blue-100"
                >
                  백테스트 중단
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 에러 메시지 */}
        {error && (
          <Card className="mb-8 border-destructive/20 bg-destructive/5">
            <CardContent className="py-6">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="ml-2">
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{getErrorIcon()}</span>
                      <div className="flex-1">
                        <h4 className="font-semibold text-destructive-foreground mb-1">
                          {getErrorTitle()}
                        </h4>
                        <p className="text-sm text-destructive-foreground/80 mb-2">
                          {error}
                        </p>
                        {errorId && (
                          <p className="text-xs text-destructive-foreground/60">
                            오류 ID: {errorId}
                          </p>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearError}
                        className="text-destructive-foreground hover:bg-destructive/20"
                      >
                        ✕
                      </Button>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        )}

        {/* 결과 표시 */}
        {results && !loading && (
          <Card className="mb-8 border-green-200 bg-green-50/50 dark:bg-green-950/20">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-green-800 dark:text-green-200">
                <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                  <span className="text-green-600 dark:text-green-400 font-bold">2</span>
                </div>
                백테스트 결과
                <Badge variant="secondary" className="ml-auto">
                  {isPortfolio ? '포트폴리오' : '단일 종목'}
                </Badge>
              </CardTitle>
              <CardDescription className="text-green-700 dark:text-green-300">
                백테스트가 성공적으로 완료되었습니다. 아래에서 상세 결과를 확인하세요.
              </CardDescription>
            </CardHeader>
            <Separator className="mb-6" />
            <CardContent>
              <BacktestResults 
                data={results} 
                isPortfolio={isPortfolio} 
              />
            </CardContent>
          </Card>
        )}

        {/* 초기 상태 안내 */}
        {!results && !loading && !error && (
          <Card className="border-dashed border-2 border-muted-foreground/20">
            <CardContent className="py-16">
              <div className="text-center space-y-6">
                <div className="w-20 h-20 mx-auto rounded-full bg-muted/50 flex items-center justify-center">
                  <TrendingUp className="w-10 h-10 text-muted-foreground" />
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">백테스트를 시작하세요</h3>
                  <p className="text-muted-foreground max-w-lg mx-auto">
                    위의 설정 양식을 통해 포트폴리오 구성, 투자 전략, 백테스트 기간을 설정한 후 
                    <strong className="text-primary"> 백테스트 실행</strong> 버튼을 클릭하여 분석을 시작하세요.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto text-sm">
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <div className="w-8 h-8 rounded bg-blue-100 dark:bg-blue-900 flex items-center justify-center mx-auto mb-2">
                      📊
                    </div>
                    <p><strong>실시간 데이터</strong><br />최신 시장 데이터로 분석</p>
                  </div>
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <div className="w-8 h-8 rounded bg-green-100 dark:bg-green-900 flex items-center justify-center mx-auto mb-2">
                      🎯
                    </div>
                    <p><strong>다양한 전략</strong><br />7가지 투자 전략 지원</p>
                  </div>
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <div className="w-8 h-8 rounded bg-purple-100 dark:bg-purple-900 flex items-center justify-center mx-auto mb-2">
                      📈
                    </div>
                    <p><strong>상세 분석</strong><br />수익률, 리스크, 차트 제공</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default BacktestPage;