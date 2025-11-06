/**
 * 포트폴리오 계산 유틸리티
 * 비중, 금액, DCA 등의 계산 로직
 */

/**
 * DCA 주기를 개월 수로 변환
 */
export const DCA_MONTHS_MAP: Record<string, number> = {
  monthly: 1,
  quarterly: 3,
  semiannually: 6,
  annually: 12,
};

/**
 * DCA 주기에 따른 총 매수 횟수 계산
 */
export const getDcaMonths = (frequency: string): number => {
  return DCA_MONTHS_MAP[frequency] || 1;
};

/**
 * 회당 투자 금액 계산
 */
export const calculateDcaMonthlyAmount = (totalAmount: number, frequency: string): number => {
  const months = getDcaMonths(frequency);
  return Math.round(totalAmount / months);
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
