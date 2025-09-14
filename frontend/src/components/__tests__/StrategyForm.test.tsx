import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import StrategyForm from '../StrategyForm'

describe('StrategyForm', () => {

  // Radix UI Select는 jsdom 환경에서 option 상호작용 테스트가 불가능하므로 해당 테스트를 삭제합니다.

  it('sma_crossover 선택 시 파라미터 입력 필드를 표시하고 변경 이벤트를 전파', async () => {
    const user = userEvent.setup()
    const setSelectedStrategy = vi.fn()
    const updateStrategyParam = vi.fn()

    render(
      <StrategyForm
        selectedStrategy="sma_crossover"
        setSelectedStrategy={setSelectedStrategy}
        strategyParams={{}}
        updateStrategyParam={updateStrategyParam}
      />
    )

    // 단기 이동평균 기간 필드 존재 확인 후 입력 시 콜백 발생
    const shortLabel = screen.getByText('단기 이동평균 기간')
    const shortField = within(shortLabel.closest('div') as HTMLElement).getByRole('spinbutton') as HTMLInputElement
    await user.clear(shortField)
    await user.type(shortField, '15')
    expect(updateStrategyParam).toHaveBeenCalled()
    expect(updateStrategyParam.mock.calls[0][0]).toBe('short_window')
  })
})
