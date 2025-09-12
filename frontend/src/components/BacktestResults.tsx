import React from 'react';
import ResultsHeader from './results/ResultsHeader';
import ChartsSection from './results/ChartsSection';
import AdditionalFeatures from './results/AdditionalFeatures';
import { BacktestResultsProps } from '../types/backtest-results';
import { Card, CardContent } from './ui/card';
import { AlertCircle } from 'lucide-react';

const BacktestResults: React.FC<BacktestResultsProps> = ({ data, isPortfolio }) => {
  // 데이터 유효성 검사
  if (!data) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card className="text-center py-16">
          <CardContent className="pt-6">
            <div className="w-16 h-16 mx-auto mb-6 flex items-center justify-center bg-yellow-100 rounded-full">
              <AlertCircle className="h-8 w-8 text-yellow-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">데이터가 없습니다</h3>
            <p className="text-muted-foreground">백테스트를 실행해 주세요.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 포트폴리오 데이터 유효성 검사
  if (isPortfolio && (!('portfolio_composition' in data) || !data.portfolio_composition)) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card className="text-center py-16">
          <CardContent className="pt-6">
            <div className="w-16 h-16 mx-auto mb-6 flex items-center justify-center bg-yellow-100 rounded-full">
              <AlertCircle className="h-8 w-8 text-yellow-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">포트폴리오 데이터가 없습니다</h3>
            <p className="text-muted-foreground">유효한 포트폴리오를 구성해 주세요.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* 헤더 */}
      <ResultsHeader data={data} isPortfolio={isPortfolio} />

      {/* 차트 섹션 */}
      <ChartsSection data={data} isPortfolio={isPortfolio} />

      {/* 추가 기능 (뉴스, 환율 등) */}
      <AdditionalFeatures data={data} isPortfolio={isPortfolio} />
    </div>
  );
};

export default BacktestResults;
