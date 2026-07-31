import '@testing-library/jest-dom'
import { expect, afterEach, beforeAll, afterAll, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'
import { server } from './mocks/server'

// Testing Library 매처 확장
expect.extend(matchers)

// MSW 서버 설정
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
})
afterAll(() => server.close())

// MSW를 위한 전역 설정
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// happy-dom은 window.alert/confirm/prompt를 구현하지 않는다.
// Vitest 4의 vi.spyOn()은 대상이 실제 함수여야 하므로 no-op 스텁을 등록한다.
Object.defineProperty(window, 'alert', {
  writable: true,
  configurable: true,
  value: function alert() {},
})
Object.defineProperty(window, 'confirm', {
  writable: true,
  configurable: true,
  value: function confirm() {
    return true
  },
})
Object.defineProperty(window, 'prompt', {
  writable: true,
  configurable: true,
  value: function prompt() {
    return null
  },
})

// IntersectionObserver 모킹
// Vitest 4부터 vi.fn()에 화살표 함수를 넘기면 `new`로 호출할 수 없으므로 class로 정의한다.
class MockIntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
  takeRecords = vi.fn(() => [])
  root: Element | null = null
  rootMargin = ''
  thresholds: ReadonlyArray<number> = []
}
global.IntersectionObserver =
  MockIntersectionObserver as unknown as typeof IntersectionObserver

// ResizeObserver 모킹
class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver