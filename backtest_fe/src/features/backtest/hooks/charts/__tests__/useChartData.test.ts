/**
 * useChartData 훅 통합 테스트 (P2-35).
 *
 * 백엔드 응답(equity_curve, daily_returns, weight_history 등)을 차트가
 * 실제로 그리는 데이터로 바꾸는 최종 조립 지점이지만 지금까지 커버리지가
 * 0%였다. chartDataTransform/dataSampling의 개별 함수 테스트와 달리, 이
 * 파일은 그 함수들이 실제로 "함께" 배선됐을 때의 동작 -- 특히 주간/월간
 * 집계 시 수익률 버킷 날짜에 맞춰 equity 값을 재구성하는 로직 -- 을
 * 검증한다. 이 재구성 로직이 잘못되면 "엉뚱한 날짜에 오래된 값이 새어
 * 들어가는" 바로 그 버그 클래스가 발생한다.
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useChartData } from '../useChartData';
import type {
  PortfolioData, PortfolioStatistics, ChartData,
} from '../../../model/types/backtest-result-types';

function sequentialDates(start: string, n: number): string[] {
  const [y, m, d] = start.split('-').map(Number) as [number, number, number];
  const base = new Date(y, m - 1, d);
  return Array.from({ length: n }, (_, i) => {
    const dt = new Date(base.getFullYear(), base.getMonth(), base.getDate() + i);
    return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
  });
}

function makeStats(overrides: Partial<PortfolioStatistics>): PortfolioStatistics {
  return {
    Start: '2024-01-01', End: '2024-01-05', Duration: '4 days',
    Initial_Value: 1000, Final_Value: 1000, Peak_Value: 1000,
    Total_Return: 0, Annual_Return: 0, Annual_Volatility: 0, Sharpe_Ratio: 0,
    Max_Drawdown: 0, Avg_Drawdown: 0, Max_Consecutive_Gains: 0, Max_Consecutive_Losses: 0,
    Total_Trading_Days: 5, Positive_Days: 0, Negative_Days: 0, Win_Rate: 0, Profit_Factor: 1,
    ...overrides,
  };
}

function makePortfolioData(overrides: Partial<PortfolioData>): PortfolioData {
  return {
    portfolio_statistics: makeStats({}),
    individual_returns: {},
    portfolio_composition: [],
    equity_curve: {},
    daily_returns: {},
    ...overrides,
  };
}

describe('useChartData: portfolio vs single-ticker discrimination', () => {
  it('recognizes a portfolio response via portfolio_composition', () => {
    const data = makePortfolioData({
      equity_curve: { '2024-01-01': 1000 },
      daily_returns: { '2024-01-01': 0 },
    });

    const { result } = renderHook(() => useChartData(data, true));

    expect(result.current.isPortfolio).toBe(true);
    expect(result.current.portfolioData).not.toBeNull();
    expect(result.current.chartData).toBeNull();
  });

  it('recognizes a single-ticker response', () => {
    const data: ChartData = {
      ticker: 'AAPL', start_date: '2024-01-01', end_date: '2024-01-05',
      equity_data: [{ date: '2024-01-01', value: 1000, return_pct: 0, drawdown_pct: 0 }],
    };

    const { result } = renderHook(() => useChartData(data, false));

    expect(result.current.isPortfolio).toBe(false);
    expect(result.current.chartData).not.toBeNull();
    expect(result.current.portfolioData).toBeNull();
  });
});

describe('useChartData: portfolioEquityData (daily aggregation, short range)', () => {
  it('zips equity_curve and daily_returns unchanged when the range is short (<=2yr)', () => {
    const data = makePortfolioData({
      portfolio_statistics: makeStats({ Start: '2024-01-01', End: '2024-01-05' }),
      equity_curve: { '2024-01-01': 1000, '2024-01-02': 1010, '2024-01-03': 1005 },
      daily_returns: { '2024-01-01': 0, '2024-01-02': 1.0, '2024-01-03': -0.4950495 },
    });

    const { result } = renderHook(() => useChartData(data, true));

    expect(result.current.aggregationType).toBe('daily');
    expect(result.current.samplingWarning).toBeUndefined();
    expect(result.current.portfolioEquityData).toEqual([
      { date: '2024-01-01', value: 1000, return_pct: 0, drawdown_pct: 0 },
      { date: '2024-01-02', value: 1010, return_pct: 1.0, drawdown_pct: 0 },
      { date: '2024-01-03', value: 1005, return_pct: -0.4950495, drawdown_pct: 0 },
    ]);
  });
});

describe('useChartData: portfolioEquityData (weekly aggregation, multi-year range)', () => {
  /**
   * 3년 구간(yearDuration > 2) -> aggregationType='weekly'. equity_curve에는
   * 의도적으로 1/7을 빼놓아서(9개 날짜만 존재), 주간 집계의 첫 버킷 태그
   * 날짜(1/7, 인덱스 기반 7번째 항목)가 equity_curve에서 직접 조회되지
   * 않고 findDataPointOnOrBefore 폴백을 타도록 만든다. 이 폴백이
   * 정확히 "그 이전 마지막 관측일"(1/6)의 값을 가져오는지, 그리고 다른
   * 날짜(예: 1/8)의 값이 잘못 새어 들어가지 않는지가 이 테스트의 핵심이다.
   */
  const dates = sequentialDates('2024-01-01', 10); // 1/1 ~ 1/10
  const equityValues = [
    1000.0, 1010.0, 1020.1, 1030.3010000000002, 1040.60401,
    1051.0100501000002, 1061.520150601, 1072.13535210701,
    1082.8567056280801, 1093.6852726843608,
  ];

  function buildData() {
    const daily_returns: Record<string, number> = {};
    dates.forEach((d) => { daily_returns[d] = 1.0; }); // 매일 +1%

    const equity_curve: Record<string, number> = {};
    dates.forEach((d, i) => {
      if (d === dates[6]) return; // 1/7만 의도적으로 빠짐
      equity_curve[d] = equityValues[i]!;
    });

    return makePortfolioData({
      portfolio_statistics: makeStats({ Start: '2020-01-01', End: '2023-01-01' }), // 3년
      equity_curve, daily_returns,
    });
  }

  it('selects the weekly bucket for a 3-year span', () => {
    const { result } = renderHook(() => useChartData(buildData(), true));
    expect(result.current.aggregationType).toBe('weekly');
  });

  it('reconstructs the missing bucket date using the last-observed-on-or-before value (not a different date\'s value)', () => {
    const { result } = renderHook(() => useChartData(buildData(), true));
    const points = result.current.portfolioEquityData;

    expect(points).toHaveLength(2); // 7일 버킷 + 3일 버킷

    const firstBucket = points[0]!;
    expect(firstBucket.date).toBe(dates[6]); // '2024-01-07'
    // 1/7은 equity_curve에 없으므로 그 직전 관측일(1/6)의 값을 가져와야 한다
    // -- 이후 날짜(1/8)의 값이 잘못 앞당겨져 쓰이면 안 된다.
    expect(firstBucket.value).toBeCloseTo(equityValues[5]!, 6); // 1/6 값
    expect(firstBucket.value).not.toBeCloseTo(equityValues[7]!, 0); // 1/8 값과는 달라야 함
    expect(firstBucket.return_pct).toBeCloseTo(7.213535210701005, 9); // (1.01^7 - 1)*100

    const secondBucket = points[1]!;
    expect(secondBucket.date).toBe(dates[9]); // '2024-01-10' (equity_curve에 직접 존재)
    expect(secondBucket.value).toBeCloseTo(equityValues[9]!, 6);
    expect(secondBucket.return_pct).toBeCloseTo(3.0301000000000133, 9); // (1.01^3 - 1)*100
  });
});

