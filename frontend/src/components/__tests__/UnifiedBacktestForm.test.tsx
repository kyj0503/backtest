import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { act } from 'react'
import userEvent from '@testing-library/user-event'
import UnifiedBacktestForm from '../UnifiedBacktestForm'

// Note: This is an integration-style test targeting the composed form.
// It simulates minimal user interactions to pass validation and verifies
// the transformed request payload (e.g., symbol uppercasing, commission conversion).

describe('UnifiedBacktestForm (integration)', () => {
  it('사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<UnifiedBacktestForm onSubmit={onSubmit} />)

    // PortfolioForm: select first row symbol to a predefined one (e.g., AAPL)
    // Table first row: first cell contains a select (combobox)
    const selects = screen.getAllByRole('combobox')
    // The very first select in the page should be the stock picker for portfolio
    const portfolioSymbolSelect = selects[0]
    await user.selectOptions(portfolioSymbolSelect, 'AAPL')

    // CommissionForm: set commission to 0.3 (%)
    // Find the label then query within its container for the input
    const commissionLabel = screen.getByText('거래 수수료')
    const commissionContainer = commissionLabel.closest('div') as HTMLElement
    const commissionNumber = within(commissionContainer).getByRole('spinbutton') as HTMLInputElement
    await user.clear(commissionNumber)
    await user.type(commissionNumber, '0.3')

    // StrategyForm: leave default (buy_and_hold) – no params required

    // Submit
    const submitBtn = screen.getByRole('button', { name: /백테스트 실행/i })
    await act(async () => {
      await user.click(submitBtn)
    })

    expect(onSubmit).toHaveBeenCalledTimes(1)
    const req = onSubmit.mock.calls[0][0]

    // Validate transformed request payload
    expect(req).toMatchObject({
      strategy: 'buy_and_hold',
      strategy_params: {},
      rebalance_frequency: 'monthly',
    })
    expect(req.portfolio[0]).toMatchObject({
      symbol: 'AAPL',
      investment_type: 'lump_sum',
      dca_periods: 12,
      asset_type: 'stock',
    })
    // Commission is provided in percent and converted to decimal
    expect(req.commission).toBeCloseTo(0.003, 6)
  })

  it('onSubmit에서 오류 발생 시 에러 메시지를 표시해야 함', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error('테스트 오류'))
    const user = userEvent.setup()

    render(<UnifiedBacktestForm onSubmit={onSubmit} />)

    // Select a valid symbol so validation passes
    const selects = screen.getAllByRole('combobox')
    await user.selectOptions(selects[0], 'AAPL')

    // Submit
    const submitBtn = screen.getByRole('button', { name: /백테스트 실행/i })
    await act(async () => {
      await user.click(submitBtn)
    })

    // Error banner should render
    expect(await screen.findByText(/입력 오류/)).toBeInTheDocument()
    expect(screen.getByText(/테스트 오류/)).toBeInTheDocument()
  })
})
