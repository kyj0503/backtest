/**
 * TradesChart(거래 수익률 분포) 테스트 (A-12)
 *
 * 청산(exit) 거래의 손익률만 산점도로 그린다. 진입만 있거나 거래가 없으면
 * 빈 상태 문구를 보여 준다. 차트 본문은 ResponsiveContainer에 크기를 줘야
 * 그려지므로 installSizedCharts()를 쓴다(ChartRendering.test.tsx와 같은 방식).
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TradesChart from '../TradesChart'
import type { TradeMarker } from '../../model/types/backtest-result-types'
import { installSizedCharts } from '@/test/sizedCharts'

installSizedCharts()

const trades: TradeMarker[] = [
  { date: '2023-01-02', type: 'entry', price: 100 },
  { date: '2023-01-05', type: 'exit', price: 104, pnl_pct: 4 },
  { date: '2023-01-06', type: 'entry', price: 105 },
  { date: '2023-01-09', type: 'exit', price: 101, pnl_pct: -3.8 },
  // 손익률이 없는 청산은 분포에서 제외한다.
  { date: '2023-01-10', type: 'exit', price: 101 },
]

describe('TradesChart', () => {
  it('청산 거래가 없으면 카드 안에 빈 상태 문구를 보여 준다', () => {
    render(<TradesChart trades={[{ date: '2023-01-02', type: 'entry', price: 100 }]} />)

    expect(screen.getByText('거래 수익률 분포')).toBeInTheDocument()
    expect(screen.getByText('표시할 거래 데이터가 없습니다.')).toBeInTheDocument()
  })

  it('거래 배열이 비었거나 배열이 아니어도 빈 상태로 처리한다', () => {
    const { unmount } = render(<TradesChart trades={[]} />)
    expect(screen.getByText('표시할 거래 데이터가 없습니다.')).toBeInTheDocument()
    unmount()

    render(<TradesChart trades={null as unknown as TradeMarker[]} />)
    expect(screen.getByText('표시할 거래 데이터가 없습니다.')).toBeInTheDocument()
  })

  it('showCard=false면 카드 제목 없이 빈 상태 문구만 보여 준다', () => {
    render(<TradesChart trades={[]} showCard={false} />)

    expect(screen.queryByText('거래 수익률 분포')).not.toBeInTheDocument()
    expect(screen.getByText('표시할 거래 데이터가 없습니다.')).toBeInTheDocument()
  })

  it('손익률이 있는 청산 거래마다 점을 하나씩 그리고, 이익/손실 색을 나눈다', () => {
    const { container } = render(<TradesChart trades={trades} />)

    expect(screen.getByText('거래 수익률 분포')).toBeInTheDocument()
    expect(screen.queryByText('표시할 거래 데이터가 없습니다.')).not.toBeInTheDocument()
    expect(container.querySelector('svg.recharts-surface')).toBeTruthy()

    const points = container.querySelectorAll('.recharts-scatter-symbol path')
    expect(points).toHaveLength(2)
    const fills = Array.from(points).map((p) => p.getAttribute('fill'))
    expect(fills).toEqual(['#198754', '#dc3545'])
  })

  it('0% 기준선과 P&L 축 라벨을 그린다', () => {
    const { container } = render(<TradesChart trades={trades} showCard={false} />)

    expect(container.querySelector('.recharts-reference-line')).toBeTruthy()
    expect(screen.getByText('P&L (%)')).toBeInTheDocument()
    expect(screen.queryByText('거래 수익률 분포')).not.toBeInTheDocument()
  })
})
