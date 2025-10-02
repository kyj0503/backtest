import { describe, it, expect } from 'vitest'
import { backtestFormReducer, backtestFormHelpers } from '../backtestFormReducer'
import { initialBacktestFormState, type BacktestFormState } from '../backtest-form-types'
import { ASSET_TYPES } from '../strategyConfig'

const cloneState = (state: BacktestFormState): BacktestFormState => JSON.parse(JSON.stringify(state))

describe('backtestFormReducer', () => {
  it('converts existing amounts to weights when switching to weight mode', () => {
    const startingState: BacktestFormState = {
      ...cloneState(initialBacktestFormState),
      portfolio: [
        {
          symbol: 'AAPL',
          amount: 6000,
          investmentType: 'lump_sum',
          dcaPeriods: 12,
          assetType: ASSET_TYPES.STOCK,
        },
        {
          symbol: 'MSFT',
          amount: 4000,
          investmentType: 'lump_sum',
          dcaPeriods: 12,
          assetType: ASSET_TYPES.STOCK,
        },
      ],
      totalInvestment: 10000,
    }

    const nextState = backtestFormReducer(startingState, {
      type: 'SET_PORTFOLIO_INPUT_MODE',
      payload: 'weight',
    })

    expect(nextState.portfolio[0].weight).toBe(60)
    expect(nextState.portfolio[1].weight).toBe(40)
    expect(nextState.portfolio[0].amount).toBe(6000)
    expect(nextState.portfolio[1].amount).toBe(4000)
    expect(nextState.portfolioInputMode).toBe('weight')
  })

  it('recalculates amounts when total investment changes in weight mode', () => {
    const weightedState: BacktestFormState = {
      ...cloneState(initialBacktestFormState),
      portfolioInputMode: 'weight',
      totalInvestment: 10000,
      portfolio: [
        {
          symbol: 'AAPL',
          amount: 6000,
          weight: 60,
          investmentType: 'lump_sum',
          dcaPeriods: 12,
          assetType: ASSET_TYPES.STOCK,
        },
        {
          symbol: 'MSFT',
          amount: 4000,
          weight: 40,
          investmentType: 'lump_sum',
          dcaPeriods: 12,
          assetType: ASSET_TYPES.STOCK,
        },
      ],
    }

    const nextState = backtestFormReducer(weightedState, {
      type: 'SET_TOTAL_INVESTMENT',
      payload: 20000,
    })

    expect(nextState.totalInvestment).toBe(20000)
    expect(nextState.portfolio[0].amount).toBe(12000)
    expect(nextState.portfolio[1].amount).toBe(8000)
  })

  it('clears weight when updating amounts directly in amount mode', () => {
    const amountModeState: BacktestFormState = {
      ...cloneState(initialBacktestFormState),
      portfolio: [
        {
          symbol: 'AAPL',
          amount: 10000,
          weight: 25,
          investmentType: 'lump_sum',
          dcaPeriods: 12,
          assetType: ASSET_TYPES.STOCK,
        },
      ],
    }

    const updated = backtestFormReducer(amountModeState, {
      type: 'UPDATE_STOCK',
      payload: { index: 0, field: 'amount', value: 15000 },
    })

    expect(updated.portfolio[0].amount).toBe(15000)
    expect(updated.portfolio[0].weight).toBeUndefined()
  })
})

describe('backtestFormHelpers', () => {
  it('validates portfolio entries and reports errors', () => {
    const errors = backtestFormHelpers.validatePortfolio([
      {
        symbol: '',
        amount: 50,
        investmentType: 'lump_sum',
        dcaPeriods: 12,
        assetType: ASSET_TYPES.STOCK,
      },
      {
        symbol: 'MSFT',
        amount: 900,
        weight: 70,
        investmentType: 'dca',
        dcaPeriods: 0,
        assetType: ASSET_TYPES.STOCK,
      },
      {
        symbol: 'CASH',
        amount: 200,
        weight: 40,
        investmentType: 'lump_sum',
        dcaPeriods: 12,
        assetType: ASSET_TYPES.CASH,
      },
    ])

    expect(errors).toContain('1번째 종목의 심볼을 입력해주세요.')
    expect(errors).toContain('1번째 종목의 투자 금액은 최소 $100 이상이어야 합니다.')
    expect(errors).toContain('2번째 종목의 DCA 기간을 설정해주세요.')
    expect(errors.some(error => error.includes('포트폴리오 비중 합계가 100%가 아닙니다'))).toBe(true)
  })
})
