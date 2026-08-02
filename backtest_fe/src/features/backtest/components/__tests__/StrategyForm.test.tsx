/**
 * StrategyForm 테스트 (P3-17 / P2-32)
 *
 * P3-17: StrategyForm은 FormField의 onChange 값을
 * `updateStrategyParam(key, value.toString())`로 다시 문자열화해서
 * 넘겼다. FormField가 숫자를 넘겨줘도 여기서 다시 문자열로 바뀌어
 * strategy_params가 `{"short_window": "15"}`처럼 문자열로 제출됐다.
 *
 * P2-32: "투자 전략" bare Select도 접근 가능한 이름이 없었다(FormField
 * 수정으로 해결되는지 여기서도 확인한다).
 */
import { describe, it, expect, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen } from '@/test/utils'
import StrategyForm from '../StrategyForm'

describe('StrategyForm', () => {
  it('숫자 파라미터를 수정하면 updateStrategyParam이 문자열이 아니라 숫자로 호출된다', async () => {
    const user = userEvent.setup()
    const updateStrategyParam = vi.fn()

    render(
      <StrategyForm
        selectedStrategy="sma_strategy"
        setSelectedStrategy={vi.fn()}
        strategyParams={{ short_window: 10, long_window: 20 }}
        updateStrategyParam={updateStrategyParam}
      />
    )

    const input = screen.getByRole('spinbutton', { name: '단기 이동평균 기간' })
    await user.clear(input)
    await user.type(input, '15')

    expect(updateStrategyParam).toHaveBeenLastCalledWith('short_window', 15)
    expect(typeof updateStrategyParam.mock.lastCall?.[1]).toBe('number')
  })

  it('"투자 전략" Select가 label로부터 접근 가능한 이름을 얻는다 (P2-32)', () => {
    render(
      <StrategyForm
        selectedStrategy="buy_hold_strategy"
        setSelectedStrategy={vi.fn()}
        strategyParams={{}}
        updateStrategyParam={vi.fn()}
      />
    )

    expect(screen.getByRole('combobox', { name: '투자 전략' })).toBeInTheDocument()
  })
})
