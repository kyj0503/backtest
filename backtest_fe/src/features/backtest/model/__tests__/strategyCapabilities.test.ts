import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createElement } from 'react';
import { resolveRebalanceFrequency, supportsDcaAndRebalancing } from '../strategyConfig';
import { validateBacktestForm } from '../../hooks/useFormValidation';
import { initialBacktestFormState, BacktestFormState, Stock } from '../types/backtest-form-types';
import CommissionForm from '../../components/CommissionForm';
import { TooltipProvider } from '@/shared/ui/tooltip';

const TECHNICAL = ['sma_strategy', 'rsi_strategy', 'macd_strategy', 'ema_strategy', 'bollinger_strategy'];

const formWith = (strategy: string, portfolio: Stock[]): BacktestFormState => ({
  ...initialBacktestFormState,
  dates: { startDate: '2023-01-03', endDate: '2024-12-31' },
  strategy: { selectedStrategy: strategy, strategyParams: {} },
  portfolio,
});

const stock = (symbol: string, investmentType: Stock['investmentType']): Stock => ({
  symbol,
  amount: 1000,
  investmentType,
  dcaFrequency: 'monthly_1',
  assetType: 'stock',
});

const DCA_ERROR = '분할 매수(DCA)를 사용할 수 없습니다';

describe('supportsDcaAndRebalancing (A-02)', () => {
  it('buy_hold_strategy와 미선택 상태만 DCA·리밸런싱을 지원한다', () => {
    expect(supportsDcaAndRebalancing('buy_hold_strategy')).toBe(true);
    expect(supportsDcaAndRebalancing(undefined)).toBe(true);
    expect(supportsDcaAndRebalancing('')).toBe(true);
    for (const strategy of TECHNICAL) {
      expect(supportsDcaAndRebalancing(strategy)).toBe(false);
    }
  });
});

describe('resolveRebalanceFrequency', () => {
  it('기술적 전략이면 state에 남은 선택값 대신 none을 돌려준다', () => {
    // 수정 전: 드롭다운은 none으로 보였지만 monthly_3이 그대로 전송됐다
    expect(resolveRebalanceFrequency('monthly_3', 'sma_strategy', 3)).toBe('none');
  });

  it('자산이 2개 미만이면 none', () => {
    expect(resolveRebalanceFrequency('monthly_3', 'buy_hold_strategy', 1)).toBe('none');
  });

  it('buy&hold + 자산 2개 이상이면 선택값을 유지한다', () => {
    expect(resolveRebalanceFrequency('monthly_3', 'buy_hold_strategy', 2)).toBe('monthly_3');
  });
});

describe('validateBacktestForm — 전략 × DCA', () => {
  it('기술적 전략에 DCA 종목이 있으면 오류를 낸다', () => {
    const errors = validateBacktestForm(
      formWith('sma_strategy', [stock('aapl', 'dca'), stock('MSFT', 'lump_sum')])
    );
    const dcaError = errors.find(e => e.includes(DCA_ERROR));
    expect(dcaError).toBeDefined();
    expect(dcaError).toContain('AAPL');
    expect(dcaError).not.toContain('MSFT');
  });

  it('기술적 전략이라도 전부 일시불이면 통과한다', () => {
    const errors = validateBacktestForm(formWith('rsi_strategy', [stock('AAPL', 'lump_sum')]));
    expect(errors.some(e => e.includes(DCA_ERROR))).toBe(false);
  });

  it('buy&hold는 DCA를 그대로 허용한다', () => {
    const errors = validateBacktestForm(formWith('buy_hold_strategy', [stock('AAPL', 'dca')]));
    expect(errors.some(e => e.includes(DCA_ERROR))).toBe(false);
  });
});

describe('CommissionForm 리밸런싱 표시', () => {
  const renderForm = (selectedStrategy: string, stockCount: number) =>
    render(
      // 앱에서는 App.tsx가 TooltipProvider를 제공한다 (FinancialTermTooltip 의존)
      createElement(TooltipProvider, null,
        createElement(CommissionForm, {
          rebalanceFrequency: 'monthly_3',
          setRebalanceFrequency: () => {},
          commission: 0.2,
          setCommission: () => {},
          stockCount,
          selectedStrategy,
        })
      )
    );

  it('기술적 전략이면 안내 문구와 함께 비활성화된다', () => {
    renderForm('sma_strategy', 3);
    expect(screen.getByText(/기술적 전략은 매수\/매도 신호를 따르므로/)).toBeInTheDocument();
  });

  it('buy&hold + 자산 2개 이상이면 리밸런싱 안내가 정상 표시된다', () => {
    renderForm('buy_hold_strategy', 2);
    expect(screen.getByText('포트폴리오 비중을 다시 맞추는 주기')).toBeInTheDocument();
  });
});
