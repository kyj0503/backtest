/**
 * 벤치마크 섹션 컴포넌트
 * S&P 500, NASDAQ 벤치마크 차트
 */

import React from 'react';
import BenchmarkIndexChart from '../BenchmarkIndexChart';
import BenchmarkReturnsChart from '../BenchmarkReturnsChart';
import { EquityPoint } from '../../../model/types';

interface BenchmarkSectionProps {
  sp500Benchmark: any[];
  nasdaqBenchmark: any[];
  sp500BenchmarkWithReturn: any[];
  nasdaqBenchmarkWithReturn: any[];
  equityDataForBenchmark: EquityPoint[];
}

export const BenchmarkSection: React.FC<BenchmarkSectionProps> = ({
  sp500Benchmark,
  nasdaqBenchmark,
  sp500BenchmarkWithReturn,
  nasdaqBenchmarkWithReturn,
  equityDataForBenchmark,
}) => {
  const hasBenchmarkData = sp500Benchmark.length > 0 || nasdaqBenchmark.length > 0;

  if (!hasBenchmarkData) {
    return null;
  }

  return (
    <>
      {/* 지수 벤치마크 차트 */}
      <BenchmarkIndexChart
        sp500Data={sp500Benchmark}
        nasdaqData={nasdaqBenchmark}
        portfolioEquityData={equityDataForBenchmark}
      />

      {/* 일일 수익률 벤치마크 차트 */}
      <BenchmarkReturnsChart sp500Data={sp500BenchmarkWithReturn} nasdaqData={nasdaqBenchmarkWithReturn} />
    </>
  );
};
