import { describe, it, expect, assert } from 'vitest';
import { DcaFrequency, getDcaPeriodInfo } from '../constants/dcaConfig';
import { Stock } from '../types/backtest-form-types';

// DCA 주기를 근사 일수로 변환하는 헬퍼 함수
const getDcaApproxDays = (frequency: DcaFrequency): number => {
  const { type, interval } = getDcaPeriodInfo(frequency);
  if (type === 'weekly') {
    return interval * 7;
  } else if (type === 'monthly') {
    return interval * 30; // 월 평균 30일
  }
  return 30;
};

// reducer의 recalcAmountsByWeight 함수 복사
const recalcAmountsByWeight = (portfolio: Stock[], totalInvestment: number, startDate?: string, endDate?: string) => {
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

  // Step 1: weight 항목들만 먼저 처리해서 총 투자액 누적
  const weightEntries: { index: number; stock: Stock }[] = [];
  let accumulatedTotal = 0;
  const results = new Map<number, number>(); // index -> amount

  portfolio.forEach((s, index) => {
    if (typeof s.weight === 'number') {
      weightEntries.push({ index, stock: s });
    }
  });

  // Step 2: weight 항목들의 비중 기반 투자액 계산 (마지막은 오차 보정)
  weightEntries.forEach(({ index, stock: s }, pos) => {
    const isLastWeightItem = pos === weightEntries.length - 1;
    const totalAmountForStock = ((s.weight ?? 0) / 100) * totalInvestment;

    if (isLastWeightItem) {
      // 마지막 weight 항목: 오차 보정 (totalInvestment - 이전까지 누적)
      const correctedTotalAmount = totalInvestment - accumulatedTotal;

      if (s.investmentType === 'dca') {
        const intervalDays = getDcaApproxDays(s.dcaFrequency || 'monthly_1');
        const dcaPeriods = Math.max(1, Math.floor(days / intervalDays) + 1);
        const perPeriodAmount = Math.round(correctedTotalAmount / dcaPeriods);
        results.set(index, perPeriodAmount);
      } else {
        results.set(index, Math.round(correctedTotalAmount));
      }
    } else {
      // 일반 weight 항목
      if (s.investmentType === 'dca') {
        const intervalDays = getDcaApproxDays(s.dcaFrequency || 'monthly_1');
        const dcaPeriods = Math.max(1, Math.floor(days / intervalDays) + 1);
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
    const amount = results.get(index);
    if (amount !== undefined) {
      return { ...s, amount };
    }
    return s;
  });
};

describe('recalcAmountsByWeight', () => {
  it('should calculate correct DCA amounts for 50/50 portfolio with $10,000', () => {
    const portfolio: Stock[] = [
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

    // 입력 종목 수만큼 그대로 반환되어야 한다 (항목 유실/추가 금지)
    expect(result).toHaveLength(2);
    const [aapl, googl] = result;
    assert.isDefined(aapl);
    assert.isDefined(googl);
    expect(aapl.symbol).toBe('AAPL');
    expect(googl.symbol).toBe('GOOGL');

    // AAPL: $5,000 / 11 periods = $454.55 → $454
    // GOOGL: ($10,000 - $4,994) / 11 = $455
    expect(aapl.amount).toBeGreaterThan(0);
    expect(googl.amount).toBeGreaterThan(0);

    // 검증: 각 종목의 총 투자액 계산
    const aapl_total = aapl.amount * 11;  // 회당 금액 × 11 periods
    const googl_total = googl.amount * 11; // 회당 금액 × 11 periods
    const combined_total = aapl_total + googl_total;

    // 총 투자액이 $10,000 근처여야 함 (±5%)
    expect(combined_total).toBeGreaterThanOrEqual(9500);
    expect(combined_total).toBeLessThanOrEqual(10500);
  });
});
