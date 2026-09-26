/**
 * PortfolioTable(데스크톱 포트폴리오 입력 표) 테스트 (A-12)
 *
 * 결과 화면에 들어가는 비중·총액의 출발점이다. 금액 모드/비중 모드별로
 * 사용자가 보는 비중·합계와, 편집 콜백이 올바른 인덱스·필드로 호출되는지 본다.
 * FinancialTermTooltip 때문에 TooltipProvider로 감싼다.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TooltipProvider } from '@/shared/ui/tooltip'
import { PortfolioTable } from '../PortfolioTable'
import type { Stock, PortfolioInputMode } from '../../../model/types/backtest-form-types'
import { calculateDcaPeriods } from '../../../utils/calculateDcaPeriods'

const START = '2023-01-01'
const END = '2023-12-31'

const twoStocks: Stock[] = [
  { symbol: 'AAPL', amount: 6000, weight: 60, investmentType: 'lump_sum', assetType: 'stock' },
  { symbol: 'MSFT', amount: 4000, weight: 40, investmentType: 'lump_sum', assetType: 'stock' },
]

const setup = (
  portfolio: Stock[],
  mode: PortfolioInputMode = 'amount',
  dates: { startDate?: string; endDate?: string } = { startDate: START, endDate: END }
) => {
  const updateStock = vi.fn()
  const removeStock = vi.fn()
  const utils = render(
    <TooltipProvider>
      <PortfolioTable
        portfolio={portfolio}
        portfolioInputMode={mode}
        updateStock={updateStock}
        removeStock={removeStock}
        {...dates}
      />
    </TooltipProvider>
  )
  return { ...utils, updateStock, removeStock }
}

const bodyRows = () => {
  const [, body] = screen.getAllByRole('rowgroup')
  return within(body as HTMLElement).getAllByRole('row')
}

const footerRow = () => {
  const groups = screen.getAllByRole('rowgroup')
  return within(groups[groups.length - 1] as HTMLElement).getByRole('row')
}

describe('PortfolioTable — 금액 모드', () => {
  it('종목마다 행을 하나씩 그리고 금액 입력을 활성화한다', () => {
    setup(twoStocks)

    expect(bodyRows()).toHaveLength(2)
    expect(screen.getByRole('spinbutton', { name: '1번째 종목 투자 금액' })).toBeEnabled()
    expect(screen.getByRole('spinbutton', { name: '1번째 종목 투자 금액' })).toHaveValue(6000)
    expect(screen.queryByRole('spinbutton', { name: '1번째 종목 비중' })).not.toBeInTheDocument()
  })

  it('비중은 금액 비율로 자동 계산해 보여 주고, 합계는 100%다', () => {
    setup(twoStocks)

    expect(within(bodyRows()[0]!).getByText('60.0%')).toBeInTheDocument()
    expect(within(bodyRows()[1]!).getByText('40.0%')).toBeInTheDocument()
    expect(footerRow()).toHaveTextContent('합계')
    expect(footerRow()).toHaveTextContent('$10,000')
    expect(footerRow()).toHaveTextContent('100.0%')
  })

  it('기간이 없으면 비중을 계산하지 않고 N/A로 표시한다', () => {
    setup(twoStocks, 'amount', {})

    expect(within(bodyRows()[0]!).getByText('N/A%')).toBeInTheDocument()
    // 합계는 입력 금액의 단순 합이다.
    expect(footerRow()).toHaveTextContent('$10,000')
  })

  it('DCA 종목은 회당 금액 × 투자 횟수로 합계·비중에 반영하고 미리보기를 보여 준다', () => {
    const periods = calculateDcaPeriods(START, END, 'monthly_1')
    const portfolio: Stock[] = [
      { symbol: 'AAPL', amount: 1000, investmentType: 'dca', dcaFrequency: 'monthly_1', assetType: 'stock' },
      { symbol: 'MSFT', amount: 1000, investmentType: 'lump_sum', assetType: 'stock' },
    ]
    setup(portfolio)

    const total = 1000 * periods + 1000
    expect(footerRow()).toHaveTextContent(`$${total.toLocaleString()}`)
    const dcaWeight = ((1000 * periods) / total * 100).toFixed(1)
    expect(within(bodyRows()[0]!).getByText(`${dcaWeight}%`)).toBeInTheDocument()
    expect(
      within(bodyRows()[0]!).getByText(new RegExp(`총 ${periods}회, 회당 \\$1,000`))
    ).toBeInTheDocument()
  })

  it('금액 입력을 바꾸면 해당 행 인덱스로 updateStock을 호출한다', async () => {
    const user = userEvent.setup()
    const { updateStock } = setup(twoStocks)

    const input = screen.getByRole('spinbutton', { name: '2번째 종목 투자 금액' })
    await user.clear(input)
    expect(updateStock).toHaveBeenLastCalledWith(1, 'amount', '')
  })
})

describe('PortfolioTable — 비중 모드', () => {
  it('금액 입력을 잠그고 비중 입력을 보여 준다', () => {
    setup(twoStocks, 'weight')

    expect(screen.getByRole('spinbutton', { name: '1번째 종목 투자 금액' })).toBeDisabled()
    expect(screen.getByRole('spinbutton', { name: '1번째 종목 비중' })).toHaveValue(60)
  })

  it('비중 합이 100%면 정상 표시한다', () => {
    setup(twoStocks, 'weight')

    const total = within(footerRow()).getByText('100.0%')
    expect(total.className).not.toMatch(/destructive/)
  })

  it('비중 합이 100%가 아니면 합계를 경고색으로 강조한다', () => {
    setup(
      [
        { ...twoStocks[0]!, weight: 50 },
        { ...twoStocks[1]!, weight: 30 },
      ],
      'weight'
    )

    const total = within(footerRow()).getByText('80.0%')
    expect(total.className).toMatch(/destructive/)
  })

  it('비중 입력은 숫자로 변환해 updateStock에 넘긴다', async () => {
    const user = userEvent.setup()
    const { updateStock } = setup(twoStocks, 'weight')

    const input = screen.getByRole('spinbutton', { name: '1번째 종목 비중' })
    await user.clear(input)
    await user.type(input, '7')
    expect(updateStock).toHaveBeenLastCalledWith(0, 'weight', expect.any(Number))
  })
})

describe('PortfolioTable — 종목 입력과 삭제', () => {
  it('목록에 없는 종목은 직접 입력칸을 보여 주고 대문자로 바꿔 전달한다', async () => {
    const user = userEvent.setup()
    const { updateStock } = setup([
      { symbol: '', amount: 1000, investmentType: 'lump_sum', assetType: 'stock' },
    ])

    const input = screen.getByRole('textbox', { name: '1번째 종목 심볼' })
    await user.type(input, 'x')
    expect(updateStock).toHaveBeenLastCalledWith(0, 'symbol', 'X')
  })

  it('목록에 있는 종목은 직접 입력칸을 숨긴다', () => {
    setup(twoStocks)
    expect(screen.queryByRole('textbox', { name: '1번째 종목 심볼' })).not.toBeInTheDocument()
  })

  it('현금 자산은 이름 입력칸을 보여 준다', async () => {
    const user = userEvent.setup()
    const { updateStock } = setup([
      ...twoStocks,
      { symbol: '', amount: 500, investmentType: 'lump_sum', assetType: 'cash' },
    ])

    const input = screen.getByRole('textbox', { name: '3번째 현금 자산 이름' })
    await user.type(input, 'K')
    expect(updateStock).toHaveBeenLastCalledWith(2, 'symbol', 'K')
  })

  it('삭제 버튼은 해당 행 인덱스로 removeStock을 호출한다', async () => {
    const user = userEvent.setup()
    const { removeStock } = setup(twoStocks)

    await user.click(within(bodyRows()[1]!).getByRole('button', { name: '삭제' }))
    expect(removeStock).toHaveBeenCalledWith(1)
  })

  it('종목이 하나뿐이면 삭제할 수 없다', () => {
    setup([twoStocks[0]!])
    expect(screen.getByRole('button', { name: '삭제' })).toBeDisabled()
  })
})
