/**
 * WeightHistoryChart(포트폴리오 비중 변화) 테스트 (A-12)
 *
 * 스택 영역 차트라 종목마다 Area 하나, 리밸런싱마다 기준선 하나가 그려진다.
 * ResponsiveContainer에 크기를 줘야 본문이 그려지므로 installSizedCharts()를 쓴다.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import WeightHistoryChart from '../WeightHistoryChart'
import type {
  RebalanceEvent,
  WeightHistoryPoint,
} from '../../../model/types/backtest-result-types'
import { installSizedCharts } from '@/test/sizedCharts'

installSizedCharts()

const composition = [{ symbol: 'AAPL' }, { symbol: 'MSFT' }, { symbol: 'CASH' }]

const history: WeightHistoryPoint[] = [
  { date: '2023-01-02', AAPL: 0.5, MSFT: 0.3, CASH: 0.2 },
  { date: '2023-01-03', AAPL: 0.52, MSFT: 0.29, CASH: 0.19 },
  { date: '2023-01-05', AAPL: 0.5, MSFT: 0.3, CASH: 0.2 },
]

const rebalances: RebalanceEvent[] = [
  // 비중 데이터에 없는 날짜 — null 포인트로 병합되어 기준선이 그려져야 한다.
  {
    date: '2023-01-04',
    trades: [{ symbol: 'AAPL', action: 'sell', shares: 1, price: 130 }],
    weights_before: { AAPL: 0.52, MSFT: 0.29, CASH: 0.19 },
    weights_after: { AAPL: 0.5, MSFT: 0.3, CASH: 0.2 },
  },
]

describe('WeightHistoryChart', () => {
  it('비중 데이터가 없으면 빈 상태 문구를 보여 준다', () => {
    render(<WeightHistoryChart weightHistory={[]} portfolioComposition={composition} />)

    expect(screen.getByText('비중 변화 데이터가 없습니다.')).toBeInTheDocument()
  })

  it('구성 종목마다 영역을 하나씩 쌓아 그린다', () => {
    const { container } = render(
      <WeightHistoryChart weightHistory={history} portfolioComposition={composition} />
    )

    expect(container.querySelector('svg.recharts-surface')).toBeTruthy()
    expect(container.querySelectorAll('.recharts-area')).toHaveLength(3)
  })

  it('범례는 알려진 종목을 표시 이름으로, 모르는 심볼은 그대로 보여 준다', () => {
    render(<WeightHistoryChart weightHistory={history} portfolioComposition={composition} />)

    expect(screen.getByText('AAPL - Apple Inc.')).toBeInTheDocument()
    expect(screen.getByText('MSFT - Microsoft Corp.')).toBeInTheDocument()
    expect(screen.getByText('CASH')).toBeInTheDocument()
  })

  it('같은 심볼이 구성에 중복돼도 영역은 하나만 그린다', () => {
    const { container } = render(
      <WeightHistoryChart
        weightHistory={history}
        portfolioComposition={[...composition, { symbol: 'AAPL' }]}
      />
    )

    expect(container.querySelectorAll('.recharts-area')).toHaveLength(3)
  })

  it('리밸런싱 날짜마다 기준선을 그린다 (비중 데이터에 없는 날짜 포함)', () => {
    const { container } = render(
      <WeightHistoryChart
        weightHistory={history}
        portfolioComposition={composition}
        rebalanceHistory={rebalances}
      />
    )

    expect(container.querySelectorAll('.recharts-reference-line')).toHaveLength(1)
  })

  it('리밸런싱이 없으면 기준선을 그리지 않는다', () => {
    const { container } = render(
      <WeightHistoryChart weightHistory={history} portfolioComposition={composition} rebalanceHistory={[]} />
    )

    expect(container.querySelector('.recharts-reference-line')).toBeNull()
  })
})
