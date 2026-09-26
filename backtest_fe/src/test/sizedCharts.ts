/**
 * happy-dom에서 Recharts ResponsiveContainer에 실제 크기를 주는 헬퍼
 *
 * happy-dom은 레이아웃 엔진이 없어 모든 요소의 크기가 0이고, 전역
 * ResizeObserver 목(setup.ts)은 콜백을 부르지 않는다. 그대로 두면
 * ResponsiveContainer가 차트 본문(svg)을 그리지 않는다.
 *
 * ChartRendering.test.tsx와 같은 방식이다: ResizeObserver를 크기를 통지하는
 * 구현으로 바꾸고, `recharts-responsive-container` 요소에만 크기를 부여한다
 * (모든 요소에 주면 Legend 높이가 플롯 영역을 잡아먹어 곡선이 사라진다).
 *
 * describe 블록(또는 파일 최상위)에서 한 번 호출한다.
 */
import { beforeAll, afterAll } from 'vitest'

export const CHART_WIDTH = 800
export const CHART_HEIGHT = 400

const sizedRect = () =>
  ({
    width: CHART_WIDTH,
    height: CHART_HEIGHT,
    top: 0,
    left: 0,
    bottom: CHART_HEIGHT,
    right: CHART_WIDTH,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  }) as DOMRect

class SizedResizeObserver {
  constructor(private callback: ResizeObserverCallback) {}

  observe(target: Element) {
    this.callback(
      [{ target, contentRect: sizedRect() } as unknown as ResizeObserverEntry],
      this as unknown as ResizeObserver
    )
  }

  unobserve() {}
  disconnect() {}
}

export function installSizedCharts() {
  const originalRO = global.ResizeObserver
  const originalRect = Object.getOwnPropertyDescriptor(
    HTMLElement.prototype,
    'getBoundingClientRect'
  )
  const nativeRect = HTMLElement.prototype.getBoundingClientRect

  beforeAll(() => {
    global.ResizeObserver = SizedResizeObserver as unknown as typeof ResizeObserver
    Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
      configurable: true,
      value(this: HTMLElement) {
        if (this.classList?.contains('recharts-responsive-container')) {
          return sizedRect()
        }
        return nativeRect.call(this)
      },
    })
  })

  afterAll(() => {
    global.ResizeObserver = originalRO
    if (originalRect) {
      Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', originalRect)
    }
  })
}
