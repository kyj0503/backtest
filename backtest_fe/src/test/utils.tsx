/**
 * 테스트 유틸리티 함수들
 */

import { render as rtlRender, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { BrowserRouter } from 'react-router-dom'

// 커스텀 렌더 함수 - 공통 프로바이더들을 포함
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => rtlRender(ui, { wrapper: AllTheProviders, ...options })

// Testing Library의 모든 유틸을 re-export
export * from '@testing-library/react'
// customRender를 render로 export
export { customRender as render }

// 모킹 헬퍼 함수들 - fixtures.ts로 이동함
export { 
  createMockBacktest,
  createMockTrade,
  createMockOHLC,
  createMockEquity,
  createMockStrategy,
  createMockBacktestRequest,
  createMockBacktestResult
} from './fixtures'

// API 모킹 헬퍼
export function mockApiResponse<T>(data: T) {
  return {
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {} as any,
  }
}

// 비동기 유틸리티 - helpers.ts로 이동함
export { waitForLoadingToFinish, sleep } from './helpers'
