/**
 * useChartData 시계열 변환 헬퍼
 *
 * 차트별 원본 시계열을 백테스트 기간에 맞게 줄이거나 재구성한다.
 * - 가격류(주가, OHLC, 환율, 비중): 기간 기반 단순 샘플링 (sampleByDateRange)
 * - 수익률이 있는 시계열(포트폴리오/단일 종목 equity, 벤치마크):
 *   일간이면 단순 샘플링, 주간/월간이면 수익률을 복리로 집계한 뒤
 *   그 버킷 날짜에 맞춰 원본 포인트를 다시 붙인다 (alignToReturnBuckets)
 *
 * React에 의존하지 않는 순수 함수만 둔다.
 */

import type {
  ChartData, PortfolioData, EquityPoint, BenchmarkSeriesPoint,
} from '../../model/types';
import {
  transformPortfolioEquityData,
  transformSingleEquityData,
  extractBenchmarkData,
} from '../../utils';
import { smartSampleByPeriod, aggregateReturns } from '@/shared/utils/dataSampling';
import type { AggregationType } from '@/shared/utils/dataSampling';

type ReturnBucket = { date: string; return_pct: number };

/**
 * 이진 탐색을 통해 특정 날짜에 해당하거나 그 이전의 데이터 포인트 찾기
 *
 * @param sortedData 날짜 기준 오름차순 정렬된 데이터 배열
 * @param targetDate 검색 대상 날짜
 * @returns 해당 날짜 또는 그 이전 데이터 포인트, 없으면 null
 *
 * @example
 * const point = findDataPointOnOrBefore(sortedData, '2024-11-01');
 */
function findDataPointOnOrBefore<T extends { date: string }>(
  sortedData: T[],
  targetDate: string
): T | null {
  if (sortedData.length === 0) return null;

  let left = 0, right = sortedData.length - 1;
  let result: T | null = null;

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    const midItem = sortedData[mid];
    if (!midItem) break;
    if (midItem.date <= targetDate) {
      result = midItem;
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }

  return result;
}

/**
 * 날짜 범위가 있으면 기간 기반 스마트 샘플링, 없으면 원본 그대로
 */
export function sampleByDateRange<T extends { date: string }>(
  rawData: T[],
  startDate?: string,
  endDate?: string
): T[] {
  if (startDate && endDate) {
    const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
    return sampledData;
  }
  return rawData;
}

/**
 * 집계된 수익률 버킷의 날짜에 맞춰 원본 시계열을 재구성
 *
 * 버킷 날짜에 원본 포인트가 없으면 그 이전 마지막 관측값을 쓰고, 그것도
 * 없으면 onMissing이 만든 포인트를 넣는다. 날짜는 버킷 날짜로, return_pct는
 * 집계 수익률로 덮어쓴다.
 */
function alignToReturnBuckets<T extends { date: string }, M>(
  rawData: T[],
  aggregatedReturns: ReturnBucket[],
  onMissing: (bucket: ReturnBucket) => M
): Array<(T & ReturnBucket) | M> {
  const dataByDate = new Map(rawData.map(item => [item.date, item]));
  const sortedRawData = [...rawData].sort((a, b) =>
    a.date < b.date ? -1 : a.date > b.date ? 1 : 0
  );

  return aggregatedReturns.map(r => {
    const item = dataByDate.get(r.date) ?? findDataPointOnOrBefore(sortedRawData, r.date);
    if (!item) {
      return onMissing(r);
    }
    return {
      ...item,
      date: r.date, // 집계 날짜로 덮어씀
      return_pct: r.return_pct,
    };
  });
}

/**
 * equity 포인트가 버킷 날짜 이전에 하나도 없을 때 넣는 값 없는 포인트 (경고 로그 포함)
 */
function missingEquityPoint(label: string) {
  return (r: ReturnBucket): EquityPoint => {
    console.warn(`[${label}] ${r.date} 날짜의 equity 데이터 없음 (집계수익률=${r.return_pct}%)`);
    return {
      date: r.date,
      value: undefined,
      return_pct: r.return_pct,
      drawdown_pct: 0,
    };
  };
}

/**
 * 포트폴리오 equity 시계열 (스마트 샘플링 + 수익률 복리 집계)
 */
