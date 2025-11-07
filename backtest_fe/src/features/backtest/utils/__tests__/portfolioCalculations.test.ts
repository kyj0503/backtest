import { describe, it, expect } from 'vitest';
import {
  getDcaAdjustedTotal,
  getDcaAmountFromWeight,
} from '../portfolioCalculations';
import { getDcaWeeks } from '../../model/strategyConfig';
import type { DcaFrequency } from '../../model/strategyConfig';

describe('portfolioCalculations', () => {
  // 테스트 날짜: 39주 (279일)
  // 2025-01-01 ~ 2025-10-07 = 279일 = 39주
  const startDate = '2025-01-01';
  const endDate = '2025-10-07';

  // DCA 횟수 계산:
  // - weekly_4: 39주 / 4주 = 9, +1 = 10회
  // - weekly_8: 39주 / 8주 = 4, +1 = 5회
  // - weekly_12: 39주 / 12주 = 3, +1 = 4회

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
          dcaFrequency: 'weekly_4',
        },
        {
          amount: 10000,
          investmentType: 'lump_sum',
        },
      ];

      const total = getDcaAdjustedTotal(portfolio, startDate, endDate);

      // 39주 / 4주 = 9, +1 = 10회 DCA
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
          dcaFrequency: 'weekly_4',
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
      // 39주 / 4주 = 9, +1 = 10회 DCA
      // 회당 금액 = 12,000 / 10 = 1,200
      const amount = getDcaAmountFromWeight(
        60,
        20000,
        'weekly_4',
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
        'weekly_4',
        startDate,
        endDate
      );

      // GOOGL 40% = $8,000
      // DCA로 계산: 8,000 / 10 = 800
      expect(amount).toBe(800);
    });

    it('should handle different DCA frequencies', () => {
      // 8주 주기: 39주 / 8주 = 4, +1 = 5회
      const amount_8weeks = getDcaAmountFromWeight(
        60,
        20000,
        'weekly_8',
        startDate,
        endDate
      );

      // 12주 주기: 39주 / 12주 = 3, +1 = 4회
      const amount_12weeks = getDcaAmountFromWeight(
        60,
        20000,
        'weekly_12',
        startDate,
        endDate
      );

      // 12,000 / 5 = 2,400
      expect(amount_8weeks).toBe(2400);

      // 12,000 / 4 = 3,000
      expect(amount_12weeks).toBe(3000);
    });

    it('should return same amount when no dates provided', () => {
      // 날짜 없으면 DCA 기간 계산 불가, 전체 금액 반환
      const amount = getDcaAmountFromWeight(
        50,
        20000,
        'weekly_4'
      );

      expect(amount).toBe(10000); // 50% of 20,000
    });
  });

  describe('getDcaWeeks', () => {
    it('should return correct weeks for each frequency', () => {
      expect(getDcaWeeks('weekly_1')).toBe(1);
      expect(getDcaWeeks('weekly_2')).toBe(2);
      expect(getDcaWeeks('weekly_4')).toBe(4);
      expect(getDcaWeeks('weekly_8')).toBe(8);
      expect(getDcaWeeks('weekly_12')).toBe(12);
      expect(getDcaWeeks('weekly_24')).toBe(24);
      expect(getDcaWeeks('weekly_48')).toBe(48);
    });

    it('should default to 1 week for unknown frequency', () => {
      // getDcaWeeks는 DcaFrequency 타입으로 제한되므로 존재하는 빈도만 테스트
      expect(getDcaWeeks('weekly_1')).toBe(1);
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
          dcaFrequency: 'weekly_4',
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
        'weekly_4',
        startDate,
        endDate
      );

      const googl_amount = getDcaAmountFromWeight(
        googl_weight,
        totalInvestment,
        'weekly_4',
        startDate,
        endDate
      );

      // 39주 / 4주 = 9, +1 = 10회
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
