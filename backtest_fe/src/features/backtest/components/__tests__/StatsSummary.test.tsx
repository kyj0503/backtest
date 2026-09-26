/**
 * StatsSummary 통계 정의 표시 테스트 (A-09, A-19)
 *
 * - Profit_Factor는 손실일이 없으면 null로 온다. 과거에는 숫자 폴백(1)으로
 *   바꿔 "1.00"을 보여 줬는데, 계산값처럼 보이는 지어낸 숫자다.
 * - Win_Rate는 두 경로 모두 일 기준(상승일 비율)이다. 거래 기준 승률은
 *   전략 경로에서만 Trade_Win_Rate로 따로 온다.
 * - Annual_Return은 시간가중(TWR) 기준임을 라벨로 밝힌다.
 */
import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import StatsSummary from '../StatsSummary';
import { TooltipProvider } from '@/shared/ui/tooltip';

const baseStats = {
  Total_Return: 12.5,
  Annual_Return: 8.25,
  Annual_Volatility: 14.2,
  Sharpe_Ratio: 0.58,
  Max_Drawdown: -9.1,
  Total_Trading_Days: 250,
  Total_Trades: 3,
  Win_Rate: 54.4,
  Profit_Factor: 1.37,
};

const renderStats = (stats: Record<string, unknown>) =>
  render(
    <TooltipProvider>
      <StatsSummary stats={stats} />
    </TooltipProvider>,
  );

/** 라벨 텍스트로 카드를 찾아 그 안의 값을 돌려준다. */
const cardFor = (label: string): HTMLElement => {
  const heading = screen.getByText(label);
  const card = heading.closest('[class*="space-y-3"]');
  if (!(card instanceof HTMLElement)) throw new Error(`card not found: ${label}`);
  return card;
};

describe('StatsSummary', () => {
  it('shows a dash instead of a made-up number when Profit_Factor is null', () => {
    renderStats({ ...baseStats, Profit_Factor: null });

    const card = cardFor('프로핏 팩터');
    expect(within(card).getByText('—')).toBeInTheDocument();
    expect(within(card).queryByText('1.00')).not.toBeInTheDocument();
  });

  it('shows the profit factor when it is a number', () => {
    renderStats(baseStats);

    expect(within(cardFor('프로핏 팩터')).getByText('1.37')).toBeInTheDocument();
  });

  it('labels the annual return as time-weighted', () => {
    renderStats(baseStats);

    const card = cardFor('연환산 수익률 (시간가중)');
    expect(within(card).getByText('8.25%')).toBeInTheDocument();
  });

  it('labels the portfolio Win_Rate as a daily (up-day) ratio', () => {
    renderStats(baseStats);

    expect(within(cardFor('승률 (일 기준)')).getByText('54.40%')).toBeInTheDocument();
    expect(screen.queryByText('거래 승률')).not.toBeInTheDocument();
  });

  it('shows the trade-based win rate separately when the strategy path provides it', () => {
    renderStats({ ...baseStats, Trade_Win_Rate: 66.67 });

    expect(within(cardFor('승률 (일 기준)')).getByText('54.40%')).toBeInTheDocument();
    expect(within(cardFor('거래 승률')).getByText('66.67%')).toBeInTheDocument();
  });

  it('shows a dash when the strategy path had no trades (Trade_Win_Rate null)', () => {
    renderStats({ ...baseStats, Trade_Win_Rate: null });

    expect(within(cardFor('거래 승률')).getByText('—')).toBeInTheDocument();
  });
});
