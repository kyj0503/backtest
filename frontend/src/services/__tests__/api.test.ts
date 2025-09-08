import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BacktestApiService } from '../api'

const errorJson = (status: number, detail: string) => new Response(JSON.stringify({ detail }), { status, headers: { 'Content-Type': 'application/json' } })

describe('BacktestApiService', () => {
  let service: BacktestApiService
  const fetchMock = vi.fn()

  beforeEach(() => {
    service = new BacktestApiService()
    vi.stubGlobal('fetch', fetchMock)
    fetchMock.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it.skip('VITE_API_BASE_URL이 있으면 해당 베이스 URL을 사용해야 함', async () => {
    // Override env and create a fresh instance (redefine to ensure override)
    Object.defineProperty(import.meta as any, 'env', {
      value: {
        DEV: true,
        PROD: false,
        MODE: 'test',
        VITE_API_BASE_URL: 'http://example.test',
      },
      writable: true,
    })
    const svc = new BacktestApiService()
    // Access private for runtime behavior verification
    const base = (svc as any).getApiBaseUrl()
    expect(base).toBe('http://example.test')
  })

  it('404 응답은 data_not_found 타입의 ApiError로 변환되어야 함', async () => {
    fetchMock.mockResolvedValue(errorJson(404, '데이터를 찾을 수 없습니다'))

    await expect(
      service.runSingleStockBacktest({
        ticker: 'AAPL', start_date: '2023-01-01', end_date: '2023-12-31', initial_cash: 10000, strategy: 'buy_and_hold', strategy_params: {}
      })
    ).rejects.toMatchObject({ type: 'data_not_found', status: 404, message: '데이터를 찾을 수 없습니다' })
  })

  it('422 응답은 validation 타입의 ApiError로 변환되어야 함', async () => {
    fetchMock.mockResolvedValue(errorJson(422, '검증 오류'))

    await expect(
      service.runPortfolioBacktest({
        portfolio: [], start_date: '2023-01-01', end_date: '2023-12-31', commission: 0.002, rebalance_frequency: 'monthly', strategy: 'buy_and_hold', strategy_params: {}
      })
    ).rejects.toMatchObject({ type: 'validation', status: 422, message: '검증 오류' })
  })

  it('429 응답은 rate_limit 타입의 ApiError로 변환되어야 함', async () => {
    fetchMock.mockResolvedValue(errorJson(429, '요청 제한 초과'))

    await expect(
      service.getStockData('AAPL', '2023-01-01', '2023-12-31')
    ).rejects.toMatchObject({ type: 'rate_limit', status: 429, message: '요청 제한 초과' })
  })
})
