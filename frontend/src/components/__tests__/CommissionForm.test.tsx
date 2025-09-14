import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CommissionForm from '../CommissionForm'

describe('CommissionForm', () => {
  it('리밸런싱 주기/수수료 변경 시 핸들러 호출', async () => {
    const user = userEvent.setup()
    const setRebalanceFrequency = vi.fn()
    const setCommission = vi.fn()

    render(
      <CommissionForm
        rebalanceFrequency="monthly"
        setRebalanceFrequency={setRebalanceFrequency}
        commission={0.2}
        setCommission={setCommission}
      />
    )

  const rLabel = screen.getByText('리밸런싱 주기')
  const rebalance = within(rLabel.closest('div') as HTMLElement).getByRole('combobox')
  // 기본 <select>라면 selectOptions 사용
  await user.selectOptions(rebalance, 'yearly')
  expect(setRebalanceFrequency).toHaveBeenCalledWith('yearly')

    const cLabel = screen.getByText('거래 수수료')
    const commissionInput = within(cLabel.closest('div') as HTMLElement).getByRole('spinbutton') as HTMLInputElement
    await user.clear(commissionInput)
    await user.type(commissionInput, '0.5')
    expect(setCommission).toHaveBeenCalled()
  })
})
