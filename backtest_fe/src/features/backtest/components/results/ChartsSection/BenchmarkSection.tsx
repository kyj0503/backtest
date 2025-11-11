/**
 * 벤치마크 섹션 컴포넌트
 * S&P 500, NASDAQ 벤치마크 차트
 */

import React, { memo } from 'react';
import BenchmarkIndexChart from '../BenchmarkIndexChart';
import BenchmarkReturnsChart from '../BenchmarkReturnsChart';
import { ResultBlock } from '../../shared';
import { EquityPoint } from '../../../model/types';

interface BenchmarkSectionProps {
  sp500Benchmark: any[];
  nasdaqBenchmark: any[];
  sp500BenchmarkWithReturn: any[];
  nasdaqBenchmarkWithReturn: any[];
  equityDataForBenchmark: EquityPoint[];
  aggregationType?: 'daily' | 'weekly' | 'monthly';
}

export const BenchmarkSection: React.FC<BenchmarkSectionProps> = memo(({
  sp500Benchmark,
  nasdaqBenchmark,
  sp500BenchmarkWithReturn,
  nasdaqBenchmarkWithReturn,
  equityDataForBenchmark,
  aggregationType = 'daily',
}) => {
  const hasBenchmarkData = sp500Benchmark.length > 0 || nasdaqBenchmark.length > 0;

  if (!hasBenchmarkData) {
    return null;
  }

  return (
    <>
      {/* 지수 벤치마크 차트 */}
      <ResultBlock title="벤치마크 비교" description="S&P 500, NASDAQ 지수와 포트폴리오 성과 비교">
        <BenchmarkIndexChart
          sp500Data={sp500Benchmark}
          nasdaqData={nasdaqBenchmark}
          portfolioEquityData={equityDataForBenchmark}
        />
      </ResultBlock>

      {/* 수익률 벤치마크 비교 차트 */}
      <ResultBlock title={`${aggregationType === 'daily' ? '일일' : aggregationType === 'weekly' ? '주간' : '월간'} 수익률 벤치마크 비교`} description="포트폴리오와 벤치마크 지수의 수익률 비교">
        <BenchmarkReturnsChart 
          sp500Data={sp500BenchmarkWithReturn} 
          nasdaqData={nasdaqBenchmarkWithReturn}
          portfolioEquityData={equityDataForBenchmark}
        />
      </ResultBlock>
    </>
  );
});

BenchmarkSection.displayName = 'BenchmarkSection';
