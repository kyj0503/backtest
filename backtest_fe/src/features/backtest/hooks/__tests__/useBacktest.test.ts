import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { act } from 'react'
import { useBacktest } from '../useBacktest'

vi.mock('../../api/backtestApi', async () => {
  const actual = await vi.importActual<any>('../../api/backtestApi')
  return {
    ...actual,
    runBacktest: vi.fn(),
  }
})

import { runBacktest } from '../../api/backtestApi'

const makeRequest = (portfolioLen = 1) => ({
  portfolio: Array.from({ length: portfolioLen }).map(() => ({
    symbol: 'AAPL',
    amount: 1000,
    investment_type: 'lump_sum' as const,
    dca_periods: 12,
    asset_type: 'stock' as const,
  })),
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  commission: 0.002,
  rebalance_frequency: 'monthly',
  strategy: 'buy_and_hold',
  strategy_params: {},
})

describe('useBacktest', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('성공 시 결과를 설정하고 isPortfolio를 올바르게 표시해야 함', async () => {
    ;(runBacktest as any).mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await result.current.runBacktest(makeRequest(2))
    })

    expect(result.current.results).toEqual({ ok: true })
    expect(result.current.isPortfolio).toBe(true)
    expect(result.current.error).toBeNull()
  })

  it('네트워크 오류를 매핑해 errorType과 메시지를 설정해야 함', async () => {
    ;(runBacktest as any).mockRejectedValue({
      message: '네트워크 오류',
      status: 0,
      type: 'network',
      errorId: undefined,
    })

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await result.current.runBacktest(makeRequest())
    })

    expect(result.current.error).toBe('네트워크 오류')
    expect(result.current.errorType).toBe('network')
    expect(result.current.errorId).toBeNull()
  })

  it('알 수 없는 오류는 unknown으로 처리해야 함', async () => {
    ;(runBacktest as any).mockRejectedValue(new Error('Boom'))

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await result.current.runBacktest(makeRequest())
    })

    expect(result.current.error).toBe('Boom')
    expect(result.current.errorType).toBe('unknown')
  })
})
