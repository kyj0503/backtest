/**
 * 라우팅 스모크 테스트
 *
 * react-router-dom v7 마이그레이션 시 라우팅 동작을 검증하기 위해 추가.
 * 실제 <BrowserRouter>(App 내부)를 그대로 사용하며, 페이지 컴포넌트만 stub으로
 * 대체해 라우트 매칭 / <Navigate> 리다이렉트 / <Link> 내비게이션만 검증한다.
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, beforeEach, vi } from 'vitest'

vi.mock('../pages/HomePage', () => ({
  default: () => <div data-testid="page-home">HomePage</div>,
}))

vi.mock('../pages/PortfolioPage', () => ({
  default: () => <div data-testid="page-portfolio">PortfolioPage</div>,
}))

import App from '../App'

const go = (path: string) => window.history.pushState({}, '', path)

describe('앱 라우팅', () => {
  beforeEach(() => {
    go('/')
  })

  it('/ 는 HomePage를 렌더링한다', async () => {
    go('/')
    render(<App />)
    expect(await screen.findByTestId('page-home')).toBeInTheDocument()
  })

  it('/backtest 는 PortfolioPage를 렌더링한다', async () => {
    go('/backtest')
    render(<App />)
    expect(await screen.findByTestId('page-portfolio')).toBeInTheDocument()
  })

  it.each(['/single-stock', '/portfolio'])(
    '레거시 경로 %s 는 /backtest 로 리다이렉트된다',
    async (legacyPath) => {
      go(legacyPath)
      render(<App />)

      expect(await screen.findByTestId('page-portfolio')).toBeInTheDocument()
      await waitFor(() => {
        expect(window.location.pathname).toBe('/backtest')
      })
    }
  )

  it('헤더의 <Link> 클릭으로 / → /backtest 이동이 동작한다', async () => {
    const user = userEvent.setup()
    go('/')
    render(<App />)

    expect(await screen.findByTestId('page-home')).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: '백테스트' }))

    expect(await screen.findByTestId('page-portfolio')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/backtest')
  })
})
