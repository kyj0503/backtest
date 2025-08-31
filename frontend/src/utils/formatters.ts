// 공통 포맷팅 함수들
export const formatCurrency = (value: number): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return 'N/A';
  }
  
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatPercent = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return 'N/A';
  }
  return `${value.toFixed(2)}%`;
};

export const formatNumber = (value: number | undefined | null, decimals: number = 2): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return 'N/A';
  }
  return value.toFixed(decimals);
};

// 날짜 유틸리티
export const formatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleDateString('ko-KR');
  } catch {
    return dateString;
  }
};

// 배지 색상 결정 함수
export const getStatVariant = (value: number, type: 'return' | 'sharpe' | 'drawdown' | 'winRate'): string => {
  switch (type) {
    case 'return':
      return value >= 0 ? 'success' : 'danger';
    case 'sharpe':
      return value >= 1 ? 'success' : value >= 0.5 ? 'warning' : 'danger';
    case 'drawdown':
      return value >= -5 ? 'success' : value >= -15 ? 'warning' : 'danger';
    case 'winRate':
      return value >= 60 ? 'success' : value >= 40 ? 'warning' : 'danger';
    default:
      return 'secondary';
  }
};

// 거래 마커 색상 결정
export const getTradeColor = (type: 'entry' | 'exit', side?: 'buy' | 'sell'): string => {
  if (type === 'entry') {
    return side === 'buy' ? '#198754' : '#dc3545'; // 초록/빨강
  } else {
    return '#ffc107'; // 노랑 (청산)
  }
};

// 포트폴리오 총 금액 계산
export const calculateTotalAmount = (portfolio: Array<{ amount: number }>): number => {
  return portfolio.reduce((sum, stock) => sum + stock.amount, 0);
};

// 비중 계산
export const calculateWeight = (amount: number, totalAmount: number): number => {
  if (totalAmount === 0) return 0;
  return (amount / totalAmount) * 100;
};
