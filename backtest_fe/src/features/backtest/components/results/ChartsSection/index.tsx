/**
 * ChartsSection 메인 컴포넌트
 * 백테스트 결과 차트들을 렌더링하는 메인 진입점
 *
 * 구조:
 * - 통계 요약 (StatsSummary)
 * - 포트폴리오/단일 종목 차트 (PortfolioCharts/SingleStockCharts)
 * - 벤치마크 차트 (BenchmarkSection)
 * - 부가 정보 (SupplementaryCharts)
 */

import React, { Suspense, memo, useState } from 'react';
import { Grid3X3, Grid } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { ChartLoading } from '@/shared/components';
import { LazyStatsSummary } from '../../lazy/LazyChartComponents';
import { ChartData, PortfolioData } from '../../../model/types';
import { useChartData } from '../../../hooks/charts/useChartData';
import { PortfolioCharts } from './PortfolioCharts';
import { SingleStockCharts } from './SingleStockCharts';
import { BenchmarkSection } from './BenchmarkSection';
import { SupplementaryCharts } from './SupplementaryCharts';

interface ChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ChartsSection: React.FC<ChartsSectionProps> = memo(({ data, isPortfolio }) => {
  // 차트 레이아웃 모드 상태 (true: 2열, false: 1열)
  const [isCompactView, setIsCompactView] = useState(true);

  // 모든 차트 데이터 변환 (커스텀 훅)
  const chartDataState = useChartData(data, isPortfolio);

  const {
    portfolioData,
    chartData,
    tickerInfo,
    stocksData,
    tradeLogs,
    statsPayload,
    portfolioEquityData,
    singleEquityData,
    singleTrades,
    singleOhlcData,
    sp500Benchmark,
    nasdaqBenchmark,
    sp500BenchmarkWithReturn,
    nasdaqBenchmarkWithReturn,
    exchangeRates,
    exchangeStats,
    volatilityEvents,
    latestNews,
    hasVolatilityEvents,
    hasNews,
    rebalanceHistory,
    weightHistory,
    aggregationType,
    samplingWarning,
  } = chartDataState;

  // 벤치마크용 equity 데이터 선택
  const equityDataForBenchmark = isPortfolio ? portfolioEquityData : singleEquityData;

  // 집계 타입에 따른 라벨
  const aggregationLabel = {
    daily: '일간',
    weekly: '주간',
    monthly: '월간',
  }[aggregationType];

  return (
    <div className="space-y-6">
      {/* 샘플링 경고 표시 */}
      {samplingWarning && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">{samplingWarning}</p>
        </div>
      )}

      {/* 1. 성과 지표 */}
      <Suspense fallback={<ChartLoading height={260} />}>
        <LazyStatsSummary stats={statsPayload} />
      </Suspense>

      {/* 2. 분석 차트 헤더 */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-foreground">분석 차트 ({aggregationLabel} 데이터)</h3>
          <p className="text-sm text-muted-foreground">
            백테스트 결과를 다양한 차트로 분석하세요
            {aggregationType !== 'daily' && ` • ${aggregationLabel} 단위로 집계되었습니다`}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsCompactView(!isCompactView)}
          className="hidden md:flex items-center gap-2"
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

      {/* 3. 모든 분석 차트 */}
      <div
        className={`grid gap-6 ${isCompactView ? 'md:grid-cols-2' : 'md:grid-cols-1'}`}
        style={{
          contain: 'layout style'
        }}
      >
        {/* 3.1 기본 차트 (포트폴리오 또는 단일 종목) */}
        {isPortfolio && portfolioData ? (
          <PortfolioCharts
            portfolioData={portfolioData}
            portfolioEquityData={portfolioEquityData}
            stocksData={stocksData}
            tickerInfo={tickerInfo}
            tradeLogs={tradeLogs}
            aggregationType={aggregationType}
          />
        ) : chartData ? (
          <SingleStockCharts
            chartData={chartData}
            singleEquityData={singleEquityData}
            singleTrades={singleTrades}
            singleOhlcData={singleOhlcData}
            stocksData={stocksData}
            tickerInfo={tickerInfo}
            tradeLogs={tradeLogs}
          />
        ) : null}

        {/* 3.2 벤치마크 차트 */}
        <BenchmarkSection
          sp500Benchmark={sp500Benchmark}
          nasdaqBenchmark={nasdaqBenchmark}
          sp500BenchmarkWithReturn={sp500BenchmarkWithReturn}
          nasdaqBenchmarkWithReturn={nasdaqBenchmarkWithReturn}
          equityDataForBenchmark={equityDataForBenchmark}
          aggregationType={aggregationType}
        />

        {/* 3.3 부가 정보 차트 */}
        <SupplementaryCharts
          exchangeRates={exchangeRates}
          exchangeStats={exchangeStats}
          volatilityEvents={volatilityEvents}
          latestNews={latestNews}
          hasVolatilityEvents={hasVolatilityEvents}
          hasNews={hasNews}
          tickerInfo={tickerInfo}
          rebalanceHistory={rebalanceHistory}
          weightHistory={weightHistory}
          portfolioComposition={portfolioData?.portfolio_composition}
        />
      </div>
    </div>
  );
});

ChartsSection.displayName = 'ChartsSection';

export default ChartsSection;