describe('useChartData: single-ticker equity data', () => {
  it('maps equity_data through the alternate return/drawdown field fallback', () => {
    const data: ChartData = {
      ticker: 'AAPL', start_date: '2024-01-01', end_date: '2024-01-03',
      equity_data: [
        // return_pct/drawdown_pct 대신 대체 필드(return/drawdown)만 있는 경우
        { date: '2024-01-01', value: 100, return: 0, drawdown: 0 } as never,
        { date: '2024-01-02', value: 105, return: 5, drawdown: -1 } as never,
      ],
    };

    const { result } = renderHook(() => useChartData(data, false));

    expect(result.current.singleEquityData).toEqual([
      { date: '2024-01-01', value: 100, return_pct: 0, drawdown_pct: 0 },
      { date: '2024-01-02', value: 105, return_pct: 5, drawdown_pct: -1 },
    ]);
  });
});

describe('useChartData: stocksData and weightHistory sampling wiring', () => {
  it('applies smart sampling to stock_data using the same start/end as the portfolio', () => {
    const data = makePortfolioData({
      portfolio_statistics: makeStats({ Start: '2024-01-01', End: '2024-01-02' }),
      equity_curve: { '2024-01-01': 1000, '2024-01-02': 1000 },
      daily_returns: { '2024-01-01': 0, '2024-01-02': 0 },
      stock_data: {
        AAPL: [
          { date: '2024-01-01', price: 100, volume: 1000 },
          { date: '2024-01-02', price: 101, volume: 1100 },
        ],
      },
    });

    const { result } = renderHook(() => useChartData(data, true));

    expect(result.current.stocksData).toEqual([
      {
        symbol: 'AAPL',
        data: [
          { date: '2024-01-01', price: 100, volume: 1000 },
          { date: '2024-01-02', price: 101, volume: 1100 },
        ],
      },
    ]);
  });

  it('passes weight_history through smart sampling unchanged for a short range', () => {
    const weight_history = [
      { date: '2024-01-01', AAA: 0.6, CASH: 0.4 },
      { date: '2024-01-02', AAA: 0.6, CASH: 0.4 },
    ];
    const data = makePortfolioData({
      portfolio_statistics: makeStats({ Start: '2024-01-01', End: '2024-01-02' }),
      equity_curve: { '2024-01-01': 1000, '2024-01-02': 1000 },
      daily_returns: { '2024-01-01': 0, '2024-01-02': 0 },
      weight_history,
    });

    const { result } = renderHook(() => useChartData(data, true));

    expect(result.current.weightHistory).toEqual(weight_history);
  });
});

