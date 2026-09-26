/**
 * 백테스트 검증 규칙 및 기본값
 */

export const VALIDATION_RULES = {
  MIN_DATE: '2000-01-01',
  MAX_DATE: '2030-12-31',
  MIN_AMOUNT: 100,
  MAX_AMOUNT: 10000000,
  MIN_COMMISSION: 0,
  MAX_COMMISSION: 5,
  MIN_WEIGHT: 0,
  MAX_WEIGHT: 100,
  MIN_STOCKS: 1,
  MAX_STOCKS: 20,
  MAX_PORTFOLIO_SIZE: 20,
  SYMBOL_MAX_LENGTH: 10,
  // 최소 백테스트 기간(일). 출처: 백엔드 Settings.min_backtest_period_days
  // (backtest_be_fast/app/core/config.py)와 이를 강제하는 엔드포인트 검증
  // (backtest_be_fast/app/api/v1/endpoints/backtest.py, 미달 시 422).
  // 연환산 지표(CAGR·샤프 지수 등)는 30일 미만 구간에서 의미가 없어 둔 하한이다.
  // 백엔드 값을 바꾸면 이 값도 함께 바꿀 것 — 어긋나면 FE가 통과시킨 요청을
  // BE가 422로 거부하거나, BE가 받아 줄 요청을 FE가 막는다.
  MIN_BACKTEST_PERIOD_DAYS: 30
};

// 백테스트 기본값
export const DEFAULT_VALUES = {
  START_DATE: '2023-01-01',
  END_DATE: '2024-12-31',
  INITIAL_AMOUNT: 10000,
  COMMISSION: 0.2, // 퍼센트
  DCA_FREQUENCY: 'monthly_1' as const,
  REBALANCE_FREQUENCY: 'monthly_1',
  STRATEGY: 'buy_hold_strategy'
};
