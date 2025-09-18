/**
 * 차트 데이터 변환 및 조작 유틸리티 함수들
 */

import { OhlcPoint, EquityPoint, TradeMarker } from '@/features/backtest/model/backtest-result-types';
import { formatChartDate, formatDate } from './dateUtils';
import { formatPercent, formatPrice, getColorByValue } from './numberUtils';

// 차트 데이터 변환
export const transformOHLCData = (data: OhlcPoint[] = []) => {
  return data.map(point => ({
    date: formatChartDate(point.date),
    timestamp: point.timestamp,
    open: point.open,
    high: point.high,
    low: point.low,
    close: point.close,
    volume: point.volume,
    fill: getColorByValue(point.close - point.open)
  }));
};

export const transformEquityData = (data: EquityPoint[] = []) => {
  return data.map(point => ({
    date: formatChartDate(point.date),
    timestamp: point.timestamp,
    equity: point.equity,
    return_pct: point.return_pct,
    drawdown_pct: point.drawdown_pct,
    fill: getColorByValue(point.return_pct)
  }));
};

export const transformTradeMarkers = (trades: TradeMarker[] = []) => {
  return trades.map(trade => ({
    ...trade,
    date: formatChartDate(trade.date),
    displayPrice: formatPrice(trade.price ?? 0),
    displayPnl: typeof trade.pnl_pct === 'number' ? formatPercent(trade.pnl_pct) : 'N/A',
    color: trade.side === 'buy' ? '#10B981' : '#EF4444',
    symbol: trade.side === 'buy' ? '▲' : '▼'
  }));
};

// 차트 설정 생성
export const createChartConfig = (type: 'line' | 'candlestick' | 'bar' | 'area' = 'line') => {
  const baseConfig = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 300,
      easing: 'easeInOutQuart' as const
    }
  };

  switch (type) {
    case 'candlestick':
      return {
        ...baseConfig,
        scales: {
          x: {
            type: 'time' as const,
            time: {
              displayFormats: {
                day: 'MM/dd',
                week: 'MM/dd',
                month: 'yyyy-MM'
              }
            }
          },
          y: {
            position: 'right' as const,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          }
        }
      };
    
    case 'area':
      return {
        ...baseConfig,
        fill: true,
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderColor: '#3B82F6',
        pointBackgroundColor: '#3B82F6'
      };
    
    case 'bar':
      return {
        ...baseConfig,
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: '#3B82F6',
        borderWidth: 1
      };
    
    default: // line
      return {
        ...baseConfig,
        borderColor: '#3B82F6',
        backgroundColor: 'transparent',
        pointBackgroundColor: '#3B82F6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5
      };
  }
};

// 색상 팔레트 생성
export const getChartColorPalette = (count: number): string[] => {
  const baseColors = [
    '#3B82F6', // blue
    '#10B981', // green
    '#F59E0B', // yellow
    '#EF4444', // red
    '#8B5CF6', // purple
    '#EC4899', // pink
    '#14B8A6', // teal
    '#F97316', // orange
    '#84CC16', // lime
    '#6366F1'  // indigo
  ];

  if (count <= baseColors.length) {
    return baseColors.slice(0, count);
  }

  // Generate additional colors if needed
  const additionalColors: string[] = [];
  for (let i = baseColors.length; i < count; i++) {
    const hue = (i * 137.508) % 360; // Golden angle approximation
    additionalColors.push(`hsl(${hue}, 70%, 50%)`);
  }

  return [...baseColors, ...additionalColors];
};

// 데이터 필터링 및 정렬
export const filterDataByDateRange = <T extends { date: string }>(
  data: T[], 
  startDate: string, 
  endDate: string
): T[] => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  return data.filter(item => {
    const itemDate = new Date(item.date);
    return itemDate >= start && itemDate <= end;
  });
};

export const sortDataByDate = <T extends { date: string }>(
  data: T[], 
  ascending = true
): T[] => {
  return [...data].sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return ascending ? dateA - dateB : dateB - dateA;
  });
};

// 데이터 집계
export const aggregateDataByPeriod = <T extends { date: string; value: number }>(
  data: T[],
  period: 'day' | 'week' | 'month' | 'quarter' | 'year'
): T[] => {
  const aggregated = new Map<string, T[]>();

  data.forEach(item => {
    const date = new Date(item.date);
    let key: string;

    switch (period) {
      case 'week':
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = formatDate(weekStart);
        break;
      case 'month':
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        break;
      case 'quarter':
        const quarter = Math.floor(date.getMonth() / 3) + 1;
        key = `${date.getFullYear()}-Q${quarter}`;
        break;
      case 'year':
        key = String(date.getFullYear());
        break;
      default: // day
        key = formatDate(date);
    }

    if (!aggregated.has(key)) {
      aggregated.set(key, []);
    }
    aggregated.get(key)!.push(item);
  });

  return Array.from(aggregated.entries()).map(([key, items]) => {
    const totalValue = items.reduce((sum, item) => sum + item.value, 0);
    const avgValue = totalValue / items.length;
    
    return {
      ...items[0],
      date: key,
      value: avgValue,
      count: items.length,
      total: totalValue
    } as T;
  });
};

// 이동평균 계산
export const calculateMovingAverage = (
  data: number[], 
  window: number
): (number | null)[] => {
  if (window <= 0 || window > data.length) {
    return data.map(() => null);
  }

  const result: (number | null)[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < window - 1) {
      result.push(null);
    } else {
      const slice = data.slice(i - window + 1, i + 1);
      const average = slice.reduce((sum, val) => sum + val, 0) / window;
      result.push(average);
    }
  }

  return result;
};

// 기술적 지표 계산
export const calculateRSI = (prices: number[], period = 14): (number | null)[] => {
  if (prices.length < period + 1) {
    return prices.map(() => null);
  }

  const changes = prices.slice(1).map((price, i) => price - prices[i]);
  const gains = changes.map(change => change > 0 ? change : 0);
  const losses = changes.map(change => change < 0 ? Math.abs(change) : 0);

  const avgGains = calculateMovingAverage(gains, period);
  const avgLosses = calculateMovingAverage(losses, period);

  return avgGains.map((avgGain, i) => {
    const avgLoss = avgLosses[i];
    if (avgGain === null || avgLoss === null || avgLoss === 0) {
      return null;
    }
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  });
};

// 차트 툴팁 포맷터
export const createTooltipFormatter = (type: 'currency' | 'percentage' | 'number' = 'number') => {
  return (value: number) => {
    switch (type) {
      case 'currency':
        return formatPrice(value);
      case 'percentage':
        return formatPercent(value);
      default:
        return value.toFixed(2);
    }
  };
};

// 차트 데이터 검증
export const validateChartData = <T extends { date: string }>(data: T[]): boolean => {
  if (!Array.isArray(data) || data.length === 0) {
    return false;
  }

  return data.every(item => 
    item.date && 
    !isNaN(new Date(item.date).getTime())
  );
};

// 빈 데이터 처리
export const fillMissingData = <T extends { date: string; value: number }>(
  data: T[],
  startDate: string,
  endDate: string,
  fillValue = 0
): T[] => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const existingDates = new Set(data.map(item => item.date));
  const filledData = [...data];

  const currentDate = new Date(start);
  while (currentDate <= end) {
    const dateStr = formatDate(currentDate);
    if (!existingDates.has(dateStr)) {
      filledData.push({
        ...data[0],
        date: dateStr,
        value: fillValue
      });
    }
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return sortDataByDate(filledData);
};
