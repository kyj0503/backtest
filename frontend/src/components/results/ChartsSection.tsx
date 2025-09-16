import React, { Suspense, memo, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  LazyOHLCChart,
  LazyEquityChart,
  LazyTradesChart,
  LazyStatsSummary,
  LazyStockPriceChart,
} from '../lazy/LazyChartComponents';
import ChartLoading from '../common/ChartLoading';
import { formatPercent } from '../../utils/formatters';
import { useStockData } from '../../hooks/useStockData';
import EnhancedChartsSection from './EnhancedChartsSection';
import { ChartData, PortfolioData, EquityPoint } from '../../types/backtest-results';
import { SectionCard } from '../common';
import { FormLegend } from '../common';
import { Loader2 } from 'lucide-react';

interface ChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ChartsSection: React.FC<ChartsSectionProps> = memo(({ data, isPortfolio }) => {
  const portfolioData = useMemo<PortfolioData | null>(
    () => (isPortfolio && 'portfolio_composition' in data ? (data as PortfolioData) : null),
    [data, isPortfolio],
  );

  const chartData = useMemo<ChartData | null>(
    () => (!isPortfolio ? (data as ChartData) : null),
    [data, isPortfolio],
  );

  const stockQuery = useMemo(
    () => {
      if (portfolioData) {
        return {
          symbols: portfolioData.portfolio_composition.map(item => item.symbol),
          startDate: portfolioData.portfolio_statistics.Start,
          endDate: portfolioData.portfolio_statistics.End,
        };
      }
      if (chartData?.ticker) {
        return {
          symbols: [chartData.ticker],
          startDate: chartData.start_date ?? '',
          endDate: chartData.end_date ?? '',
        };
      }
      return { symbols: [] as string[], startDate: '', endDate: '' };
    },
    [chartData, portfolioData],
  );

  const { stocksData, loading: loadingStockData } = useStockData(stockQuery);

  const formatCurrency = useMemo(
    () => (value: number): string => {
      if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
      if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
      if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
      return value.toLocaleString();
    },
    [],
  );

  const equityChartData = useMemo<EquityPoint[]>(() => {
    if (!portfolioData) return [];
    return Object.entries(portfolioData.equity_curve).map(([date, value]) => ({
      date,
      value,
      return_pct: portfolioData.daily_returns[date] ?? 0,
      drawdown_pct: 0,
    }));
  }, [portfolioData]);

  const renderPortfolioCharts = () => {
    if (!portfolioData) return null;
    const { portfolio_statistics, portfolio_composition } = portfolioData;
    const isMultipleStocks = portfolio_composition.length > 1;

    return (
      <>
        <Suspense fallback={<ChartLoading height={260} />}>
          <LazyStatsSummary stats={portfolio_statistics} />
        </Suspense>

        <SectionCard
          title="누적 자산 가치"
          description="기간 동안의 누적 자산曲선을 확인하세요"
        >
          <ResponsiveContainer width="100%" height={360}>
            <AreaChart data={equityChartData}>
              <defs>
                <linearGradient id="portfolioValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value: string) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis tickFormatter={(value: number) => formatCurrency(value)} />
              <Tooltip
                formatter={(value: number) => [formatCurrency(value), isMultipleStocks ? '포트폴리오 가치' : '자산 가치']}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Area type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} fill="url(#portfolioValue)" />
            </AreaChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard
          title="일일 수익률"
          description="일별 수익률 변동을 살펴보며 변동성을 파악하세요"
        >
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={equityChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value: string) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis tickFormatter={(value: number) => `${value.toFixed(1)}%`} />
              <Tooltip
                formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Line type="monotone" dataKey="return_pct" stroke="#f97316" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard
          title="개별 자산 주가"
          description="포트폴리오 구성 자산들의 가격 흐름"
          actions={
            <FormLegend
              items={[
                { label: `${portfolio_composition.length}개 구성 자산`, tone: 'accent' },
                { label: '동일 축으로 비교', tone: 'muted' },
              ]}
            />
          }
        >
          {loadingStockData ? (
            <div className="flex flex-col items-center gap-3 py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">자산 데이터를 불러오는 중입니다...</p>
            </div>
          ) : stocksData.length > 0 ? (
            <Suspense fallback={<ChartLoading height={360} />}>
              <LazyStockPriceChart stocksData={stocksData} />
            </Suspense>
          ) : (
            <p className="text-sm text-muted-foreground">표시할 자산 데이터가 없습니다.</p>
          )}
        </SectionCard>
      </>
    );
  };

  const renderSingleStockCharts = () => {
    if (!chartData) return null;
    return (
      <>
        <Suspense fallback={<ChartLoading height={260} />}>
          <LazyStatsSummary stats={chartData.summary_stats || {}} />
        </Suspense>

        <SectionCard title="OHLC 차트" description="가격 변동과 거래 시그널을 확인하세요">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyOHLCChart
              data={chartData.ohlc_data ?? []}
              indicators={chartData.indicators ?? []}
              trades={chartData.trade_markers ?? []}
            />
          </Suspense>
        </SectionCard>

        <SectionCard title="수익률 곡선" description="전략의 누적 수익률을 확인하세요">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyEquityChart data={chartData.equity_data ?? []} />
          </Suspense>
        </SectionCard>

        <SectionCard
          title="개별 주가"
          description="백테스트 기간 동안의 주가 흐름"
        >
          {loadingStockData ? (
            <div className="flex flex-col items-center gap-3 py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">자산 데이터를 불러오는 중입니다...</p>
            </div>
          ) : stocksData.length > 0 ? (
            <Suspense fallback={<ChartLoading height={360} />}>
              <LazyStockPriceChart stocksData={stocksData} />
            </Suspense>
          ) : (
            <p className="text-sm text-muted-foreground">표시할 주가 데이터가 없습니다.</p>
          )}
        </SectionCard>

        {chartData.trade_markers && chartData.trade_markers.length > 0 && chartData.strategy !== 'buy_and_hold' && (
          <SectionCard title="거래 내역" description="전략이 실행한 체결 신호">
            <Suspense fallback={<ChartLoading height={360} />}>
              <LazyTradesChart trades={chartData.trade_markers} />
            </Suspense>
          </SectionCard>
        )}
      </>
    );
  };

  return (
    <div className="space-y-6">
      {portfolioData ? renderPortfolioCharts() : renderSingleStockCharts()}

      <EnhancedChartsSection data={data} isPortfolio={isPortfolio} />
    </div>
  );
});

ChartsSection.displayName = 'ChartsSection';

export default ChartsSection;
