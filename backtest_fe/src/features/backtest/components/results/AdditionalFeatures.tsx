import React, { ReactNode, Suspense } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
} from 'recharts';
import { ChartData, PortfolioData } from '../../model/backtest-result-types';
import { FormLegend } from '@/shared/components';
import { cn } from '@/shared/lib/core/utils';
import {
  LazyExchangeRateChart,
  LazyStockVolatilityNews,
} from '../lazy/LazyChartComponents';
import ChartLoading from '@/shared/components/ChartLoading';

interface AdditionalFeaturesProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
  className?: string;
}

const FeatureBlock: React.FC<{ title: string; description?: string; actions?: ReactNode; children: ReactNode }> = ({
  title,
  description,
  actions,
  children,
}) => (
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

const AdditionalFeatures: React.FC<AdditionalFeaturesProps> = ({
  data,
  isPortfolio,
  className = '',
}) => {
  // 포트폴리오 결과인 경우
  const sections: Array<{ key: string; node: ReactNode }> = [];

  // 벤치마크 데이터 추출
  const sp500Benchmark = (data as ChartData).sp500_benchmark ?? (data as PortfolioData).sp500_benchmark;
  const nasdaqBenchmark = (data as ChartData).nasdaq_benchmark ?? (data as PortfolioData).nasdaq_benchmark;

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

  const addExchangeRateCard = (start: string, end: string) => {
    sections.push({
      key: 'exchange',
      node: (
        <FeatureBlock
          title="환율 추이"
          description="동일 기간의 원/달러 환율 변동"
        >
          <Suspense fallback={<ChartLoading height={260} />}>
            <LazyExchangeRateChart startDate={start} endDate={end} />
          </Suspense>
        </FeatureBlock>
      ),
    });
  };

  const addBenchmarkCards = () => {
    if (sp500Benchmark && sp500Benchmark.length > 0) {
      sections.push({
        key: 'sp500',
        node: (
          <FeatureBlock
            title="S&P 500 벤치마크"
            description="지수 수준과 일일 수익률을 함께 확인하세요"
            actions={<FormLegend items={[{ label: '좌측: 지수 · 우측: 일일 수익률', tone: 'muted' }]} />}
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
          </FeatureBlock>
        ),
      });
    }

    if (nasdaqBenchmark && nasdaqBenchmark.length > 0) {
      sections.push({
        key: 'nasdaq',
        node: (
          <FeatureBlock
            title="NASDAQ 벤치마크"
            description="지수 수준과 일일 수익률을 함께 확인하세요"
            actions={<FormLegend items={[{ label: '좌측: 지수 · 우측: 일일 수익률', tone: 'muted' }]} />}
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
          </FeatureBlock>
        ),
      });
    }
  };

  const addNewsCard = (symbols: string[], start: string, end: string) => {
    sections.push({
      key: 'news',
      node: (
        <FeatureBlock
          title="주가 급등락 뉴스"
          description="백테스트 기간 중 주요 뉴스 흐름"
          actions={<FormLegend items={[{ label: symbols.join(' · '), tone: 'muted' }]} />}
        >
          <Suspense fallback={<ChartLoading height={260} />}>
            <LazyStockVolatilityNews symbols={symbols} startDate={start} endDate={end} />
          </Suspense>
        </FeatureBlock>
      ),
    });
  };

  if (isPortfolio && 'portfolio_composition' in data) {
    const portfolioData = data as PortfolioData;
    const { portfolio_statistics, portfolio_composition } = portfolioData;
    const symbols = Array.from(
      new Set(portfolio_composition.map(item => item.symbol.replace(/_\d+$/, ''))),
    );
    addBenchmarkCards();
    addExchangeRateCard(portfolio_statistics.Start, portfolio_statistics.End);
    addNewsCard(symbols, portfolio_statistics.Start, portfolio_statistics.End);
  } else {
    const chartData = data as ChartData;
    if (!chartData.ticker || !chartData.start_date || !chartData.end_date) {
      return null;
    }
    addBenchmarkCards();
    addExchangeRateCard(chartData.start_date, chartData.end_date);
    addNewsCard([chartData.ticker], chartData.start_date, chartData.end_date);
  }

  // 뉴스 섹션 분리 (전체 너비 사용)
  const newsSection = sections.find(section => section.key === 'news');
  const otherSections = sections.filter(section => section.key !== 'news');

  return (
    <div className={cn('space-y-6', className)}>
      {/* 다른 섹션들 (2열 그리드) */}
      {otherSections.length > 0 && (
        <div className="grid gap-6 xl:grid-cols-2">
          {otherSections.map(({ key, node }) => (
            <div key={key}>{node}</div>
          ))}
        </div>
      )}

      {/* 뉴스 섹션 (전체 너비) */}
      {newsSection && (
        <div>{newsSection.node}</div>
      )}
    </div>
  );
};

export default AdditionalFeatures;
