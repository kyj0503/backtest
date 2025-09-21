/**
 * 테스트 유틸리티 함수들
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

// 모킹 헬퍼 함수들
export const createMockBacktestResult = () => ({
  status: 'success' as const,
  backtest_type: 'single_stock' as const,
  data: {
    ticker: 'AAPL',
    strategy: 'buy_and_hold',
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    ohlc_data: [],
    equity_data: [],
    trade_markers: [],
    indicators: [],
    summary_stats: {
      total_return_pct: 15.5,
      total_trades: 2,
      win_rate_pct: 100,
      max_drawdown_pct: -5.2,
      sharpe_ratio: 1.2,
      profit_factor: 2.1,
    }
  }
})

export const createMockStrategy = () => ({
  name: 'buy_and_hold',
  description: 'Simple buy and hold strategy',
  parameters: [],
  category: 'basic'
})

// API 모킹 헬퍼
export const mockApiResponse = <T>(data: T) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {} as any,
})

// 비동기 유틸리티
export const waitForLoadingToFinish = () => 
  new Promise(resolve => setTimeout(resolve, 0))

// 에러 바운더리 테스트용
export const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}