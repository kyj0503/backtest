import '@testing-library/jest-dom'
import { expect, afterEach, beforeAll, afterAll, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'
import { server } from './mocks/server'

// Testing Library 매처 확장
expect.extend(matchers)

// MSW 서버 설정
// onUnhandledRequest: 'error' (P3-03) — 모킹되지 않은 요청은 경고로 흘려보내지
// 않고 테스트를 실패시킨다. 'warn'이었을 때는 핸들러 누락이 콘솔 경고로만
// 남고 테스트는 그대로 초록불이라, 실제로는 아무 응답도 받지 못한 컴포넌트가
// 우연히(로딩/에러 상태 등으로) 단언을 통과하는 경우를 놓칠 수 있었다.
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
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