describe('useChartData: volatility/news presence flags', () => {
  it('reports hasVolatilityEvents/hasNews as false when all entries are empty', () => {
    const data = makePortfolioData({
      volatility_events: { AAPL: [] },
      latest_news: { AAPL: [] },
    });

    const { result } = renderHook(() => useChartData(data, true));

    expect(result.current.hasVolatilityEvents).toBe(false);
    expect(result.current.hasNews).toBe(false);
  });

  it('reports hasVolatilityEvents/hasNews as true when at least one symbol has entries', () => {
    const data = makePortfolioData({
      volatility_events: {
        AAPL: [{ date: '2024-01-01', daily_return: 12, close_price: 100, volume: 1000, event_type: '급등' }],
      },
      latest_news: {
        AAPL: [{ title: 't', link: 'l', description: 'd', pubDate: '2024-01-01' }],
      },
    });

    const { result } = renderHook(() => useChartData(data, true));

    expect(result.current.hasVolatilityEvents).toBe(true);
    expect(result.current.hasNews).toBe(true);
  });
});

describe('useChartData: statsPayload extraction', () => {
  it('extracts a copy of portfolio_statistics for portfolio results', () => {
    const stats = makeStats({ Total_Return: 12.3 });
    const data = makePortfolioData({ portfolio_statistics: stats });

    const { result } = renderHook(() => useChartData(data, true));

    expect(result.current.statsPayload).toEqual(stats);
  });

  it('extracts summary_stats for single-ticker results', () => {
    const data: ChartData = {
      ticker: 'AAPL', summary_stats: { Sharpe_Ratio: 1.5 },
    };

    const { result } = renderHook(() => useChartData(data, false));

    expect(result.current.statsPayload).toEqual({ Sharpe_Ratio: 1.5 });
  });
});

/**
 * 특성화 테스트 (A-16).
 *
 * useChartData.ts를 차트별 변환 모듈로 나누기 전에, 기존 테스트가 닿지
 * 않던 경로(단일 종목·벤치마크의 주간 집계 재구성, OHLC/환율 샘플링,
 * equity가 없는 버킷의 폴백, 날짜 범위가 없는 응답, 단일 종목의 stock_data,
 * 월간 집계와 10년 초과 경고, memo 참조 안정성)의 현재 동작을 고정한다.
 */
