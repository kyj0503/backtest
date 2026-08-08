/**
 * chartDataTransform 순수 함수 단위 테스트 (P2-35).
 *
 * 이 파일의 함수들은 백엔드 응답을 차트 컴포넌트가 소비하는 형태로 바꾸는
 * 변환 계층이다 -- 지금까지 어떤 테스트도 이 파일을 임포트하지 않았다.
 * 특히 nullish coalescing(??) 기반 폴백 체인이 실수로 `||`로 바뀌면
 * "0%"(정상값)가 "누락값"으로 잘못 취급되는 회귀가 생길 수 있어, 그 부분을
 * 명시적으로 겨냥한 테스트를 포함한다.
 */
import { describe, it, expect } from 'vitest';
import {
  formatCurrencyCompact,
  formatKRW,
  transformPortfolioEquityData,
  transformSingleEquityData,
  transformTradeMarkers,
  transformOhlcData,
  withBenchmarkReturn,
  transformStockData,
  extractTradeLogs,
  extractBenchmarkData,
  extractStatsPayload,
} from '../chartDataTransform';
import type { ChartData, PortfolioData, EquityPoint } from '../../model/types/backtest-result-types';

describe('formatCurrencyCompact', () => {
  it('formats sub-1000 values via toLocaleString with no suffix', () => {
    expect(formatCurrencyCompact(0)).toBe('0');
    expect(formatCurrencyCompact(999)).toBe('999');
  });

  it('formats thousands with a K suffix', () => {
    expect(formatCurrencyCompact(1000)).toBe('1.0K');
    expect(formatCurrencyCompact(1500)).toBe('1.5K');
  });

  it('rounds up to "1000.0K" just under the 1e6 boundary rather than switching to M', () => {
    // 999999 / 1000 = 999.999 -> toFixed(1)이 "1000.0"으로 반올림하지만,
    // 분기 판단 자체는 1e6 미만이므로 여전히 K 접미사가 붙는다 (실제 동작을
    // 있는 그대로 고정 -- "1.0M"이 아니다).
    expect(formatCurrencyCompact(999999)).toBe('1000.0K');
  });

  it('formats millions and billions', () => {
    expect(formatCurrencyCompact(1000000)).toBe('1.0M');
    expect(formatCurrencyCompact(1500000)).toBe('1.5M');
    expect(formatCurrencyCompact(2500000000)).toBe('2.5B');
  });

  it('formats negative sub-1000 values via toLocaleString (no suffix branch matches)', () => {
    expect(formatCurrencyCompact(-500)).toBe('-500');
  });
});

describe('formatKRW', () => {
  it('formats with thousands separators and zero decimals by default', () => {
    expect(formatKRW(1234567)).toBe('₩1,234,567');
  });

  it('respects an explicit decimals argument', () => {
    expect(formatKRW(1234.5, 2)).toBe('₩1,234.50');
  });

  it('formats zero', () => {
    expect(formatKRW(0)).toBe('₩0');
  });
});

describe('transformPortfolioEquityData', () => {
  it('zips equity curve and daily returns by date, with drawdown_pct hardcoded to 0', () => {
    const result = transformPortfolioEquityData(
      { '2024-01-01': 1000, '2024-01-02': 1010 },
      { '2024-01-01': 0, '2024-01-02': 1.0 },
    );

    expect(result).toEqual([
      { date: '2024-01-01', value: 1000, return_pct: 0, drawdown_pct: 0 },
      { date: '2024-01-02', value: 1010, return_pct: 1.0, drawdown_pct: 0 },
    ]);
  });

  it('falls back to 0 when a date is missing from dailyReturns', () => {
    const result = transformPortfolioEquityData(
      { '2024-01-01': 1000 },
      {}, // dailyReturns가 비어있음
    );

    expect(result[0]?.return_pct).toBe(0);
  });
});

describe('transformSingleEquityData', () => {
  it('falls back to alternate field names (return/drawdown) when return_pct/drawdown_pct are absent', () => {
    const input = [
      { date: '2024-01-01', value: 100, return: 5, drawdown: -2 } as unknown as EquityPoint,
    ];

    const result = transformSingleEquityData(input);

    expect(result[0]?.return_pct).toBe(5);
    expect(result[0]?.drawdown_pct).toBe(-2);
  });

  it('preserves an explicit 0 rather than falling back (?? not ||, regression guard)', () => {
    // return_pct/drawdown_pct가 명시적으로 0이면, 값이 다른 대체 필드(.return/.drawdown)가
    // 있어도 그쪽으로 폴백하면 안 된다. `??`가 실수로 `||`로 바뀌면 이 테스트가 깨진다.
    const input = [
      {
        date: '2024-01-01', value: 100,
        return_pct: 0, drawdown_pct: 0,
        return: 99, drawdown: 99,
      } as unknown as EquityPoint,
    ];

    const result = transformSingleEquityData(input);

    expect(result[0]?.return_pct).toBe(0);
    expect(result[0]?.drawdown_pct).toBe(0);
  });
});

