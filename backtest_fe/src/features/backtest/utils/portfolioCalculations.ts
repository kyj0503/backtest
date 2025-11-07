/**
 * 포트폴리오 계산 유틸리티
 * 비중, 금액, DCA 등의 계산 로직
 */

/**
 * DCA 주기를 주 수로 변환
 */
export const DCA_WEEKS_MAP: Record<string, number> = {
  weekly_1: 1,
  weekly_2: 2,
  weekly_4: 4,
  weekly_8: 8,
  weekly_12: 12,
  weekly_24: 24,
  weekly_48: 48,
};

/**
 * DCA 주기에 따른 주 수 반환
 */
export const getDcaWeeks = (frequency: string): number => {
  return DCA_WEEKS_MAP[frequency] || 4;
};

/**
 * 회당 투자 금액 계산 (주 단위)
 */
export const calculateDcaPeriodAmount = (totalAmount: number, frequency: string): number => {
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
