/**
 * 숫자 포맷팅 및 계산 유틸리티 함수들
 */

// 기본 포맷팅 함수들
export const formatCurrency = (value: number): string => {
  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(1)}B`;
  } else if (value >= 1e6) {
    return `${(value / 1e6).toFixed(1)}M`;
  } else if (value >= 1e3) {
    return `${(value / 1e3).toFixed(1)}K`;
  }
  return value.toLocaleString();
};

export const formatPercent = (value: number, decimals = 2): string => {
  return `${value > 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

export const formatPrice = (value: number, decimals = 2): string => {
  return `$${value.toFixed(decimals)}`;
};

export const formatKoreanCurrency = (value: number): string => {
  if (value >= 1e8) {
    return `${(value / 1e8).toFixed(1)}억원`;
  } else if (value >= 1e4) {
    return `${(value / 1e4).toFixed(1)}만원`;
  }
  return `${value.toLocaleString()}원`;
};

// 확장된 포맷팅 함수들
export const formatNumber = (value: number, decimals = 0): string => {
  return value.toLocaleString('ko-KR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

export const formatLargeNumber = (value: number): string => {
  if (Math.abs(value) >= 1e12) {
    return `${(value / 1e12).toFixed(1)}T`;
  } else if (Math.abs(value) >= 1e9) {
    return `${(value / 1e9).toFixed(1)}B`;
  } else if (Math.abs(value) >= 1e6) {
    return `${(value / 1e6).toFixed(1)}M`;
  } else if (Math.abs(value) >= 1e3) {
    return `${(value / 1e3).toFixed(1)}K`;
  }
  return formatNumber(value);
};

export const formatCompactNumber = (value: number): string => {
  return new Intl.NumberFormat('ko-KR', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(value);
};

export const formatScientific = (value: number, decimals = 2): string => {
  return value.toExponential(decimals);
};

export const formatRatio = (numerator: number, denominator: number, decimals = 2): string => {
  if (denominator === 0) return 'N/A';
  return (numerator / denominator).toFixed(decimals);
};

// 백분율 관련 함수들
export const formatBasisPoints = (value: number): string => {
  return `${(value * 10000).toFixed(0)}bp`;
};

export const formatPercentChange = (oldValue: number, newValue: number, decimals = 2): string => {
  if (oldValue === 0) return 'N/A';
  const change = ((newValue - oldValue) / oldValue) * 100;
  return formatPercent(change, decimals);
};

export const formatAbsoluteChange = (oldValue: number, newValue: number, decimals = 2): string => {
  const change = newValue - oldValue;
  const sign = change > 0 ? '+' : '';
  return `${sign}${formatNumber(change, decimals)}`;
};

// 재무 관련 포맷팅
export const formatVolume = (value: number): string => {
  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(1)}B`;
  } else if (value >= 1e6) {
    return `${(value / 1e6).toFixed(1)}M`;
  } else if (value >= 1e3) {
    return `${(value / 1e3).toFixed(1)}K`;
  }
  return formatNumber(value);
};

export const formatMarketCap = (value: number): string => {
  return formatLargeNumber(value);
};

export const formatSharpeRatio = (value: number): string => {
  return value.toFixed(3);
};

export const formatVolatility = (value: number): string => {
  return formatPercent(value * 100);
};

export const formatBeta = (value: number): string => {
  return value.toFixed(3);
};

export const formatDrawdown = (value: number): string => {
  return formatPercent(Math.abs(value));
};

// 숫자 검증 및 파싱
export const isValidNumber = (value: unknown): boolean => {
  if (typeof value === 'number') {
    return !isNaN(value) && isFinite(value);
  }
  if (typeof value === 'string') {
    const num = parseFloat(value);
    return !isNaN(num) && isFinite(num);
  }
  return false;
};

export const parseNumber = (value: string): number | null => {
  const num = parseFloat(value);
  return isValidNumber(num) ? num : null;
};

export const parsePercentage = (value: string): number | null => {
  const cleaned = value.replace('%', '');
  const num = parseFloat(cleaned);
  return isValidNumber(num) ? num / 100 : null;
};

export const parseCurrency = (value: string): number | null => {
  const cleaned = value.replace(/[^\d.-]/g, '');
  return parseNumber(cleaned);
};

// 수학적 계산 함수들
export const clamp = (value: number, min: number, max: number): number => {
  return Math.min(Math.max(value, min), max);
};

export const round = (value: number, decimals = 0): number => {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
};

export const roundUp = (value: number, decimals = 0): number => {
  const factor = Math.pow(10, decimals);
  return Math.ceil(value * factor) / factor;
};

export const roundDown = (value: number, decimals = 0): number => {
  const factor = Math.pow(10, decimals);
  return Math.floor(value * factor) / factor;
};

export const average = (values: number[]): number => {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
};

export const median = (values: number[]): number => {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 
    ? (sorted[mid - 1] + sorted[mid]) / 2 
    : sorted[mid];
};

export const standardDeviation = (values: number[]): number => {
  if (values.length === 0) return 0;
  const avg = average(values);
  const squaredDiffs = values.map(value => Math.pow(value - avg, 2));
  return Math.sqrt(average(squaredDiffs));
};

export const variance = (values: number[]): number => {
  if (values.length === 0) return 0;
  const avg = average(values);
  const squaredDiffs = values.map(value => Math.pow(value - avg, 2));
  return average(squaredDiffs);
};

// 범위 및 스케일링
export const normalize = (value: number, min: number, max: number): number => {
  if (max === min) return 0;
  return (value - min) / (max - min);
};

export const denormalize = (normalizedValue: number, min: number, max: number): number => {
  return normalizedValue * (max - min) + min;
};

export const scale = (value: number, fromMin: number, fromMax: number, toMin: number, toMax: number): number => {
  const normalized = normalize(value, fromMin, fromMax);
  return denormalize(normalized, toMin, toMax);
};

// 안전한 나눗셈
export const safeDivide = (numerator: number, denominator: number, fallback = 0): number => {
  return denominator === 0 ? fallback : numerator / denominator;
};

// 컬러 계산 (차트용)
export const getColorByValue = (value: number, threshold = 0): string => {
  return value >= threshold ? '#10B981' : '#EF4444'; // green : red
};

export const getIntensityColor = (value: number, min: number, max: number): string => {
  const intensity = normalize(Math.abs(value), min, max);
  const alpha = clamp(intensity, 0.1, 1);
  const color = value >= 0 ? '16, 185, 129' : '239, 68, 68'; // green or red RGB
  return `rgba(${color}, ${alpha})`;
};
