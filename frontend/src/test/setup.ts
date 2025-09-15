import '@testing-library/jest-dom'

// Fix for Radix UI hasPointerCapture issue in jsdom
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = function () {
    return false
  }
}

if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = function () {
    // no-op
  }
}

if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = function () {
    // no-op  
  }
}

// Mock environment variables for tests
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

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  unobserve: vi.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  unobserve: vi.fn(),
}))

// Ensure chart containers have non-zero size in JSDOM-based tests
Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
  configurable: true,
  get() {
    return 800
  },
})

Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
  configurable: true,
  get() {
    return 600
  },
})

Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  configurable: true,
  get() {
    return 800
  },
})

Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
  configurable: true,
  get() {
    return 600
  },
})

// Provide a basic getBoundingClientRect with width/height for components
// that rely on layout measurements (e.g., Recharts ResponsiveContainer)
if (!Element.prototype.getBoundingClientRect ||
    Element.prototype.getBoundingClientRect.toString().includes('[native code]') === false) {
  // no-op: keep existing implementation if provided by JSDOM
}
const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect
Element.prototype.getBoundingClientRect = function () {
  const rect = originalGetBoundingClientRect ? originalGetBoundingClientRect.call(this) : undefined
  const base = {
    x: 0,
    y: 0,
    top: 0,
    left: 0,
    bottom: 600,
    right: 800,
    width: 800,
    height: 600,
    toJSON: () => {},
  } as DOMRect
  return Object.assign(base, rect)
}

// Set up environment variables for testing
Object.defineProperty(import.meta, 'env', {
  value: {
    DEV: true,
    PROD: false,
    MODE: 'test',
    VITE_API_BASE_URL: 'http://localhost:8001',
  },
  writable: true,
})

// Suppress or filter noisy console messages in test environment
const _origWarn = console.warn.bind(console)
console.warn = (...args: any[]) => {
  try {
    const message = args.map(a => String(a)).join(' ')
    // Known noisy warnings we can safely ignore in CI tests
    if (
      message.includes('ReactDOMTestUtils.act is deprecated') ||
      message.includes('React Router Future Flag Warning') ||
      message.includes('Relative route resolution within Splat routes is changing') ||
      message.includes('The width(0) and height(0) of chart should be greater than 0')
    ) {
      return
    }
  } catch (e) {
    // fallthrough to original warn
  }
  _origWarn(...args)
}

const _origError = console.error.bind(console)
console.error = (...args: any[]) => {
  try {
    const message = args.map(a => String(a)).join(' ')
    // Suppress noisy or expected test-time errors that are logged in tests
    if (
      message.includes('ReactDOMTestUtils.act is deprecated') ||
      message.includes('The width(0) and height(0) of chart should be greater than 0')
    ) {
      return
    }
  } catch (e) {
    // fallthrough
  }
  _origError(...args)
}

const _origLog = console.log.bind(console)
console.log = (...args: any[]) => {
  try {
    const message = args.map(a => String(a)).join(' ')
    // Tests print helpful debug lines like "Portfolio data being sent"; suppress to reduce CI noise
    if (message.includes('Portfolio data being sent') || message.includes('Strategy params being sent')) {
      return
    }
  } catch (e) {
    // fallthrough
  }
  _origLog(...args)
}

// Additionally filter certain messages written directly to stderr (some libs write warnings directly)
const _origStderrWrite = (process.stderr as any).write.bind(process.stderr)
;(process.stderr as any).write = (chunk: any, encoding?: any, cb?: any) => {
  try {
    const message = typeof chunk === 'string' ? chunk : String(chunk)
    if (
      message.includes('ReactDOMTestUtils.act is deprecated') ||
      message.includes('React Router Future Flag Warning') ||
      message.includes('Relative route resolution within Splat routes is changing') ||
      message.includes('The width(0) and height(0) of chart should be greater than 0')
    ) {
      return true
    }
  } catch (e) {
    // fallthrough
  }
  return _origStderrWrite(chunk, encoding, cb)
}
