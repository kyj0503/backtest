import { describe, it, expect, beforeEach, beforeAll, afterAll, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'
import { BacktestService } from '../backtestService'
import { apiClient } from '@/shared/api/client'
import type {
  BacktestRequest,
  UnifiedBacktestResponse,
} from '../../model/types/api-types'

const baseRequest: BacktestRequest = {
  portfolio: [
    { symbol: 'AAPL', amount: 10000, investment_type: 'lump_sum', asset_type: 'stock' },
  ],
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  strategy: 'buy_hold_strategy',
  strategy_params: { window: 20 },
  commission: 0.002,
  rebalance_frequency: 'weekly_4',
}

describe('BacktestService (integration)', () => {
  const TEST_BASE_URL = 'http://localhost:3000'

  beforeAll(() => {
    // MSW 서버를 테스트용 baseURL과 함께 설정
    apiClient.defaults.baseURL = TEST_BASE_URL
  })

  afterAll(() => {
    // 원래 baseURL로 복원
    apiClient.defaults.baseURL = ''
  })

  beforeEach(() => {
    server.resetHandlers()
  })

  afterEach(() => {
    server.resetHandlers()
  })

  it('executes a backtest and returns the unified payload', async () => {
    let capturedBody: BacktestRequest | undefined

    const mockResponse: UnifiedBacktestResponse = {
      status: 'success',
      backtest_type: 'single_stock',
      data: {
        ticker: 'AAPL',
        strategy: 'buy_hold_strategy',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        ohlc_data: [],
        equity_data: [],
        trade_markers: [],
        indicators: [],
        summary_stats: {
          total_return_pct: 12.5,
          total_trades: 4,
          win_rate_pct: 75,
          max_drawdown_pct: -5.2,
          sharpe_ratio: 1.3,
          profit_factor: 1.8,
        },
      },
    }

    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, async ({ request }) => {
        capturedBody = await request.json()
        return HttpResponse.json(mockResponse)
      })
    )

    const result = await BacktestService.executeBacktest(baseRequest)

    expect(capturedBody).toEqual(baseRequest)
    expect(result).toEqual(mockResponse)
  })

  it('propagates API failures as rejected promises', async () => {
    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, () =>
        HttpResponse.json({ message: 'failed' }, { status: 500 })
      )
    )

    await expect(BacktestService.executeBacktest(baseRequest)).rejects.toThrow()
  })
})
