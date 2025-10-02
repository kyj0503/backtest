import React, { useRef } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import ResultsHeader from './results/ResultsHeader';
import ChartsSection from './results/ChartsSection';
import AdditionalFeatures from './results/AdditionalFeatures';
import { BacktestResultsProps } from '../model/backtest-result-types';
import { AlertCircle, FileImage, FileText } from 'lucide-react';
import { Button } from '@/shared/ui/button';

const BacktestResults: React.FC<BacktestResultsProps> = ({ data, isPortfolio }) => {
  const resultsRef = useRef<HTMLDivElement>(null);

  const downloadAsImage = async () => {
    if (!resultsRef.current) {
      console.error('No element to capture');
      return;
    }
    try {
      const canvas = await html2canvas(resultsRef.current, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
      });
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `backtest-results-${new Date().toISOString().split('T')[0]}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Image download failed:', error);
      alert('이미지 다운로드에 실패했습니다. 콘솔을 확인하세요.');
    }
  };

  const downloadAsPDF = async () => {
    if (!resultsRef.current) {
      console.error('No element to capture');
      return;
    }
    try {
      const canvas = await html2canvas(resultsRef.current, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
      });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 210;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      // 한 페이지에 맞추기 위해 높이 조정
      const pageHeight = 297;
      if (imgHeight > pageHeight) {
        // 여러 페이지로 나누기
        let remainingHeight = imgHeight;
        while (remainingHeight > 0) {
          const sliceHeight = Math.min(remainingHeight, pageHeight);
          const sliceY = imgHeight - remainingHeight;
          pdf.addImage(imgData, 'PNG', 0, -sliceY, imgWidth, imgHeight, '', 'FAST');
          remainingHeight -= sliceHeight;
          if (remainingHeight > 0) {
            pdf.addPage();
          }
        }
      } else {
        pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
      }

      pdf.save(`backtest-results-${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (error) {
      console.error('PDF download failed:', error);
      alert('PDF 다운로드에 실패했습니다. 콘솔을 확인하세요.');
    }
  };

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
    <div ref={resultsRef} className="mx-auto w-full max-w-screen-2xl space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <ResultsHeader data={data} isPortfolio={isPortfolio} />
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={downloadAsImage}>
            <FileImage className="w-4 h-4 mr-2" />
            이미지 다운로드
          </Button>
          <Button variant="outline" size="sm" onClick={downloadAsPDF}>
            <FileText className="w-4 h-4 mr-2" />
            PDF 다운로드
          </Button>
        </div>
      </div>

      <section className="space-y-8 rounded-[32px] border border-border/40 bg-card/30 p-8 shadow-sm">
        <ChartsSection data={data} isPortfolio={isPortfolio} />
        <AdditionalFeatures data={data} isPortfolio={isPortfolio} />
      </section>
    </div>
  );
};

export default BacktestResults;
