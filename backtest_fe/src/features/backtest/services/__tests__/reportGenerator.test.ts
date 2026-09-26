/**
 * 리포트(텍스트/CSV)의 통계 정의 표시 테스트 (A-09, A-19)
 *
 * Profit_Factor는 손실일이 없으면 null로 온다 — `.toFixed`를 바로 부르면
 * 리포트 다운로드가 TypeError로 죽는다. 연환산 수익률은 시간가중 기준, Win_Rate는
 * 일 기준이라는 것을 라벨로 밝힌다.
 */
import { describe, it, expect } from 'vitest';
import { generateCSVReport, generateTextReport } from '../reportGenerator';
import type { BacktestResultData, PortfolioStatistics } from '../../model/types/backtest-result-types';

const makeStats = (overrides: Partial<PortfolioStatistics> = {}): PortfolioStatistics => ({
  Start: '2024-01-01',
  End: '2024-12-31',
  Duration: '365 days',
  Initial_Value: 1000,
  Final_Value: 1100,
  Peak_Value: 1150,
  Total_Return: 10,
  Annual_Return: 12.34,
  Annual_Volatility: 15,
  Sharpe_Ratio: 0.8,
  Max_Drawdown: -5,
  Avg_Drawdown: -2,
  Max_Consecutive_Gains: 4,
  Max_Consecutive_Losses: 3,
  Total_Trading_Days: 250,
  Positive_Days: 130,
  Negative_Days: 110,
  Win_Rate: 52,
  Profit_Factor: 1.25,
  ...overrides,
});

const makeData = (stats: PortfolioStatistics): BacktestResultData =>
  ({
    portfolio_statistics: stats,
    individual_returns: {},
    portfolio_composition: [],
    equity_curve: {},
    daily_returns: {},
  }) as unknown as BacktestResultData;

describe('reportGenerator statistics', () => {
  it('does not crash and prints N/A when Profit_Factor is null', () => {
    const data = makeData(makeStats({ Profit_Factor: null }));

    const text = generateTextReport(data, true);
    const csv = generateCSVReport(data, true);

    expect(text).toMatch(/프로핏 팩터\s*: N\/A/);
    expect(csv).toContain('프로핏 팩터,N/A');
  });

  it('labels the annual return as time-weighted and the win rate as daily', () => {
    const data = makeData(makeStats());

    const text = generateTextReport(data, true);
    const csv = generateCSVReport(data, true);

    expect(text).toMatch(/연환산 수익률\(시간가중\)\s*: 12\.34%/);
    expect(csv).toContain('연환산 수익률(시간가중),12.34%');
    expect(text).toMatch(/승률\(일 기준\)\s*: 52\.00%/);
    expect(csv).toContain('승률(일 기준),52.00%');
  });

  it('includes the trade-based win rate only when the strategy path provides it', () => {
    const withTrades = makeData(makeStats({ Trade_Win_Rate: 60 }));
    const withoutTrades = makeData(makeStats());

    expect(generateTextReport(withTrades, true)).toMatch(/거래 승률\s*: 60\.00%/);
    expect(generateCSVReport(withTrades, true)).toContain('거래 승률,60.00%');
    expect(generateTextReport(withoutTrades, true)).not.toContain('거래 승률');
  });

  it('prints N/A when the strategy path had no trades (Trade_Win_Rate null)', () => {
    const data = makeData(makeStats({ Trade_Win_Rate: null, Profit_Factor: null }));

    expect(generateTextReport(data, true)).toMatch(/거래 승률\s*: N\/A/);
    expect(generateCSVReport(data, true)).toContain('거래 승률,N/A');
  });
});
