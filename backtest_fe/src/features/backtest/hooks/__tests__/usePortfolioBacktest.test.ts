/**
 * usePortfolioBacktest(useBacktest) 에러 노출 회귀 테스트 (P1-09 / P2-29)
 *
 * 버그: 훅의 catch 블록이 `err.message`(axios의 일반 메시지, 예:
 * "Request failed with status code 422")를 error 상태로 저장했다. 실제 백엔드
 * detail 메시지는 무시된 채 폼 모달에만 노출되고, 페이지 레벨 Alert에는
 * 사용자에게 쓸모없는 일반 문자열만 남았다.
 *
 * 수정 후: 훅은 client.ts의 extractErrorMessage를 사용해 실제 백엔드 메시지를
 * error 상태에 담아야 한다.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'
import { apiClient } from '@/shared/api/client'
import { useBacktest } from '../usePortfolioBacktest'
import type { BacktestRequest } from '../../model/types/api-types'

const baseRequest: BacktestRequest = {
  portfolio: [
    { symbol: 'AAPL', amount: 10000, investment_type: 'lump_sum', asset_type: 'stock' },
  ],
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  strategy: 'buy_hold_strategy',
  strategy_params: {},
  commission: 0.002,
  rebalance_frequency: 'monthly_1',
}

describe('useBacktest 에러 처리 (usePortfolioBacktest.ts)', () => {
  const TEST_BASE_URL = 'http://localhost:3000'

  beforeAll(() => {
    apiClient.defaults.baseURL = TEST_BASE_URL
  })

  afterAll(() => {
    apiClient.defaults.baseURL = ''
  })

  afterEach(() => {
    server.resetHandlers()
  })

  it('FastAPI 문자열 detail 에러를 실제 메시지로 노출한다 (일반 axios 메시지가 아님)', async () => {
    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, () =>
        HttpResponse.json({ detail: '포트폴리오 구성이 올바르지 않습니다.' }, { status: 422 })
      )
    )

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await expect(result.current.runBacktest(baseRequest)).rejects.toBeTruthy()
    })

    await waitFor(() => {
      expect(result.current.error).toBe('포트폴리오 구성이 올바르지 않습니다.')
    })
    // 회귀 방지: axios의 일반 메시지("Request failed with status code ...")로
    // 남아있으면 안 된다.
    expect(result.current.error).not.toMatch(/status code/i)
  })

  it('Pydantic 검증 에러 배열도 실제 메시지로 노출한다', async () => {
    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, () =>
        HttpResponse.json(
          {
            detail: [
              { loc: ['body', 'commission'], msg: '수수료율은 0 이상이어야 합니다.', type: 'value_error' },
            ],
          },
          { status: 422 }
        )
      )
    )

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await expect(result.current.runBacktest(baseRequest)).rejects.toBeTruthy()
    })

    await waitFor(() => {
      expect(result.current.error).toContain('수수료율은 0 이상이어야 합니다.')
    })
  })

  it('성공 시에는 error가 null로 유지된다 (회귀 방지)', async () => {
    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, () =>
        HttpResponse.json({ status: 'success', data: {} })
      )
    )

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await result.current.runBacktest(baseRequest)
    })

    expect(result.current.error).toBeNull()
  })
})
