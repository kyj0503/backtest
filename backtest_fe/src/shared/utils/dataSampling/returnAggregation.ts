/**
 * 수익률 집계 (dataSampling 내부 모듈)
 *
 * 일간 수익률을 주간/월간 버킷의 복리 수익률로 합성한다. 가격 샘플링과 달리
 * 버킷 안의 모든 일간 수익률이 결과에 반영된다.
 */

import { parseLocalDate, getWeekdayOccurrence, getNextMonthNthWeekday } from './calendar';

/**
 * 일간 수익률을 주간/월간 수익률로 변환
 *
 * @param dailyReturns 일간 수익률 데이터 { date: string, return_pct: number }
 * @param aggregationType 'daily' | 'weekly' | 'monthly'
 * @returns 집계된 수익률 데이터
 */
export function aggregateReturns<T extends { date: string; return_pct: number }>(
  dailyReturns: T[],
  aggregationType: 'daily' | 'weekly' | 'monthly'
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];

  // 명시적으로 daily 처리 (타입 안정성 향상)
  if (aggregationType === 'daily') return dailyReturns;
  if (aggregationType === 'weekly') return aggregateWeeklyReturns(dailyReturns);
  if (aggregationType === 'monthly') return aggregateMonthlyReturns(dailyReturns);

  return dailyReturns;
}

/**
 * 주간 수익률 계산 (7일 단위, 복리 기반)
 * 
 * ⚠️ 주의: 배열 인덱스 기반 집계로, 실제 달력 주 경계와 일치하지 않을 수 있습니다.
 * - 데이터가 월요일이 아닌 날짜에 시작하면 첫 주는 7일 미만일 수 있습니다.
 * - 금융 백테스트에서 주간 리밸런싱 등의 경우 실제 주 경계(월~일)와 다를 수 있습니다.
 * - 매 7번째 항목마다 집계되므로 중간에 거래일이 없는 날이 있어도 카운트됩니다.
 * 
 * @param dailyReturns 일간 수익률 배열
 * @returns 7일 단위로 집계된 복리 수익률
 */
function aggregateWeeklyReturns<T extends { date: string; return_pct: number }>(
  dailyReturns: T[]
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];

  const weekly: T[] = [];
  const DAYS_PER_WEEK = 7;
  let currentWeekData: T[] = [];

  for (let i = 0; i < dailyReturns.length; i++) {
    const item = dailyReturns[i];
    if (!item) continue;
    currentWeekData.push(item);

    // 7일마다 또는 마지막 데이터일 때 주간 수익률 계산
    if ((i + 1) % DAYS_PER_WEEK === 0 || i === dailyReturns.length - 1) {
      if (currentWeekData.length > 0) {
        const weeklyReturn = calculateCompoundReturn(currentWeekData);
        const lastDay = currentWeekData[currentWeekData.length - 1];
        if (lastDay) {
          weekly.push({
            ...lastDay,
            return_pct: weeklyReturn,
          });
        }
        currentWeekData = [];
      }
    }
  }

  return weekly;
}

/**
 * 월간 수익률 계산 (실제 달력 월 기준, 복리 기반)
 *
 * ⚠️ 주의: 실제 달력 월 경계로 집계됩니다.
 * - Nth Weekday 방식: 시작일이 1월 10일(2번째 수요일)이면, 2월의 2번째 수요일까지가 한 달
 * - 백엔드의 DCA/리밸런싱 로직과 동일한 방식으로 월 경계를 계산합니다
 * - 복리 수익률: (1 + r1) * (1 + r2) * ... - 1
 *
 * @param dailyReturns 일간 수익률 배열
 * @returns 실제 달력 월 단위로 집계된 복리 수익률
 */
