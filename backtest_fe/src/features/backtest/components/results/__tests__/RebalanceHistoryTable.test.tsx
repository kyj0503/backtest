/**
 * RebalanceHistoryTable 테스트 (A-12)
 *
 * 리밸런싱 이벤트 목록 → 행 펼침 → 거래 내역·전후 비중 확인 흐름.
 * 현금 조정(increase/decrease)은 백엔드가 shares 없이 amount만 보낸다
 * (portfolio_rebalancer.py) — 그 형태도 깨지지 않고 표시되는지 본다.
 */
import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RebalanceHistoryTable from '../RebalanceHistoryTable'
import type { RebalanceEvent } from '../../../model/types/backtest-result-types'

const events: RebalanceEvent[] = [
  {
    date: '2023-02-01',
    trades: [
      { symbol: 'AAPL', action: 'sell', shares: 2.5, price: 140 },
      { symbol: 'MSFT', action: 'buy', shares: 1.25, price: 250 },
    ],
    weights_before: { AAPL: 0.65, MSFT: 0.35 },
    weights_after: { AAPL: 0.6, MSFT: 0.4 },
    commission_cost: 1.234,
  },
  {
    date: '2023-03-01',
    trades: [
      // 현금 조정: shares 없이 amount만 온다.
      { symbol: 'CASH', action: 'increase', amount: 300, price: 1 } as unknown as RebalanceEvent['trades'][number],
      { symbol: 'AAPL', action: 'sell', shares: 2, price: 150 },
    ],
    weights_before: { AAPL: 0.55, CASH: 0.45 },
    weights_after: { AAPL: 0.5, CASH: 0.5 },
  },
]

const rowButton = (dateText: RegExp) => screen.getByRole('button', { name: dateText })

describe('RebalanceHistoryTable', () => {
  it('이벤트가 없으면 빈 상태 안내를 보여 준다', () => {
    render(<RebalanceHistoryTable rebalanceHistory={[]} />)

    expect(screen.getByText('리밸런싱 이벤트가 없습니다.')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('이벤트 수와 각 이벤트의 날짜·거래 종목 수·수수료를 요약해 보여 준다', () => {
    render(<RebalanceHistoryTable rebalanceHistory={events} />)

    expect(screen.getByText('총 2회의 리밸런싱이 발생했습니다')).toBeInTheDocument()
    const first = rowButton(/2023년 2월 1일/)
    expect(first).toHaveTextContent('2개 종목 거래')
    expect(first).toHaveTextContent('수수료: $1.23')
    // 수수료 정보가 없는 이벤트는 수수료를 표시하지 않는다.
    expect(rowButton(/2023년 3월 1일/)).not.toHaveTextContent('수수료')
  })

  it('처음에는 접혀 있고, 행을 누르면 거래 내역과 전후 비중을 펼친다', async () => {
    const user = userEvent.setup()
    render(<RebalanceHistoryTable rebalanceHistory={events} />)

    expect(screen.queryByText('거래 내역')).not.toBeInTheDocument()

    await user.click(rowButton(/2023년 2월 1일/))

    const panel = screen.getByText('거래 내역').parentElement!.parentElement as HTMLElement
    expect(within(panel).getByText('매도')).toBeInTheDocument()
    expect(within(panel).getByText('매수')).toBeInTheDocument()
    expect(within(panel).getByText(/2\.50주 @/)).toBeInTheDocument()
    expect(within(panel).getByText('리밸런싱 전')).toBeInTheDocument()
    expect(within(panel).getByText('65.00%')).toBeInTheDocument()
    expect(within(panel).getByText('리밸런싱 후')).toBeInTheDocument()
    expect(within(panel).getByText('60.00%')).toBeInTheDocument()
  })

  it('펼친 행을 다시 누르면 접힌다', async () => {
    const user = userEvent.setup()
    render(<RebalanceHistoryTable rebalanceHistory={events} />)

    await user.click(rowButton(/2023년 2월 1일/))
    expect(screen.getByText('거래 내역')).toBeInTheDocument()
    await user.click(rowButton(/2023년 2월 1일/))
    expect(screen.queryByText('거래 내역')).not.toBeInTheDocument()
  })

  it('여러 행을 동시에 펼칠 수 있다', async () => {
    const user = userEvent.setup()
    render(<RebalanceHistoryTable rebalanceHistory={events} />)

    await user.click(rowButton(/2023년 2월 1일/))
    await user.click(rowButton(/2023년 3월 1일/))
    expect(screen.getAllByText('거래 내역')).toHaveLength(2)
  })

  it('현금 조정 거래(shares 없음)는 금액과 "현금"으로 표시한다', async () => {
    const user = userEvent.setup()
    render(<RebalanceHistoryTable rebalanceHistory={events} />)

    await user.click(rowButton(/2023년 3월 1일/))

    expect(screen.getByText('증가')).toBeInTheDocument()
    const cashRow = screen.getByText('현금').closest('div.rounded') as HTMLElement
    expect(within(cashRow).getByText('CASH')).toBeInTheDocument()
    expect(within(cashRow).getByText(/300/)).toBeInTheDocument()
  })
})
