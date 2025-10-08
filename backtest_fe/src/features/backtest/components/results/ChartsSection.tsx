import React, { Suspense, memo, useMemo, useState } from 'react';
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
  LazyExchangeRateChart,
  LazyStockVolatilityNews,
} from '../lazy/LazyChartComponents';
import ChartLoading from '@/shared/components/ChartLoading';
import { useStockData } from '../../hooks/useStockData';
import { ChartData, PortfolioData, EquityPoint, TradeMarker, OhlcPoint } from '../../model/backtest-result-types';
import { FormLegend } from '@/shared/components';
import { Loader2, Grid3X3, Grid } from 'lucide-react';
import { Button } from '@/shared/ui/button';

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
  // 차트 레이아웃 모드 상태 (true: 2열, false: 1열)
  const [isCompactView, setIsCompactView] = useState(true);
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

  // 벤치마크 데이터
  const sp500Benchmark = useMemo<any[]>(
    () => (data as ChartData).sp500_benchmark ?? (data as PortfolioData).sp500_benchmark ?? [],
    [data],
  );

  const nasdaqBenchmark = useMemo<any[]>(
    () => (data as ChartData).nasdaq_benchmark ?? (data as PortfolioData).nasdaq_benchmark ?? [],
    [data],
  );

  const formatDateTick = (value: string) => {
    const date = new Date(value);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  const withBenchmarkReturn = (points: any[]) =>
    points?.map((point, index) => {
      if (index === 0) {
        return { ...point, return_pct: 0 };
      }
      const prev = points[index - 1];
      const returnPct = ((point.close - prev.close) / prev.close) * 100;
      return { ...point, return_pct: returnPct };
    }) ?? [];

  // 날짜 정보
  const startDate = portfolioData
    ? portfolioData.portfolio_statistics.Start
    : chartData?.start_date ?? '';
  const endDate = portfolioData
    ? portfolioData.portfolio_statistics.End
    : chartData?.end_date ?? '';

  // 심볼 정보
  const newsSymbols = useMemo(() => {
    if (portfolioData) {
      return Array.from(
        new Set(portfolioData.portfolio_composition.map(item => item.symbol.replace(/_\d+$/, ''))),
      );
    }
    return chartData?.ticker ? [chartData.ticker] : [];
  }, [portfolioData, chartData?.ticker]);

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
        <ResultBlock title="수익률 & 드로우다운 차트" description="전략의 누적 수익률과 드로우다운을 확인하세요" key="single-equity">
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
            <LazyTradesChart trades={singleTrades as any} showCard={false} />
          </Suspense>
        </ResultBlock>,
      );
    }

    return cards;
  };

  // 모든 차트를 하나의 배열로 통합
  const renderAllCharts = (): React.ReactNode[] => {
    const allCharts: React.ReactNode[] = [];
    
    // 1. 기본 차트 추가 (OHLC, 누적 수익률, 개별 주가, 거래 내역)
    const baseCharts = portfolioData ? renderPortfolioCharts() : renderSingleStockCharts();
    if (baseCharts) {
      allCharts.push(...baseCharts);
    }

    // 2. 벤치마크 차트
    if (sp500Benchmark.length > 0) {
      allCharts.push(
        <ResultBlock
          title="S&P 500 벤치마크"
          description="지수 수준과 일일 수익률을 함께 확인하세요"
          actions={<FormLegend items={[{ label: '좌측: 지수 · 우측: 일일 수익률', tone: 'muted' }]} />}
          key="sp500"
        >
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={withBenchmarkReturn(sp500Benchmark)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDateTick} />
              <YAxis yAxisId="left" orientation="left" />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => `${value.toFixed(1)}%`} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === 'close') return [value.toFixed(2), '지수'];
                  if (name === 'return_pct') return [`${value.toFixed(2)}%`, '일일 수익률'];
                  return [value, name];
                }}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Area yAxisId="left" type="monotone" dataKey="close" stroke="#3b82f6" fillOpacity={0.15} fill="#3b82f6" />
              <Line yAxisId="right" type="monotone" dataKey="return_pct" stroke="#ef4444" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ResultBlock>
      );
    }

    if (nasdaqBenchmark.length > 0) {
      allCharts.push(
        <ResultBlock
          title="NASDAQ 벤치마크"
          description="지수 수준과 일일 수익률을 함께 확인하세요"
          actions={<FormLegend items={[{ label: '좌측: 지수 · 우측: 일일 수익률', tone: 'muted' }]} />}
          key="nasdaq"
        >
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={withBenchmarkReturn(nasdaqBenchmark)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDateTick} />
              <YAxis yAxisId="left" orientation="left" />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => `${value.toFixed(1)}%`} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === 'close') return [value.toFixed(2), '지수'];
                  if (name === 'return_pct') return [`${value.toFixed(2)}%`, '일일 수익률'];
                  return [value, name];
                }}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Area yAxisId="left" type="monotone" dataKey="close" stroke="#3b82f6" fillOpacity={0.15} fill="#3b82f6" />
              <Line yAxisId="right" type="monotone" dataKey="return_pct" stroke="#ef4444" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ResultBlock>
      );
    }

    // 3. 환율 차트
    if (startDate && endDate) {
      allCharts.push(
        <ResultBlock
          title="환율 추이"
          description="동일 기간의 원/달러 환율 변동"
          key="exchange-rate"
        >
          <Suspense fallback={<ChartLoading height={260} />}>
            <LazyExchangeRateChart startDate={startDate} endDate={endDate} showCard={false} />
          </Suspense>
        </ResultBlock>
      );
    }

    return allCharts;
  };

  const allChartCards = renderAllCharts();

  // 뉴스 섹션 (별도 렌더링, 전체 너비)
  const renderNewsSection = () => {
    if (!startDate || !endDate || newsSymbols.length === 0) return null;

    return (
      <ResultBlock
        title="주가 급등락 뉴스"
        description="백테스트 기간 중 주요 뉴스 흐름"
        actions={<FormLegend items={[{ label: newsSymbols.join(' · '), tone: 'muted' }]} />}
        key="news"
      >
        <Suspense fallback={<ChartLoading height={260} />}>
          <LazyStockVolatilityNews symbols={newsSymbols} startDate={startDate} endDate={endDate} />
        </Suspense>
      </ResultBlock>
    );
  };

  return (
    <div className="space-y-6">
      {/* 1. 성과 지표 */}
      <Suspense fallback={<ChartLoading height={260} />}>
        <LazyStatsSummary stats={statsPayload} />
      </Suspense>

      {/* 2. 분석 차트 */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-foreground">분석 차트</h3>
          <p className="text-sm text-muted-foreground">
            백테스트 결과를 다양한 차트로 분석하세요
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsCompactView(!isCompactView)}
          className="flex items-center gap-2"
        >
          {isCompactView ? (
            <>
              <Grid className="w-4 h-4" />
              넓게 보기
            </>
          ) : (
            <>
              <Grid3X3 className="w-4 h-4" />
              컴팩트 보기
            </>
          )}
        </Button>
      </div>

      {/* 모든 분석 차트 (OHLC, 수익률, 주가, 거래내역, 벤치마크, 환율) */}
      <div className={`grid gap-6 ${isCompactView ? 'md:grid-cols-2' : 'md:grid-cols-1'}`}>
        {allChartCards.map((card, index) => (
          <div key={index} className="flex flex-col">
            {card}
          </div>
        ))}
      </div>

      {/* 3. 뉴스 섹션 (전체 너비) */}
      {renderNewsSection()}
    </div>
  );
});

ChartsSection.displayName = 'ChartsSection';

export default ChartsSection;
