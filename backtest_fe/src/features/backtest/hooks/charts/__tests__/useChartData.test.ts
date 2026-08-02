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
import { describe, it, expect } from 'vitest';
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