export function buildPortfolioEquitySeries(
  portfolioData: PortfolioData,
  startDate: string | undefined,
  endDate: string | undefined,
  aggregationType: AggregationType
): EquityPoint[] {
  // 원본 데이터 변환
  const rawEquityData = transformPortfolioEquityData(
    portfolioData.equity_curve,
    portfolioData.daily_returns
  );

  // 날짜 범위가 없으면 원본 반환
  if (!startDate || !endDate) {
    return rawEquityData;
  }

  // 일간 집계: 기존 샘플링 방식 사용
  if (aggregationType === 'daily') {
    return sampleByDateRange(rawEquityData, startDate, endDate);
  }

  // 주간/월간 집계: 수익률의 날짜에 맞춰 equity 데이터 재구성
  const dailyReturnsArray = Object.entries(portfolioData.daily_returns).map(([date, return_pct]) => ({
    date,
    return_pct: return_pct as number,
  }));

  const aggregatedReturns = aggregateReturns(dailyReturnsArray, aggregationType);

  return alignToReturnBuckets(rawEquityData, aggregatedReturns, missingEquityPoint('포트폴리오 차트'));
}

/**
 * 단일 종목 equity 시계열 (스마트 샘플링 + 수익률 복리 집계)
 */
export function buildSingleEquitySeries(
  equityData: EquityPoint[],
  startDate: string | undefined,
  endDate: string | undefined,
  aggregationType: AggregationType
): EquityPoint[] {
  // 원본 데이터 변환
  const rawData = transformSingleEquityData(equityData);

  // 날짜 범위가 없으면 원본 반환
  if (!startDate || !endDate) {
    return rawData;
  }

  // 일간 집계: 기존 샘플링 방식 사용
  if (aggregationType === 'daily') {
    return sampleByDateRange(rawData, startDate, endDate);
  }

  // 주간/월간 집계: 수익률의 날짜에 맞춰 equity 데이터 재구성
  // EquityPoint.return_pct는 리밸런싱 마커 포인트에서 null일 수 있지만
  // (PortfolioCharts.tsx 참고), rawData는 원본 equity curve에서 바로
  // 변환된 값이라 이 경로에서는 실제로 null이 나타나지 않는다.
  // aggregateReturns가 number를 요구하므로 방어적으로 0을 대입한다.
  const dailyReturnsArray = rawData.map(point => ({
    date: point.date,
    return_pct: point.return_pct ?? 0,
  }));

  const aggregatedReturns = aggregateReturns(dailyReturnsArray, aggregationType);

  return alignToReturnBuckets(rawData, aggregatedReturns, missingEquityPoint('단일종목 차트'));
}

const BENCHMARK_LABELS: Record<'sp500' | 'nasdaq', string> = {
  sp500: 'S&P 500 벤치마크',
  nasdaq: 'NASDAQ 벤치마크',
};

/**
 * 벤치마크 시계열 (스마트 샘플링 + 수익률 복리 집계)
 *
 * 백엔드가 return_pct를 계산해서 보내므로 그대로 집계에 사용한다.
 */
export function buildBenchmarkSeries(
  data: ChartData | PortfolioData,
  benchmarkType: 'sp500' | 'nasdaq',
  startDate: string | undefined,
  endDate: string | undefined,
  aggregationType: AggregationType
): BenchmarkSeriesPoint[] {
  const rawData = extractBenchmarkData(data, benchmarkType);
  if (!startDate || !endDate || rawData.length === 0) {
    return rawData;
  }

  // 일간 집계: 기존 샘플링 방식
  if (aggregationType === 'daily') {
    return sampleByDateRange(rawData, startDate, endDate);
  }

  // 주간/월간 집계: 수익률의 날짜에 맞춰 데이터 재구성
  const dailyReturnsArray = rawData.map(point => ({
    date: point.date,
    return_pct: (point as BenchmarkSeriesPoint).return_pct ?? 0,
  }));

  const aggregatedReturns = aggregateReturns(dailyReturnsArray, aggregationType);

  return alignToReturnBuckets(rawData, aggregatedReturns, r => {
    console.warn(`[${BENCHMARK_LABELS[benchmarkType]}] ${r.date} 날짜의 데이터 없음 (집계수익률=${r.return_pct}%)`);
    return { date: r.date, close: 0, return_pct: r.return_pct };
  });
}