describe('transformTradeMarkers', () => {
  it('keeps entry markers as entry', () => {
    const result = transformTradeMarkers([{ date: '2024-01-01', type: 'entry' }]);
    expect(result[0]?.type).toBe('entry');
  });

  it('keeps exit markers as exit', () => {
    const result = transformTradeMarkers([{ date: '2024-01-01', type: 'exit' }]);
    expect(result[0]?.type).toBe('exit');
  });

  it('defaults any non-entry type to exit', () => {
    const result = transformTradeMarkers([
      { date: '2024-01-01', type: 'unexpected' as unknown as 'entry' },
    ]);
    expect(result[0]?.type).toBe('exit');
  });
});

describe('transformOhlcData', () => {
  it('coerces volume through Number(), defaulting missing volume to 0', () => {
    const result = transformOhlcData([
      { date: '2024-01-01', open: 1, high: 2, low: 0.5, close: 1.5, volume: undefined as unknown as number },
      { date: '2024-01-02', open: 1, high: 2, low: 0.5, close: 1.5, volume: '1234' as unknown as number },
    ]);

    expect(result[0]?.volume).toBe(0);
    expect(result[1]?.volume).toBe(1234);
  });
});

describe('withBenchmarkReturn', () => {
  it('returns an empty array for undefined input', () => {
    expect(withBenchmarkReturn(undefined as never)).toEqual([]);
  });

  it('returns an empty array for an empty array', () => {
    expect(withBenchmarkReturn([])).toEqual([]);
  });

  it('sets the first point to 0% and computes day-over-day pct change for the rest', () => {
    const result = withBenchmarkReturn([
      { date: '2024-01-01', close: 100 },
      { date: '2024-01-02', close: 110 }, // +10%
      { date: '2024-01-03', close: 99 },  // -10% from 110
    ]);

    expect(result[0]?.return_pct).toBe(0);
    expect(result[1]?.return_pct).toBeCloseTo(10, 9);
    expect(result[2]?.return_pct).toBeCloseTo(-10, 9);
  });
});

describe('transformStockData', () => {
  it('returns an empty array for falsy input', () => {
    expect(transformStockData(undefined as never)).toEqual([]);
  });

  it('filters to a single symbol when ticker is provided and present', () => {
    const result = transformStockData(
      {
        AAPL: [{ date: '2024-01-01', price: 100, volume: 1 }],
        MSFT: [{ date: '2024-01-01', price: 200, volume: 1 }],
      },
      'AAPL',
    );

    expect(result).toEqual([
      { symbol: 'AAPL', data: [{ date: '2024-01-01', price: 100, volume: 1 }] },
    ]);
  });

  it('falls back to all symbols when the given ticker is not present in stockData', () => {
    const result = transformStockData(
      { AAPL: [{ date: '2024-01-01', price: 100, volume: 1 }] },
      'NONEXISTENT',
    );

    expect(result.map((r) => r.symbol)).toEqual(['AAPL']);
  });

  it('maps every symbol when no ticker is provided', () => {
    const result = transformStockData({
      AAPL: [{ date: '2024-01-01', price: 100, volume: 1 }],
      MSFT: [{ date: '2024-01-01', price: 200, volume: 1 }],
    });

    expect(result.map((r) => r.symbol).sort()).toEqual(['AAPL', 'MSFT']);
  });
});

describe('extractTradeLogs', () => {
  it('returns an empty object for undefined strategyDetails', () => {
    expect(extractTradeLogs(undefined)).toEqual({});
  });

  it('includes only symbols with a real trade_log array', () => {
    const result = extractTradeLogs({
      AAPL: { trade_log: [{ EntryTime: '2024-01-01', EntryPrice: 100, Size: 1 }] },
      MSFT: {}, // trade_log 없음
      GOOG: { trade_log: 'not-an-array' as unknown as never },
    });

    expect(Object.keys(result)).toEqual(['AAPL']);
  });
});

describe('extractBenchmarkData', () => {
  it('extracts sp500_benchmark when present', () => {
    const data = { sp500_benchmark: [{ date: '2024-01-01', close: 100 }] } as unknown as ChartData;
    expect(extractBenchmarkData(data, 'sp500')).toEqual([{ date: '2024-01-01', close: 100 }]);
  });

  it('returns an empty array when the benchmark is absent', () => {
    const data = {} as ChartData;
    expect(extractBenchmarkData(data, 'nasdaq')).toEqual([]);
  });
});

describe('extractStatsPayload', () => {
  it('returns a shallow copy of portfolio_statistics for portfolio results', () => {
    const stats = { Total_Return: 12.3 };
    const data = { portfolio_statistics: stats } as unknown as PortfolioData;

    const result = extractStatsPayload(data, true);

    expect(result).toEqual(stats);
    expect(result).not.toBe(stats); // 스프레드 복사이므로 참조가 달라야 한다
  });

  it('returns summary_stats for non-portfolio (single ticker) results', () => {
    const data = { summary_stats: { Sharpe_Ratio: 1.2 } } as unknown as ChartData;
    expect(extractStatsPayload(data, false)).toEqual({ Sharpe_Ratio: 1.2 });
  });

  it('returns an empty object when summary_stats is absent', () => {
    const data = {} as ChartData;
    expect(extractStatsPayload(data, false)).toEqual({});
  });
});
