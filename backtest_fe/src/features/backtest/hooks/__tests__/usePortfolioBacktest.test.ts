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
import { http, HttpResponse, delay } from 'msw'
import { server } from '@/test/mocks/server'
import { apiClient, BACKTEST_REQUEST_TIMEOUT_MS } from '@/shared/api/client'
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

/**
 * 타임아웃/취소 회귀 테스트 (P2-30)
 *
 * 버그: client.ts는 `axios.create({ baseURL })`뿐이라 타임아웃이 없었다.
 * 연결이 정지되면 요청이 영원히 pending 상태로 남아 제출 버튼이 계속
 * disabled로 잠긴다. 컴포넌트가 언마운트되거나 새 제출이 이전 요청을
 * 대체(supersede)해도 이전 요청은 취소되지 않고 계속 진행되며, 나중에
 * 도착하는 응답이 최신 상태를 덮어쓸 수 있었다.
 *
 * 수정 후: apiClient에 nginx의 proxy_read_timeout(180s)보다 긴 타임아웃을
 * 두고, AbortController로 언마운트/대체 시 실제로 요청을 취소한다.
 */
describe('useBacktest 타임아웃/취소 (P2-30)', () => {
  const TEST_BASE_URL = 'http://localhost:3000'

  beforeAll(() => {
    apiClient.defaults.baseURL = TEST_BASE_URL
  })

  afterAll(() => {
    apiClient.defaults.baseURL = ''
    apiClient.defaults.timeout = BACKTEST_REQUEST_TIMEOUT_MS
  })

  afterEach(() => {
    server.resetHandlers()
    // 개별 테스트가 apiClient.defaults.timeout을 바꿔도 다음 테스트로
    // 새어나가지 않게 항상 실제 기본값으로 되돌린다.
    apiClient.defaults.timeout = BACKTEST_REQUEST_TIMEOUT_MS
  })

  it('타임아웃이 발생하면 무한 대기 상태로 남지 않고 사용자에게 보여줄 에러로 노출된다', async () => {
    // 실제 185s를 기다릴 수 없으니, 이 테스트에서만 타임아웃을 짧게 줄이고
    // 응답은 그보다 오래 걸리게 만들어 같은 코드 경로(axios 타임아웃 →
    // extractErrorMessage)를 그대로 검증한다.
    apiClient.defaults.timeout = 50

    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, async () => {
        await delay(300)
        return HttpResponse.json({ status: 'success', data: {} })
      })
    )

    const { result } = renderHook(() => useBacktest())

    await act(async () => {
      await expect(result.current.runBacktest(baseRequest)).rejects.toBeTruthy()
    })

    // pending 상태로 멈춰있지 않고 로딩이 풀려야 한다.
    expect(result.current.isLoading).toBe(false)
    expect(typeof result.current.error).toBe('string')
    expect(result.current.error).toBeTruthy()
  })

  it('컴포넌트가 언마운트되면 진행 중인 요청을 실제로 취소한다', async () => {
    let capturedSignal: AbortSignal | undefined
    let notifyHandlerStarted: () => void
    const handlerStarted = new Promise<void>((resolve) => {
      notifyHandlerStarted = resolve
    })

    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, async ({ request }) => {
        capturedSignal = request.signal ?? undefined
        notifyHandlerStarted()
        await delay(500)
        return HttpResponse.json({ status: 'success', data: {} })
      })
    )

    const { result, unmount } = renderHook(() => useBacktest())

    let runPromise: Promise<unknown> = Promise.resolve()
    act(() => {
      runPromise = result.current.runBacktest(baseRequest).catch(() => undefined)
    })

    // 핸들러가 signal을 캡처할 때까지 기다려 요청이 이미 나간 뒤에
    // 언마운트하도록 한다 (그렇지 않으면 fetch가 시작되기도 전에 취소되어
    // 핸들러가 아예 호출되지 않을 수 있다).
    await handlerStarted

    unmount()

    await act(async () => {
      await runPromise
    })

    expect(capturedSignal).toBeDefined()
    expect(capturedSignal?.aborted).toBe(true)
  })

  it('새 제출이 이전 요청을 대체하면 이전 요청을 취소하고 최신 응답만 상태에 반영한다', async () => {
    let callCount = 0
    let firstSignal: AbortSignal | undefined
    let notifyFirstStarted: () => void
    const firstStarted = new Promise<void>((resolve) => {
      notifyFirstStarted = resolve
    })

    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, async ({ request }) => {
        callCount += 1
        if (callCount === 1) {
          firstSignal = request.signal ?? undefined
          notifyFirstStarted()
          await delay(500)
          return HttpResponse.json({ status: 'success', data: { call: 1 } })
        }
        return HttpResponse.json({ status: 'success', data: { call: 2 } })
      })
    )

    const { result } = renderHook(() => useBacktest())

    let firstPromise: Promise<unknown> = Promise.resolve()
    act(() => {
      firstPromise = result.current.runBacktest(baseRequest).catch(() => undefined)
    })

    await firstStarted

    await act(async () => {
      await result.current.runBacktest(baseRequest)
    })

    await firstPromise

    expect(firstSignal?.aborted).toBe(true)
    expect(result.current.result).toEqual({ status: 'success', data: { call: 2 } })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })
})
