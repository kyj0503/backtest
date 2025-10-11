import { describe, it, expect, beforeEach, beforeAll, afterAll, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'
import { BacktestService } from '../backtestService'
import type {
  BacktestRequest,
  UnifiedBacktestResponse,
  NewsResponse,
} from '../../model/api-types'

const baseRequest: BacktestRequest = {
  portfolio: [
    { symbol: 'AAPL', amount: 10000, investment_type: 'lump_sum', asset_type: 'stock' },
  ],
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  strategy: 'buy_and_hold',
  strategy_params: { window: 20 },
  commission: 0.002,
  rebalance_frequency: 'monthly',
}

describe('BacktestService (integration)', () => {
  beforeAll(() => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:3000/api')
  })

  afterAll(() => {
    vi.unstubAllEnvs()
  })

  beforeEach(() => {
    server.resetHandlers()
  })

  it('executes a backtest and returns the unified payload', async () => {
    let capturedBody: BacktestRequest | undefined

    const mockResponse: UnifiedBacktestResponse = {
      status: 'success',
      backtest_type: 'single_stock',
      data: {
        ticker: 'AAPL',
        strategy: 'buy_and_hold',
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
      http.post('http://localhost:3000/api/v1/backtest', async ({ request }) => {
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
      http.post('http://localhost:3000/api/v1/backtest', () => HttpResponse.json({ message: 'failed' }, { status: 500 }))
    )

    await expect(BacktestService.executeBacktest(baseRequest)).rejects.toThrow('Request failed with status code 500')
  })

  it('sends query parameters when searching news', async () => {
    const capturedQueries: Record<string, string> = {}

    const mockNews: NewsResponse = {
      lastBuildDate: '2024-01-01',
      total: 1,
      start: 1,
      display: 5,
      items: [
        {
          title: 'Sample news',
          link: 'https://example.com/news',
          description: 'Example description',
          pubDate: '2024-01-01',
        },
      ],
    }

    server.use(
      http.get('http://localhost:3000/api/v1/naver-news/search', ({ request }) => {
        const url = new URL(request.url)
        url.searchParams.forEach((value, key) => {
          capturedQueries[key] = value
        })
        return HttpResponse.json(mockNews)
      })
    )

    const result = await BacktestService.searchNews('AAPL', 5)

    expect(result).toEqual(mockNews)
    expect(capturedQueries).toEqual({ query: 'AAPL', display: '5' })
  })
})
