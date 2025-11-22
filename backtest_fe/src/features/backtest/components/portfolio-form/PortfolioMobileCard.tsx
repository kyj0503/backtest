import React, { ChangeEvent } from 'react';
import { Card, CardContent } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { FinancialTermTooltip } from '@/shared/components';
import { Stock, PortfolioInputMode } from '../../model/types/backtest-form-types';
import { PREDEFINED_STOCKS, ASSET_TYPES, DCA_FREQUENCY_OPTIONS } from '../../model/strategyConfig';
import { getDcaAdjustedTotal } from '../../utils/portfolioCalculations';
import { calculateDcaPeriods } from '../../utils/calculateDcaPeriods';
import { DcaPreview } from './DcaPreview';
import { Trash2 } from 'lucide-react';

interface PortfolioMobileCardProps {
  stock: Stock;
  index: number;
  portfolio: Stock[];
  portfolioInputMode: PortfolioInputMode;
  updateStock: (index: number, field: keyof Stock, value: string | number) => void;
  removeStock: (index: number) => void;
  startDate?: string;
  endDate?: string;
}

export const PortfolioMobileCard: React.FC<PortfolioMobileCardProps> = ({
  stock,
  index,
  portfolio,
  portfolioInputMode,
  updateStock,
  removeStock,
  startDate,
  endDate,
}) => {
  const dcaAdjustedTotal = getDcaAdjustedTotal(portfolio, startDate, endDate);
  let stockTotalAmount = stock.amount;
  let weightPercent = '0.0';

  if (startDate && endDate) {
    if (stock.investmentType === 'dca') {
      const dcaPeriods = calculateDcaPeriods(startDate, endDate, stock.dcaFrequency || 'monthly_1');
      stockTotalAmount = stock.amount * dcaPeriods;
    }
    weightPercent = dcaAdjustedTotal > 0
      ? ((stockTotalAmount / dcaAdjustedTotal) * 100).toFixed(1)
      : '0.0';
  }

  return (
    <Card key={`stock_mobile_${index}`} className="relative">
      <CardContent className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <Badge variant="outline" className="text-sm font-semibold">
            자산 #{index + 1}
          </Badge>
          <Button
            type="button"
            onClick={() => removeStock(index)}
            disabled={portfolio.length <= 1}
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:bg-destructive/10"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-medium text-muted-foreground">
            <FinancialTermTooltip term="종목">종목/자산</FinancialTermTooltip>
          </Label>
          {stock.assetType === ASSET_TYPES.CASH ? (
            <Input
              type="text"
              value={stock.symbol || ''}
              onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'symbol', e.target.value)}
              placeholder="현금 자산 이름 입력 (예: USD, KRW)"
              maxLength={20}
              className="w-full bg-accent/50"
            />
          ) : (
            <>
              <Select
                value={stock.symbol === '' || !PREDEFINED_STOCKS.slice(1).some(opt => opt.value === stock.symbol) ? 'CUSTOM' : stock.symbol}
                onValueChange={(value) => {
                  if (value === 'CUSTOM') {
                    updateStock(index, 'symbol', '');
                  } else {
                    updateStock(index, 'symbol', value);
                  }
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="종목 선택" />
                </SelectTrigger>
                <SelectContent position="popper" sideOffset={5}>
                  <SelectItem value="CUSTOM">직접 입력</SelectItem>
                  {PREDEFINED_STOCKS.slice(1).map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {(stock.symbol === '' || !PREDEFINED_STOCKS.slice(1).some(opt => opt.value === stock.symbol)) && (
                <Input
                  type="text"
                  value={stock.symbol}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => {
                    const upperValue = e.target.value.toUpperCase();
                    updateStock(index, 'symbol', upperValue);
                  }}
                  placeholder="종목 심볼 입력 (예: AAPL)"
                  maxLength={10}
                  className="w-full mt-2"
                  autoComplete="off"
                />
              )}
            </>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label className="text-xs font-medium text-muted-foreground">
              <FinancialTermTooltip term="투자 금액">투자 금액 ($)</FinancialTermTooltip>
            </Label>
            <Input
              type="number"
              value={stock.amount}
              onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'amount', e.target.value)}
              min="100"
              step="100"
              disabled={portfolioInputMode === 'weight'}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium text-muted-foreground">
              <FinancialTermTooltip term="자산">자산 타입</FinancialTermTooltip>
            </Label>
            <Select
              value={stock.assetType || ASSET_TYPES.STOCK}
              onValueChange={(value) => updateStock(index, 'assetType', value)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ASSET_TYPES.STOCK}>주식</SelectItem>
                <SelectItem value={ASSET_TYPES.CASH}>현금</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-medium text-muted-foreground">
            <FinancialTermTooltip term="투자 방식">투자 방식</FinancialTermTooltip>
          </Label>
          <Select
            value={stock.investmentType}
            onValueChange={(value) => updateStock(index, 'investmentType', value)}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="lump_sum">일시불 투자</SelectItem>
              <SelectItem value="dca">분할 매수 (DCA)</SelectItem>
            </SelectContent>
          </Select>
          {stock.investmentType === 'dca' && (
            <>
              <Select
                value={stock.dcaFrequency || 'monthly_1'}
                onValueChange={(value) => updateStock(index, 'dcaFrequency', value)}
              >
                <SelectTrigger className="w-full mt-2">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DCA_FREQUENCY_OPTIONS.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {stock.dcaFrequency && (
                <DcaPreview stock={stock} startDate={startDate} endDate={endDate} />
              )}
            </>
          )}
        </div>

        <div className="pt-2 border-t border-border/50">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">
              <FinancialTermTooltip term="투자 비중">포트폴리오 비중</FinancialTermTooltip>
            </span>
            {portfolioInputMode === 'weight' ? (
              <Input
                type="number"
                value={typeof stock.weight === 'number' ? stock.weight : ''}
                onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'weight', Number(e.target.value))}
                min="0"
                max="100"
                step="0.1"
                className="w-20 h-8 px-2 text-sm text-right"
              />
            ) : (
              <Badge variant="secondary" className="text-sm font-semibold">
                {startDate && endDate ? `${weightPercent}%` : 'N/A'}
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
