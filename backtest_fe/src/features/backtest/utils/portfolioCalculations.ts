/**
 * 포트폴리오 계산 유틸리티
 * 비중, 금액, DCA 등의 계산 로직
 */

import { getDcaWeeks, type DcaFrequency } from '../model/strategyConfig';

/**
 * 회당 투자 금액 계산 (주 단위)
 */
export const calculateDcaPeriodAmount = (totalAmount: number, frequency: DcaFrequency): number => {
  const weeks = getDcaWeeks(frequency);
  return Math.round(totalAmount / weeks);
};

/**
 * 포트폴리오 총 투자 금액 계산
 */
export const calculateTotalAmount = (portfolio: Array<{ amount: number }>): number => {
  return portfolio.reduce((sum, stock) => sum + (stock.amount || 0), 0);
};

/**
 * 비중을 금액으로 변환
 */
export const weightToAmount = (weight: number, totalInvestment: number): number => {
  return (weight / 100) * totalInvestment;
};

/**
 * 금액을 비중으로 변환
 */
export const amountToWeight = (amount: number, totalAmount: number): number => {
  if (totalAmount === 0) return 0;
  return (amount / totalAmount) * 100;
};

/**
 * 비중 계산 (amountToWeight의 별칭)
 * @deprecated Use amountToWeight instead
 */
export const calculateWeight = amountToWeight;

/**
 * 포트폴리오 비중 합계 계산
 */
export const calculateTotalWeight = (portfolio: Array<{ weight?: number }>): number => {
  return portfolio.reduce((sum, stock) => sum + (stock.weight || 0), 0);
};

/**
 * 비중 검증 (합계가 100%인지)
 */
export const validateWeightSum = (portfolio: Array<{ weight?: number }>): boolean => {
  const total = calculateTotalWeight(portfolio);
  return Math.abs(total - 100) < 0.01; // 소수점 오차 허용
};

/**
 * DCA를 고려한 총 투자 금액 계산
 * 분할매수(DCA)의 경우 회당 금액 × 투자 횟수로 실제 총액 계산
 * 
 * @param portfolio - 포트폴리오 배열
 * @param startDate - 백테스트 시작 날짜 (DCA 기간 계산용)
 * @param endDate - 백테스트 종료 날짜 (DCA 기간 계산용)
 * @returns DCA를 고려한 총 투자 금액
 */
export const getDcaAdjustedTotal = (
  portfolio: Array<{
    amount: number;
    investmentType?: 'lump_sum' | 'dca';
    dcaFrequency?: DcaFrequency;
  }>,
  startDate?: string,
  endDate?: string
): number => {
  if (!startDate || !endDate) {
    // 날짜가 없으면 DCA 횟수 계산 불가, 입력된 amount 합계 반환
    return portfolio.reduce((sum, stock) => sum + (stock.amount || 0), 0);
  }

  const start = new Date(startDate);
  const end = new Date(endDate);
  const timeDiff = end.getTime() - start.getTime();
  const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
  const weeks = Math.floor(days / 7);

  return portfolio.reduce((sum, stock) => {
    const amount = stock.amount || 0;
    
    if (stock.investmentType === 'dca') {
      // DCA: 회당 금액 × (투자 횟수)
      // 투자 횟수 = (백테스트 기간(주) / 투자 간격(주)) + 1 (0주차 첫 투자 포함)
      const intervalWeeks = getDcaWeeks(stock.dcaFrequency || 'weekly_4');
      const dcaPeriods = Math.max(1, Math.floor(weeks / intervalWeeks) + 1);
      return sum + (amount * dcaPeriods);
    } else {
      // 일시불: 입력한 금액 그대로
      return sum + amount;
    }
  }, 0);
};

/**
 * 비중 기준 모드에서 DCA를 고려한 회당 투자 금액 계산
 * 
 * @param weight - 종목의 비중(%)
 * @param totalInvestment - 전체 투자 금액
 * @param dcaFrequency - DCA 주기
 * @param startDate - 백테스트 시작 날짜
 * @param endDate - 백테스트 종료 날짜
 * @returns 회당 투자 금액
 */
export const getDcaAmountFromWeight = (
  weight: number,
  totalInvestment: number,
  dcaFrequency: DcaFrequency,
  startDate?: string,
  endDate?: string
): number => {
  // 총액 = 비중 × 전체 투자금액
  const totalAmount = (weight / 100) * totalInvestment;
  
  if (!startDate || !endDate) {
    // 날짜가 없으면 DCA 기간 계산 불가, 전체 비중금액 반환
    return Math.round(totalAmount);
  }

  const start = new Date(startDate);
  const end = new Date(endDate);
  const timeDiff = end.getTime() - start.getTime();
  const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
  const weeks = Math.floor(days / 7);

  // DCA 투자 횟수 = (백테스트 기간(주) / 투자 간격(주)) + 1
  const intervalWeeks = getDcaWeeks(dcaFrequency || 'weekly_4');
  const dcaPeriods = Math.max(1, Math.floor(weeks / intervalWeeks) + 1);

  // 회당 투자 금액 = 총액 / 투자 횟수
  return Math.round(totalAmount / dcaPeriods);
};

