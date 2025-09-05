/**
 * 날짜 포맷팅 유틸리티 함수들
 */

export const formatDate = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString('ko-KR');
};

export const formatDateTime = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString('ko-KR') + ' ' + dateObj.toLocaleTimeString('ko-KR');
};

export const formatChartDate = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
};

export const formatDateRange = (startDate: string, endDate: string): string => {
  return `${formatDate(startDate)} ~ ${formatDate(endDate)}`;
};

export const isValidDateRange = (startDate: string, endDate: string): boolean => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  return start <= end && start <= new Date() && end <= new Date();
};
