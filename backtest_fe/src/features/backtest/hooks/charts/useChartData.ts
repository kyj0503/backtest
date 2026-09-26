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
 *
 * **모듈 구성**:
 * - 이 파일: memo 배선과 반환 형태만 담당
 * - chartDataSelectors.ts: 응답에서 원본 조각 선택, 기간/샘플링 단위 판정
 * - chartSeriesBuilders.ts: 차트별 샘플링과 수익률 버킷 재구성
 */

import { useMemo } from 'react';
import {
  ChartData, PortfolioData, EquityPoint, TradeMarker, OhlcPoint,
  TickerInfo, BenchmarkSeriesPoint, ExchangeRatePoint, ExchangeRateStats,
  VolatilityEvent, NewsItem, RebalanceEvent, WeightHistoryPoint,
  TradeLog, StockDataItem,
} from '../../model/types';
import {
  transformTradeMarkers,
  transformOhlcData,
  extractTradeLogs,
  extractStatsPayload,
} from '../../utils';
import {
  resolveDateRange,
  resolveSamplingMeta,
  collectStocksData,
  hasAnyEntries,
} from './chartDataSelectors';
import {
  sampleByDateRange,
  buildPortfolioEquitySeries,
  buildSingleEquitySeries,
  buildBenchmarkSeries,
} from './chartSeriesBuilders';

export interface UseChartDataReturn {
  // 데이터 타입 구분
  portfolioData: PortfolioData | null;
  chartData: ChartData | null;
  isPortfolio: boolean;

  // 공통 데이터
  tickerInfo: Record<string, TickerInfo>;
  stocksData: StockDataItem[];
  tradeLogs: Record<string, TradeLog[]>;
  statsPayload: Record<string, unknown>;

  // 포트폴리오 데이터
  portfolioEquityData: EquityPoint[];

  // 단일 종목 데이터
  singleEquityData: EquityPoint[];
  singleTrades: TradeMarker[];
  singleOhlcData: OhlcPoint[];

  // 벤치마크 데이터
  sp500Benchmark: BenchmarkSeriesPoint[];
  nasdaqBenchmark: BenchmarkSeriesPoint[];
  sp500BenchmarkWithReturn: BenchmarkSeriesPoint[];
  nasdaqBenchmarkWithReturn: BenchmarkSeriesPoint[];

  // 환율 데이터
  exchangeRates: ExchangeRatePoint[];
  exchangeStats: ExchangeRateStats | undefined;

  // 급등락/뉴스 데이터
  volatilityEvents: Record<string, VolatilityEvent[]>;
  latestNews: Record<string, NewsItem[]>;
  hasVolatilityEvents: boolean;
  hasNews: boolean;

  // 리밸런싱 데이터
  rebalanceHistory: RebalanceEvent[];
  weightHistory: WeightHistoryPoint[];

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
  const { startDate, endDate } = useMemo(
    () => resolveDateRange(isPortfolio, portfolioData, chartData),
    [isPortfolio, portfolioData, chartData]
  );

  // 종목 메타데이터
  const tickerInfo = useMemo<Record<string, TickerInfo>>(() => {
    return portfolioData?.ticker_info || ('ticker_info' in data ? (data as PortfolioData).ticker_info : undefined) || {};
  }, [portfolioData, data]);

