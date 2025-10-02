/**
 * ErrorBoundary 컴포넌트 테스트
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import ErrorBoundary from '../ErrorBoundary'

// 에러를 발생시킬 테스트용 컴포넌트
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>정상 컴포넌트</div>
}

describe('ErrorBoundary', () => {
  // console.error 억제 (테스트 출력을 깔끔하게 유지)
  const originalError = console.error
  beforeEach(() => {
    console.error = vi.fn()
  })

  afterEach(() => {
    console.error = originalError
  })

  it('에러가 없으면 자식 컴포넌트를 정상 렌더링한다', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('정상 컴포넌트')).toBeInTheDocument()
  })

  it('에러가 발생하면 에러 UI를 표시한다', async () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(await screen.findByText(/오류가 발생했습니다/i)).toBeInTheDocument()
    expect(screen.getByText(/예상치 못한 오류로 인해/i)).toBeInTheDocument()
    
    consoleSpy.mockRestore()
  })

  it('다시 시도 버튼을 표시한다', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByRole('button', { name: /다시 시도/i })).toBeInTheDocument()
  })

  it('페이지 새로고침 버튼을 표시한다', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByRole('button', { name: /페이지 새로고침/i })).toBeInTheDocument()
  })

  it('다시 시도 버튼을 클릭하면 에러 상태를 리셋한다', async () => {
    const user = userEvent.setup()
    
    let shouldThrow = true
    const TestComponent = () => {
      if (shouldThrow) {
        throw new Error('Test error message')
      }
      return <div>정상 컴포넌트</div>
    }

    render(
      <ErrorBoundary>
        <TestComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText(/오류가 발생했습니다/i)).toBeInTheDocument()

    const retryButton = screen.getByRole('button', { name: /다시 시도/i })
    
    // 에러를 throw하지 않도록 플래그 변경
    shouldThrow = false
    
    await user.click(retryButton)

    // 다시 시도를 클릭하면 에러 상태가 리셋되고, 정상 컴포넌트가 표시됨
    expect(screen.getByText('정상 컴포넌트')).toBeInTheDocument()
  })

  it('페이지 새로고침 버튼을 클릭하면 window.location.reload를 호출한다', async () => {
    const user = userEvent.setup()
    const reloadMock = vi.fn()
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true,
    })

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    const reloadButton = await screen.findByRole('button', { name: /페이지 새로고침/i })
    await user.click(reloadButton)

    expect(reloadMock).toHaveBeenCalledTimes(1)
    consoleSpy.mockRestore()
  })

  it('커스텀 fallback UI를 제공하면 사용한다', () => {
    const customFallback = <div>커스텀 에러 메시지</div>

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('커스텀 에러 메시지')).toBeInTheDocument()
    expect(screen.queryByText(/오류가 발생했습니다/i)).not.toBeInTheDocument()
  })

  it('에러 ID를 표시한다', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText(/오류 ID:/i)).toBeInTheDocument()
  })

  it('DEV 모드에서 에러 상세 정보를 표시한다', () => {
    // DEV 모드인지 확인
    if (import.meta.env.DEV) {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // 개발자 정보 섹션이 있는지 확인
      expect(screen.getByText(/개발자 정보/i)).toBeInTheDocument()
      // getAllByText를 사용하여 여러 인스턴스 중 하나를 확인
      const errorMessages = screen.getAllByText(/Test error message/i)
      expect(errorMessages.length).toBeGreaterThan(0)
    }
  })
})
