/**
 * DCA 투자 횟수 계산 유틸
 *
 * **역할**:
 * - DCA 기간을 정확하게 계산하는 공유 함수
 * - 중복 제거로 유지보수성 향상
 * - 백테스트 기간과 DCA 주기를 기반으로 투자 횟수 계산
 *
 * **계산 공식**:
 * 1. 백테스트 기간을 주 단위로 변환
 * 2. DCA 주기(주)로 나누어 기본 횟수 계산
 * 3. +1 하여 0주차(첫 투자) 포함
 *
 * **예시**:
 * - 40주 기간 + 4주 주기 → 40/4 = 10, +1 = 11회
 * - 52주 기간 + 24주 주기 → 52/24 = 2.16, floor = 2, +1 = 3회
 *
 * **의존성**:
 * - model/strategyConfig.ts: getDcaWeeks 함수
 *
 * **사용 위치**:
 * - backtestFormReducer.ts: recalcAmountsByWeight 함수
 * - PortfolioForm.tsx: 인라인 가중치 계산
 * - portfolioCalculations.ts: getDcaAdjustedTotal 함수
 */

import { getDcaWeeks, type DcaFrequency } from '../model/strategyConfig';

/**
 * DCA 투자 횟수를 계산합니다.
 * @param startDate - 백테스트 시작 날짜 (YYYY-MM-DD)
 * @param endDate - 백테스트 종료 날짜 (YYYY-MM-DD)
 * @param frequency - DCA 주기 (weekly_1, weekly_2, weekly_4, ...)
 * @returns DCA 투자 횟수 (최소 1)
 */
export const calculateDcaPeriods = (
  startDate: string,
  endDate: string,
  frequency: DcaFrequency
): number => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  // 백테스트 기간을 일 단위로 계산
  const timeDiff = end.getTime() - start.getTime();
  const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
  
  // 주 단위로 변환
  const weeks = Math.floor(days / 7);
  
  // DCA 주기(주)
  const intervalWeeks = getDcaWeeks(frequency);
  
  // 투자 횟수 = (백테스트 기간(주) / 투자 간격(주)) + 1 (0주차 첫 투자 포함)
  return Math.max(1, Math.floor(weeks / intervalWeeks) + 1);
};
