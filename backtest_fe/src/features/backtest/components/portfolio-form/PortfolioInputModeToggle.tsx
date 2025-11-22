import React from 'react';
import { Button } from '@/shared/ui/button';
import { PortfolioInputMode } from '../../model/types/backtest-form-types';

interface PortfolioInputModeToggleProps {
  mode: PortfolioInputMode;
  onModeChange: (mode: PortfolioInputMode) => void;
}

export const PortfolioInputModeToggle: React.FC<PortfolioInputModeToggleProps> = ({ mode, onModeChange }) => {
  return (
    <div className="inline-flex items-center gap-1 rounded-full border border-border/70 bg-background p-1 shadow-sm">
      <Button
        type="button"
        onClick={() => onModeChange('amount')}
        variant={mode === 'amount' ? 'secondary' : 'ghost'}
        className="rounded-full px-4 py-1 text-sm"
      >
        금액 기준
      </Button>
      <Button
        type="button"
        onClick={() => onModeChange('weight')}
        variant={mode === 'weight' ? 'secondary' : 'ghost'}
        className="rounded-full px-4 py-1 text-sm"
      >
        비중 기준
      </Button>
    </div>
  );
};