describe('characterization: single-ticker weekly aggregation', () => {
  const dates = sequentialDates('2024-01-01', 10); // 1/1 ~ 1/10

  function buildSingle(): ChartData {
    return {
      ticker: 'AAPL', start_date: '2020-01-01', end_date: '2023-01-01', // 3년 -> weekly
      equity_data: dates.map((date, i) => ({ date, value: 100 + i, return_pct: 1, drawdown_pct: -i })),
      ohlc_data: dates.map((date, i) => ({ date, open: i, high: i, low: i, close: i, volume: i })),
      exchange_rates: dates.map((date, i) => ({ date, rate: 1300 + i })),
      // S&P 500은 1/7을 빼서, 인덱스 기반 주간 버킷의 태그 날짜가 1/8로 밀리게 한다.
      sp500_benchmark: dates.filter((d) => d !== '2024-01-07')
        .map((date, i) => ({ date, close: 4000 + i, return_pct: 1 })) as ChartData['sp500_benchmark'],
      nasdaq_benchmark: dates
        .map((date, i) => ({ date, close: 15000 + i, return_pct: 2 })) as ChartData['nasdaq_benchmark'],
      trade_markers: [
        { date: '2024-01-02', price: 101, type: 'entry' },
        { date: '2024-01-05', price: 104, type: 'sell' as never },
      ],
    };
  }

  it('re-tags single-ticker equity to each compounded return bucket, keeping that day\'s value/drawdown', () => {
    const { result } = renderHook(() => useChartData(buildSingle(), false));

    expect(result.current.aggregationType).toBe('weekly');
    expect(result.current.samplingWarning).toBeUndefined();
    const points = result.current.singleEquityData;
    expect(points.map((p) => [p.date, p.value, p.drawdown_pct])).toEqual([
      ['2024-01-07', 106, -6],
      ['2024-01-10', 109, -9],
    ]);
    expect(points[0]!.return_pct).toBeCloseTo(7.213535210700983, 9); // 1.01^7 - 1
    expect(points[1]!.return_pct).toBeCloseTo(3.030099999999991, 9); // 1.01^3 - 1
  });

  it('samples OHLC and exchange rates by index (price sampling, not compounding)', () => {
    const { result } = renderHook(() => useChartData(buildSingle(), false));

    expect(result.current.singleOhlcData.map((p) => p.date)).toEqual(['2024-01-01', '2024-01-08', '2024-01-10']);
    expect(result.current.exchangeRates).toEqual([
      { date: '2024-01-01', rate: 1300 },
      { date: '2024-01-08', rate: 1307 },
      { date: '2024-01-10', rate: 1309 },
    ]);
  });

  it('compounds benchmark returns per bucket and keeps the bucket day\'s close', () => {
    const { result } = renderHook(() => useChartData(buildSingle(), false));
    const sp = result.current.sp500Benchmark;
    const nq = result.current.nasdaqBenchmark;

    expect(sp.map((p) => [p.date, p.close])).toEqual([['2024-01-08', 4006], ['2024-01-10', 4008]]);
    expect(sp[0]!.return_pct).toBeCloseTo(7.213535210700983, 9);
    expect(sp[1]!.return_pct).toBeCloseTo(2.0100000000000007, 9);
    expect(nq.map((p) => [p.date, p.close])).toEqual([['2024-01-07', 15006], ['2024-01-10', 15009]]);
    expect(nq[0]!.return_pct).toBeCloseTo(14.868566764928005, 9); // 1.02^7 - 1
    expect(nq[1]!.return_pct).toBeCloseTo(6.120799999999993, 9); // 1.02^3 - 1
    // *WithReturn은 같은 배열의 별칭이다.
    expect(result.current.sp500BenchmarkWithReturn).toBe(sp);
    expect(result.current.nasdaqBenchmarkWithReturn).toBe(nq);
  });

  it('normalizes trade marker types to entry/exit', () => {
    const { result } = renderHook(() => useChartData(buildSingle(), false));

    expect(result.current.singleTrades.map((t) => t.type)).toEqual(['entry', 'exit']);
  });

  it('returns identical references on rerender with the same input (memoized)', () => {
    const data = buildSingle();
    const { result, rerender } = renderHook(() => useChartData(data, false));
    const first = result.current;

    rerender();

    expect(result.current.singleEquityData).toBe(first.singleEquityData);
    expect(result.current.singleOhlcData).toBe(first.singleOhlcData);
    expect(result.current.sp500Benchmark).toBe(first.sp500Benchmark);
    expect(result.current.exchangeRates).toBe(first.exchangeRates);
    expect(result.current.stocksData).toBe(first.stocksData);
  });
});

