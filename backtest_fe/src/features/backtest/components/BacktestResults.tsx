import React, { useRef } from 'react';
import ChartsSection from './results/ChartsSection';
import WarningBanner from './results/WarningBanner';
import { BacktestResultsProps } from '../model/types/backtest-result-types';
import { AlertCircle, FileDown, FileSpreadsheet } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { HEADING_STYLES, TEXT_STYLES } from '@/shared/styles/design-tokens';
import { generateTextReport, generateCSVReport } from '../services/reportGenerator';

const BacktestResults: React.FC<BacktestResultsProps> = ({ data, isPortfolio }) => {
  const resultsRef = useRef<HTMLDivElement>(null);

  const downloadAsTextReport = () => {
    try {
      const reportText = generateTextReport(data, isPortfolio);
      const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `backtest-report-${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Report download failed:', error);
      alert('리포트 다운로드에 실패했습니다. 콘솔을 확인하세요.');
    }
  };

  const downloadAsCSV = () => {
    try {
      const csvContent = generateCSVReport(data, isPortfolio);
      const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `backtest-report-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('CSV download failed:', error);
      alert('CSV 다운로드에 실패했습니다. 콘솔을 확인하세요.');
    }
  };

  if (!data) {
    return (
      <div className="mx-auto w-full lg:max-w-[1600px] rounded-3xl border-2 border-border/50 bg-card/50 backdrop-blur-sm p-8 sm:p-16 text-center shadow-lg">
        <div className="mx-auto mb-4 sm:mb-6 flex h-16 w-16 sm:h-20 sm:w-20 items-center justify-center rounded-2xl bg-yellow-100 shadow-md">
          <AlertCircle className="h-8 w-8 sm:h-10 sm:w-10 text-yellow-600" />
        </div>
        <h3 className={`${HEADING_STYLES.h1} mb-3 text-xl sm:text-2xl`}>데이터가 없습니다</h3>
        <p className={`${TEXT_STYLES.body} text-sm sm:text-base`}>백테스트를 실행해 주세요.</p>
      </div>
    );
  }

  if (isPortfolio && (!('portfolio_composition' in data) || !data.portfolio_composition)) {
    return (
      <div className="mx-auto w-full lg:max-w-[1600px] rounded-3xl border-2 border-border/50 bg-card/50 backdrop-blur-sm p-8 sm:p-16 text-center shadow-lg">
        <div className="mx-auto mb-4 sm:mb-6 flex h-16 w-16 sm:h-20 sm:w-20 items-center justify-center rounded-2xl bg-yellow-100 shadow-md">
          <AlertCircle className="h-8 w-8 sm:h-10 sm:w-10 text-yellow-600" />
        </div>
        <h3 className={`${HEADING_STYLES.h1} mb-3 text-xl sm:text-2xl`}>포트폴리오 데이터가 없습니다</h3>
        <p className={`${TEXT_STYLES.body} text-sm sm:text-base`}>유효한 포트폴리오를 구성해 주세요.</p>
      </div>
    );
  }

  return (
    <div ref={resultsRef} className="mx-auto w-full lg:max-w-screen-2xl space-y-4 sm:space-y-6 mt-6 sm:mt-8">
      {isPortfolio && 'warnings' in data && data.warnings && data.warnings.length > 0 && (
        <WarningBanner warnings={data.warnings} />
      )}

      <div className="flex justify-end gap-2 px-1 sm:px-3 lg:px-0 mb-4 sm:mb-6">
        <Button variant="outline" size="default" onClick={downloadAsCSV} className="shadow-sm text-xs sm:text-sm">
          <FileSpreadsheet className="w-3 h-3 sm:w-4 sm:h-4 mr-2" />
          CSV 다운로드
        </Button>
        <Button variant="outline" size="default" onClick={downloadAsTextReport} className="shadow-sm text-xs sm:text-sm">
          <FileDown className="w-3 h-3 sm:w-4 sm:h-4 mr-2" />
          텍스트 리포트
        </Button>
      </div>

      <ChartsSection data={data} isPortfolio={isPortfolio} />
    </div>
  );
};

export default BacktestResults;
