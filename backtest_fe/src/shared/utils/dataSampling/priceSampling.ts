/**
 * 가격/가치 시계열 샘플링 (dataSampling 내부 모듈)
 *
 * 가격·equity·비중처럼 "그 시점의 값"인 시계열에서 대표 포인트를 골라낸다.
 * 값을 합성하지 않고 원본 항목을 그대로 고른다는 점이 수익률 집계
 * (returnAggregation, 복리 합성)와 다르다.
 */

import { parseLocalDate, getWeekdayOccurrence, getNextMonthNthWeekday } from './calendar';

/**
 * 가격/가치 데이터를 주간 간격으로 샘플링합니다 (단순 샘플링)
 * 
 * ⚠️ 주의:
 * - 이 함수는 가격/가치/equity 데이터용으로, 매 7번째 항목을 선택합니다 (단순 샘플링)
 * - 수익률 데이터는 이 함수를 사용하지 않습니다 (aggregateReturns() 사용)
 * - 배열 인덱스 기반이므로 실제 달력 주(월~일)와 일치하지 않습니다
 * - 예: 데이터가 수요일에 시작하면 첫 "주간" 포인트는 다음 수요일 데이터입니다
 * 
 * @param data 원본 일간 데이터 (가격, equity, value 등)
 * @returns 매 7번째 데이터 포인트만 포함된 배열
 */
export function aggregateToWeekly<T extends { date: string }>(data: T[]): T[] {
  if (!data || data.length === 0) return [];

  const weekly: T[] = [];
  const DAYS_PER_WEEK = 7;

  // 첫 데이터는 항상 포함
  const firstItem = data[0];
  if (!firstItem) return [];
  weekly.push(firstItem);

  // 7일 간격으로 데이터 추출
  for (let i = DAYS_PER_WEEK; i < data.length; i += DAYS_PER_WEEK) {
    const item = data[i];
    if (item) weekly.push(item);
  }

  // 마지막 데이터가 7일 간격에 포함되지 않았다면 추가
  const lastIndex = data.length - 1;
  const lastItem = data[lastIndex];
  if (lastIndex > 0 && lastItem && lastItem !== weekly[weekly.length - 1]) {
    weekly.push(lastItem);
  }

  return weekly;
}

/**
 * 가격/가치 데이터를 월간 간격으로 샘플링합니다 (실제 달력 월 기준)
 *
 * ⚠️ 주의:
 * - 이 함수는 가격/가치/equity 데이터용으로, 실제 달력 월 기준으로 샘플링합니다
 * - 수익률 데이터는 이 함수를 사용하지 않습니다 (aggregateReturns() 사용)
 * - Nth Weekday 방식: 시작일이 1월 10일(2번째 수요일)이면, 다음은 2월의 2번째 수요일
 * - 백엔드의 DCA/리밸런싱 로직과 동일한 방식으로 월 경계를 계산합니다
 *
 * @param data 원본 일간 데이터 (가격, equity, value 등)
 * @returns 실제 달력 월 기준으로 샘플링된 배열
 */
export function aggregateToMonthly<T extends { date: string }>(data: T[]): T[] {
  if (!data || data.length === 0) return [];

  const monthly: T[] = [];

  // 첫 데이터는 항상 포함
  const firstItem = data[0];
  if (!firstItem) return [];
  monthly.push(firstItem);

  // 시작 날짜의 "몇 번째 요일" 계산 (로컬 타임존)
  const startDate = parseLocalDate(firstItem.date);
  const originalNth = getWeekdayOccurrence(startDate);

  // 데이터를 Map으로 변환 (O(1) 조회를 위함)
  const dataByDate = new Map<string, T>();
  for (const item of data) {
    dataByDate.set(item.date, item);
  }

  // 다음 월 날짜 계산하며 샘플링
  let currentDate = startDate;
  const lastItemData = data[data.length - 1];
  if (!lastItemData) return monthly;
  const lastDateStr = lastItemData.date;
  const lastDate = parseLocalDate(lastDateStr);

  // 무한 루프 방지: 백테스트 기간의 최대 월 수 기반 상한 설정
  // data.length는 일별 데이터이므로 너무 큼 (예: 10년 = 2500일)
  // 실제 필요한 반복: 백테스트 월 수 (예: 10년 = ~120회)
  const daysDiff = (lastDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24);
  // 더 견고한 반복 상한: 월 수 추정 (28일/월 기준 + 버퍼), 최소 12회 (1년)
  const estimatedMonths = Math.ceil(daysDiff / 28) + 2;
  const maxIterations = Math.max(estimatedMonths, 12);
  let iterations = 0;

  while (true) {
    // 안전장치: 무한 루프 방지
    if (++iterations > maxIterations) {
      console.error('[dataSampling] Monthly sampling exceeded max iterations');
      break;
    }

    // 다음 달의 Nth Weekday 계산
    const nextDate = getNextMonthNthWeekday(currentDate, originalNth);

    // 실제 거래일 탐색: 계산된 날짜가 비거래일(주말/공휴일)일 수 있으므로
    // 최대 7일 앞으로 이동하며 실제 데이터가 있는 날짜 찾기
    let found = false;
    let searchDate = nextDate;

    for (let dayOffset = 0; dayOffset < 7; dayOffset++) {
      // 로컬 타임존 기준으로 날짜 문자열 생성 (parseLocalDate와 일관성 유지)
      const year = searchDate.getFullYear();
      const month = String(searchDate.getMonth() + 1).padStart(2, '0');
      const day = String(searchDate.getDate()).padStart(2, '0');
      const searchDateStr = `${year}-${month}-${day}`;
      const foundItem = dataByDate.get(searchDateStr);

      if (foundItem) {
        // 마지막 항목과 날짜로 비교하여 중복 방지
        const lastItem = monthly[monthly.length - 1];
        if (lastItem?.date !== foundItem.date) {
          monthly.push(foundItem);
        }
        found = true;
        currentDate = parseLocalDate(foundItem.date);
        break;
      }

      // 다음 날짜로 이동 (1일 증가, DST 및 월/년 경계 자동 처리)
      searchDate = new Date(
        searchDate.getFullYear(),
        searchDate.getMonth(),
        searchDate.getDate() + 1
      );
    }

    // 더 이상 데이터가 없으면 종료
    if (!found) break;

    // 다음 계산된 날짜가 데이터 범위를 벗어나면 종료
    if (nextDate > lastDate) break;
  }

  // 마지막 데이터가 포함되지 않았다면 추가
  const lastItem = data[data.length - 1];
  if (lastItem && monthly[monthly.length - 1] !== lastItem) {
    monthly.push(lastItem);
  }

  return monthly;
}
