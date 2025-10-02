/**
 * 테스트 픽스처 (목 데이터 생성 헬퍼)
 */

export const createMockBacktest = (overrides: Partial<any> = {}) => ({
  id: 1,
  ticker: 'AAPL',
  strategy: 'buy_and_hold',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  total_return_pct: 15.5,
  total_trades: 2,
  win_rate_pct: 100,
  max_drawdown_pct: -5.2,
  sharpe_ratio: 1.2,
  profit_factor: 2.1,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides
})

export const createMockTrade = (overrides: Partial<any> = {}) => ({
  id: 1,
  date: '2023-01-01',
  type: 'buy',
  ticker: 'AAPL',
  price: 100,
  quantity: 10,
  commission: 1,
  ...overrides
})

export const createMockOHLC = (overrides: Partial<any> = {}) => ({
  date: '2023-01-01',
  open: 100,
  high: 105,
  low: 99,
  close: 103,
  volume: 1000000,
  ...overrides
})

export const createMockEquity = (overrides: Partial<any> = {}) => ({
  date: '2023-01-01',
  equity: 10000,
  ...overrides
})

export const createMockStrategy = (overrides: Partial<any> = {}) => ({
  name: 'buy_and_hold',
  description: 'Simple buy and hold strategy',
  parameters: [],
  category: 'basic',
  ...overrides
})

export const createMockBacktestRequest = (overrides: Partial<any> = {}) => ({
  ticker: 'AAPL',
  strategy: 'buy_and_hold',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  initial_capital: 10000,
  parameters: {},
  ...overrides
})

export const createMockBacktestResult = (overrides: Partial<any> = {}) => ({
  status: 'success',
  backtest_type: 'single_stock',
  data: {
    ticker: 'AAPL',
    strategy: 'buy_and_hold',
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    ohlc_data: [createMockOHLC()],
    equity_data: [createMockEquity()],
    trade_markers: [createMockTrade()],
    indicators: [],
    summary_stats: {
      total_return_pct: 15.5,
      total_trades: 2,
      win_rate_pct: 100,
      max_drawdown_pct: -5.2,
      sharpe_ratio: 1.2,
      profit_factor: 2.1,
    }
  },
  ...overrides
})
