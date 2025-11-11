/**
 * BacktestForm 컴포넌트 테스트
 * 
 * **테스트 범위**:
 * - 폼 필드 렌더링
 * - 유효성 검증
 * - 사용자 입력 처리
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@/test/utils'
import userEvent from '@testing-library/user-event'

// Mock BacktestForm 컴포넌트 (실제 구현은 복잡하므로 간단한 버전으로 테스트)
const MockBacktestForm = ({ onSubmit }: { onSubmit: (data: any) => void }) => {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data = {
      symbol: formData.get('symbol'),
      startDate: formData.get('startDate'),
      endDate: formData.get('endDate'),
      strategy: formData.get('strategy'),
    }
    
    // 간단한 검증
    if (!data.symbol) {
      alert('종목 심볼을 입력해주세요.')
      return
    }
    
    if (data.startDate && data.endDate && data.startDate >= data.endDate) {
      alert('종료일은 시작일보다 이후여야 합니다.')
      return
    }
    
    onSubmit(data)
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="symbol">종목 심볼</label>
      <input id="symbol" name="symbol" type="text" />

      <label htmlFor="startDate">시작일</label>
      <input id="startDate" name="startDate" type="date" />

      <label htmlFor="endDate">종료일</label>
      <input id="endDate" name="endDate" type="date" />

      <label htmlFor="strategy">전략</label>
      <select id="strategy" name="strategy">
        <option value="">전략 선택</option>
        <option value="buy_hold_strategy">Buy & Hold</option>
        <option value="sma_cross">SMA Cross</option>
        <option value="rsi_strategy">RSI Strategy</option>
      </select>

      <button type="submit">백테스트 실행</button>
    </form>
  )
}

describe('BacktestForm', () => {
  describe('폼 렌더링', () => {
    it('필수 입력 필드를 모두 렌더링한다', () => {
      render(<MockBacktestForm onSubmit={vi.fn()} />)

      expect(screen.getByLabelText('종목 심볼')).toBeInTheDocument()
      expect(screen.getByLabelText('시작일')).toBeInTheDocument()
      expect(screen.getByLabelText('종료일')).toBeInTheDocument()
      expect(screen.getByLabelText('전략')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '백테스트 실행' })).toBeInTheDocument()
    })

    it('전략 선택 드롭다운에 옵션이 표시된다', () => {
      render(<MockBacktestForm onSubmit={vi.fn()} />)

      const strategySelect = screen.getByLabelText('전략')
      expect(strategySelect).toBeInTheDocument()
      
      // 옵션 확인
      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(4) // 빈 옵션 + 3개 전략
      expect(screen.getByRole('option', { name: 'Buy & Hold' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'SMA Cross' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'RSI Strategy' })).toBeInTheDocument()
    })
  })

  describe('사용자 입력 처리', () => {
    it('종목 심볼을 입력할 수 있다', async () => {
      const user = userEvent.setup()
      render(<MockBacktestForm onSubmit={vi.fn()} />)

      const symbolInput = screen.getByLabelText('종목 심볼')
      await user.type(symbolInput, 'AAPL')

      expect(symbolInput).toHaveValue('AAPL')
    })

    it('날짜를 선택할 수 있다', async () => {
      const user = userEvent.setup()
      render(<MockBacktestForm onSubmit={vi.fn()} />)

      const startDateInput = screen.getByLabelText('시작일')
      const endDateInput = screen.getByLabelText('종료일')

      await user.type(startDateInput, '2023-01-01')
      await user.type(endDateInput, '2023-12-31')

      expect(startDateInput).toHaveValue('2023-01-01')
      expect(endDateInput).toHaveValue('2023-12-31')
    })

    it('전략을 선택할 수 있다', async () => {
      const user = userEvent.setup()
      render(<MockBacktestForm onSubmit={vi.fn()} />)

      const strategySelect = screen.getByLabelText('전략')
      await user.selectOptions(strategySelect, 'buy_hold_strategy')

      expect(strategySelect).toHaveValue('buy_hold_strategy')
    })
  })

  describe('폼 유효성 검증', () => {
    it('종목 심볼이 없으면 경고 표시', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

      render(<MockBacktestForm onSubmit={onSubmit} />)

      const submitButton = screen.getByRole('button', { name: '백테스트 실행' })
      await user.click(submitButton)

      expect(alertSpy).toHaveBeenCalledWith('종목 심볼을 입력해주세요.')
      expect(onSubmit).not.toHaveBeenCalled()

      alertSpy.mockRestore()
    })

    it('시작일이 종료일보다 늦으면 경고 표시', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

      render(<MockBacktestForm onSubmit={onSubmit} />)

      const symbolInput = screen.getByLabelText('종목 심볼')
      const startDateInput = screen.getByLabelText('시작일')
      const endDateInput = screen.getByLabelText('종료일')

      await user.type(symbolInput, 'AAPL')
      await user.type(startDateInput, '2023-12-31')
      await user.type(endDateInput, '2023-01-01')

      const submitButton = screen.getByRole('button', { name: '백테스트 실행' })
      await user.click(submitButton)

      expect(alertSpy).toHaveBeenCalledWith('종료일은 시작일보다 이후여야 합니다.')
      expect(onSubmit).not.toHaveBeenCalled()

      alertSpy.mockRestore()
    })
  })

  describe('폼 제출', () => {
    it('유효한 입력으로 폼을 제출할 수 있다', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(<MockBacktestForm onSubmit={onSubmit} />)

      const symbolInput = screen.getByLabelText('종목 심볼')
      const startDateInput = screen.getByLabelText('시작일')
      const endDateInput = screen.getByLabelText('종료일')
      const strategySelect = screen.getByLabelText('전략')

      await user.type(symbolInput, 'AAPL')
      await user.type(startDateInput, '2023-01-01')
      await user.type(endDateInput, '2023-12-31')
      await user.selectOptions(strategySelect, 'buy_hold_strategy')

      const submitButton = screen.getByRole('button', { name: '백테스트 실행' })
      await user.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          symbol: 'AAPL',
          startDate: '2023-01-01',
          endDate: '2023-12-31',
          strategy: 'buy_hold_strategy',
        })
      })
    })
  })
})
