/**
 * 결과 화면 테스트용 응답 픽스처 (A-12)
 *
 * 백엔드 POST /api/v1/backtest 응답의 `data` 부분을 흉내 낸다. 형태는
 * `portfolio_manager_service.py`의 buy&hold 경로와 `backtest-result-types.ts`를
 * 기준으로 했다. 기간은 일간 집계 구간(2년 미만)에 들도록 짧게 잡아
 * 샘플링이 개입하지 않게 한다.
 *
 * 승률·프로핏 팩터·연간 수익률은 의미와 표시가 바뀌는 중이라(다른 작업),
 * 이 픽스처 값에 기대는 단정을 테스트에 쓰지 않는다. 값은 타입을 채우기 위한 것이다.
 */
import type {
  ChartData,
  PortfolioData,
  PortfolioStatistics,
} from '@/features/backtest/model/types/backtest-result-types'
import type { UnifiedBacktestResponse } from '@/features/backtest/model/types/api-types'

export const RESULT_DATES = [
  '2023-01-02',
  '2023-01-03',
  '2023-01-04',
  '2023-01-05',
  '2023-01-06',
  '2023-01-09',
  '2023-01-10',
  '2023-01-11',
] as const

const series = <T>(fn: (i: number) => T): Record<string, T> =>
  Object.fromEntries(RESULT_DATES.map((d, i) => [d, fn(i)]))

export const makePortfolioStatistics = (
  overrides: Partial<PortfolioStatistics> = {}
): PortfolioStatistics => ({
  Start: RESULT_DATES[0],
  End: RESULT_DATES[7],
  Duration: '9 days',
  Initial_Value: 10000,
  Final_Value: 10700,
  Peak_Value: 10750,
  Total_Return: 7,
  Annual_Return: 12,
  Annual_Volatility: 18,
  Sharpe_Ratio: 1.1,
  Max_Drawdown: -3.2,
  Avg_Drawdown: -1.1,
  Max_Consecutive_Gains: 3,
  Max_Consecutive_Losses: 1,
  Total_Trading_Days: RESULT_DATES.length,
  Positive_Days: 5,
  Negative_Days: 3,
  Win_Rate: 60,
  Profit_Factor: 1.4,
  ...overrides,
})

/** AAPL 60% + MSFT 40% buy&hold 포트폴리오. warnings는 빈 배열(정상 응답 계약). */
export const makePortfolioData = (overrides: Partial<PortfolioData> = {}): PortfolioData => ({
  portfolio_statistics: makePortfolioStatistics(),
  // BE 계약: return은 이미 백분율(8 = 8%), weight는 0~1 비율이다
  // (portfolio_manager_service.py의 `(end_price / start_price - 1) * 100`).
  individual_returns: {
    AAPL: { weight: 0.6, return: 8, start_price: 125, end_price: 135 },
    MSFT: { weight: 0.4, return: 5, start_price: 240, end_price: 252 },
  },
  portfolio_composition: [
    { symbol: 'AAPL', weight: 0.6 },
    { symbol: 'MSFT', weight: 0.4 },
  ],
  equity_curve: series((i) => 10000 + i * 100),
  daily_returns: series((i) => (i === 0 ? 0 : 1)),
  ticker_info: {
    AAPL: { symbol: 'AAPL', currency: 'USD', company_name: 'Apple Inc.', exchange: 'NASDAQ' },
    MSFT: { symbol: 'MSFT', currency: 'USD', company_name: 'Microsoft Corp.', exchange: 'NASDAQ' },
  },
  stock_data: {
    AAPL: RESULT_DATES.map((date, i) => ({ date, price: 125 + i, volume: 1000 })),
    MSFT: RESULT_DATES.map((date, i) => ({ date, price: 240 + i, volume: 1000 })),
  },
  rebalance_history: [],
  weight_history: [],
  warnings: [],
  ...overrides,
})

/** SMA 전략 단일 종목 결과. 청산 거래 2건(이익 1, 손실 1). */
export const makeSingleStockData = (overrides: Partial<ChartData> = {}): ChartData => ({
  ticker: 'AAPL',
  strategy: 'sma_strategy',
  start_date: RESULT_DATES[0],
  end_date: RESULT_DATES[7],
  ohlc_data: RESULT_DATES.map((date, i) => ({
    date,
    open: 100 + i,
    high: 103 + i,
    low: 99 + i,
    close: 101 + i,
    volume: 1000 + i,
  })),
  equity_data: RESULT_DATES.map((date, i) => ({
    date,
    value: 10000 + i * 50,
    return_pct: i * 0.5,
    drawdown_pct: 0,
  })),
  trade_markers: [
    { date: RESULT_DATES[1], type: 'entry', price: 102, side: 'buy', quantity: 10 },
    { date: RESULT_DATES[3], type: 'exit', price: 104, side: 'sell', pnl_pct: 1.96 },
    { date: RESULT_DATES[4], type: 'entry', price: 105, side: 'buy', quantity: 10 },
    { date: RESULT_DATES[6], type: 'exit', price: 103, side: 'sell', pnl_pct: -1.9 },
  ],
  indicators: [],
  summary_stats: {
    total_return_pct: 3.5,
    total_trades: 2,
    max_drawdown_pct: -2.1,
    sharpe_ratio: 0.9,
  },
  ...overrides,
})

export const benchmarkSeries = (base: number) =>
  RESULT_DATES.map((date, i) => ({ date, close: base + i * 10, return_pct: i === 0 ? 0 : 0.5 }))

export const makePortfolioResponse = (
  overrides: Partial<PortfolioData> = {}
): UnifiedBacktestResponse => ({
  status: 'success',
  backtest_type: 'portfolio',
  // UnifiedBacktestResponse.data는 API 스키마 타입(PortfolioBacktestResponse)이지만
  // 화면은 결과 타입(PortfolioData)으로 읽는다. 두 타입이 따로 정의돼 있어 캐스팅한다.
  data: makePortfolioData(overrides) as unknown as UnifiedBacktestResponse['data'],
})
