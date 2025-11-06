/**
 * 포맷팅 유틸리티 함수들
 * 날짜, 통화, 가격, 퍼센트 등의 포맷팅을 담당
 */

/**
 * 통화 값을 축약 형식으로 포맷팅
 * @example formatCurrency(1500000) => "1.5M"
 * @example formatCurrency(1500) => "1.5K"
 */
export const formatCurrency = (value: number): string => {
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toLocaleString();
};

/**
 * 가격을 통화 형식으로 포맷팅
 * @example formatPrice(1234.56) => "$1,234.56"
 */
export const formatPrice = (value: number): string => {
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

/**
 * 퍼센트 값을 포맷팅
 * @example formatPercent(12.3456) => "12.35%"
 */
export const formatPercent = (value: number, decimals: number = 2): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * 날짜를 짧은 형식으로 포맷팅 (차트용)
 * @example formatDateShort("2025-01-15") => "1/15"
 */
export const formatDateShort = (value: string): string => {
  const date = new Date(value);
  return `${date.getMonth() + 1}/${date.getDate()}`;
};

/**
 * 날짜를 긴 형식으로 포맷팅
 * @example formatDateLong("2025-01-15") => "2025년 1월 15일"
 */
export const formatDateLong = (value: string): string => {
  const date = new Date(value);
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
};

/**
 * ISO 날짜 문자열에서 날짜 부분만 추출
 * @example extractDate("2020-01-06T00:00:00") => "2020-01-06"
 * @example extractDate("2020-01-06 12:00:00") => "2020-01-06"
 */
export const extractDate = (dateTimeString: string): string => {
  return dateTimeString.split('T')[0].split(' ')[0];
};

/**
 * 원화를 포맷팅
 * @example formatKRW(1234567) => "₩1,234,567"
 */
export const formatKRW = (value: number, decimals: number = 0): string => {
  return `₩${value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};
