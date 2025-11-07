/**
 * 차트 데이터 변환 유틸리티
 * 백엔드 응답을 차트 컴포넌트에서 사용할 수 있는 형식으로 변환
 */

import { EquityPoint, TradeMarker, OhlcPoint, ChartData, PortfolioData } from '../model/types/backtest-result-types';
import { formatChartDate } from '@/shared/lib/utils/dateUtils';

// ============================================
// 포맷팅 함수들 (차트 표시용)
// ============================================

/**
 * 통화 값을 축약 형식으로 포맷팅 (차트용)
 * @example formatCurrencyCompact(1500000) => "1.5M"
 * @example formatCurrencyCompact(1500) => "1.5K"
 */
export const formatCurrencyCompact = (value: number): string => {
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toLocaleString();
};

/**
 * @deprecated Use formatCurrencyCompact instead
 */
export const formatCurrency = formatCurrencyCompact;

/**
 * 날짜를 짧은 형식으로 포맷팅 (차트용)
 * @example formatDateShort("2025-01-15") => "1/15"
 */
export const formatDateShort = formatChartDate;

/**
 * 원화를 포맷팅
 * @example formatKRW(1234567) => "₩1,234,567"
 */
export const formatKRW = (value: number, decimals: number = 0): string => {
  return `₩${value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};

// ============================================
// 데이터 변환 함수들
// ============================================

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
      // 백엔드에서 이미 실제 심볼 이름으로 제공하므로 그대로 사용
      logs[symbol] = stats.trade_log;
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
