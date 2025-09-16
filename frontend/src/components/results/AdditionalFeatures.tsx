import React, { ReactNode } from 'react';
import { ChartData, PortfolioData } from '../../types/backtest-results';
import { FormLegend } from '../common';
import { cn } from '../../lib/utils';
import {
  LazyExchangeRateChart,
  LazyStockVolatilityNews,
} from '../lazy/LazyChartComponents';
import ChartLoading from '../common/ChartLoading';
import { Suspense } from 'react';

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
    addExchangeRateCard(portfolio_statistics.Start, portfolio_statistics.End);
    addNewsCard(symbols, portfolio_statistics.Start, portfolio_statistics.End);
  } else {
    const chartData = data as ChartData;
    if (!chartData.ticker || !chartData.start_date || !chartData.end_date) {
      return null;
    }
    addExchangeRateCard(chartData.start_date, chartData.end_date);
    addNewsCard([chartData.ticker], chartData.start_date, chartData.end_date);
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-2', className)}>
      {sections.map(({ key, node }) => (
        <div key={key}>{node}</div>
      ))}
    </div>
  );
};

export default AdditionalFeatures;
