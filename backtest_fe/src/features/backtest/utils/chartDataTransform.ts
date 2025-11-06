/**
 * 차트 데이터 변환 유틸리티
 * 백엔드 응답을 차트 컴포넌트에서 사용할 수 있는 형식으로 변환
 */

import { EquityPoint, TradeMarker, OhlcPoint, ChartData, PortfolioData } from '../model/types/backtest-result-types';

/**
 * 포트폴리오 equity curve 데이터를 EquityPoint 배열로 변환
 */
export const transformPortfolioEquityData = (
  equityCurve: Record<string, number>,
  dailyReturns: Record<string, number>
): EquityPoint[] => {
  return Object.entries(equityCurve).map(([date, value]) => ({
    date,
    value,
    return_pct: Number(dailyReturns[date] ?? 0),
    drawdown_pct: 0,
  }));
};

/**
 * 단일 종목 equity 데이터를 EquityPoint 배열로 변환
 */
export const transformSingleEquityData = (
  equityData: any[]
): EquityPoint[] => {
  return equityData.map(point => ({
    date: point.date,
    value: point.value,
    return_pct: Number(point.return_pct ?? point.return ?? 0),
    drawdown_pct: Number(point.drawdown_pct ?? point.drawdown ?? 0),
  }));
};

/**
 * 거래 마커 데이터를 TradeMarker 배열로 변환
 */
export const transformTradeMarkers = (
  tradeMarkers: any[]
): TradeMarker[] => {
  return tradeMarkers.map(marker => ({
    ...marker,
    type: marker.type === 'entry' ? 'entry' : 'exit',
  }));
};

/**
 * OHLC 데이터를 OhlcPoint 배열로 변환
 */
export const transformOhlcData = (
  ohlcData: any[]
): OhlcPoint[] => {
  return ohlcData.map(point => ({
    ...point,
    volume: Number(point.volume ?? 0),
  }));
};

/**
 * 벤치마크 데이터에 일일 수익률 계산 추가
 */
export const withBenchmarkReturn = (points: any[]): any[] => {
  return points?.map((point, index) => {
    if (index === 0) {
      return { ...point, return_pct: 0 };
    }
    const prev = points[index - 1];
    const returnPct = ((point.close - prev.close) / prev.close) * 100;
    return { ...point, return_pct: returnPct };
  }) ?? [];
};

/**
 * stock_data를 배열 형식으로 변환
 */
export const transformStockData = (
  stockData: Record<string, any>,
  ticker?: string
): Array<{ symbol: string; data: any[] }> => {
  if (!stockData) return [];

  if (ticker && stockData[ticker]) {
    return [{ symbol: ticker, data: stockData[ticker] }];
  }

  return Object.entries(stockData).map(([symbol, data]) => ({
    symbol,
    data,
  }));
};

/**
 * strategy_details에서 trade_log 추출 (symbol별)
 */
export const extractTradeLogs = (
  strategyDetails?: Record<string, any>
): Record<string, any[]> => {
  const logs: Record<string, any[]> = {};

  if (!strategyDetails) return logs;

  Object.entries(strategyDetails).forEach(([symbol, stats]) => {
    if (stats.trade_log && Array.isArray(stats.trade_log)) {
      // 원본 심볼로 매핑 (예: "AAPL_1" → "AAPL", "MSFT_0" → "MSFT")
      const cleanSymbol = symbol.split('_')[0];
      logs[cleanSymbol] = stats.trade_log;
    }
  });

  return logs;
};

/**
 * 통합 응답에서 벤치마크 데이터 추출
 */
export const extractBenchmarkData = (
  data: ChartData | PortfolioData,
  benchmarkType: 'sp500' | 'nasdaq'
): any[] => {
  const chartBenchmark = (data as ChartData)[`${benchmarkType}_benchmark`];
  const portfolioBenchmark = (data as PortfolioData)[`${benchmarkType}_benchmark`];
  return chartBenchmark ?? portfolioBenchmark ?? [];
};

/**
 * 통합 응답에서 통계 데이터 추출
 */
export const extractStatsPayload = (
  data: ChartData | PortfolioData,
  isPortfolio: boolean
): Record<string, unknown> => {
  if (isPortfolio && 'portfolio_statistics' in data) {
    return { ...(data as PortfolioData).portfolio_statistics } as Record<string, unknown>;
  }
  return (data as ChartData).summary_stats ?? {};
};
