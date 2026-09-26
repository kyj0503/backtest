/**
 * 기간 기반 스마트 샘플링 (dataSampling 내부 모듈, 공개 API는 index.ts)
 *
 * **역할**:
 * - 대량의 차트 데이터 포인트를 성능 최적화를 위해 샘플링
 * - 백테스트 기간에 따라 적절한 시간 단위로 집계
 * - 시각적 품질을 유지하면서 렌더링 부하 감소
 * 
 * **전략**:
 * - 1일: 오류 (최소 2일 이상 필요)
 * - 2일 ~ 2년: 일간 데이터 (원본 그대로)
 * - 2년 초과 ~ 5년: 주간 데이터
 * - 5년 초과 ~ 10년: 월간 데이터
 * - 10년 초과: 월간 데이터 + 경고
 */

import { aggregateToWeekly, aggregateToMonthly } from './priceSampling';

/** 차트 데이터 집계 단위 */
export type AggregationType = 'daily' | 'weekly' | 'monthly';

/**
 * 백테스트 기간 계산 (년 단위)
 * 
 * @param startDate 시작 날짜 (문자열 또는 Date 객체)
 * @param endDate 종료 날짜 (문자열 또는 Date 객체)
 * @returns 백테스트 기간 (년 단위)
 * @throws Error 유효하지 않은 날짜 또는 endDate가 startDate보다 작은 경우
 */
function calculateYearDuration(startDate: string | Date, endDate: string | Date): number {
  const start = typeof startDate === 'string' ? new Date(startDate) : startDate;
  const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
  
  // 날짜 유효성 검증
  if (isNaN(start.getTime())) {
    throw new Error(`유효하지 않은 시작 날짜: ${startDate}`);
  }
  if (isNaN(end.getTime())) {
    throw new Error(`유효하지 않은 종료 날짜: ${endDate}`);
  }
  
  const diffMs = end.getTime() - start.getTime();
  
  // 종료 날짜가 시작 날짜보다 작은 경우
  if (diffMs < 0) {
    throw new Error(`종료 날짜가 시작 날짜보다 작을 수 없습니다: ${startDate} ~ ${endDate}`);
  }
  
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays / 365.25; // 윤년 고려
}

/**
 * 백테스트 기간에 따른 스마트 샘플링
 * 
 * @param data 원본 데이터 (date 필드 필수)
 * @param startDate 백테스트 시작일
 * @param endDate 백테스트 종료일
 * @returns 집계된 데이터 및 메타 정보
 */
export function smartSampleByPeriod<T extends { date: string }>(
  data: T[],
  startDate?: string | Date,
  endDate?: string | Date
): {
  data: T[];
  aggregationType: AggregationType;
  warning?: string;
} {
  if (!data || data.length === 0) {
    return { data: [], aggregationType: 'daily' };
  }

  // 날짜 정보가 없으면 원본 반환
  if (!startDate || !endDate) {
    return { data, aggregationType: 'daily' };
  }

  const yearDuration = calculateYearDuration(startDate, endDate);

  // 1일 미만: 원본 데이터 반환 (다운스트림 처리 안전성)
  if (yearDuration < (2 / 365.25)) {
    return {
      data,
      aggregationType: 'daily',
      warning: '백테스트 기간은 최소 2일 이상이어야 합니다.',
    };
  }

  // 2일 ~ 2년: 일간 데이터 (원본 그대로)
  if (yearDuration <= 2) {
    return { data, aggregationType: 'daily' };
  }

  // 2년 초과 ~ 5년: 주간 데이터
  if (yearDuration <= 5) {
    return {
      data: aggregateToWeekly(data),
      aggregationType: 'weekly',
    };
  }

  // 5년 초과: 월간 데이터
  const warning = yearDuration > 10 ? '10년 초과 백테스트는 월간 데이터로 표시됩니다.' : undefined;
  
  return {
    data: aggregateToMonthly(data),
    aggregationType: 'monthly',
    warning,
  };
}
