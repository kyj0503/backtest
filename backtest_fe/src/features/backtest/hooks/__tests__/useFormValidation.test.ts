import { describe, it, expect } from 'vitest';
import { getBacktestPeriodDays, validateBacktestForm } from '../useFormValidation';
import { initialBacktestFormState, BacktestFormState } from '../../model/types/backtest-form-types';
import { VALIDATION_RULES } from '../../model/strategyConfig';

// A-17: 백엔드는 (end_date - start_date).days < 30이면 422로 거부한다
// (backtest_be_fast/app/api/v1/endpoints/backtest.py). FE가 제출 전에 같은 규칙으로 막는다.

const formWithDates = (startDate: string, endDate: string): BacktestFormState => ({
  ...initialBacktestFormState,
  dates: { startDate, endDate },
  strategy: { selectedStrategy: 'buy_hold_strategy', strategyParams: {} },
  portfolio: [{
    symbol: 'AAPL',
    amount: 10000,
    investmentType: 'lump_sum',
    dcaFrequency: 'monthly_1',
    assetType: 'stock',
  }],
});

const PERIOD_ERROR = '백테스트 기간이 너무 짧습니다';

describe('최소 백테스트 기간 상수', () => {
  it('백엔드 Settings.min_backtest_period_days 기본값(30)과 같다', () => {
    expect(VALIDATION_RULES.MIN_BACKTEST_PERIOD_DAYS).toBe(30);
  });
});

describe('getBacktestPeriodDays', () => {
  it('백엔드와 같이 종료일 - 시작일로 센다', () => {
    expect(getBacktestPeriodDays('2023-01-01', '2023-01-31')).toBe(30);
    expect(getBacktestPeriodDays('2023-01-01', '2023-01-10')).toBe(9);
  });

  it('월·윤년 경계를 넘어도 달력 일수를 센다', () => {
    expect(getBacktestPeriodDays('2024-02-01', '2024-03-02')).toBe(30);
    expect(getBacktestPeriodDays('2023-12-15', '2024-01-14')).toBe(30);
  });

  it('형식이 잘못되면 null', () => {
    expect(getBacktestPeriodDays('2023/01/01', '2023-01-31')).toBeNull();
    expect(getBacktestPeriodDays('2023-01-01', '')).toBeNull();
  });
});

describe('validateBacktestForm — 최소 기간 (A-17)', () => {
  it('30일 미만이면 백엔드와 같은 문구로 오류를 낸다', () => {
    const errors = validateBacktestForm(formWithDates('2023-01-01', '2023-01-10'));
    expect(errors).toContain('백테스트 기간이 너무 짧습니다: 9일 (최소 30일 필요)');
  });

  it('29일은 거부한다', () => {
    const errors = validateBacktestForm(formWithDates('2023-01-01', '2023-01-30'));
    expect(errors.some(e => e.includes(PERIOD_ERROR))).toBe(true);
  });

  it('정확히 30일은 통과한다 (백엔드 경계와 동일)', () => {
    const errors = validateBacktestForm(formWithDates('2023-01-01', '2023-01-31'));
    expect(errors).toEqual([]);
  });

  it('시작일이 종료일 이후면 기간 오류 대신 순서 오류만 낸다', () => {
    const errors = validateBacktestForm(formWithDates('2023-01-31', '2023-01-01'));
    expect(errors).toContain('시작 날짜는 종료 날짜보다 이전이어야 합니다.');
    expect(errors.some(e => e.includes(PERIOD_ERROR))).toBe(false);
  });

  it('날짜가 비어 있으면 기간 오류를 내지 않는다', () => {
    const errors = validateBacktestForm(formWithDates('', '2023-01-31'));
    expect(errors).toContain('시작 날짜를 선택해주세요.');
    expect(errors.some(e => e.includes(PERIOD_ERROR))).toBe(false);
  });
});
