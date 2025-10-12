import { describe, it, expect } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useBacktestForm } from '../useBacktestForm'

const fillValidPortfolio = (actions: ReturnType<typeof useBacktestForm>['actions']) => {
  act(() => {
    actions.updateStock(0, 'symbol', 'AAPL')
    actions.updateStock(0, 'amount', 10000)
    actions.setStartDate('2023-01-01')
    actions.setEndDate('2023-12-31')
    actions.setCommission(0.2)
  })
}

describe('useBacktestForm', () => {
  it('applies strategy defaults when strategy changes', async () => {
    const { result } = renderHook(() => useBacktestForm())

    act(() => {
      result.current.actions.setSelectedStrategy('sma_strategy')
    })

    await waitFor(() => {
      expect(result.current.state.strategy.strategyParams).toEqual({
        short_window: 10,
        long_window: 20,
      })
    })
  })

  it('supports weight-based allocations and keeps total amount in sync', () => {
    const { result } = renderHook(() => useBacktestForm())

    act(() => {
      result.current.actions.setPortfolioInputMode('weight')
      result.current.actions.setTotalInvestment(20000)
      result.current.actions.updateStock(0, 'weight', 50)
      result.current.actions.addStock()
      result.current.actions.updateStock(1, 'symbol', 'MSFT')
      result.current.actions.updateStock(1, 'weight', 50)
    })

    expect(result.current.state.portfolioInputMode).toBe('weight')
    expect(result.current.state.portfolio[0].amount).toBe(10000)
    expect(result.current.state.portfolio[1].amount).toBe(10000)
    expect(result.current.helpers.getTotalAmount()).toBe(20000)
  })

  it('validates portfolio and returns errors for invalid input', () => {
    const { result } = renderHook(() => useBacktestForm())

    act(() => {
      result.current.actions.updateStock(0, 'amount', 50)
      result.current.actions.updateStock(0, 'symbol', '')
      result.current.actions.setStartDate('2023-12-31')
      result.current.actions.setEndDate('2023-01-01')
      result.current.actions.setCommission(10)
    })

    const errors = result.current.helpers.validateForm()
    expect(errors).toEqual(expect.arrayContaining([
      '1번째 종목의 투자 금액은 최소 $100 이상이어야 합니다.',
      '시작 날짜는 종료 날짜보다 이전이어야 합니다.',
      '수수료는 0% ~ 5% 사이여야 합니다.',
    ]))
  })

  it('passes validation when form is filled with valid data', () => {
    const { result } = renderHook(() => useBacktestForm())
    fillValidPortfolio(result.current.actions)

    const errors = result.current.helpers.validateForm()
    expect(errors).toHaveLength(0)
  })
})