function aggregateMonthlyReturns<T extends { date: string; return_pct: number }>(
  dailyReturns: T[]
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];

  const monthly: T[] = [];

  // 시작 날짜의 "몇 번째 요일" 계산 (로컬 타임존)
  const firstItem = dailyReturns[0];
  if (!firstItem) return [];
  const startDate = parseLocalDate(firstItem.date);
  const originalNth = getWeekdayOccurrence(startDate);

  let currentMonthData: T[] = [];
  let currentMonthEndDate = getNextMonthNthWeekday(startDate, originalNth);

  for (let i = 0; i < dailyReturns.length; i++) {
    const item = dailyReturns[i];
    if (!item) continue;
    const itemDate = parseLocalDate(item.date);

    // 다음 달 경계를 넘었거나 마지막 데이터일 때
    const isLastItem = i === dailyReturns.length - 1;
    const crossedMonthBoundary = itemDate >= currentMonthEndDate;

    if (crossedMonthBoundary || isLastItem) {
      // 여러 달을 건너뛴 경우 처리 (마지막 아이템 포함)
      // Note: 데이터가 없는 달은 월별 집계에 포함하지 않음 (의도된 동작)
      // 예: 상장폐지/거래정지로 3개월 갭 발생 시, 해당 3개월은 결과에 나타나지 않음
      // 백엔드도 동일하게 처리 (실제 거래 데이터가 있는 월만 집계)
      let itemAddedInWhile = false;
      let safetyCounter = 0;
      const MAX_MONTH_ITERATIONS = 60; // 5년치 월 수 (안전장치)
      
      while (itemDate >= currentMonthEndDate) {
        if (++safetyCounter > MAX_MONTH_ITERATIONS) {
          console.error('[dataSampling] Monthly aggregation exceeded safety limit');
          break;
        }
        
        if (currentMonthData.length > 0) {
          // 현재 달 데이터 마감
          const monthlyReturn = calculateCompoundReturn(currentMonthData);
          const lastDay = currentMonthData[currentMonthData.length - 1];
          if (lastDay) {
            monthly.push({
              ...lastDay,
              return_pct: monthlyReturn,
            });
          }
          currentMonthData = [];
        }
        
        // 다음 달 경계로 이동
        currentMonthEndDate = getNextMonthNthWeekday(currentMonthEndDate, originalNth);
        
        // 현재 아이템이 새로운 경계 내에 있으면 추가하고 종료
        if (itemDate < currentMonthEndDate) {
          currentMonthData.push(item);
          itemAddedInWhile = true;
          break;
        }
      }
      
      // 마지막 아이템 처리 (while 루프를 거치지 않은 경우만)
      // while 조건이 처음부터 false였다면 (itemDate < currentMonthEndDate)
      if (isLastItem && itemDate < currentMonthEndDate && !itemAddedInWhile) {
        currentMonthData.push(item);
      }
      
      // 마지막 아이템 처리: 남은 데이터 마감
      if (isLastItem && currentMonthData.length > 0) {
        const monthlyReturn = calculateCompoundReturn(currentMonthData);
        const lastDay = currentMonthData[currentMonthData.length - 1];
        if (lastDay) {
          monthly.push({
            ...lastDay,
            return_pct: monthlyReturn,
          });
        }
      }
    } else {
      // 경계를 넘지 않은 경우 현재 달 데이터에 추가
      currentMonthData.push(item);
    }
  }

  return monthly;
}

/**
 * 복리 수익률 계산
 * 
 * @param returns 일간 수익률 배열
 * @returns 누적 복리 수익률 (백분율)
 */
function calculateCompoundReturn<T extends { return_pct: number }>(returns: T[]): number {
  if (returns.length === 0) return 0;

  // 복리 공식: (1 + r1) * (1 + r2) * ... - 1
  let compoundedValue = 1;
  for (const item of returns) {
    const dailyReturn = item.return_pct / 100; // 백분율 → 소수
    compoundedValue *= (1 + dailyReturn);
  }

  return (compoundedValue - 1) * 100; // 소수 → 백분율
}
