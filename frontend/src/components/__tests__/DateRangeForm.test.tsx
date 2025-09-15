import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { act } from 'react'
import DateRangeForm from '../DateRangeForm'

describe('DateRangeForm', () => {
  it('시작/종료 날짜 변경 시 핸들러 호출', async () => {
    const user = userEvent.setup()
    const setStartDate = vi.fn()
    const setEndDate = vi.fn()

    render(
      <DateRangeForm
        startDate="2023-01-01"
        setStartDate={setStartDate}
        endDate="2023-12-31"
        setEndDate={setEndDate}
      />
    )

    const sLabel = screen.getByText('시작 날짜')
    const startWrap = sLabel.closest('div') as HTMLElement
    const startInput = startWrap.querySelector('input[type="date"]') as HTMLInputElement
    await act(async () => {
      await user.clear(startInput)
      await user.type(startInput, '2023-02-01')
    })
    expect(setStartDate).toHaveBeenCalled()

    const eLabel = screen.getByText('종료 날짜')
    const endWrap = eLabel.closest('div') as HTMLElement
    const endInput = endWrap.querySelector('input[type="date"]') as HTMLInputElement
    await act(async () => {
      await user.clear(endInput)
      await user.type(endInput, '2023-11-30')
    })
    expect(setEndDate).toHaveBeenCalled()
  })
})
