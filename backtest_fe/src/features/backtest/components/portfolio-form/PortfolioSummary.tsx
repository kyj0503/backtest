import React from 'react';
import { Card, CardContent } from '@/shared/ui/card';
import { Label } from '@/shared/ui/label';
import { Input } from '@/shared/ui/input';
import { Badge } from '@/shared/ui/badge';
import { FinancialTermTooltip } from '@/shared/components';
import { Stock, PortfolioInputMode } from '../../model/types/backtest-form-types';
import { getDcaAdjustedTotal } from '../../utils/portfolioCalculations';

interface PortfolioSummaryProps {
  portfolio: Stock[];
  portfolioInputMode: PortfolioInputMode;
  totalInvestment: number;
  setTotalInvestment: (amount: number) => void;
  startDate?: string;
  endDate?: string;
}

export const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({
  portfolio,
  portfolioInputMode,
  totalInvestment,
  setTotalInvestment,
  startDate,
  endDate,
}) => {
  const dcaAdjustedTotal = getDcaAdjustedTotal(portfolio, startDate, endDate);

  if (portfolioInputMode === 'weight') {
    const totalWeight = portfolio.reduce((sum, stock) => {
      return sum + (typeof stock.weight === 'number' ? stock.weight : 0);
    }, 0);
    const isValid = Math.abs(totalWeight - 100) < 0.01;
    const displayWeight = totalWeight.toFixed(1);

    return (
      <Card className="bg-muted/30">
        <CardContent className="p-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-semibold text-muted-foreground whitespace-nowrap">
                <FinancialTermTooltip term="투자 금액">
                  전체 투자금액($)
                </FinancialTermTooltip>
              </Label>
              <Input
                type="number"
                min={1}
                step={0.01}
                value={totalInvestment}
                onChange={e => setTotalInvestment(Number(e.target.value))}
                className="h-8 w-24 rounded-full border-0 bg-background text-right text-sm shadow-none focus-visible:ring-1"
              />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">총 비중</span>
              <Badge variant={isValid ? "secondary" : "destructive"} className="font-bold">
                {displayWeight}%
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-muted/30">
      <CardContent className="p-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">합계</span>
            <span className="text-lg font-bold">${dcaAdjustedTotal.toLocaleString()}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">총 비중</span>
            <Badge variant="secondary" className="font-bold">100.0%</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