  // 주가 데이터 (스마트 샘플링 적용)
  const stocksData = useMemo(() => {
    const rawStocksData = collectStocksData(data, portfolioData, chartData);

    // 주가 데이터에 스마트 샘플링 적용
    if (startDate && endDate) {
      return rawStocksData.map(({ symbol, data }) => ({
        symbol,
        data: sampleByDateRange(data, startDate, endDate),
      }));
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
  const { aggregationType, samplingWarning } = useMemo(
    () => resolveSamplingMeta(startDate, endDate),
    [startDate, endDate]
  );

  // 포트폴리오 equity 데이터 (스마트 샘플링 + 수익률 복리 집계)
  const portfolioEquityData = useMemo<EquityPoint[]>(() => {
    if (!portfolioData) return [];
    return buildPortfolioEquitySeries(portfolioData, startDate, endDate, aggregationType);
  }, [portfolioData, startDate, endDate, aggregationType]);

  // 단일 종목 equity 데이터 (스마트 샘플링 + 수익률 복리 집계)
  const singleEquityData = useMemo<EquityPoint[]>(() => {
    if (!chartData?.equity_data) return [];
    return buildSingleEquitySeries(chartData.equity_data, startDate, endDate, aggregationType);
  }, [chartData?.equity_data, startDate, endDate, aggregationType]);

  // 단일 종목 거래 마커
  const singleTrades = useMemo<TradeMarker[]>(() => {
    if (!chartData?.trade_markers) return [];
    return transformTradeMarkers(chartData.trade_markers);
  }, [chartData?.trade_markers]);

  // 단일 종목 OHLC 데이터 (스마트 샘플링 적용)
  const singleOhlcData = useMemo<OhlcPoint[]>(() => {
    if (!chartData?.ohlc_data) return [];
    return sampleByDateRange(transformOhlcData(chartData.ohlc_data), startDate, endDate);
  }, [chartData?.ohlc_data, startDate, endDate]);

  // 벤치마크 데이터 (스마트 샘플링 + 수익률 복리 집계)
  const sp500Benchmark = useMemo<BenchmarkSeriesPoint[]>(
    () => buildBenchmarkSeries(data, 'sp500', startDate, endDate, aggregationType),
    [data, startDate, endDate, aggregationType]
  );

  const nasdaqBenchmark = useMemo<BenchmarkSeriesPoint[]>(
    () => buildBenchmarkSeries(data, 'nasdaq', startDate, endDate, aggregationType),
    [data, startDate, endDate, aggregationType]
  );

  // 백엔드에서 이미 return_pct를 계산해서 보내므로 그대로 사용
  const sp500BenchmarkWithReturn = sp500Benchmark;
  const nasdaqBenchmarkWithReturn = nasdaqBenchmark;

  // 환율 데이터 (스마트 샘플링 적용)
  const exchangeRates = useMemo<ExchangeRatePoint[]>(() => {
    const rawData: ExchangeRatePoint[] =
      portfolioData?.exchange_rates
      || (data as ChartData).exchange_rates
      || [];
    return rawData.length > 0 ? sampleByDateRange(rawData, startDate, endDate) : rawData;
  }, [portfolioData, data, startDate, endDate]);

  const exchangeStats = useMemo<ExchangeRateStats | undefined>(() => {
    return 'exchange_stats' in data ? data.exchange_stats : undefined;
  }, [data]);

  // 급등락 이벤트
  const volatilityEvents = useMemo<Record<string, VolatilityEvent[]>>(() => {
    return portfolioData?.volatility_events
      || ('volatility_events' in data ? (data as PortfolioData).volatility_events : undefined)
      || {};
  }, [portfolioData, data]);

  const hasVolatilityEvents = useMemo(() => hasAnyEntries(volatilityEvents), [volatilityEvents]);

  // 뉴스 데이터
  const latestNews = useMemo<Record<string, NewsItem[]>>(() => {
    return portfolioData?.latest_news
      || ('latest_news' in data ? (data as PortfolioData).latest_news : undefined)
      || {};
  }, [portfolioData, data]);

  const hasNews = useMemo(() => hasAnyEntries(latestNews), [latestNews]);

  // 리밸런싱 데이터
  const rebalanceHistory = useMemo(() => {
    return portfolioData?.rebalance_history || [];
  }, [portfolioData]);

  // 포트폴리오 비중 변화 (스마트 샘플링 적용)
  const weightHistory = useMemo(() => {
    const rawData = portfolioData?.weight_history || [];
    return rawData.length > 0 ? sampleByDateRange(rawData, startDate, endDate) : rawData;
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
