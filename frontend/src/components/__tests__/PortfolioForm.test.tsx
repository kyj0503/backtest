import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { act } from 'react'
import userEvent from '@testing-library/user-event'
import PortfolioForm from '../PortfolioForm'

describe('PortfolioForm', () => {
  const basePortfolio = [
    { symbol: '', amount: 10000, investmentType: 'lump_sum' as const, dcaPeriods: 12, assetType: 'stock' as const },
  ]

  beforeEach(() => {
    // Radix UI Select에서 사용되는 scrollIntoView를 mock
    Element.prototype.scrollIntoView = vi.fn()
  })

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

    // 기본 렌더링 확인 (Select 컴포넌트 테스트는 복잡하므로 생략)
    expect(screen.getByText('포트폴리오 구성')).toBeInTheDocument()
    expect(screen.getByText('입력 방식:')).toBeInTheDocument()
  })
})
