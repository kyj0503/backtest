/**
 * 결과 화면(BacktestResults → ChartsSection) 사용자 흐름 테스트 (A-12)
 *
 * 결과 조합 컴포넌트가 응답 형태에 따라 사용자에게 무엇을 보여 주는지를
 * 텍스트·역할 기준으로 고정한다. 스냅샷은 쓰지 않는다.
 *
 * - 정상: 성과 지표 + 포트폴리오 차트 블록 + 다운로드 버튼
 * - warnings 배너: 배치7 A-03 계약 — buy&hold 응답에도 `warnings` 키가 항상
 *   있고, 비어 있지 않을 때만 "주의사항" 배너가 뜬다
 * - 부분 데이터: 구성 종목 일부의 주가/비중 데이터가 빠진 응답
 * - 빈 데이터: data 없음, 포트폴리오 구성 없음, 주가 데이터 없음
 * - 벤치마크·리밸런싱·비중 변화 등 ChartsSection 하위 조합
 * - 단일 종목: 전략 거래가 있을 때만 거래 차트가 나온다
 * - 다운로드: CSV/텍스트 리포트 생성과 실패 시 안내
 *
 * 승률·프로핏 팩터·연환산 수익률은 다른 작업에서 의미와 표시를 바꾸는 중이라
 * 이 테스트는 그 값이나 라벨 문구를 단정하지 않는다.
 *
 * 차트 본문(svg)은 happy-dom에서 크기가 0이라 그려지지 않는다. 여기서는
 * ResultBlock의 제목/figure 역할로 "어떤 차트 블록이 보이는가"만 본다.
 * 차트 내부 렌더링은 TradesChart/WeightHistoryChart 테스트에서 크기를 주고 확인한다.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactElement } from 'react'
import { TooltipProvider } from '@/shared/ui/tooltip'
import BacktestResults from '../BacktestResults'
import type { BacktestResultData } from '../../model/types/backtest-result-types'
import {
  RESULT_DATES,
  benchmarkSeries,
  makePortfolioData,
  makeSingleStockData,
} from '@/test/fixtures/backtestResults'

const toastError = vi.fn()
vi.mock('sonner', () => ({
  toast: { error: (...args: unknown[]) => toastError(...args) },
}))

// StatsSummary는 FinancialTermTooltip(Radix Tooltip)을 쓰므로 Provider가 필요하다.
const renderWithProviders = (ui: ReactElement) => render(<TooltipProvider>{ui}</TooltipProvider>)

const renderPortfolio = (data: BacktestResultData) =>
  renderWithProviders(<BacktestResults data={data} isPortfolio={true} />)

/** 지연 로딩되는 StatsSummary가 뜰 때까지 기다린다. */
const waitForResults = () => screen.findByRole('heading', { name: '백테스트 성과' })

const figure = (title: string) => screen.queryByRole('figure', { name: `${title} 차트` })

describe('BacktestResults — 정상 포트폴리오 결과', () => {
  it('성과 지표, 포트폴리오 차트 블록, 다운로드 버튼을 보여 준다', async () => {
    renderPortfolio(makePortfolioData())

    await waitForResults()
    // 총 수익률 카드는 이번 변경 대상이 아니므로 값까지 확인한다.
    expect(screen.getByText('총 수익률')).toBeInTheDocument()
    expect(screen.getByText('7.00%')).toBeInTheDocument()

    expect(screen.getByRole('heading', { name: /분석 차트 \(일간 데이터\)/ })).toBeInTheDocument()
    expect(figure('누적 자산 가치')).toBeInTheDocument()
    expect(figure('일일 수익률')).toBeInTheDocument()
    expect(figure('개별 자산 주가')).toBeInTheDocument()

    expect(screen.getByRole('button', { name: /CSV 다운로드/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /텍스트 리포트/ })).toBeInTheDocument()
  })

  it('단일 종목 전용 차트(OHLC 등)는 포트폴리오 결과에 나오지 않는다', async () => {
    renderPortfolio(makePortfolioData())
    await waitForResults()

    expect(figure('OHLC 차트')).not.toBeInTheDocument()
    expect(figure('거래 내역')).not.toBeInTheDocument()
  })

  it('레이아웃 토글 버튼으로 넓게/컴팩트 보기를 오간다', async () => {
    const user = userEvent.setup()
    renderPortfolio(makePortfolioData())
    await waitForResults()

    await user.click(screen.getByRole('button', { name: '넓게 보기' }))
    expect(screen.getByRole('button', { name: '컴팩트 보기' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '컴팩트 보기' }))
    expect(screen.getByRole('button', { name: '넓게 보기' })).toBeInTheDocument()
  })
})

