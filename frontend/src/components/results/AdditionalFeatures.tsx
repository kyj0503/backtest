import React from 'react';
import ExchangeRateChart from '../ExchangeRateChart';
import StockVolatilityNews from '../StockVolatilityNews';
import { ChartData, PortfolioData } from '../../types/backtest-results';

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
  if (isPortfolio && 'portfolio_composition' in data) {
    const portfolioData = data as PortfolioData;
    const { portfolio_statistics, portfolio_composition } = portfolioData;

    return (
      <div className={className}>
        {/* 원달러 환율 차트 */}
        <ExchangeRateChart 
          startDate={portfolio_statistics.Start}
          endDate={portfolio_statistics.End}
          className="mb-8"
        />

        {/* 주가 급등/급락 뉴스 */}
        <StockVolatilityNews
          symbols={portfolio_composition.map(item => {
            // 포트폴리오에서 심볼 뒤의 인덱스(_0, _1 등)를 제거
            return item.symbol.replace(/_\d+$/, '');
          })}
          startDate={portfolio_statistics.Start}
          endDate={portfolio_statistics.End}
          className="mb-8"
        />
      </div>
    );
  }

  // 단일 종목 결과인 경우
  const chartData = data as ChartData;
  
  if (!chartData.ticker || !chartData.start_date || !chartData.end_date) {
    return null;
  }

  return (
    <div className={className}>
      {/* 원달러 환율 차트 */}
      <ExchangeRateChart 
        startDate={chartData.start_date}
        endDate={chartData.end_date}
        className="mb-8"
      />

      {/* 주가 급등/급락 뉴스 */}
      <StockVolatilityNews
        symbols={[chartData.ticker]}
        startDate={chartData.start_date}
        endDate={chartData.end_date}
        className="mb-8"
      />
    </div>
  );
};

export default AdditionalFeatures;
