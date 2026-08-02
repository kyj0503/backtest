/**
 * FormField 접근성 / 숫자 입력 인체공학 테스트 (P2-32 / P3-17)
 *
 * P2-32: FormField.tsx는 <Label>을 컨트롤 옆에 렌더링만 할 뿐 htmlFor/id로
 * 묶지 않았다. 그래서 전략/날짜/수수료 섹션의 모든 입력이 스크린리더에게
 * 무명(unnamed)이었다 — getByLabelText/getByRole(..., {name})로 찾을 수
 * 없었다. bare Select 트리거도 접근 가능한 이름이 없었다.
 *
 * P3-17: type="number" 필드는 `parseFloat(e.target.value) || 0`으로 매
 * 입력마다 커밋했다. 그 결과 필드를 비울 수 없었고(즉시 0으로 스냅),
 * '-'나 '.5' 같은 부분 입력이 거부됐다.
 */
import { describe, it, expect, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen } from '@/test/utils'
import { FormField } from '../FormField'

describe('FormField 접근성 (P2-32)', () => {
  it('text 타입 입력이 label과 프로그램적으로 연결된다', () => {
    render(<FormField label="종목 심볼" type="text" value="AAPL" onChange={vi.fn()} />)

    expect(screen.getByRole('textbox', { name: '종목 심볼' })).toBeInTheDocument()
  })

  it('number 타입 입력이 label과 프로그램적으로 연결된다', () => {
    render(<FormField label="거래 수수료" type="number" value={0.2} onChange={vi.fn()} />)

    expect(screen.getByRole('spinbutton', { name: '거래 수수료' })).toBeInTheDocument()
  })

  it('date 타입 입력이 label과 프로그램적으로 연결된다', () => {
    render(<FormField label="시작 날짜" type="date" value="2023-01-01" onChange={vi.fn()} />)

    expect(screen.getByLabelText('시작 날짜')).toBeInTheDocument()
  })

  it('textarea가 label과 프로그램적으로 연결된다', () => {
    render(<FormField label="메모" type="textarea" value="" onChange={vi.fn()} />)

    expect(screen.getByRole('textbox', { name: '메모' })).toBeInTheDocument()
  })

  it('select(bare Select 트리거)가 label로부터 접근 가능한 이름을 얻는다', () => {
    render(
      <FormField
        label="투자 전략"
        type="select"
        value="buy_hold_strategy"
        onChange={vi.fn()}
        options={[{ value: 'buy_hold_strategy', label: '매수 후 보유' }]}
      />
    )

    expect(screen.getByRole('combobox', { name: '투자 전략' })).toBeInTheDocument()
  })
})

describe('FormField 숫자 입력 인체공학 (P3-17)', () => {
  it('숫자 필드를 비울 수 있고 0으로 스냅되지 않는다', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<FormField label="거래 수수료" type="number" value={5} onChange={onChange} />)

    const input = screen.getByRole('spinbutton', { name: '거래 수수료' })
    await user.clear(input)

    expect(input).toHaveValue(null) // 빈 number input의 표시값
    expect(onChange).not.toHaveBeenCalledWith(0)
  })

  it("입력 중 '-'를 그대로 보여준다 (즉시 거부/0으로 스냅하지 않음)", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<FormField label="거래 수수료" type="number" value={5} onChange={onChange} />)

    const input = screen.getByRole('spinbutton', { name: '거래 수수료' })
    await user.clear(input)
    await user.type(input, '-')

    expect(input).toHaveValue(null)
    expect(onChange).not.toHaveBeenCalledWith(0)
    expect(onChange).not.toHaveBeenCalledWith(expect.anything())
  })

  it("'.5'처럼 선행 0이 없는 소수를 입력하면 0.5로 커밋된다", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<FormField label="거래 수수료" type="number" value={5} onChange={onChange} />)

    const input = screen.getByRole('spinbutton', { name: '거래 수수료' })
    await user.clear(input)
    await user.type(input, '.5')

    expect(onChange).toHaveBeenLastCalledWith(0.5)
    expect(typeof onChange.mock.lastCall?.[0]).toBe('number')
  })

  it('완성된 숫자를 입력하면 문자열이 아니라 숫자로 onChange가 호출된다', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<FormField label="단기 이동평균 기간" type="number" value={10} onChange={onChange} />)

    const input = screen.getByRole('spinbutton', { name: '단기 이동평균 기간' })
    await user.clear(input)
    await user.type(input, '15')

    expect(onChange).toHaveBeenLastCalledWith(15)
    expect(typeof onChange.mock.lastCall?.[0]).toBe('number')
    // NaN이 부모로 전달되면 안 된다.
    for (const call of onChange.mock.calls) {
      expect(Number.isNaN(call[0])).toBe(false)
    }
  })

  it('전략 변경처럼 외부에서 value가 바뀌면 로컬 텍스트도 다시 동기화된다', () => {
    const { rerender } = render(
      <FormField label="단기 이동평균 기간" type="number" value={10} onChange={vi.fn()} />
    )

    let input = screen.getByRole('spinbutton', { name: '단기 이동평균 기간' })
    expect(input).toHaveValue(10)

    rerender(<FormField label="단기 이동평균 기간" type="number" value={20} onChange={vi.fn()} />)

    input = screen.getByRole('spinbutton', { name: '단기 이동평균 기간' })
    expect(input).toHaveValue(20)
  })
})
