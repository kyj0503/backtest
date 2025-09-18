import React from 'react';
import ResultsHeader from './results/ResultsHeader';
import ChartsSection from './results/ChartsSection';
import AdditionalFeatures from './results/AdditionalFeatures';
import { BacktestResultsProps } from '../model/backtest-result-types';
import { AlertCircle } from 'lucide-react';

const BacktestResults: React.FC<BacktestResultsProps> = ({ data, isPortfolio }) => {
  // 데이터 유효성 검사
  if (!data) {
    return (
      <div className="mx-auto max-w-[1600px] rounded-[32px] border border-border/40 bg-card/30 p-12 text-center shadow-sm">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
          <AlertCircle className="h-8 w-8 text-yellow-600" />
        </div>
        <h3 className="text-xl font-semibold mb-2">데이터가 없습니다</h3>
        <p className="text-sm text-muted-foreground">백테스트를 실행해 주세요.</p>
      </div>
    );
  }

  // 포트폴리오 데이터 유효성 검사
  if (isPortfolio && (!('portfolio_composition' in data) || !data.portfolio_composition)) {
    return (
      <div className="mx-auto max-w-[1600px] rounded-[32px] border border-border/40 bg-card/30 p-12 text-center shadow-sm">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
          <AlertCircle className="h-8 w-8 text-yellow-600" />
        </div>
        <h3 className="text-xl font-semibold mb-2">포트폴리오 데이터가 없습니다</h3>
        <p className="text-sm text-muted-foreground">유효한 포트폴리오를 구성해 주세요.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-8">
      {/* 헤더 */}
      <ResultsHeader data={data} isPortfolio={isPortfolio} />

      <section className="space-y-8 rounded-[32px] border border-border/40 bg-card/30 p-8 shadow-sm">
        <ChartsSection data={data} isPortfolio={isPortfolio} />
        <AdditionalFeatures data={data} isPortfolio={isPortfolio} />
      </section>
    </div>
  );
};

export default BacktestResults;
