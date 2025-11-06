/**
 * ChartsSection 데이터 변환 훅
 * ChartsSection의 복잡한 데이터 변환 로직을 커스텀 훅으로 분리
 */

import { useMemo } from 'react';
import { ChartData, PortfolioData, EquityPoint, TradeMarker, OhlcPoint } from '../../model/types';
import {
  transformPortfolioEquityData,
  transformSingleEquityData,
  transformTradeMarkers,
  transformOhlcData,
  withBenchmarkReturn,
  extractTradeLogs,
  extractBenchmarkData,
  extractStatsPayload,
} from '../../utils';

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

  // 종목 메타데이터
  const tickerInfo = useMemo(() => {
    return portfolioData?.ticker_info || (data as any).ticker_info || {};
  }, [portfolioData, data]);

  // 주가 데이터
  const stocksData = useMemo(() => {
    if (portfolioData?.stock_data) {
      return Object.entries(portfolioData.stock_data).map(([symbol, data]) => ({
        symbol,
        data,
      }));
    }
    if (chartData?.ticker && (data as any).stock_data) {
      const stockData = (data as any).stock_data[chartData.ticker];
      if (stockData) {
        return [{ symbol: chartData.ticker, data: stockData }];
      }
    }
    return [];
  }, [portfolioData, chartData, data]);

  // 거래 로그
  const tradeLogs = useMemo(() => {
    return extractTradeLogs(portfolioData?.strategy_details);
  }, [portfolioData]);

  // 통계 데이터
  const statsPayload = useMemo<Record<string, unknown>>(() => {
    return extractStatsPayload(data, isPortfolio);
  }, [portfolioData, chartData]);

  // 포트폴리오 equity 데이터
  const portfolioEquityData = useMemo<EquityPoint[]>(() => {
    if (!portfolioData) return [];
    return transformPortfolioEquityData(
      portfolioData.equity_curve,
      portfolioData.daily_returns
    );
  }, [portfolioData]);

  // 단일 종목 equity 데이터
  const singleEquityData = useMemo<EquityPoint[]>(() => {
    if (!chartData?.equity_data) return [];
    return transformSingleEquityData(chartData.equity_data);
  }, [chartData?.equity_data]);

  // 단일 종목 거래 마커
  const singleTrades = useMemo<TradeMarker[]>(() => {
    if (!chartData?.trade_markers) return [];
    return transformTradeMarkers(chartData.trade_markers);
  }, [chartData?.trade_markers]);

  // 단일 종목 OHLC 데이터
  const singleOhlcData = useMemo<OhlcPoint[]>(() => {
    if (!chartData?.ohlc_data) return [];
    return transformOhlcData(chartData.ohlc_data);
  }, [chartData?.ohlc_data]);

  // 벤치마크 데이터
  const sp500Benchmark = useMemo<any[]>(() => {
    return extractBenchmarkData(data, 'sp500');
  }, [data]);

  const nasdaqBenchmark = useMemo<any[]>(() => {
    return extractBenchmarkData(data, 'nasdaq');
  }, [data]);

  const sp500BenchmarkWithReturn = useMemo(() => {
    return withBenchmarkReturn(sp500Benchmark);
  }, [sp500Benchmark]);

  const nasdaqBenchmarkWithReturn = useMemo(() => {
    return withBenchmarkReturn(nasdaqBenchmark);
  }, [nasdaqBenchmark]);

  // 환율 데이터
  const exchangeRates = useMemo(() => {
    return portfolioData?.exchange_rates || (data as any).exchange_rates || [];
  }, [portfolioData, data]);

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

  const weightHistory = useMemo(() => {
    return portfolioData?.weight_history || [];
  }, [portfolioData]);

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
  };
};
