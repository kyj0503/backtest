import React, { Suspense, memo, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { 
  LazyOHLCChart, 
  LazyEquityChart, 
  LazyTradesChart, 
  LazyStatsSummary, 
  LazyStockPriceChart 
} from '../lazy/LazyChartComponents';
import ChartLoading from '../common/ChartLoading';
import { formatPercent } from '../../utils/formatters';
import { useStockData } from '../../hooks/useStockData';
import EnhancedChartsSection from './EnhancedChartsSection';
import { 
  ChartData, 
  PortfolioData
} from '../../types/backtest-results';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Loader2 } from 'lucide-react';

interface ChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ChartsSection: React.FC<ChartsSectionProps> = memo(({ data, isPortfolio }) => {
  // 화폐 포맷터 함수 메모이제이션
  const formatCurrency = useMemo(() => (value: number): string => {
    if (value >= 1e9) {
      return `${(value / 1e9).toFixed(1)}B`;
    } else if (value >= 1e6) {
      return `${(value / 1e6).toFixed(1)}M`;
    } else if (value >= 1e3) {
      return `${(value / 1e3).toFixed(1)}K`;
    }
    return value.toLocaleString();
  }, []);

  // 포트폴리오 차트 렌더링
  const renderPortfolioCharts = () => {
    if (!isPortfolio || !('portfolio_composition' in data)) {
      return null;
    }

    const portfolioData = data as PortfolioData;
    const { portfolio_statistics, portfolio_composition, equity_curve, daily_returns } = portfolioData;

    // 주가 데이터 페칭 훅 사용
    const symbols = portfolio_composition.map(item => item.symbol);
    const { 
      stocksData, 
      loading: loadingStockData 
    } = useStockData({
      symbols,
      startDate: portfolio_statistics.Start,
      endDate: portfolio_statistics.End
    });

    // equity_curve를 배열로 변환
    const equityChartData = Object.entries(equity_curve).map(([date, value]) => ({
      date,
      value: value,
      return_pct: daily_returns[date] || 0,
      drawdown_pct: 0 // 포트폴리오에서는 drawdown 계산이 필요하면 추가
    }));

    const isMultipleStocks = portfolio_composition.length > 1;

    return (
      <>
        /* 백테스트 성과 통계 */
        <Suspense fallback={<ChartLoading height={300} />}>
          <LazyStatsSummary stats={{
            Total_Return: portfolio_statistics.Total_Return || 0,
            Annual_Return: portfolio_statistics.Annual_Return || 0,
            Annual_Volatility: portfolio_statistics.Annual_Volatility || 0,
            Sharpe_Ratio: portfolio_statistics.Sharpe_Ratio || 0,
            Max_Drawdown: portfolio_statistics.Max_Drawdown || 0,
            Total_Trading_Days: portfolio_statistics.Total_Trading_Days || 0,
            Win_Rate: portfolio_statistics.Win_Rate || 0,
            Avg_Drawdown: portfolio_statistics.Avg_Drawdown || 0,
            profit_factor: portfolio_statistics.Profit_Factor || 1.0
          }} />
        </Suspense>

        {/* 포트폴리오 백테스트 결과 차트 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">백테스트 수익률 곡선</CardTitle>
          </CardHeader>
          <CardContent>
            <Suspense fallback={<ChartLoading height={400} />}>
              <LazyEquityChart data={equityChartData} />
            </Suspense>
          </CardContent>
        </Card>        {/* 개별 종목 주가 차트 */}
        {loadingStockData ? (
          <Card className="p-8 text-center">
            <div className="flex flex-col items-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-muted-foreground">개별 종목 주가 데이터를 가져오는 중...</p>
            </div>
          </Card>
        ) : stocksData.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                개별 종목 주가 변동 ({stocksData.length}개 종목)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Suspense fallback={<ChartLoading height={400} />}>
                <LazyStockPriceChart stocksData={stocksData} />
              </Suspense>
            </CardContent>
          </Card>
        ) : null}

        {/* 주요 성과 지표 */}
        <Card>
          <CardHeader>
            <CardTitle>{isMultipleStocks ? '포트폴리오' : '종목'} 성과 요약</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-sm font-medium text-muted-foreground mb-2">총 수익률</p>
                <p className={`text-2xl font-bold ${(portfolio_statistics.Total_Return || 0) >= 0 ? 'text-green-600' : 'text-destructive'}`}>
                  {formatPercent(portfolio_statistics.Total_Return)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-muted-foreground mb-2">연간 수익률</p>
                <p className={`text-xl font-semibold ${(portfolio_statistics.Annual_Return || 0) >= 0 ? 'text-green-600' : 'text-destructive'}`}>
                  {formatPercent(portfolio_statistics.Annual_Return)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-muted-foreground mb-2">샤프 비율</p>
                <p className="text-xl font-semibold text-foreground">{portfolio_statistics.Sharpe_Ratio ? portfolio_statistics.Sharpe_Ratio.toFixed(2) : 'N/A'}</p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-muted-foreground mb-2">최대 낙폭</p>
                <p className="text-xl font-semibold text-destructive">{formatPercent(portfolio_statistics.Max_Drawdown)}</p>
              </div>
            </div>

            {/* 추가 통계 정보 */}
            {portfolio_statistics && (
              <div className="mt-8">
                <h3 className="text-lg font-semibold mb-4">상세 통계</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">투자 기간</span>
                      <span className="text-sm font-medium">{portfolio_statistics.Duration}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">초기 자산</span>
                      <span className="text-sm font-medium">{formatCurrency(portfolio_statistics.Initial_Value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">최종 자산</span>
                      <span className="text-sm font-medium">{formatCurrency(portfolio_statistics.Final_Value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">최고 자산</span>
                      <span className="text-sm font-medium">{formatCurrency(portfolio_statistics.Peak_Value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">연간 변동성</span>
                      <span className="text-sm font-medium">{formatPercent(portfolio_statistics.Annual_Volatility)}</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">최대 연속 상승</span>
                      <span className="text-sm font-medium text-green-600">{portfolio_statistics.Max_Consecutive_Gains || 0}일</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">최대 연속 하락</span>
                      <span className="text-sm font-medium text-destructive">{portfolio_statistics.Max_Consecutive_Losses || 0}일</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">총 거래일</span>
                      <span className="text-sm font-medium">{portfolio_statistics.Total_Trading_Days || 0}일</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">평균 낙폭</span>
                      <span className="text-sm font-medium">{formatPercent(portfolio_statistics.Avg_Drawdown)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">상승일/하락일</span>
                      <span className="text-sm font-medium">
                        <span className="text-green-600">{portfolio_statistics.Positive_Days || 0}</span>
                        {' / '}
                        <span className="text-destructive">{portfolio_statistics.Negative_Days || 0}</span>
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">승률</span>
                      <span className="text-sm font-medium">{formatPercent(portfolio_statistics.Win_Rate)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 자산 곡선 차트 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">자산 곡선</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={equityChartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: any) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: number) => formatCurrency(value)}
                />
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), isMultipleStocks ? '포트폴리오 가치' : '자산 가치']}
                  labelFormatter={(label: any) => `날짜: ${label}`}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#8884d8" 
                  fillOpacity={1} 
                  fill="url(#colorValue)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 일일 수익률 차트 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">일일 수익률 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={equityChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: any) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: number) => `${value.toFixed(1)}%`}
                />
                <Tooltip 
                  formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
                  labelFormatter={(label: any) => `날짜: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="return_pct" 
                  stroke="#ff7300" 
                  strokeWidth={1}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </>
    );
  };

  // 단일 종목 차트 렌더링
  const renderSingleStockCharts = () => {
    const chartData = data as ChartData;
    
    return (
      <>
        <Suspense fallback={<ChartLoading height={300} />}>
          <LazyStatsSummary stats={chartData.summary_stats || {}} />
        </Suspense>

        {/* 백테스트 결과 차트 (단일 종목) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">백테스트 결과</CardTitle>
          </CardHeader>
          <CardContent>
            <Suspense fallback={<ChartLoading height={400} />}>
              <LazyOHLCChart 
                data={chartData.ohlc_data || []} 
                indicators={chartData.indicators || []} 
                trades={chartData.trade_markers || []} 
              />
            </Suspense>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">수익률 곡선</CardTitle>
          </CardHeader>
          <CardContent>
            <Suspense fallback={<ChartLoading height={400} />}>
              <LazyEquityChart data={chartData.equity_data || []} />
            </Suspense>
          </CardContent>
        </Card>

        {/* 개별 주가 차트 (단일 종목) */}
        {chartData.ticker && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">개별 주가 변동</CardTitle>
            </CardHeader>
            <CardContent>
              <Suspense fallback={<ChartLoading height={400} />}>
                <LazyStockPriceChart 
                  stocksData={[{
                    symbol: chartData.ticker,
                    data: chartData.ohlc_data?.map(item => ({
                      date: item.date,
                      price: item.close,
                      volume: item.volume
                    })) || []
                  }]} 
                />
              </Suspense>
            </CardContent>
          </Card>
        )}

        {/* 거래 내역 차트 (단일 종목, Buy and Hold 전략 제외) */}
        {chartData.trade_markers && chartData.trade_markers.length > 0 && 
         chartData.strategy !== 'buy_and_hold' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">거래 내역</CardTitle>
            </CardHeader>
            <CardContent>
              <Suspense fallback={<ChartLoading height={400} />}>
                <LazyTradesChart trades={chartData.trade_markers} />
              </Suspense>
            </CardContent>
          </Card>
        )}
      </>
    );
  };

  return (
    <>
      {isPortfolio ? renderPortfolioCharts() : renderSingleStockCharts()}
      
      {/* 추가 데이터 차트 (환율, 벤치마크 등) - 다시 활성화 */}
      <EnhancedChartsSection data={data} isPortfolio={isPortfolio} />
    </>
  );
});

ChartsSection.displayName = 'ChartsSection';

export default ChartsSection;
