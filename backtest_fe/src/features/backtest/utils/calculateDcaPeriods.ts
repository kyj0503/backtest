/**
 * DCA 투자 횟수 계산 유틸
 *
 * **역할**:
 * - DCA 기간을 근사적으로 계산하는 공유 함수 (UI 표시용)
 * - 중복 제거로 유지보수성 향상
 * - 백테스트 기간과 DCA 주기를 기반으로 투자 횟수 추정
 *
 * **계산 공식 (30일 근사)**:
 * 1. 백테스트 기간을 일 단위로 계산
 * 2. 주기 타입에 따라 근사 일수 계산
 *    - weekly: interval × 7일
 *    - monthly: interval × 30일 (근사)
 * 3. 투자 횟수 = (백테스트 일수 / 주기 일수) + 1
 *
 * **주의**:
 * - 이 함수는 30일 근사를 사용하여 빠른 추정값 제공 (UI 표시용)
 * - 실제 백테스트는 백엔드의 정확한 Nth Weekday 로직 사용 (28~35일 간격)
 * - DCA 횟수 차이: ±1~2회 오차 가능 (장기 백테스트 시)
 * - 총 투자금액 계산은 근사값이며, 실제 백테스트 결과와 차이가 있을 수 있음
 * - DcaPreview에 표시되는 횟수와 총액은 참고용 추정값
 *
 * **예시**:
 * - 300일 기간 + monthly_1 (30일) → 300/30 = 10, +1 = 11회 (실제: 10~11회)
 * - 180일 기간 + monthly_3 (90일) → 180/90 = 2, +1 = 3회 (실제: 2~3회)
 *
 * **의존성**:
 * - model/constants/dcaConfig.ts: getDcaPeriodInfo 함수
 *
 * **사용 위치**:
 * - backtestFormReducer.ts: recalcAmountsByWeight 함수
 * - PortfolioForm.tsx: 인라인 가중치 계산
 * - portfolioCalculations.ts: getDcaAdjustedTotal 함수
 */

import { getDcaPeriodInfo, type DcaFrequency } from '../model/constants/dcaConfig';

/**
 * DCA 투자 횟수를 계산합니다.
 * @param startDate - 백테스트 시작 날짜 (YYYY-MM-DD)
 * @param endDate - 백테스트 종료 날짜 (YYYY-MM-DD)
 * @param frequency - DCA 주기 (weekly_1, weekly_2, monthly_1, ...)
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
  
  // 주기 정보 가져오기
  const { type, interval } = getDcaPeriodInfo(frequency);
  
  // 주기를 일 단위로 변환 (근사값)
  // UI 표시용 30일 근사 사용 - 상세 내용은 함수 독스트링 참조
  let intervalDays: number;
  if (type === 'weekly') {
    intervalDays = interval * 7;
  } else if (type === 'monthly') {
    intervalDays = interval * 30; // 월 평균 30일로 근사
  } else {
    intervalDays = 30; // 기본값
  }
  
  // 투자 횟수 = (백테스트 기간(일) / 투자 간격(일)) + 1 (첫 투자 포함)
  return Math.max(1, Math.floor(days / intervalDays) + 1);
};
