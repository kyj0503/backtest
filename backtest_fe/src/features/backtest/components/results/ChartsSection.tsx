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
import ChartLoading from '@/shared/components/ChartLoading';
import { useStockData } from '../../hooks/useStockData';
import EnhancedChartsSection from './EnhancedChartsSection';
import { ChartData, PortfolioData, EquityPoint, TradeMarker, OhlcPoint } from '../../model/backtest-result-types';
import { FormLegend } from '@/shared/components';
import { Loader2 } from 'lucide-react';

interface ChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ResultBlock: React.FC<{
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}> = ({ title, description, actions, children }) => (
  <div className="space-y-3 rounded-2xl border border-border/40 bg-card/30 p-5 shadow-sm">
    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-1">
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
    <div>{children}</div>
  </div>
);

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

  const portfolioEquityData = useMemo<EquityPoint[]>(() => {
    if (!portfolioData) return [];
    return Object.entries(portfolioData.equity_curve).map(([date, value]) => ({
      date,
      value,
      return_pct: Number(portfolioData.daily_returns[date] ?? 0),
      drawdown_pct: 0,
    }));
  }, [portfolioData]);

  const singleEquityData = useMemo<EquityPoint[]>(() => {
    if (!chartData?.equity_data) return [];
    return chartData.equity_data.map(point => ({
      date: point.date,
      value: point.value,
      return_pct: Number(point.return_pct ?? (point as Record<string, unknown>).return ?? 0),
      drawdown_pct: Number(point.drawdown_pct ?? (point as Record<string, unknown>).drawdown ?? 0),
    }));
  }, [chartData?.equity_data]);

  const singleTrades = useMemo<TradeMarker[]>(() => {
    if (!chartData?.trade_markers) return [];
    return chartData.trade_markers.map(marker => ({
      ...marker,
      type: marker.type === 'entry' ? 'entry' : 'exit',
    }));
  }, [chartData?.trade_markers]);

  const singleOhlcData = useMemo<OhlcPoint[]>(() => {
    if (!chartData?.ohlc_data) return [];
    return chartData.ohlc_data.map(point => ({
      ...point,
      volume: Number(point.volume ?? 0),
    }));
  }, [chartData?.ohlc_data]);

  const statsPayload = useMemo<Record<string, unknown>>(() => {
    if (portfolioData) {
      return { ...portfolioData.portfolio_statistics } as Record<string, unknown>;
    }
    return chartData?.summary_stats ?? {};
  }, [portfolioData, chartData?.summary_stats]);

  const renderPortfolioCharts = (): React.ReactNode[] | null => {
    if (!portfolioData) return null;
    const { portfolio_composition } = portfolioData;
    const isMultipleStocks = portfolio_composition.length > 1;

    const cards: React.ReactNode[] = [
      (
        <ResultBlock
          title="누적 자산 가치"
          description="기간 동안 누적 자산 가치 변화를 확인하세요"
          key="portfolio-equity"
        >
          <ResponsiveContainer width="100%" height={360}>
            <AreaChart data={portfolioEquityData}>
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
        </ResultBlock>
      ),
      (
        <ResultBlock
          title="일일 수익률"
          description="일별 수익률 변동을 살펴보며 변동성을 파악하세요"
          key="portfolio-daily"
        >
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={portfolioEquityData}>
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
        </ResultBlock>
      ),
      (
        <ResultBlock
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
          key="portfolio-prices"
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
        </ResultBlock>
      ),
    ];

    return cards;
  };

  const renderSingleStockCharts = (): React.ReactNode[] | null => {
    if (!chartData) return null;
    const cards: React.ReactNode[] = [
      (
        <ResultBlock title="OHLC 차트" description="가격 변동과 거래 시그널을 확인하세요" key="single-ohlc">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyOHLCChart
              data={singleOhlcData as any}
              indicators={(chartData.indicators ?? []) as any}
              trades={singleTrades as any}
            />
          </Suspense>
        </ResultBlock>
      ),
      (
        <ResultBlock title="누적 수익률" description="전략의 누적 수익률을 확인하세요" key="single-equity">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyEquityChart data={singleEquityData as any} />
          </Suspense>
        </ResultBlock>
      ),
      (
        <ResultBlock
          title="개별 주가"
          description="백테스트 기간 동안의 주가 흐름"
          key="single-prices"
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
        </ResultBlock>
      ),
    ];

    if (singleTrades.length > 0 && chartData.strategy !== 'buy_and_hold') {
      cards.push(
        <ResultBlock title="거래 내역" description="전략이 실행한 체결 신호" key="single-trades">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyTradesChart trades={singleTrades as any} />
          </Suspense>
        </ResultBlock>,
      );
    }

    return cards;
  };

  const chartCards = portfolioData ? renderPortfolioCharts() : renderSingleStockCharts();

  return (
    <div className="space-y-6">
      <Suspense fallback={<ChartLoading height={260} />}>
        <LazyStatsSummary stats={statsPayload} />
      </Suspense>

      <div className="grid gap-6 xl:grid-cols-3">
        {chartCards?.map((card, index) => (
          <div key={index} className="flex flex-col">
            {card}
          </div>
        ))}
      </div>

      <EnhancedChartsSection data={data} isPortfolio={isPortfolio} />
    </div>
  );
});

ChartsSection.displayName = 'ChartsSection';

export default ChartsSection;
