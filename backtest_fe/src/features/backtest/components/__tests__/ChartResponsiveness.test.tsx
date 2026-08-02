/**
 * 차트 리사이즈 반응성 테스트 (P2-33)
 *
 * **배경**:
 * - StockPriceChart / BenchmarkIndexChart는 마진·틱 간격·각도를
 *   렌더 시점의 `window.innerWidth`로 직접 계산했다.
 * - 최초 마운트 이후 브라우저 창 크기가 바뀌어도 다시 렌더링되지 않는 한
 *   차트가 갱신되지 않아, 사실상 "최초 로드 시점의 화면 폭"에 고정됐다.
 * - resize 이벤트를 구독하는 작은 훅(useViewportWidth)으로 교체해
 *   리사이즈에 반응하도록 수정했다.
 *
 * **검증 방법**:
 * - happy-dom에는 레이아웃 엔진이 없어 ResponsiveContainer의 실제 크기가
 *   0이 된다. ChartRendering.test.tsx와 동일하게 ResizeObserver와
 *   getBoundingClientRect를 모킹해 컨테이너에 고정 크기를 부여한다.
 * - Recharts v3 XAxis는 `angle`/`text-anchor` prop을
 *   `.recharts-cartesian-axis-tick-line` 엘리먼트의 속성으로 그대로
 *   내려보낸다 (happy-dom 환경 기준, 실측 확인). 폭이 좁을 때는
 *   angle="-45"/text-anchor="end", 넓을 때는 angle="0"/text-anchor="middle"이며,
 *   interval 값 차이로 렌더링되는 틱 개수도 달라진다.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, act, cleanup } from '@testing-library/react';
import StockPriceChart from '../StockPriceChart';
import BenchmarkIndexChart from '../results/BenchmarkIndexChart';

const CHART_WIDTH = 800;
const CHART_HEIGHT = 400;

const ORIGINAL_RO = global.ResizeObserver;
const ORIGINAL_RECT = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  'getBoundingClientRect'
);
const ORIGINAL_INNER_WIDTH = window.innerWidth;
const nativeRect = HTMLElement.prototype.getBoundingClientRect;

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
  }) as DOMRect;

class SizedResizeObserver {
  constructor(private callback: ResizeObserverCallback) {}

  observe(target: Element) {
    this.callback(
      [{ target, contentRect: sizedRect() } as unknown as ResizeObserverEntry],
      this as unknown as ResizeObserver
    );
  }

  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = SizedResizeObserver as unknown as typeof ResizeObserver;
  Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
    configurable: true,
    value(this: HTMLElement) {
      if (this.classList?.contains('recharts-responsive-container')) {
        return sizedRect();
      }
      return nativeRect.call(this);
    },
  });
});

afterAll(() => {
  global.ResizeObserver = ORIGINAL_RO;
  if (ORIGINAL_RECT) {
    Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', ORIGINAL_RECT);
  }
  setInnerWidth(ORIGINAL_INNER_WIDTH);
});

afterEach(() => {
  cleanup();
});

function setInnerWidth(width: number) {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
}

function firstTickLine(container: HTMLElement) {
  return container.querySelector('.recharts-cartesian-axis-tick-line');
}

function tickCount(container: HTMLElement) {
  return container.querySelectorAll('.recharts-cartesian-axis-tick').length;
}

const stocksData = [
  {
    symbol: 'AAPL',
    data: Array.from({ length: 40 }, (_, i) => ({
      date: `2023-01-${String((i % 28) + 1).padStart(2, '0')}`,
      price: 100 + i,
    })),
  },
];

const sp500Data = Array.from({ length: 40 }, (_, i) => ({
  date: `2023-01-${String((i % 28) + 1).padStart(2, '0')}`,
  close: 4000 + i,
}));
const nasdaqData = Array.from({ length: 40 }, (_, i) => ({
  date: `2023-01-${String((i % 28) + 1).padStart(2, '0')}`,
  close: 13000 + i,
}));
const portfolioEquityData = Array.from({ length: 40 }, (_, i) => ({
  date: `2023-01-${String((i % 28) + 1).padStart(2, '0')}`,
  return_pct: i * 0.1,
  drawdown_pct: -i * 0.05,
}));

describe('차트 리사이즈 반응성 (P2-33)', () => {
  describe('StockPriceChart', () => {
    it('마운트 시점의 뷰포트 폭에 따라 X축 각도/틱 개수가 다르게 렌더링된다', () => {
      setInnerWidth(500);
      const { container: narrow } = render(<StockPriceChart stocksData={stocksData} />);
      expect(firstTickLine(narrow)?.getAttribute('angle')).toBe('-45');
      expect(firstTickLine(narrow)?.getAttribute('text-anchor')).toBe('end');

      setInnerWidth(1200);
      const { container: wide } = render(<StockPriceChart stocksData={stocksData} />);
      expect(firstTickLine(wide)?.getAttribute('angle')).toBe('0');
      expect(firstTickLine(wide)?.getAttribute('text-anchor')).toBe('middle');

      // 좁은 화면은 interval이 커져(라벨 스킵 증가) 넓은 화면보다 틱이 적다
      expect(tickCount(narrow)).toBeLessThan(tickCount(wide));
    });

    it('마운트 이후 창 크기가 바뀌면 다시 렌더링되어 각도/틱 개수가 갱신된다', () => {
      setInnerWidth(1200);
      const { container } = render(<StockPriceChart stocksData={stocksData} />);

      const wideAngle = firstTickLine(container)?.getAttribute('angle');
      const wideTickCount = tickCount(container);
      expect(wideAngle).toBe('0');

      act(() => {
        setInnerWidth(400);
        window.dispatchEvent(new Event('resize'));
      });

      const narrowAngle = firstTickLine(container)?.getAttribute('angle');
      const narrowTickCount = tickCount(container);

      expect(narrowAngle).toBe('-45');
      expect(narrowAngle).not.toBe(wideAngle);
      expect(narrowTickCount).toBeLessThan(wideTickCount);
    });
  });

  describe('BenchmarkIndexChart', () => {
    it('마운트 시점의 뷰포트 폭에 따라 X축 각도/틱 개수가 다르게 렌더링된다', () => {
      setInnerWidth(500);
      const { container: narrow } = render(
        <BenchmarkIndexChart
          sp500Data={sp500Data}
          nasdaqData={nasdaqData}
          portfolioEquityData={portfolioEquityData}
        />
      );
      expect(firstTickLine(narrow)?.getAttribute('angle')).toBe('-45');

      setInnerWidth(1200);
      const { container: wide } = render(
        <BenchmarkIndexChart
          sp500Data={sp500Data}
          nasdaqData={nasdaqData}
          portfolioEquityData={portfolioEquityData}
        />
      );
      expect(firstTickLine(wide)?.getAttribute('angle')).toBe('0');

      expect(tickCount(narrow)).toBeLessThan(tickCount(wide));
    });

    it('마운트 이후 창 크기가 바뀌면 다시 렌더링되어 각도/틱 개수가 갱신된다', () => {
      setInnerWidth(1200);
      const { container } = render(
        <BenchmarkIndexChart
          sp500Data={sp500Data}
          nasdaqData={nasdaqData}
          portfolioEquityData={portfolioEquityData}
        />
      );

      const wideAngle = firstTickLine(container)?.getAttribute('angle');
      const wideTickCount = tickCount(container);
      expect(wideAngle).toBe('0');

      act(() => {
        setInnerWidth(400);
        window.dispatchEvent(new Event('resize'));
      });

      const narrowAngle = firstTickLine(container)?.getAttribute('angle');
      const narrowTickCount = tickCount(container);

      expect(narrowAngle).toBe('-45');
      expect(narrowAngle).not.toBe(wideAngle);
      expect(narrowTickCount).toBeLessThan(wideTickCount);
    });
  });
});
