/**
 * 테스트용 React 컴포넌트와 렌더링 유틸리티
 */

import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/hooks/useAuth'

// 커스텀 렌더 함수 - 공통 프로바이더들을 포함
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }

// 에러 바운더리 테스트용 컴포넌트
export const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}

// 로딩 상태 테스트용 컴포넌트
export const LoadingComponent = ({ isLoading }: { isLoading: boolean }) => {
  if (isLoading) {
    return <div>Loading...</div>
  }
  return <div>Content loaded</div>
}