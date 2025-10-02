import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useBacktest } from '../useBacktest'
import type { BacktestRequest } from '../../model/api-types'
import type { ApiError } from '../../api/backtestApi'
import { runBacktest } from '../../api/backtestApi'

vi.mock('../../api/backtestApi', () => ({
  runBacktest: vi.fn(),
}))

const mockRunBacktest = vi.mocked(runBacktest)

const baseRequest: BacktestRequest = {
  portfolio: [
    { symbol: 'AAPL', amount: 5000, investment_type: 'lump_sum', asset_type: 'stock' },
    { symbol: 'MSFT', amount: 5000, investment_type: 'lump_sum', asset_type: 'stock' },
  ],
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  strategy: 'buy_and_hold',
  strategy_params: { window: 20 },
  commission: 0.002,
  rebalance_frequency: 'monthly',
}

let logSpy: ReturnType<typeof vi.spyOn> | undefined

describe('useBacktest', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
  })

  afterEach(() => {
    logSpy?.mockRestore()
  })

  it('handles successful execution with wrapper response', async () => {
    const apiResponse = {
      backtest_type: 'portfolio' as const,
      data: {
        summary_stats: { total_return_pct: 12.5 },
      },
    }
    mockRunBacktest.mockResolvedValueOnce(apiResponse)

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await result.current.runBacktest(baseRequest)
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.results).toEqual(apiResponse.data)
    expect(result.current.isPortfolio).toBe(true)
    expect(result.current.error).toBeNull()
    expect(mockRunBacktest).toHaveBeenCalledWith(baseRequest)
  })

  it('derives portfolio flag from request when API does not return wrapper', async () => {
    const flatResponse = { message: 'ok' }
    mockRunBacktest.mockResolvedValueOnce(flatResponse)

    const request: BacktestRequest = {
      ...baseRequest,
      portfolio: [{ symbol: 'AAPL', amount: 10000, investment_type: 'lump_sum', asset_type: 'stock' }],
    }

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await result.current.runBacktest(request)
    })

    expect(result.current.results).toEqual(flatResponse)
    expect(result.current.isPortfolio).toBe(false)
  })

  it('handles API errors and exposes clearError/clearResults helpers', async () => {
    const error: ApiError = {
      message: 'Validation failed',
      status: 422,
      type: 'validation',
      errorId: 'ERR-1234',
    }
    mockRunBacktest.mockRejectedValueOnce(error)

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await result.current.runBacktest(baseRequest)
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.results).toBeNull()
    expect(result.current.error).toBe('Validation failed')
    expect(result.current.errorType).toBe('validation')
    expect(result.current.errorId).toBe('ERR-1234')

    act(() => {
      result.current.clearError()
      result.current.clearResults()
    })

    expect(result.current.error).toBeNull()
    expect(result.current.errorType).toBeNull()
    expect(result.current.errorId).toBeNull()
    expect(result.current.results).toBeNull()
  })
})
