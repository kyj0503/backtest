/**
 * useChartData 입력 선택 헬퍼
 *
 * 백테스트 응답(포트폴리오/단일 종목)에서 차트가 쓸 원본 조각을 골라내고,
 * 백테스트 기간으로 샘플링 단위를 판정한다. 값을 줄이거나 재구성하는 일은
 * chartSeriesBuilders.ts가 맡는다. React에 의존하지 않는 순수 함수만 둔다.
 */

import type { ChartData, PortfolioData, StockDataItem } from '../../model/types';
import { smartSampleByPeriod } from '@/shared/utils/dataSampling';
import type { AggregationType } from '@/shared/utils/dataSampling';

export interface ChartDateRange {
  startDate: string | undefined;
  endDate: string | undefined;
}

export interface SamplingMeta {
  aggregationType: AggregationType;
  samplingWarning: string | undefined;
}

/**
 * 백테스트 날짜 범위 추출 (포트폴리오: 통계의 Start/End, 단일 종목: start_date/end_date)
 */
export function resolveDateRange(
  isPortfolio: boolean,
  portfolioData: PortfolioData | null,
  chartData: ChartData | null
): ChartDateRange {
  if (isPortfolio && portfolioData) {
    return {
      startDate: portfolioData.portfolio_statistics.Start,
      endDate: portfolioData.portfolio_statistics.End,
    };
  }
  if (!isPortfolio && chartData) {
    return {
      startDate: chartData.start_date,
      endDate: chartData.end_date,
    };
  }
  return { startDate: undefined, endDate: undefined };
}

/**
 * 백테스트 기간으로 샘플링 단위(일간/주간/월간)와 경고를 판정
 */
export function resolveSamplingMeta(startDate?: string, endDate?: string): SamplingMeta {
  if (!startDate || !endDate) {
    return { aggregationType: 'daily' as const, samplingWarning: undefined };
  }

  // 임시 데이터로 샘플링 전략 확인
  const { aggregationType: type, warning } = smartSampleByPeriod(
    [{ date: startDate }],
    startDate,
    endDate
  );

  return { aggregationType: type, samplingWarning: warning };
}

/**
 * 종목별 주가 시계열 수집 (샘플링 전 원본)
 *
 * 포트폴리오는 stock_data 전체를, 단일 종목은 자기 티커의 시계열만 쓴다.
 */
export function collectStocksData(
  data: ChartData | PortfolioData,
  portfolioData: PortfolioData | null,
  chartData: ChartData | null
): StockDataItem[] {
  let rawStocksData: StockDataItem[] = [];

  if (portfolioData?.stock_data) {
    rawStocksData = Object.entries(portfolioData.stock_data).map(([symbol, data]) => ({
      symbol,
      data,
    }));
  } else if (chartData?.ticker && 'stock_data' in data) {
    const portfolioStyleData = data as PortfolioData;
    const stockData = portfolioStyleData.stock_data?.[chartData.ticker];
    if (stockData) {
      rawStocksData = [{ symbol: chartData.ticker, data: stockData }];
    }
  }

  return rawStocksData;
}

/**
 * 종목별 목록 중 하나라도 비어 있지 않은지 (급등락/뉴스 표시 여부)
 */
export function hasAnyEntries<T>(bySymbol: Record<string, T[]>): boolean {
  return Object.keys(bySymbol).some(
    symbol => bySymbol[symbol] && bySymbol[symbol].length > 0
  );
}
