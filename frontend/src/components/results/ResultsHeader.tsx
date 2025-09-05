import React from 'react';
import { ChartData, PortfolioData, Stock } from '../../types/backtest-results';

interface ResultsHeaderProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ResultsHeader: React.FC<ResultsHeaderProps> = ({ data, isPortfolio }) => {
  // 포트폴리오 결과인 경우
  if (isPortfolio && 'portfolio_composition' in data) {
    const portfolioData = data as PortfolioData;
    const { portfolio_statistics, portfolio_composition } = portfolioData;
    const isMultipleStocks = portfolio_composition.length > 1;

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-2">
          {isMultipleStocks ? '📈 포트폴리오 백테스트 결과' : '📊 단일 종목 백테스트 결과'}
        </h2>
        <p className="text-gray-600">
          {portfolio_composition.map((item: Stock) => item.symbol).join(', ')} | 
          {portfolio_statistics.Start} ~ {portfolio_statistics.End}
        </p>
      </div>
    );
  }

  // 단일 종목 결과인 경우
  const chartData = data as ChartData;
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-2xl font-bold text-blue-600 mb-2">
        📊 {chartData.ticker} - {chartData.strategy} 백테스트 결과
      </h2>
      <p className="text-gray-600">상세한 차트 분석과 거래 내역을 확인하세요</p>
    </div>
  );
};

export default ResultsHeader;