describe('BacktestResults — warnings 배너 (배치7 A-03 계약)', () => {
  it('warnings가 있으면 "주의사항" 배너에 각 경고를 보여 준다', async () => {
    renderPortfolio(
      makePortfolioData({
        warnings: [
          'XYZ 가격 데이터를 불러오지 못해 제외했습니다 (제외 금액 $5,000)',
          'MSFT 상장일 이전 기간이 포함되어 있습니다',
        ],
      })
    )
    await waitForResults()

    const title = screen.getByRole('heading', { name: '주의사항' })
    const banner = title.parentElement as HTMLElement
    expect(within(banner).getByText(/XYZ 가격 데이터를 불러오지 못해 제외했습니다/)).toBeInTheDocument()
    expect(within(banner).getByText(/MSFT 상장일 이전 기간이 포함되어 있습니다/)).toBeInTheDocument()
  })

  it('warnings가 빈 배열이면 배너를 띄우지 않는다', async () => {
    renderPortfolio(makePortfolioData({ warnings: [] }))
    await waitForResults()

    expect(screen.queryByRole('heading', { name: '주의사항' })).not.toBeInTheDocument()
  })

  it('warnings 키가 없어도(구버전 응답) 배너 없이 결과를 보여 준다', async () => {
    const data = makePortfolioData()
    delete data.warnings
    renderPortfolio(data)
    await waitForResults()

    expect(screen.queryByRole('heading', { name: '주의사항' })).not.toBeInTheDocument()
    expect(figure('누적 자산 가치')).toBeInTheDocument()
  })

  it('배너는 결과 본문보다 앞(상단)에 온다', async () => {
    renderPortfolio(makePortfolioData({ warnings: ['경고 하나'] }))
    const statsHeading = await waitForResults()
    const bannerHeading = screen.getByRole('heading', { name: '주의사항' })

    expect(
      bannerHeading.compareDocumentPosition(statsHeading) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
  })
})

describe('BacktestResults — 부분 데이터', () => {
  it('로드 실패 종목이 빠진 응답(A-03): 남은 종목 기준으로 결과와 경고를 함께 보여 준다', async () => {
    // BE는 가격 데이터가 없는 종목을 구성·금액에서 빼고 warnings에 사유를 싣는다.
    const data = makePortfolioData({
      portfolio_composition: [{ symbol: 'AAPL', weight: 1 }],
      individual_returns: {
        AAPL: { weight: 1, return: 8, start_price: 125, end_price: 135 },
      },
      stock_data: {
        AAPL: RESULT_DATES.map((date, i) => ({ date, price: 125 + i, volume: 1000 })),
      },
      warnings: ['NOPE 가격 데이터가 없어 백테스트에서 제외했습니다'],
    })
    renderPortfolio(data)
    await waitForResults()

    expect(screen.getByText(/NOPE 가격 데이터가 없어/)).toBeInTheDocument()
    expect(figure('누적 자산 가치')).toBeInTheDocument()
    expect(figure('개별 자산 주가')).toBeInTheDocument()
  })

  it('구성은 2종목인데 주가 데이터가 1종목뿐이어도 화면이 깨지지 않는다', async () => {
    const data = makePortfolioData({
      stock_data: {
        AAPL: RESULT_DATES.map((date, i) => ({ date, price: 125 + i, volume: 1000 })),
      },
    })
    renderPortfolio(data)
    await waitForResults()

    expect(figure('개별 자산 주가')).toBeInTheDocument()
    expect(screen.queryByText(/차트를 렌더링하는 중 오류가 발생했습니다/)).not.toBeInTheDocument()
  })

  it('비중 변화 데이터에 일부 종목 키가 없어도 비중 변화 블록을 그린다', async () => {
    const data = makePortfolioData({
      weight_history: RESULT_DATES.map((date) => ({ date, AAPL: 0.6 })),
    })
    renderPortfolio(data)
    await waitForResults()

    expect(figure('포트폴리오 비중 변화')).toBeInTheDocument()
    expect(screen.queryByText(/차트를 렌더링하는 중 오류가 발생했습니다/)).not.toBeInTheDocument()
  })
})

describe('BacktestResults — 빈 데이터', () => {
  it('data가 없으면 실행 안내를 보여 준다', () => {
    renderWithProviders(
      <BacktestResults data={null as unknown as BacktestResultData} isPortfolio={true} />
    )

    expect(screen.getByRole('heading', { name: '데이터가 없습니다' })).toBeInTheDocument()
    expect(screen.getByText('백테스트를 실행해 주세요.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /CSV 다운로드/ })).not.toBeInTheDocument()
  })

  it('포트폴리오 모드인데 구성 정보가 없으면 구성 안내를 보여 준다', () => {
    const { portfolio_composition: _omit, ...rest } = makePortfolioData()
    void _omit
    renderPortfolio(rest as unknown as BacktestResultData)

    expect(screen.getByRole('heading', { name: '포트폴리오 데이터가 없습니다' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '백테스트 성과' })).not.toBeInTheDocument()
  })

  it('주가 데이터가 비어 있으면 개별 자산 주가 블록에 빈 상태 문구를 보여 준다', async () => {
    renderPortfolio(makePortfolioData({ stock_data: {} }))
    await waitForResults()

    const block = figure('개별 자산 주가') as HTMLElement
    expect(within(block).getByText('표시할 자산 데이터가 없습니다.')).toBeInTheDocument()
  })

  it('선택 데이터(벤치마크·환율·뉴스·급등락·리밸런싱)가 없으면 해당 블록을 숨긴다', async () => {
    renderPortfolio(makePortfolioData())
    await waitForResults()

    expect(figure('벤치마크 비교')).not.toBeInTheDocument()
    expect(figure('환율 추이')).not.toBeInTheDocument()
    expect(figure('리밸런싱 히스토리')).not.toBeInTheDocument()
    expect(figure('포트폴리오 비중 변화')).not.toBeInTheDocument()
    expect(screen.queryByText(/급등락/)).not.toBeInTheDocument()
  })
})

describe('BacktestResults — 부가 데이터 수집 상태 (A-08 supplemental_status)', () => {
  const notice = () => screen.queryByRole('status', { name: '부가 데이터 수집 상태' })

  it('시간 초과·오류 섹션을 "데이터 없음"과 구분해 안내한다', async () => {
    renderPortfolio(
      makePortfolioData({
        supplemental_status: {
          ticker_info: 'ok',
          stock_data: 'ok',
          volatility_events: 'empty',
          exchange_rates: 'skipped',
          benchmarks: 'error',
          news: 'timeout',
        },
      })
    )
    await waitForResults()

    const box = notice() as HTMLElement
    expect(box).toBeInTheDocument()
    expect(box).toHaveTextContent('최신 뉴스(시간 초과)')
    expect(box).toHaveTextContent('벤치마크 지수(오류)')
    // 정상적으로 비었거나(empty) 요청하지 않은(skipped) 섹션은 안내하지 않는다
    expect(box).not.toHaveTextContent('급등락')
    expect(box).not.toHaveTextContent('환율')
  })

  it('모든 섹션이 ok/empty/skipped면 안내하지 않는다', async () => {
    renderPortfolio(
      makePortfolioData({
        supplemental_status: {
          ticker_info: 'ok',
          stock_data: 'ok',
          volatility_events: 'empty',
          exchange_rates: 'skipped',
          benchmarks: 'ok',
          news: 'empty',
        },
      })
    )
    await waitForResults()
    expect(notice()).not.toBeInTheDocument()
  })

  it('supplemental_status가 없는 구버전 응답도 안내 없이 결과를 보여 준다', async () => {
    renderPortfolio(makePortfolioData())
    await waitForResults()
    expect(notice()).not.toBeInTheDocument()
  })
})

describe('BacktestResults — ChartsSection 하위 조합', () => {
  it('S&P 500·NASDAQ 벤치마크가 있으면 벤치마크 비교와 수익률 비교 블록을 보여 준다', async () => {
    renderPortfolio(
      makePortfolioData({
        sp500_benchmark: benchmarkSeries(4000),
        nasdaq_benchmark: benchmarkSeries(11000),
      })
    )
    await waitForResults()

    expect(figure('벤치마크 비교')).toBeInTheDocument()
    expect(figure('일일 수익률 벤치마크 비교')).toBeInTheDocument()
  })

  it('벤치마크가 한쪽(S&P 500)만 있어도 벤치마크 블록을 보여 준다', async () => {
    renderPortfolio(makePortfolioData({ sp500_benchmark: benchmarkSeries(4000) }))
    await waitForResults()

    expect(figure('벤치마크 비교')).toBeInTheDocument()
  })

  it('리밸런싱 이력과 비중 변화가 있으면 두 블록을 모두 보여 준다', async () => {
    renderPortfolio(
      makePortfolioData({
        rebalance_history: [
          {
            date: RESULT_DATES[4],
            trades: [{ symbol: 'AAPL', action: 'sell', shares: 1.5, price: 129 }],
            weights_before: { AAPL: 0.62, MSFT: 0.38 },
            weights_after: { AAPL: 0.6, MSFT: 0.4 },
            commission_cost: 0.39,
          },
        ],
        weight_history: RESULT_DATES.map((date) => ({ date, AAPL: 0.6, MSFT: 0.4 })),
      })
    )
    await waitForResults()

    const history = figure('리밸런싱 히스토리') as HTMLElement
    expect(within(history).getByText('총 1회의 리밸런싱이 발생했습니다')).toBeInTheDocument()
    expect(figure('포트폴리오 비중 변화')).toBeInTheDocument()
  })

  it('단일 종목 포트폴리오는 비중 변화 블록을 숨긴다 (항상 100%라 의미 없음)', async () => {
    renderPortfolio(
      makePortfolioData({
        portfolio_composition: [{ symbol: 'AAPL', weight: 1 }],
        weight_history: RESULT_DATES.map((date) => ({ date, AAPL: 1 })),
      })
    )
    await waitForResults()

    expect(figure('포트폴리오 비중 변화')).not.toBeInTheDocument()
  })

  it('환율 데이터와 통계가 있으면 환율 추이와 주요 지점을 보여 준다', async () => {
    renderPortfolio(
      makePortfolioData({
        exchange_rates: RESULT_DATES.map((date, i) => ({ date, rate: 1300 + i })),
        exchange_stats: {
          start_point: { date: RESULT_DATES[0], rate: 1300 },
          end_point: { date: RESULT_DATES[7], rate: 1307 },
          high_point: { date: RESULT_DATES[7], rate: 1307 },
        },
      })
    )
    await waitForResults()

    const block = figure('환율 추이') as HTMLElement
    for (const label of ['시작점', '종료점', '최고점', '최저점']) {
      expect(within(block).getByText(label)).toBeInTheDocument()
    }
    // low_point가 없는 응답(빈 통계 일부)은 '-'로 표시한다.
    expect(within(block).getByText('-')).toBeInTheDocument()
  })

  it('급등락 이벤트와 뉴스가 있으면 각각의 섹션을 보여 준다', async () => {
    renderPortfolio(
      makePortfolioData({
        volatility_events: {
          AAPL: [
            { date: RESULT_DATES[2], daily_return: 6.1, close_price: 127, volume: 5000, event_type: '급등' },
          ],
        },
        latest_news: {
          AAPL: [
            {
              title: '애플 신제품 발표',
              link: 'https://example.com/a',
              description: '설명',
              pubDate: 'Mon, 09 Jan 2023 10:00:00 +0900',
            },
          ],
        },
      })
    )
    await waitForResults()

    expect(screen.getAllByText(/급등/).length).toBeGreaterThan(0)
    expect(screen.getByText('애플 신제품 발표')).toBeInTheDocument()
  })

  it('10년을 넘는 기간은 월간 집계 안내와 샘플링 경고를 보여 준다', async () => {
    renderPortfolio(
      makePortfolioData({
        portfolio_statistics: {
          ...makePortfolioData().portfolio_statistics,
          Start: '2010-01-04',
          End: '2023-01-11',
        },
      })
    )
    await waitForResults()

    expect(screen.getByRole('heading', { name: /분석 차트 \(월간 데이터\)/ })).toBeInTheDocument()
    expect(screen.getByText(/월간 단위로 집계되었습니다/)).toBeInTheDocument()
    expect(figure('월간 수익률')).toBeInTheDocument()
  })
})

describe('BacktestResults — 단일 종목 결과', () => {
  const renderSingle = (data = makeSingleStockData()) =>
    renderWithProviders(<BacktestResults data={data} isPortfolio={false} />)

  it('OHLC·수익률 차트를 보여 주고 포트폴리오 전용 블록은 숨긴다', async () => {
    renderSingle()
    await waitForResults()

    expect(figure('OHLC 차트')).toBeInTheDocument()
    expect(figure('수익률 & 드로우다운 차트')).toBeInTheDocument()
    expect(figure('누적 자산 가치')).not.toBeInTheDocument()
  })

  it('전략 거래가 있으면 거래 내역과 매매신호 블록을 보여 준다', async () => {
    renderSingle()
    await waitForResults()

    expect(figure('거래 내역')).toBeInTheDocument()
    expect(figure('매매신호 그래프')).toBeInTheDocument()
  })

  it('buy&hold 결과는 거래 차트를 보여 주지 않는다', async () => {
    renderSingle(makeSingleStockData({ strategy: 'buy_hold_strategy' }))
    await waitForResults()

    expect(figure('거래 내역')).not.toBeInTheDocument()
    expect(figure('매매신호 그래프')).not.toBeInTheDocument()
  })

  it('단일 종목 결과에는 warnings 배너를 띄우지 않는다 (포트폴리오 전용 계약)', async () => {
    renderSingle(
      { ...makeSingleStockData(), warnings: ['무시되는 경고'] } as unknown as ReturnType<
        typeof makeSingleStockData
      >
    )
    await waitForResults()

    expect(screen.queryByRole('heading', { name: '주의사항' })).not.toBeInTheDocument()
  })

  it('주가 데이터가 없으면 개별 주가 블록에 빈 상태 문구를 보여 준다', async () => {
    renderSingle()
    await waitForResults()

    const block = figure('개별 주가') as HTMLElement
    expect(within(block).getByText('표시할 주가 데이터가 없습니다.')).toBeInTheDocument()
  })
})

describe('BacktestResults — 리포트 다운로드', () => {
  let createdBlobs: Blob[]
  let clickedDownloads: string[]

  beforeEach(() => {
    createdBlobs = []
    clickedDownloads = []
    toastError.mockClear()
    vi.spyOn(URL, 'createObjectURL').mockImplementation((obj: Blob | MediaSource) => {
      createdBlobs.push(obj as Blob)
      return 'blob:mock'
    })
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement
    ) {
      clickedDownloads.push(this.download)
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('CSV 다운로드는 BOM이 붙은 CSV 파일을 내려받게 한다', async () => {
    const user = userEvent.setup()
    renderPortfolio(makePortfolioData())
    await waitForResults()

    await user.click(screen.getByRole('button', { name: /CSV 다운로드/ }))

    expect(clickedDownloads).toHaveLength(1)
    expect(clickedDownloads[0]).toMatch(/^backtest-report-\d{4}-\d{2}-\d{2}\.csv$/)
    const text = await createdBlobs[0]!.text()
    expect(text.charCodeAt(0)).toBe(0xfeff)
    expect(text).toContain('포트폴리오 구성')
    expect(text).toContain('AAPL,60.00')
    expect(toastError).not.toHaveBeenCalled()
  })

  it('주식+현금 리밸런싱 결과도 CSV로 내려받을 수 있다 (현금 조정 거래 포함)', async () => {
    const user = userEvent.setup()
    renderPortfolio(
      makePortfolioData({
        rebalance_history: [
          {
            date: RESULT_DATES[4],
            trades: [
              { symbol: 'AAPL', action: 'sell', shares: 2, price: 130 },
              { symbol: 'CASH', action: 'increase', amount: 260, price: 1 },
            ],
            weights_before: { AAPL: 0.55, CASH: 0.45 },
            weights_after: { AAPL: 0.5, CASH: 0.5 },
          },
        ],
      })
    )
    await waitForResults()

    await user.click(screen.getByRole('button', { name: /CSV 다운로드/ }))

    expect(toastError).not.toHaveBeenCalled()
    expect(await createdBlobs[0]!.text()).toContain('CASH,증가,260.00')
  })

  it('텍스트 리포트는 .txt 파일을 내려받게 한다', async () => {
    const user = userEvent.setup()
    renderPortfolio(makePortfolioData())
    await waitForResults()

    await user.click(screen.getByRole('button', { name: /텍스트 리포트/ }))

    expect(clickedDownloads[0]).toMatch(/\.txt$/)
    const text = await createdBlobs[0]!.text()
    expect(text).toContain('백테스트 결과 리포트')
    expect(text).toContain('[ 포트폴리오 백테스트 ]')
  })

  it('다운로드 중 오류가 나면 사용자에게 오류 토스트로 알린다', async () => {
    const user = userEvent.setup()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(URL, 'createObjectURL').mockImplementation(() => {
      throw new Error('blob 생성 실패')
    })
    renderPortfolio(makePortfolioData())
    await waitForResults()

    await user.click(screen.getByRole('button', { name: /CSV 다운로드/ }))
    expect(toastError).toHaveBeenCalledWith(expect.stringContaining('CSV 다운로드에 실패했습니다'))

    await user.click(screen.getByRole('button', { name: /텍스트 리포트/ }))
    expect(toastError).toHaveBeenCalledWith(expect.stringContaining('리포트 다운로드에 실패했습니다'))
  })
})
