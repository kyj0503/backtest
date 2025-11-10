/**
 * ChartsSection 데이터 변환 훅
 *
 * **역할**:
 * - ChartsSection의 복잡한 데이터 변환 로직을 커스텀 훅으로 분리
 * - 백테스트 기간에 따라 스마트 샘플링 적용 (일간/주간/월간)
 * - 가격 데이터: 단순 샘플링 (간격마다 데이터 포인트 추출)
 * - 수익률 데이터: 복리 집계 (여러 일간 수익률을 주간/월간 복리 수익률로 변환)
 *
 * **샘플링 전략**:
 * - 2일~2년: 일간 데이터 (원본 그대로)
 * - 2년~5년: 주간 집계 (7일 간격)
 * - 5년~10년: 월간 집계 (실제 달력 월 기준)
 * - 10년 초과: 월간 집계 + 경고 표시
 * 
 * **복리 계산 대상**:
 * - portfolioEquityData.return_pct
 * - singleEquityData.return_pct
 * - sp500Benchmark.return_pct
 * - nasdaqBenchmark.return_pct
 */

import { useMemo } from 'react';
import { ChartData, PortfolioData, EquityPoint, TradeMarker, OhlcPoint } from '../../model/types';
import {
  transformPortfolioEquityData,
  transformSingleEquityData,
  transformTradeMarkers,
  transformOhlcData,
  extractTradeLogs,
  extractBenchmarkData,
  extractStatsPayload,
} from '../../utils';
import { smartSampleByPeriod, aggregateReturns } from '@/shared/utils/dataSampling';

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
    if (sortedData[mid].date <= targetDate) {
      result = sortedData[mid];
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }
  
  return result;
}

export interface UseChartDataReturn {
  // 데이터 타입 구분
  portfolioData: PortfolioData | null;
  chartData: ChartData | null;
  isPortfolio: boolean;

  // 공통 데이터
  tickerInfo: Record<string, any>;
  stocksData: Array<{ symbol: string; data: any[] }>;
  tradeLogs: Record<string, any[]>;
  statsPayload: Record<string, unknown>;

  // 포트폴리오 데이터
  portfolioEquityData: EquityPoint[];

  // 단일 종목 데이터
  singleEquityData: EquityPoint[];
  singleTrades: TradeMarker[];
  singleOhlcData: OhlcPoint[];

  // 벤치마크 데이터
  sp500Benchmark: any[];
  nasdaqBenchmark: any[];
  sp500BenchmarkWithReturn: any[];
  nasdaqBenchmarkWithReturn: any[];

  // 환율 데이터
  exchangeRates: any[];
  exchangeStats: any;

  // 급등락/뉴스 데이터
  volatilityEvents: Record<string, any[]>;
  latestNews: Record<string, any[]>;
  hasVolatilityEvents: boolean;
  hasNews: boolean;

  // 리밸런싱 데이터
  rebalanceHistory: any[];
  weightHistory: any[];

  // 샘플링 메타 정보
  aggregationType: 'daily' | 'weekly' | 'monthly';
  samplingWarning?: string;
}

/**
 * ChartsSection에서 사용하는 모든 차트 데이터를 변환하고 제공
 */
