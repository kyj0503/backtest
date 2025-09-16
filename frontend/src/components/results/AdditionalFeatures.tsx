import React from 'react';
import { ChartData, PortfolioData } from '../../types/backtest-results';
import { SectionCard, FormLegend } from '../common';
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

const AdditionalFeatures: React.FC<AdditionalFeaturesProps> = ({ 
  data, 
  isPortfolio, 
  className = "" 
}) => {
  // 포트폴리오 결과인 경우
  const sections = [];

  const addExchangeRateCard = (start: string, end: string) => {
    sections.push(
      <SectionCard
        key="exchange"
        title="환율 추이"
        description="동일 기간의 원/달러 환율 변동"
      >
        <Suspense fallback={<ChartLoading height={260} />}>
          <LazyExchangeRateChart startDate={start} endDate={end} />
        </Suspense>
      </SectionCard>,
    );
  };

  const addNewsCard = (symbols: string[], start: string, end: string) => {
    sections.push(
      <SectionCard
        key="news"
        title="주가 급등락 뉴스"
        description="백테스트 기간 중 주요 뉴스 흐름"
        actions={<FormLegend items={[{ label: symbols.join(' · '), tone: 'muted' }]} />}
      >
        <Suspense fallback={<ChartLoading height={260} />}>
          <LazyStockVolatilityNews symbols={symbols} startDate={start} endDate={end} />
        </Suspense>
      </SectionCard>,
    );
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

  return <div className={`space-y-6 ${className}`.trim()}>{sections}</div>;
};

export default AdditionalFeatures;
