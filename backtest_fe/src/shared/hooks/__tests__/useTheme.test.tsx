/**
 * useTheme 전역 상태 테스트 (P2-31)
 *
 * 예전에는 useTheme()을 호출하는 컴포넌트(App.tsx:13, Header.tsx:16,
 * ThemeSelector.tsx:102)마다 독립적인 useState 인스턴스가 생겼다. DOM
 * class·CSS 변수·localStorage 같은 부수효과로만 "동기화된 것처럼" 보였을
 * 뿐이었고, Radix Dialog가 닫힘 상태에서 ThemeSelector를 언마운트해 주는
 * 우연 덕분에 실제로는 드러나지 않았다. ThemeSelector를 상시 렌더링하거나
 * showDarkModeToggle을 Header와 동시에 켜면 desync가 발생했다(한쪽에서
 * 토글해도 다른 쪽 인스턴스는 갱신 전 stale한 isDarkMode를 계속 들고 있음).
 *
 * 지금은 ThemeProvider(React Context)가 유일한 소스이므로, 이 훅을
 * 구독하는 모든 컴포넌트는 항상 같은 상태를 봐야 한다.
 */
import type { ReactNode } from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { renderHook } from '@testing-library/react'
import { render, screen } from '@/test/utils'
import { ThemeProvider, useTheme } from '../useTheme'
import Header from '@/shared/components/layout/Header'
import ThemeSelector from '@/shared/components/layout/ThemeSelector'

const wrapper = ({ children }: { children: ReactNode }) => (
  <ThemeProvider>{children}</ThemeProvider>
)

/**
 * src/test/setup.ts는 window.matchMedia를 `writable: true`(하지만
 * configurable은 명시하지 않음, 즉 false)로 정의한다. vi.spyOn(...).
 * mockRestore()는 이런 경우 원래 구현을 온전히 복원하지 못하고 인자 없는
 * vi.fn()(항상 undefined 반환)으로 남길 수 있어, 다음 테스트에서
 * "Cannot read properties of undefined"로 이어질 수 있다. 그래서 함수
 * 참조를 직접 저장/복원한다 — writable: true라 단순 대입은 항상 허용된다.
 */
const withMatchMediaMock = (matches: boolean, run: () => void) => {
  const original = window.matchMedia
  window.matchMedia = ((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as typeof window.matchMedia
  try {
    run()
  } finally {
    window.matchMedia = original
  }
}

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('ThemeProvider 밖에서 호출하면 명확한 에러를 던진다', () => {
    expect(() => renderHook(() => useTheme())).toThrow(/ThemeProvider/)
  })

  it('저장된 테마/다크모드를 localStorage에서 복원한다', () => {
    localStorage.setItem('selected-theme', 'amber-minimal')
    localStorage.setItem('dark-mode', 'true')

    const { result } = renderHook(() => useTheme(), { wrapper })

    expect(result.current.currentTheme).toBe('amber-minimal')
    expect(result.current.isDarkMode).toBe(true)
  })

  it('dark-mode가 저장되어 있지 않으면 시스템 테마 선호(다크)를 따른다', () => {
    withMatchMediaMock(true, () => {
      const { result } = renderHook(() => useTheme(), { wrapper })
      expect(result.current.isDarkMode).toBe(true)
    })
  })

  it('dark-mode가 저장되어 있지 않으면 시스템 테마 선호(라이트)를 따른다', () => {
    withMatchMediaMock(false, () => {
      const { result } = renderHook(() => useTheme(), { wrapper })
      expect(result.current.isDarkMode).toBe(false)
    })
  })

  it('두 컴포넌트가 같은 ThemeProvider를 구독하면 한쪽의 변경이 다른 쪽에 즉시 반영된다', async () => {
    const user = userEvent.setup()

    render(
      <ThemeProvider>
        <Header />
        <ThemeSelector showDarkModeToggle />
      </ThemeProvider>
    )

    // 초기 상태: 라이트 모드(비활성) — 두 컴포넌트가 같은 값을 본다.
    expect(screen.getByText(/다크 모드:/)).toHaveTextContent('비활성')

    // Header의 다크 모드 토글 버튼을 클릭한다.
    await user.click(screen.getByRole('button', { name: '다크 모드로 전환' }))

    // 형제로 렌더링된 ThemeSelector가 별도 useState 인스턴스였다면 이 값은
    // 여전히 '비활성'으로 남아 desync가 재현됐을 것이다.
    expect(screen.getByText(/다크 모드:/)).toHaveTextContent('활성')
  })
})
