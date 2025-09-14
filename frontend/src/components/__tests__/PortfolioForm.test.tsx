import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { act } from 'react'
import userEvent from '@testing-library/user-event'
import PortfolioForm from '../PortfolioForm'

describe('PortfolioForm', () => {
  const basePortfolio = [
    { symbol: '', amount: 10000, investmentType: 'lump_sum' as const, dcaPeriods: 12, assetType: 'stock' as const },
  ]

  it('렌더링 및 주요 액션(addStock/addCash/removeStock) 트리거', async () => {
    const user = userEvent.setup()
    const updateStock = vi.fn()
    const addStock = vi.fn()
    const addCash = vi.fn()
    const removeStock = vi.fn()
    const getTotalAmount = vi.fn(() => 10000)

    render(
      <PortfolioForm
        portfolio={basePortfolio}
        updateStock={updateStock}
        addStock={addStock}
        addCash={addCash}
        removeStock={removeStock}
        getTotalAmount={getTotalAmount}
        portfolioInputMode={"amount"}
  setPortfolioInputMode={vi.fn()}
  totalInvestment={10000}
  setTotalInvestment={vi.fn()}
      />
    )

    // 종목 추가 버튼
    await act(async () => {
      await user.click(screen.getByRole('button', { name: '+ 종목 추가' }))
    })
    expect(addStock).toHaveBeenCalled()

    // 현금 추가 버튼
    await act(async () => {
      await user.click(screen.getByRole('button', { name: '현금 추가' }))
    })
    expect(addCash).toHaveBeenCalled()

    // 심볼 드롭다운 변경 (AAPL)
    const symbolSelect = screen.getAllByRole('combobox')[0]
    // 실제 <select>라면 selectOptions 사용
    await act(async () => {
      await user.selectOptions(symbolSelect, 'AAPL')
    })
    expect(updateStock).toHaveBeenCalled()
  })
})
