import { describe, it, expect } from 'vitest';

// 기본 설정 가져오기
const getDcaWeeks = (frequency: string): number => {
  const freqMap: Record<string, number> = {
    'weekly_1': 1,
    'weekly_2': 2,
    'monthly_1': 4,    // 매월 (약 4주)
    'monthly_2': 8,    // 2개월마다
    'monthly_3': 12,   // 분기
    'monthly_6': 24,   // 반년
    'monthly_12': 48,  // 1년
  };
  return freqMap[frequency] || 4;
};

// reducer의 recalcAmountsByWeight 함수 복사
const recalcAmountsByWeight = (portfolio: any[], totalInvestment: number, startDate?: string, endDate?: string) => {
  if (!startDate || !endDate || totalInvestment === 0) {
    // 날짜 정보 없으면 기본 계산
    return portfolio.map(s =>
      typeof s.weight === 'number'
        ? { ...s, amount: Math.round((s.weight / 100) * totalInvestment) }
        : s
    );
  }

  const start = new Date(startDate);
  const end = new Date(endDate);
  const timeDiff = end.getTime() - start.getTime();
  const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
  const weeks = Math.floor(days / 7);

  // Step 1: weight 항목들만 먼저 처리해서 총 투자액 누적
  const weightIndices: number[] = [];
  let accumulatedTotal = 0;
  const results = new Map<number, number>(); // index -> amount

  portfolio.forEach((s, index) => {
    if (typeof s.weight === 'number') {
      weightIndices.push(index);
    }
  });

  // Step 2: weight 항목들의 비중 기반 투자액 계산 (마지막은 오차 보정)
  weightIndices.forEach((index, pos) => {
    const s = portfolio[index];
    const isLastWeightItem = pos === weightIndices.length - 1;
    const totalAmountForStock = (s.weight / 100) * totalInvestment;

    if (isLastWeightItem) {
      // 마지막 weight 항목: 오차 보정 (totalInvestment - 이전까지 누적)
      const correctedTotalAmount = totalInvestment - accumulatedTotal;
      
      if (s.investmentType === 'dca') {
        const intervalWeeks = getDcaWeeks(s.dcaFrequency || 'monthly_1');
        const dcaPeriods = Math.max(1, Math.floor(weeks / intervalWeeks) + 1);
        const perPeriodAmount = Math.round(correctedTotalAmount / dcaPeriods);
        results.set(index, perPeriodAmount);
      } else {
        results.set(index, Math.round(correctedTotalAmount));
      }
    } else {
      // 일반 weight 항목
      if (s.investmentType === 'dca') {
        const intervalWeeks = getDcaWeeks(s.dcaFrequency || 'monthly_1');
        const dcaPeriods = Math.max(1, Math.floor(weeks / intervalWeeks) + 1);
        const perPeriodAmount = Math.round(totalAmountForStock / dcaPeriods);
        results.set(index, perPeriodAmount);
        accumulatedTotal += Math.round(totalAmountForStock);
      } else {
        const roundedAmount = Math.round(totalAmountForStock);
        results.set(index, roundedAmount);
        accumulatedTotal += roundedAmount;
      }
    }
  });

  // Step 3: 최종 결과 반영
  return portfolio.map((s, index) => {
    if (results.has(index)) {
      return { ...s, amount: results.get(index)! };
    }
    return s;
  });
};

describe('recalcAmountsByWeight', () => {
  it('should calculate correct DCA amounts for 50/50 portfolio with $10,000', () => {
    const portfolio = [
      {
        symbol: 'AAPL',
        amount: 0,
        weight: 50,
        investmentType: 'dca',
        dcaFrequency: 'monthly_1',
        assetType: 'stock',
      },
      {
        symbol: 'GOOGL',
        amount: 0,
        weight: 50,
        investmentType: 'dca',
        dcaFrequency: 'monthly_1',
        assetType: 'stock',
      },
    ];

    const result = recalcAmountsByWeight(portfolio, 10000, '2025-01-01', '2025-10-31');
    
    console.log('Portfolio after recalc:', result);
    
    // AAPL: $5,000 / 11 periods = $454.55 → $454
    // GOOGL: ($10,000 - $4,994) / 11 = $455
    expect(result[0].amount).toBeGreaterThan(0);
    expect(result[1].amount).toBeGreaterThan(0);
    
    // 검증: 각 종목의 총 투자액 계산
    const aapl_total = result[0].amount * 11;  // 회당 금액 × 11 periods
    const googl_total = result[1].amount * 11; // 회당 금액 × 11 periods
    const combined_total = aapl_total + googl_total;
    
    console.log(`AAPL: $${result[0].amount}/period × 11 = $${aapl_total}`);
    console.log(`GOOGL: $${result[1].amount}/period × 11 = $${googl_total}`);
    console.log(`Total: $${combined_total}`);
    
    // 총 투자액이 $10,000 근처여야 함 (±5%)
    expect(combined_total).toBeGreaterThanOrEqual(9500);
    expect(combined_total).toBeLessThanOrEqual(10500);
  });
});
