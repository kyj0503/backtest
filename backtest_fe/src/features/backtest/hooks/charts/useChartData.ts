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
  extractTradeLogs,
  extractBenchmarkData,
  extractStatsPayload,
} from '../../utils';
import { smartSampleByPeriod } from '@/shared/utils/dataSampling';

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

  // 포트폴리오 equity 데이터 (스마트 샘플링 적용)
  const portfolioEquityData = useMemo<EquityPoint[]>(() => {
    if (!portfolioData) return [];
    const rawData = transformPortfolioEquityData(
      portfolioData.equity_curve,
      portfolioData.daily_returns
    );

    if (startDate && endDate) {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }

    return rawData;
  }, [portfolioData, startDate, endDate]);

  // 단일 종목 equity 데이터 (스마트 샘플링 적용)
  const singleEquityData = useMemo<EquityPoint[]>(() => {
    if (!chartData?.equity_data) return [];
    const rawData = transformSingleEquityData(chartData.equity_data);

    if (startDate && endDate) {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }

    return rawData;
  }, [chartData?.equity_data, startDate, endDate]);

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

  // 벤치마크 데이터 (스마트 샘플링 적용)
  const sp500Benchmark = useMemo<any[]>(() => {
    const rawData = extractBenchmarkData(data, 'sp500');
    if (startDate && endDate && rawData.length > 0) {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }
    return rawData;
  }, [data, startDate, endDate]);

  const nasdaqBenchmark = useMemo<any[]>(() => {
    const rawData = extractBenchmarkData(data, 'nasdaq');
    if (startDate && endDate && rawData.length > 0) {
      const { data: sampledData } = smartSampleByPeriod(rawData, startDate, endDate);
      return sampledData;
    }
    return rawData;
  }, [data, startDate, endDate]);

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

  // 샘플링 메타 정보 계산
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
