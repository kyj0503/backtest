/**
 * 화폐 포맷팅 유틸리티 함수들
 */

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

export const formatPercent = (value: number): string => {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
};

export const formatPrice = (value: number): string => {
  return `$${value.toFixed(2)}`;
};

export const formatKoreanCurrency = (value: number): string => {
  if (value >= 1e8) {
    return `${(value / 1e8).toFixed(1)}억원`;
  } else if (value >= 1e4) {
    return `${(value / 1e4).toFixed(1)}만원`;
  }
  return `${value.toLocaleString()}원`;
};
