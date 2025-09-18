/**
 * 날짜 포맷팅 및 조작 유틸리티 함수들
 */

// 기본 포맷팅 함수들
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

// 확장된 포맷팅 함수들
export const formatDateToISO = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

export const formatDateToInput = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return formatDateToISO(dateObj);
};

export const formatRelativeTime = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - dateObj.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return '방금 전';
  if (diffMins < 60) return `${diffMins}분 전`;
  if (diffHours < 24) return `${diffHours}시간 전`;
  if (diffDays < 7) return `${diffDays}일 전`;
  return formatDate(dateObj);
};

export const formatPeriod = (days: number): string => {
  if (days < 7) return `${days}일`;
  if (days < 30) return `${Math.floor(days / 7)}주`;
  if (days < 365) return `${Math.floor(days / 30)}개월`;
  return `${Math.floor(days / 365)}년`;
};

// 날짜 검증 함수들
export const isValidDateRange = (startDate: string, endDate: string): boolean => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  return start <= end && start <= new Date() && end <= new Date();
};

export const isWeekend = (date: string | Date): boolean => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const dayOfWeek = dateObj.getDay();
  return dayOfWeek === 0 || dayOfWeek === 6;
};

export const isBusinessDay = (date: string | Date): boolean => {
  return !isWeekend(date);
};

export const isValidDate = (dateString: string): boolean => {
  const date = new Date(dateString);
  return !isNaN(date.getTime()) && dateString !== '';
};

// 날짜 계산 함수들
export const addDays = (date: Date, days: number): Date => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
};

export const addMonths = (date: Date, months: number): Date => {
  const result = new Date(date);
  result.setMonth(result.getMonth() + months);
  return result;
};

export const addYears = (date: Date, years: number): Date => {
  const result = new Date(date);
  result.setFullYear(result.getFullYear() + years);
  return result;
};

export const getDaysBetween = (startDate: string | Date, endDate: string | Date): number => {
  const start = typeof startDate === 'string' ? new Date(startDate) : startDate;
  const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
  const diffTime = Math.abs(end.getTime() - start.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

export const getBusinessDaysBetween = (startDate: string | Date, endDate: string | Date): number => {
  const start = typeof startDate === 'string' ? new Date(startDate) : startDate;
  const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
  
  let count = 0;
  const currentDate = new Date(start);
  
  while (currentDate <= end) {
    if (isBusinessDay(currentDate)) {
      count++;
    }
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  return count;
};

// 날짜 범위 생성
export const getDateRange = (startDate: Date, endDate: Date): Date[] => {
  const dates: Date[] = [];
  const currentDate = new Date(startDate);
  
  while (currentDate <= endDate) {
    dates.push(new Date(currentDate));
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  return dates;
};

export const getBusinessDateRange = (startDate: Date, endDate: Date): Date[] => {
  return getDateRange(startDate, endDate).filter(date => isBusinessDay(date));
};

// 미리 정의된 날짜 범위들
export const getPresetDateRanges = () => {
  const today = new Date();
  const yesterday = addDays(today, -1);
  const lastWeek = addDays(today, -7);
  const lastMonth = addMonths(today, -1);
  const lastThreeMonths = addMonths(today, -3);
  const lastSixMonths = addMonths(today, -6);
  const lastYear = addYears(today, -1);
  const lastTwoYears = addYears(today, -2);
  const lastFiveYears = addYears(today, -5);

  return {
    '어제': { start: yesterday, end: yesterday },
    '지난 주': { start: lastWeek, end: today },
    '지난 달': { start: lastMonth, end: today },
    '지난 3개월': { start: lastThreeMonths, end: today },
    '지난 6개월': { start: lastSixMonths, end: today },
    '지난 1년': { start: lastYear, end: today },
    '지난 2년': { start: lastTwoYears, end: today },
    '지난 5년': { start: lastFiveYears, end: today },
  };
};

// 타임존 관련
export const getTimezone = (): string => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

export const formatDateWithTimezone = (date: string | Date, timezone?: string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString('ko-KR', {
    timeZone: timezone || getTimezone(),
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};
