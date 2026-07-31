/**
 * 차트 SVG 렌더링 회귀 테스트 (recharts v3)
 *
 * **테스트 범위**:
 * - 커스텀 yAxisId를 쓰는 차트(EquityChart, OHLCChart)에서 가로 그리드가
 *   Y축 눈금에 맞춰 그려지는지 검증한다.
 *
 * **배경 (recharts v2 → v3 breaking change)**:
 * - v3부터 CartesianGrid는 자체 xAxisId/yAxisId(기본값 0)를 가지며,
 *   이 값이 실제 YAxis의 yAxisId와 일치해야 해당 축의 눈금 기준으로
 *   가로 그리드 라인을 그린다.
 * - 불일치 시 그리드는 사라지지 않고 "경계선 2줄"로만 축소되어 그려지므로
 *   타입 에러도 런타임 에러도 없이 조용히 눈금선만 사라진다.
 *   → 그래서 라인 개수를 직접 세는 방식으로 검증한다.
 *
 * **한계**:
 * - ResponsiveContainer는 happy-dom에서 크기가 0이므로 우회하기 위해
 *   차트 내부 구조를 직접 렌더링하지 않고 실제 컴포넌트를 렌더링하되,
 *   컨테이너 크기를 강제로 지정한다.
 * - 색상/여백/툴팁 서식 등 시각적 요소는 검증하지 않는다.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { render } from '@testing-library/react';
import EquityChart from '../EquityChart';
import OHLCChart from '../OHLCChart';

// ResponsiveContainer가 실제 크기를 갖도록 강제한다.
// happy-dom은 레이아웃 엔진이 없어 모든 요소의 크기가 0이며,
// 전역 ResizeObserver 목(src/test/setup.ts)은 콜백을 호출하지 않는다.
// 이 파일에서만 크기를 통지하는 ResizeObserver로 교체한다.
const CHART_WIDTH = 800;
const CHART_HEIGHT = 400;

const ORIGINAL_RO = global.ResizeObserver;
const ORIGINAL_RECT = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  'getBoundingClientRect'
);
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

  // ResponsiveContainer가 읽는 컨테이너 요소에만 크기를 부여한다.
  // 모든 요소에 크기를 주면 Legend 높이가 400px로 잡혀 플롯 영역이
  // 음수 높이가 되고 축/그리드/곡선이 전부 사라진다.
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
});

const equityData = Array.from({ length: 10 }, (_, i) => ({
  date: `2023-01-${String(i + 1).padStart(2, '0')}`,
  return_pct: i * 1.5,
  drawdown_pct: -i * 0.4,
}));

const ohlcData = Array.from({ length: 10 }, (_, i) => ({
  date: `2023-01-${String(i + 1).padStart(2, '0')}`,
  open: 100 + i,
  high: 105 + i,
  low: 95 + i,
  close: 102 + i,
  volume: 1000 + i * 10,
}));

describe('차트 SVG 렌더링 (recharts v3)', () => {
  describe('EquityChart', () => {
    it('SVG와 데이터 곡선을 렌더링한다', () => {
      const { container } = render(<EquityChart data={equityData} />);

      expect(container.querySelector('svg.recharts-surface')).toBeTruthy();
      // 수익률 Line + 드로우다운 Area
      expect(container.querySelectorAll('.recharts-curve').length).toBeGreaterThan(0);
    });

    it('가로 그리드가 Y축 눈금에 맞춰 그려진다 (경계선 2줄이 아님)', () => {
      const { container } = render(<EquityChart data={equityData} />);

      const horizontal = container.querySelectorAll(
        '.recharts-cartesian-grid-horizontal line'
      );
      // yAxisId 불일치 시 2줄(위/아래 경계)로 축소된다.
      expect(horizontal.length).toBeGreaterThan(2);
    });

    it('좌/우 Y축을 모두 렌더링한다', () => {
      const { container } = render(<EquityChart data={equityData} />);

      expect(container.querySelectorAll('.recharts-yAxis').length).toBe(2);
    });
  });

  describe('OHLCChart', () => {
    it('가로 그리드가 price 축 눈금에 맞춰 그려진다', () => {
      const { container } = render(
        <OHLCChart data={ohlcData} indicators={[]} trades={[]} />
      );

      const horizontal = container.querySelectorAll(
        '.recharts-cartesian-grid-horizontal line'
      );
      expect(horizontal.length).toBeGreaterThan(2);
    });

    it('거래량 Bar와 종가 Line을 렌더링한다', () => {
      const { container } = render(
        <OHLCChart data={ohlcData} indicators={[]} trades={[]} />
      );

      expect(container.querySelectorAll('.recharts-bar-rectangle').length).toBeGreaterThan(0);
      expect(container.querySelectorAll('.recharts-line-curve').length).toBeGreaterThan(0);
    });
  });
});
