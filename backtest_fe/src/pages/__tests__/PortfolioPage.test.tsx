/**
 * 백테스트 페이지 결과 흐름 테스트 (A-12)
 *
 * 제출 → 실제 useBacktest 훅 → BacktestService(axios fetch adapter) → MSW 응답 →
 * 결과 화면/오류 Alert까지 한 번에 검증한다. 입력 폼은 이 테스트의 관심사가
 * 아니고(BacktestForm/StrategyForm 테스트가 따로 있다) Radix Select 조작이
 * 무거우므로, 고정 요청을 onSubmit으로 넘기는 버튼으로 대체한다.
 *
 * 특히 배치7 A-03 계약 — buy&hold 응답의 `data.warnings`가 비어 있지 않으면
 * 결과 상단에 경고 배너, 빈 배열이면 배너 없음 — 을 네트워크 경로 그대로 고정한다.
 */
import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse, delay } from 'msw'
import { server } from '@/test/mocks/server'
import { apiClient } from '@/shared/api/client'
import { TooltipProvider } from '@/shared/ui/tooltip'
import { makePortfolioResponse } from '@/test/fixtures/backtestResults'
import type { BacktestRequest } from '@/features/backtest/model/types/api-types'
import PortfolioPage from '../PortfolioPage'

const request: BacktestRequest = {
  portfolio: [
    { symbol: 'AAPL', amount: 6000, investment_type: 'lump_sum', asset_type: 'stock' },
    { symbol: 'MSFT', amount: 4000, investment_type: 'lump_sum', asset_type: 'stock' },
  ],
  start_date: '2023-01-02',
  end_date: '2023-01-11',
  strategy: 'buy_hold_strategy',
  strategy_params: {},
  commission: 0.002,
  rebalance_frequency: 'none',
}

vi.mock('@/features/backtest/components/PortfolioBacktestForm', () => ({
  default: ({
    onSubmit,
    loading,
  }: {
    onSubmit: (req: BacktestRequest) => Promise<unknown>
    loading: boolean
  }) => (
    <button
      type="button"
      disabled={loading}
      // 실제 폼처럼 실패를 삼킨다 — 오류 표시는 페이지 Alert의 몫이다.
      onClick={() => onSubmit(request).catch(() => {})}
    >
      백테스트 실행
    </button>
  ),
}))

const TEST_BASE_URL = 'http://localhost:3000'
const ENDPOINT = `${TEST_BASE_URL}/api/v1/backtest`

beforeAll(() => {
  apiClient.defaults.baseURL = TEST_BASE_URL
})

afterAll(() => {
  apiClient.defaults.baseURL = ''
})

const renderPage = () =>
  render(
    <TooltipProvider>
      <PortfolioPage />
    </TooltipProvider>
  )

const submit = async () => {
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: '백테스트 실행' }))
  return user
}

describe('PortfolioPage 결과 흐름', () => {
  it('실행 전에는 시작 안내를 보여 준다', () => {
    renderPage()
    expect(screen.getByText('나만의 투자 전략을 검증해보세요')).toBeInTheDocument()
  })

  it('정상 응답: 로딩 표시 후 결과 화면을 보여 주고 안내 카드를 숨긴다', async () => {
    server.use(
      http.post(ENDPOINT, async () => {
        await delay(50)
        return HttpResponse.json(makePortfolioResponse())
      })
    )
    renderPage()
    await submit()

    expect(await screen.findByText('백테스트 실행 중...')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: '백테스트 성과' })).toBeInTheDocument()
    expect(screen.queryByText('백테스트 실행 중...')).not.toBeInTheDocument()
    expect(screen.queryByText('나만의 투자 전략을 검증해보세요')).not.toBeInTheDocument()
    expect(screen.getByRole('figure', { name: '누적 자산 가치 차트' })).toBeInTheDocument()
  })

  it('warnings가 담긴 buy&hold 응답이면 결과 위에 경고 배너를 띄운다', async () => {
    server.use(
      http.post(ENDPOINT, () =>
        HttpResponse.json(
          makePortfolioResponse({
            warnings: ['NOPE: 가격 데이터가 없어 제외했습니다 (제외 금액 $4,000)'],
          })
        )
      )
    )
    renderPage()
    await submit()

    expect(await screen.findByRole('heading', { name: '주의사항' })).toBeInTheDocument()
    expect(screen.getByText(/NOPE: 가격 데이터가 없어 제외했습니다/)).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: '백테스트 성과' })).toBeInTheDocument()
  })

  it('warnings가 빈 배열이면 경고 배너 없이 결과만 보여 준다', async () => {
    server.use(http.post(ENDPOINT, () => HttpResponse.json(makePortfolioResponse({ warnings: [] }))))
    renderPage()
    await submit()

    expect(await screen.findByRole('heading', { name: '백테스트 성과' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '주의사항' })).not.toBeInTheDocument()
  })

  it('API 오류(422): 백엔드 detail 메시지를 오류 Alert로 보여 주고 결과는 그리지 않는다', async () => {
    server.use(
      http.post(ENDPOINT, () =>
        HttpResponse.json(
          { detail: '기술적 전략은 DCA/리밸런싱을 지원하지 않습니다.' },
          { status: 422 }
        )
      )
    )
    renderPage()
    await submit()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('오류가 발생했습니다')
    expect(alert).toHaveTextContent('기술적 전략은 DCA/리밸런싱을 지원하지 않습니다.')
    expect(screen.queryByRole('heading', { name: '백테스트 성과' })).not.toBeInTheDocument()
    // 오류가 떠 있는 동안 시작 안내 카드는 숨긴다.
    expect(screen.queryByText('나만의 투자 전략을 검증해보세요')).not.toBeInTheDocument()
  })

  it('API 오류(500): 오류 Alert를 닫으면 시작 안내로 돌아간다', async () => {
    server.use(
      http.post(ENDPOINT, () =>
        HttpResponse.json({ detail: '서버 내부 오류' }, { status: 500 })
      )
    )
    renderPage()
    const user = await submit()

    expect(await screen.findByRole('alert')).toHaveTextContent('서버 내부 오류')
    await user.click(screen.getByRole('button', { name: '닫기' }))

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByText('나만의 투자 전략을 검증해보세요')).toBeInTheDocument()
  })

  it('오류 후 재실행에 성공하면 오류 Alert가 사라지고 결과를 보여 준다', async () => {
    server.use(
      http.post(ENDPOINT, () => HttpResponse.json({ detail: '일시적 오류' }, { status: 503 }), {
        once: true,
      }),
      http.post(ENDPOINT, () => HttpResponse.json(makePortfolioResponse()))
    )
    renderPage()
    const user = await submit()
    expect(await screen.findByRole('alert')).toHaveTextContent('일시적 오류')

    await user.click(screen.getByRole('button', { name: '백테스트 실행' }))

    expect(await screen.findByRole('heading', { name: '백테스트 성과' })).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
  })

  it('200이지만 포트폴리오 구성이 빠진 응답은 빈 결과 안내를 보여 준다', async () => {
    const response = makePortfolioResponse()
    const { portfolio_composition: _omit, ...rest } = response.data as unknown as Record<
      string,
      unknown
    >
    void _omit
    server.use(http.post(ENDPOINT, () => HttpResponse.json({ ...response, data: rest })))
    renderPage()
    await submit()

    expect(
      await screen.findByRole('heading', { name: '포트폴리오 데이터가 없습니다' })
    ).toBeInTheDocument()
  })
})
