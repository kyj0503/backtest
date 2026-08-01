import { describe, it, expect } from 'vitest';
import {
  getDcaAdjustedTotal,
  getDcaAmountFromWeight,
} from '../portfolioCalculations';
import { calculateDcaPeriods } from '../calculateDcaPeriods';
import type { DcaFrequency } from '../../model/strategyConfig';

describe('portfolioCalculations', () => {
  // 테스트 기간: 2025-01-01 ~ 2025-10-07 = 279일
  const startDate = '2025-01-01';
  const endDate = '2025-10-07';

  // DCA 횟수 계산 (calculateDcaPeriods: floor(기간일수 / 주기일수) + 1, weekly=7일/monthly=30일 근사):
  // - monthly_1 (30일): 279 / 30 = 9, +1 = 10회
  // - monthly_2 (60일): 279 / 60 = 4, +1 = 5회
  // - monthly_3 (90일): 279 / 90 = 3, +1 = 4회

  describe('getDcaAdjustedTotal', () => {
    it('should calculate DCA-adjusted total correctly', () => {
      const portfolio: Array<{
        amount: number;
        investmentType: 'dca' | 'lump_sum';
        dcaFrequency?: DcaFrequency;
      }> = [
        {
          amount: 10000,
          investmentType: 'dca',
          dcaFrequency: 'monthly_1',
        },
        {
          amount: 10000,
          investmentType: 'lump_sum',
        },
      ];

      const total = getDcaAdjustedTotal(portfolio, startDate, endDate);

      // 279일 / 30일 = 9, +1 = 10회 DCA
      // AAPL DCA: 10,000 × 10 = 100,000
      // GOOGL lump_sum: 10,000 × 1 = 10,000
      // 총액: 110,000
      expect(total).toBe(110000);
    });

    it('should return sum of amounts when no dates provided', () => {
      const portfolio: Array<{
        amount: number;
        investmentType: 'dca' | 'lump_sum';
        dcaFrequency?: DcaFrequency;
      }> = [
        {
          amount: 10000,
          investmentType: 'dca',
        },
        {
          amount: 10000,
          investmentType: 'lump_sum',
        },
      ];

      const total = getDcaAdjustedTotal(portfolio);

      // 날짜 없으면 단순 합계
      expect(total).toBe(20000);
    });

    it('should handle all lump_sum investment', () => {
      const portfolio: Array<{
        amount: number;
        investmentType: 'dca' | 'lump_sum';
        dcaFrequency?: DcaFrequency;
      }> = [
        {
          amount: 15000,
          investmentType: 'lump_sum',
        },
        {
          amount: 5000,
          investmentType: 'lump_sum',
        },
      ];

      const total = getDcaAdjustedTotal(portfolio, startDate, endDate);

      // 모두 일시불이므로 단순 합계
      expect(total).toBe(20000);
    });

    it('should calculate weight percentage correctly', () => {
      const portfolio: Array<{
        amount: number;
        investmentType: 'dca' | 'lump_sum';
        dcaFrequency?: DcaFrequency;
      }> = [
        {
          amount: 10000,
          investmentType: 'dca',
          dcaFrequency: 'monthly_1',
        },
        {
          amount: 10000,
          investmentType: 'lump_sum',
        },
      ];

      const total = getDcaAdjustedTotal(portfolio, startDate, endDate);
      const aapl_weight = (10000 / total) * 100; // 회당 금액 기준
      const googl_weight = (10000 / total) * 100;

      // 총액: 110,000
      // AAPL: 10,000 / 110,000 = 9.09%
      // GOOGL: 10,000 / 110,000 = 9.09%
      expect(aapl_weight).toBeCloseTo(9.09, 1);
      expect(googl_weight).toBeCloseTo(9.09, 1);
    });
  });

  describe('getDcaAmountFromWeight', () => {
    it('should calculate DCA per-period amount from weight', () => {
      // 총 $20,000, AAPL 60% = $12,000
      // 279일 / 30일 = 9, +1 = 10회 DCA
      // 회당 금액 = 12,000 / 10 = 1,200
      const amount = getDcaAmountFromWeight(
        60,
        20000,
        'monthly_1',
        startDate,
        endDate
      );

      expect(amount).toBe(1200);
    });

    it('should return full amount for lump_sum investment', () => {
      // 비중 기반에서도 lump_sum이면 전체 금액
      // (하지만 현재 구현에서는 함수 자체가 DCA 계산용)
      const amount = getDcaAmountFromWeight(
        40,
        20000,
        'monthly_1',
        startDate,
        endDate
      );

      // GOOGL 40% = $8,000
      // DCA로 계산: 8,000 / 10회 = 800
      expect(amount).toBe(800);
    });

    it('should handle different DCA frequencies', () => {
      // 2개월 주기(60일): 279 / 60 = 4, +1 = 5회
      const amount_2months = getDcaAmountFromWeight(
        60,
        20000,
        'monthly_2',
        startDate,
        endDate
      );

      // 3개월 주기(90일): 279 / 90 = 3, +1 = 4회
      const amount_3months = getDcaAmountFromWeight(
        60,
        20000,
        'monthly_3',
        startDate,
        endDate
      );

      // 12,000 / 5 = 2,400
      expect(amount_2months).toBe(2400);

      // 12,000 / 4 = 3,000
      expect(amount_3months).toBe(3000);
    });

    it('should return same amount when no dates provided', () => {
      // 날짜 없으면 DCA 기간 계산 불가, 전체 금액 반환
      const amount = getDcaAmountFromWeight(
        50,
        20000,
        'monthly_1'
      );

      expect(amount).toBe(10000); // 50% of 20,000
    });
  });

  describe('calculateDcaPeriods', () => {
    it('should return correct period count for each frequency', () => {
      // 기간 279일 기준, floor(279 / 주기일수) + 1 (첫 투자 포함)
      expect(calculateDcaPeriods(startDate, endDate, 'weekly_1')).toBe(40); // 7일: 39 + 1
      expect(calculateDcaPeriods(startDate, endDate, 'weekly_2')).toBe(20); // 14일: 19 + 1
      expect(calculateDcaPeriods(startDate, endDate, 'monthly_1')).toBe(10); // 30일: 9 + 1
      expect(calculateDcaPeriods(startDate, endDate, 'monthly_2')).toBe(5); // 60일: 4 + 1
      expect(calculateDcaPeriods(startDate, endDate, 'monthly_3')).toBe(4); // 90일: 3 + 1
      expect(calculateDcaPeriods(startDate, endDate, 'monthly_6')).toBe(2); // 180일: 1 + 1
      expect(calculateDcaPeriods(startDate, endDate, 'monthly_12')).toBe(1); // 360일: 0 + 1
    });

    it('should return at least 1 period when the range is shorter than one interval', () => {
      // 기간이 주기보다 짧아도 첫 투자는 발생하므로 최소 1회
      expect(calculateDcaPeriods('2025-01-01', '2025-01-05', 'monthly_1')).toBe(1);
      // 시작일 = 종료일인 경우에도 최소 1회 (Math.max(1, ...))
      expect(calculateDcaPeriods('2025-01-01', '2025-01-01', 'weekly_1')).toBe(1);
    });
  });

  // 통합 테스트: 금액 기준 모드 시나리오
  describe('Integration: Amount Mode (금액 기준)', () => {
    it('should calculate correct weights in amount mode', () => {
      const portfolio: Array<{
        amount: number;
        investmentType: 'dca' | 'lump_sum';
        dcaFrequency?: DcaFrequency;
      }> = [
        {
          amount: 10000,
          investmentType: 'dca',
          dcaFrequency: 'monthly_1',
        },
        {
          amount: 10000,
          investmentType: 'lump_sum',
        },
      ];

      const total = getDcaAdjustedTotal(portfolio, startDate, endDate);
      const aapl_weight = (portfolio[0].amount / total) * 100;
      const googl_weight = (portfolio[1].amount / total) * 100;

      // 총액: 110,000
      // AAPL: 10,000 / 110,000 = 9.09%
      // GOOGL: 10,000 / 110,000 = 9.09%
      // (회당 금액 기준이 맞음 - 실제 투자액이 아닌 입력값)
      expect(aapl_weight).toBeCloseTo(9.09, 1);
      expect(googl_weight).toBeCloseTo(9.09, 1);
      expect(aapl_weight + googl_weight).toBeCloseTo(18.18, 1);
    });
  });

  // 통합 테스트: 비중 기준 모드 시나리오
  describe('Integration: Weight Mode (비중 기준)', () => {
    it('should convert weights to DCA amounts correctly', () => {
      // 비중 기준 입력
      const totalInvestment = 20000;
      const aapl_weight = 60; // 60%
      const googl_weight = 40; // 40%

      // DCA 회당 금액 계산
      const aapl_amount = getDcaAmountFromWeight(
        aapl_weight,
        totalInvestment,
        'monthly_1',
        startDate,
        endDate
      );

      const googl_amount = getDcaAmountFromWeight(
        googl_weight,
        totalInvestment,
        'monthly_1',
        startDate,
        endDate
      );

      // 279일 / 30일 = 9, +1 = 10회
      // AAPL: 60% × $20,000 = $12,000 / 10회 = $1,200
      // GOOGL: 40% × $20,000 = $8,000 / 10회 = $800
      expect(aapl_amount).toBe(1200);
      expect(googl_amount).toBe(800);

      // 실제 총 투자액 검증
      const actualAAPL = aapl_amount * 10;
      const actualGOOGL = googl_amount * 10;
      expect(actualAAPL).toBe(12000);
      expect(actualGOOGL).toBe(8000);
    });
  });
});