export const useChartData = (
  data: ChartData | PortfolioData,
  isPortfolio: boolean
): UseChartDataReturn => {
  // 데이터 타입 구분
  const portfolioData = useMemo<PortfolioData | null>(
    () => (isPortfolio && 'portfolio_composition' in data ? (data as PortfolioData) : null),
    [data, isPortfolio]
  );

  const chartData = useMemo<ChartData | null>(
    () => (!isPortfolio ? (data as ChartData) : null),
    [data, isPortfolio]
  );

  // 백테스트 날짜 범위 추출
  const { startDate, endDate } = useMemo(() => {
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
  }, [isPortfolio, portfolioData, chartData]);

  // 종목 메타데이터
  const tickerInfo = useMemo(() => {
    return portfolioData?.ticker_info || (data as any).ticker_info || {};
  }, [portfolioData, data]);

  // 주가 데이터 (스마트 샘플링 적용)
  const stocksData = useMemo(() => {
    let rawStocksData: Array<{ symbol: string; data: any[] }> = [];
    
    if (portfolioData?.stock_data) {
      rawStocksData = Object.entries(portfolioData.stock_data).map(([symbol, data]) => ({
        symbol,
        data,
      }));
    } else if (chartData?.ticker && (data as any).stock_data) {
      const stockData = (data as any).stock_data[chartData.ticker];
      if (stockData) {
        rawStocksData = [{ symbol: chartData.ticker, data: stockData }];
      }
    }

    // 주가 데이터에 스마트 샘플링 적용
    if (startDate && endDate) {
      return rawStocksData.map(({ symbol, data }) => {
        const { data: sampledData } = smartSampleByPeriod(data, startDate, endDate);
        return { symbol, data: sampledData };
      });
    }

    return rawStocksData;
  }, [portfolioData, chartData, data, startDate, endDate]);

  // 거래 로그
  const tradeLogs = useMemo(() => {
    return extractTradeLogs(portfolioData?.strategy_details);
  }, [portfolioData]);

  // 통계 데이터
  const statsPayload = useMemo<Record<string, unknown>>(() => {
    return extractStatsPayload(data, isPortfolio);
  }, [data, isPortfolio]);

  // 샘플링 메타 정보 계산 (먼저 계산하여 다른 곳에서 사용)
  const { aggregationType, samplingWarning } = useMemo(() => {
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
  }, [startDate, endDate]);

  // 포트폴리오 equity 데이터 (스마트 샘플링 + 수익률 복리 집계)
  const portfolioEquityData = useMemo<EquityPoint[]>(() => {
    if (!portfolioData) return [];
    
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
      const { data: sampledEquityData } = smartSampleByPeriod(rawEquityData, startDate, endDate);
      return sampledEquityData;
    }

    // 주간/월간 집계: 수익률의 날짜에 맞춰 equity 데이터 재구성
    const dailyReturnsArray = Object.entries(portfolioData.daily_returns).map(([date, return_pct]) => ({
      date,
      return_pct: return_pct as number,
    }));

    const aggregatedReturns = aggregateReturns(dailyReturnsArray, aggregationType);
    
    // 집계된 수익률의 날짜에 맞춰 equity curve를 재구성
    const equityByDate = new Map(rawEquityData.map(eq => [eq.date, eq]));
    const sortedRawEquity = [...rawEquityData].sort((a, b) => 
      a.date < b.date ? -1 : a.date > b.date ? 1 : 0
    );

    return aggregatedReturns.map(r => {
      const eq = equityByDate.get(r.date) ?? findDataPointOnOrBefore(sortedRawEquity, r.date);
      if (!eq) {
        console.warn(`[포트폴리오 차트] ${r.date} 날짜의 equity 데이터 없음 (집계수익률=${r.return_pct}%)`);
        return { 
          date: r.date, 
          value: null as any, 
          return_pct: r.return_pct, 
          drawdown_pct: null as any 
        };
      }
      return {
        ...eq,
        date: r.date, // 집계 날짜로 덮어씀
        return_pct: r.return_pct,
      };
    });
  }, [portfolioData, startDate, endDate, aggregationType]);

  // 단일 종목 equity 데이터 (스마트 샘플링 + 수익률 복리 집계)
  const singleEquityData = useMemo<EquityPoint[]>(() => {
    if (!chartData?.equity_data) return [];
    
    // 원본 데이터 변환
    const rawData = transformSingleEquityData(chartData.equity_data);

    // 날짜 범위가 없으면 원본 반환
    if (!startDate || !endDate) {
      return rawData;
    }

    // 일간 집계: 기존 샘플링 방식 사용
    if (aggregationType === 'daily') {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }

    // 주간/월간 집계: 수익률의 날짜에 맞춰 equity 데이터 재구성
    const dailyReturnsArray = rawData.map(point => ({
      date: point.date,
      return_pct: point.return_pct,
    }));

    const aggregatedReturns = aggregateReturns(dailyReturnsArray, aggregationType);
    
    // 집계된 수익률의 날짜에 맞춰 equity curve를 재구성
    const equityByDate = new Map(rawData.map(eq => [eq.date, eq]));
    const sortedRawEquity = [...rawData].sort((a, b) => 
      a.date < b.date ? -1 : a.date > b.date ? 1 : 0
    );

    return aggregatedReturns.map(r => {
      const eq = equityByDate.get(r.date) ?? findDataPointOnOrBefore(sortedRawEquity, r.date);
      if (!eq) {
        console.warn(`[단일종목 차트] ${r.date} 날짜의 equity 데이터 없음 (집계수익률=${r.return_pct}%)`);
        return { 
          date: r.date, 
          value: null as any, 
          return_pct: r.return_pct, 
          drawdown_pct: null as any 
        };
      }
      return {
        ...eq,
        date: r.date,
        return_pct: r.return_pct,
      };
    });
  }, [chartData?.equity_data, startDate, endDate, aggregationType]);

  // 단일 종목 거래 마커
  const singleTrades = useMemo<TradeMarker[]>(() => {
    if (!chartData?.trade_markers) return [];
    return transformTradeMarkers(chartData.trade_markers);
  }, [chartData?.trade_markers]);

  // 단일 종목 OHLC 데이터 (스마트 샘플링 적용)
  const singleOhlcData = useMemo<OhlcPoint[]>(() => {
    if (!chartData?.ohlc_data) return [];
    const rawData = transformOhlcData(chartData.ohlc_data);

    if (startDate && endDate) {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }

    return rawData;
  }, [chartData?.ohlc_data, startDate, endDate]);

  // 벤치마크 데이터 (스마트 샘플링 + 수익률 복리 집계)
  const sp500Benchmark = useMemo<any[]>(() => {
    const rawData = extractBenchmarkData(data, 'sp500');
    if (!startDate || !endDate || rawData.length === 0) {
      return rawData;
    }

    // 일간 집계: 기존 샘플링 방식
    if (aggregationType === 'daily') {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }

    // 주간/월간 집계: 수익률의 날짜에 맞춰 데이터 재구성
    const dailyReturnsArray = rawData.map(point => ({
      date: point.date,
      return_pct: point.return_pct ?? 0,
    }));

    const aggregatedReturns = aggregateReturns(dailyReturnsArray, aggregationType);
    
    const dataByDate = new Map(rawData.map(item => [item.date, item]));
    const sortedRawData = [...rawData].sort((a, b) => 
      a.date < b.date ? -1 : a.date > b.date ? 1 : 0
    );

    return aggregatedReturns.map(r => {
      const item = dataByDate.get(r.date) ?? findDataPointOnOrBefore(sortedRawData, r.date);
      if (!item) {
        console.warn(`[S&P 500 벤치마크] ${r.date} 날짜의 데이터 없음 (집계수익률=${r.return_pct}%)`);
        return { date: r.date, value: null as any, return_pct: r.return_pct };
      }
      return {
        ...item,
        date: r.date,
        return_pct: r.return_pct,
      };
    });
  }, [data, startDate, endDate, aggregationType]);

  const nasdaqBenchmark = useMemo<any[]>(() => {
    const rawData = extractBenchmarkData(data, 'nasdaq');
    if (!startDate || !endDate || rawData.length === 0) {
      return rawData;
    }

    // 일간 집계: 기존 샘플링 방식
    if (aggregationType === 'daily') {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }

    // 주간/월간 집계: 수익률의 날짜에 맞춰 데이터 재구성
    const dailyReturnsArray = rawData.map(point => ({
      date: point.date,
      return_pct: point.return_pct ?? 0,
    }));

    const aggregatedReturns = aggregateReturns(dailyReturnsArray, aggregationType);
    
    const dataByDate = new Map(rawData.map(item => [item.date, item]));
    const sortedRawData = [...rawData].sort((a, b) => 
      a.date < b.date ? -1 : a.date > b.date ? 1 : 0
    );

    return aggregatedReturns.map(r => {
      const item = dataByDate.get(r.date) ?? findDataPointOnOrBefore(sortedRawData, r.date);
      if (!item) {
        console.warn(`[NASDAQ 벤치마크] ${r.date} 날짜의 데이터 없음 (집계수익률=${r.return_pct}%)`);
        return { date: r.date, value: null as any, return_pct: r.return_pct };
      }
      return {
        ...item,
        date: r.date,
        return_pct: r.return_pct,
      };
    });
  }, [data, startDate, endDate, aggregationType]);

  // 백엔드에서 이미 return_pct를 계산해서 보내므로 그대로 사용
  const sp500BenchmarkWithReturn = sp500Benchmark;
  const nasdaqBenchmarkWithReturn = nasdaqBenchmark;

  // 환율 데이터 (스마트 샘플링 적용)
  const exchangeRates = useMemo(() => {
    const rawData = portfolioData?.exchange_rates || (data as any).exchange_rates || [];
    if (startDate && endDate && rawData.length > 0) {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }
    return rawData;
  }, [portfolioData, data, startDate, endDate]);

  const exchangeStats = useMemo(() => {
    return (data as any).exchange_stats;
  }, [data]);

  // 급등락 이벤트
  const volatilityEvents = useMemo(() => {
    return portfolioData?.volatility_events || (data as any).volatility_events || {};
  }, [portfolioData, data]);

  const hasVolatilityEvents = useMemo(() => {
    return Object.keys(volatilityEvents).some(
      symbol => volatilityEvents[symbol] && volatilityEvents[symbol].length > 0
    );
  }, [volatilityEvents]);

  // 뉴스 데이터
  const latestNews = useMemo(() => {
    return portfolioData?.latest_news || (data as any).latest_news || {};
  }, [portfolioData, data]);

  const hasNews = useMemo(() => {
    return Object.keys(latestNews).some(
      symbol => latestNews[symbol] && latestNews[symbol].length > 0
    );
  }, [latestNews]);

  // 리밸런싱 데이터
  const rebalanceHistory = useMemo(() => {
    return portfolioData?.rebalance_history || [];
  }, [portfolioData]);

  // 포트폴리오 비중 변화 (스마트 샘플링 적용)
  const weightHistory = useMemo(() => {
    const rawData = portfolioData?.weight_history || [];
    if (startDate && endDate && rawData.length > 0) {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }
    return rawData;
  }, [portfolioData, startDate, endDate]);

  return {
    portfolioData,
    chartData,
    isPortfolio,
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
  };
};
