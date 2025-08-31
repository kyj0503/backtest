import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ErrorBoundary from '../ErrorBoundary'

// 에러를 발생시키는 테스트 컴포넌트
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('테스트 에러입니다')
  }
  return <div>정상 컴포넌트</div>
}

describe('ErrorBoundary', () => {
  it('정상적인 컴포넌트를 렌더링해야 함', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('정상 컴포넌트')).toBeInTheDocument()
  })

  it('에러가 발생하면 에러 UI를 표시해야 함', () => {
    // 콘솔 에러를 숨기기 위한 mock
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument()
    expect(screen.getByText(/예상치 못한 오류로 인해/)).toBeInTheDocument()
    expect(screen.getByText('다시 시도')).toBeInTheDocument()
    expect(screen.getByText('페이지 새로고침')).toBeInTheDocument()
    
    consoleSpy.mockRestore()
  })

  it('커스텀 폴백 UI를 사용할 수 있어야 함', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const customFallback = <div>커스텀 에러 메시지</div>
    
    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('커스텀 에러 메시지')).toBeInTheDocument()
    expect(screen.queryByText('오류가 발생했습니다')).not.toBeInTheDocument()
    
    consoleSpy.mockRestore()
  })
})