describe('characterization: portfolio equity fallback and monthly aggregation', () => {
  it('emits a value-less point and warns when no equity exists on or before a return bucket', () => {
    const dates = sequentialDates('2024-01-01', 10);
    const data = makePortfolioData({
      portfolio_statistics: makeStats({ Start: '2020-01-01', End: '2023-01-01' }), // weekly
      // equity는 1/9부터만 있다 -> 첫 버킷(1/7)에는 on-or-before 값도 없다.
      equity_curve: Object.fromEntries(dates.slice(8).map((d) => [d, 1000])),
      daily_returns: Object.fromEntries(dates.map((d) => [d, 1])),
    });
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    try {
      const { result } = renderHook(() => useChartData(data, true));
      const points = result.current.portfolioEquityData;

      expect(points).toHaveLength(2);
      expect(points[0]).toEqual({
        date: '2024-01-07', value: undefined, return_pct: expect.closeTo(7.213535210700983, 9), drawdown_pct: 0,
      });
      expect(points[1]).toEqual({
        date: '2024-01-10', value: 1000, return_pct: expect.closeTo(3.030099999999991, 9), drawdown_pct: 0,
      });
      expect(warnSpy).toHaveBeenCalledTimes(1);
      expect(warnSpy.mock.calls[0]![0]).toContain('[포트폴리오 차트] 2024-01-07');
    } finally {
      warnSpy.mockRestore();
    }
  });

  it('aggregates monthly with the >10y warning and samples every series on the same month boundaries', () => {
    const dates = sequentialDates('2024-01-01', 40); // 1/1 ~ 2/9
    const data = makePortfolioData({
      portfolio_statistics: makeStats({ Start: '2010-01-01', End: '2021-01-01' }), // 11년
      equity_curve: Object.fromEntries(dates.map((d, i) => [d, 1000 + i])),
      daily_returns: Object.fromEntries(dates.map((d) => [d, 0.5])),
      weight_history: dates.map((d) => ({ date: d, A: 1 })),
      stock_data: { A: dates.map((d, i) => ({ date: d, price: i, volume: 0 })) },
      exchange_rates: dates.map((d, i) => ({ date: d, rate: i })),
    });

    const { result } = renderHook(() => useChartData(data, true));
    const r = result.current;

    expect(r.aggregationType).toBe('monthly');
    expect(r.samplingWarning).toBe('10년 초과 백테스트는 월간 데이터로 표시됩니다.');
    // 수익률 버킷은 경계 하루 전(2/4)과 마지막 날(2/9)에 마감된다.
    expect(r.portfolioEquityData.map((p) => [p.date, p.value])).toEqual([['2024-02-04', 1034], ['2024-02-09', 1039]]);
    expect(r.portfolioEquityData[0]!.return_pct).toBeCloseTo(19.072689037155687, 9); // 1.005^35 - 1
    expect(r.portfolioEquityData[1]!.return_pct).toBeCloseTo(2.5251253128124374, 9); // 1.005^5 - 1
    // 가격류 시계열은 경계 당일(2/5)을 샘플링한다.
    const priceDates = ['2024-01-01', '2024-02-05', '2024-02-09'];
    expect(r.weightHistory.map((w) => w.date)).toEqual(priceDates);
    expect(r.stocksData[0]!.data.map((p) => p.date)).toEqual(priceDates);
    expect(r.exchangeRates.map((p) => p.date)).toEqual(priceDates);
  });
});

describe('characterization: responses without a date range or with single-ticker stock_data', () => {
  it('returns transformed single-ticker series unsampled when start/end dates are absent', () => {
    const data: ChartData = {
      ticker: 'X',
      equity_data: [{ date: '2024-01-01', value: 1, return_pct: 1, drawdown_pct: 0 }],
      ohlc_data: [{ date: '2024-01-01', open: 1, high: 1, low: 1, close: 1, volume: undefined as never }],
    };

    const { result } = renderHook(() => useChartData(data, false));

    expect(result.current.aggregationType).toBe('daily');
    expect(result.current.singleEquityData).toEqual([{ date: '2024-01-01', value: 1, return_pct: 1, drawdown_pct: 0 }]);
    expect(result.current.singleOhlcData).toEqual([
      { date: '2024-01-01', open: 1, high: 1, low: 1, close: 1, volume: 0 },
    ]);
  });

  it('picks only the ticker\'s own series from stock_data on a single-ticker response', () => {
    const data = {
      ticker: 'AAPL', start_date: '2024-01-01', end_date: '2024-01-02',
      stock_data: { AAPL: [{ date: '2024-01-01', price: 1, volume: 1 }], MSFT: [] },
    } as ChartData;

    const { result } = renderHook(() => useChartData(data, false));

    expect(result.current.stocksData).toEqual([
      { symbol: 'AAPL', data: [{ date: '2024-01-01', price: 1, volume: 1 }] },
    ]);
    expect(result.current.tradeLogs).toEqual({});
    expect(result.current.rebalanceHistory).toEqual([]);
  });
});
