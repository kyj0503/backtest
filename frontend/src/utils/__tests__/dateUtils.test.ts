import { describe, it, expect } from 'vitest';
import {
  formatDate,
  formatDateTime,
  formatChartDate,
  formatDateRange,
  formatDateToISO,
  formatDateToInput,
  formatRelativeTime,
  formatPeriod,
  isValidDateRange,
  isWeekend,
  isBusinessDay,
  isValidDate,
  addDays,
  addMonths,
  addYears,
  getDaysBetween,
  getBusinessDaysBetween,
  getDateRange,
  getBusinessDateRange,
  getPresetDateRanges,
  getTimezone,
  formatDateWithTimezone
} from '../dateUtils';

describe('dateUtils', () => {
  describe('formatDate', () => {
    it('날짜 문자열을 한국어 형식으로 포맷해야 함', () => {
      const result = formatDate('2023-12-25');
      expect(result).toBe('2023. 12. 25.');
    });

    it('Date 객체를 한국어 형식으로 포맷해야 함', () => {
      const date = new Date('2023-12-25');
      const result = formatDate(date);
      expect(result).toBe('2023. 12. 25.');
    });
  });

  describe('formatDateTime', () => {
    it('날짜와 시간을 모두 포함하여 포맷해야 함', () => {
      const result = formatDateTime('2023-12-25T10:30:00');
      expect(result).toContain('2023. 12. 25.');
      expect(result).toContain(':');
    });
  });

  describe('formatChartDate', () => {
    it('차트용 간단한 날짜 형식으로 포맷해야 함', () => {
      const result = formatChartDate('2023-12-25');
      expect(result).toBe('12/25');
    });
  });

  describe('formatDateRange', () => {
    it('날짜 범위를 올바른 형식으로 포맷해야 함', () => {
      const result = formatDateRange('2023-01-01', '2023-12-31');
      expect(result).toBe('2023. 1. 1. ~ 2023. 12. 31.');
    });
  });

  describe('formatDateToISO', () => {
    it('Date 객체를 ISO 형식으로 변환해야 함', () => {
      const date = new Date('2023-12-25');
      const result = formatDateToISO(date);
      expect(result).toBe('2023-12-25');
    });
  });

  describe('formatDateToInput', () => {
    it('input 필드용 날짜 형식으로 변환해야 함', () => {
      const result = formatDateToInput('2023-12-25');
      expect(result).toBe('2023-12-25');
    });
  });

  describe('formatRelativeTime', () => {
    it('방금 전 시간을 올바르게 표시해야 함', () => {
      const now = new Date();
      const result = formatRelativeTime(now);
      expect(result).toBe('방금 전');
    });

    it('몇 분 전을 올바르게 표시해야 함', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      const result = formatRelativeTime(fiveMinutesAgo);
      expect(result).toBe('5분 전');
    });

    it('몇 시간 전을 올바르게 표시해야 함', () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
      const result = formatRelativeTime(twoHoursAgo);
      expect(result).toBe('2시간 전');
    });
  });

  describe('formatPeriod', () => {
    it('일 단위로 기간을 포맷해야 함', () => {
      expect(formatPeriod(5)).toBe('5일');
    });

    it('주 단위로 기간을 포맷해야 함', () => {
      expect(formatPeriod(14)).toBe('2주');
    });

    it('개월 단위로 기간을 포맷해야 함', () => {
      expect(formatPeriod(60)).toBe('2개월');
    });

    it('년 단위로 기간을 포맷해야 함', () => {
      expect(formatPeriod(730)).toBe('2년');
    });
  });

  describe('isValidDateRange', () => {
    it('현재보다 이전의 유효한 날짜 범위에 대해 true를 반환해야 함', () => {
      const lastYear = new Date();
      lastYear.setFullYear(lastYear.getFullYear() - 1);
      const lastMonth = new Date();
      lastMonth.setMonth(lastMonth.getMonth() - 1);
      
      const startDate = formatDateToISO(lastYear);
      const endDate = formatDateToISO(lastMonth);
      
      expect(isValidDateRange(startDate, endDate)).toBe(true);
    });

    it('시작일이 종료일보다 늦은 경우 false를 반환해야 함', () => {
      expect(isValidDateRange('2023-12-31', '2023-01-01')).toBe(false);
    });

    it('미래 날짜에 대해 false를 반환해야 함', () => {
      const futureDate = new Date();
      futureDate.setFullYear(futureDate.getFullYear() + 1);
      const futureDateString = formatDateToISO(futureDate);
      
      expect(isValidDateRange('2023-01-01', futureDateString)).toBe(false);
    });
  });

  describe('isWeekend', () => {
    it('토요일에 대해 true를 반환해야 함', () => {
      expect(isWeekend('2023-12-23')).toBe(true); // 토요일
    });

    it('일요일에 대해 true를 반환해야 함', () => {
      expect(isWeekend('2023-12-24')).toBe(true); // 일요일
    });

    it('평일에 대해 false를 반환해야 함', () => {
      expect(isWeekend('2023-12-25')).toBe(false); // 월요일
    });
  });

  describe('isBusinessDay', () => {
    it('평일에 대해 true를 반환해야 함', () => {
      expect(isBusinessDay('2023-12-25')).toBe(true); // 월요일
    });

    it('주말에 대해 false를 반환해야 함', () => {
      expect(isBusinessDay('2023-12-23')).toBe(false); // 토요일
      expect(isBusinessDay('2023-12-24')).toBe(false); // 일요일
    });
  });

  describe('isValidDate', () => {
    it('유효한 날짜 문자열에 대해 true를 반환해야 함', () => {
      expect(isValidDate('2023-12-25')).toBe(true);
    });

    it('무효한 날짜 문자열에 대해 false를 반환해야 함', () => {
      expect(isValidDate('invalid-date')).toBe(false);
      expect(isValidDate('')).toBe(false);
    });
  });

  describe('addDays', () => {
    it('날짜에 일수를 추가해야 함', () => {
      const date = new Date('2023-12-25');
      const result = addDays(date, 5);
      expect(result.getDate()).toBe(30);
    });

    it('음수 일수로 날짜를 빼야 함', () => {
      const date = new Date('2023-12-25');
      const result = addDays(date, -5);
      expect(result.getDate()).toBe(20);
    });
  });

  describe('addMonths', () => {
    it('날짜에 월수를 추가해야 함', () => {
      const date = new Date('2023-12-25');
      const result = addMonths(date, 2);
      expect(result.getMonth()).toBe(1); // 2월 (0-based)
      expect(result.getFullYear()).toBe(2024);
    });
  });

  describe('addYears', () => {
    it('날짜에 년수를 추가해야 함', () => {
      const date = new Date('2023-12-25');
      const result = addYears(date, 2);
      expect(result.getFullYear()).toBe(2025);
    });
  });

  describe('getDaysBetween', () => {
    it('두 날짜 간의 일수를 계산해야 함', () => {
      const result = getDaysBetween('2023-01-01', '2023-01-10');
      expect(result).toBe(9);
    });

    it('Date 객체 간의 일수를 계산해야 함', () => {
      const start = new Date('2023-01-01');
      const end = new Date('2023-01-10');
      const result = getDaysBetween(start, end);
      expect(result).toBe(9);
    });
  });

  describe('getBusinessDaysBetween', () => {
    it('두 날짜 간의 영업일수를 계산해야 함', () => {
      // 2023-12-25 (월) ~ 2023-12-29 (금) = 5 영업일
      const result = getBusinessDaysBetween('2023-12-25', '2023-12-29');
      expect(result).toBe(5);
    });

    it('주말이 포함된 기간의 영업일수를 계산해야 함', () => {
      // 2023-12-22 (금) ~ 2023-12-26 (화) = 3 영업일 (금, 월, 화)
      const result = getBusinessDaysBetween('2023-12-22', '2023-12-26');
      expect(result).toBe(3);
    });
  });

  describe('getDateRange', () => {
    it('날짜 범위의 모든 날짜를 반환해야 함', () => {
      const start = new Date('2023-01-01');
      const end = new Date('2023-01-03');
      const result = getDateRange(start, end);
      
      expect(result).toHaveLength(3);
      expect(result[0].getDate()).toBe(1);
      expect(result[1].getDate()).toBe(2);
      expect(result[2].getDate()).toBe(3);
    });
  });

  describe('getBusinessDateRange', () => {
    it('날짜 범위의 영업일만 반환해야 함', () => {
      // 2023-12-22 (금) ~ 2023-12-26 (화) 중 영업일만
      const start = new Date('2023-12-22');
      const end = new Date('2023-12-26');
      const result = getBusinessDateRange(start, end);
      
      // 금요일, 월요일, 화요일 = 3일
      expect(result.length).toBeLessThanOrEqual(5);
      expect(result.every(date => isBusinessDay(date))).toBe(true);
    });
  });

  describe('getPresetDateRanges', () => {
    it('미리 정의된 날짜 범위들을 반환해야 함', () => {
      const presets = getPresetDateRanges();
      
      expect(presets).toHaveProperty('어제');
      expect(presets).toHaveProperty('지난 주');
      expect(presets).toHaveProperty('지난 달');
      expect(presets).toHaveProperty('지난 1년');
      
      expect(presets['지난 1년'].start).toBeInstanceOf(Date);
      expect(presets['지난 1년'].end).toBeInstanceOf(Date);
    });
  });

  describe('getTimezone', () => {
    it('현재 타임존을 반환해야 함', () => {
      const timezone = getTimezone();
      expect(typeof timezone).toBe('string');
      expect(timezone.length).toBeGreaterThan(0);
    });
  });

  describe('formatDateWithTimezone', () => {
    it('특정 타임존으로 날짜를 포맷해야 함', () => {
      const result = formatDateWithTimezone('2023-12-25', 'Asia/Seoul');
      expect(result).toContain('2023');
      expect(result).toContain('12');
      expect(result).toContain('25');
    });

    it('타임존을 지정하지 않으면 현재 타임존을 사용해야 함', () => {
      const result = formatDateWithTimezone('2023-12-25');
      expect(result).toContain('2023');
      expect(result).toContain('12');
      expect(result).toContain('25');
    });
  });
});
