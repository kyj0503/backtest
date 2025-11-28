import React, { ChangeEvent } from 'react';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table';
import { FinancialTermTooltip } from '@/shared/components';
import { Stock, PortfolioInputMode } from '../../model/types/backtest-form-types';
import { PREDEFINED_STOCKS, ASSET_TYPES, DCA_FREQUENCY_OPTIONS } from '../../model/strategyConfig';
import { getDcaAdjustedTotal } from '../../utils/portfolioCalculations';
import { calculateDcaPeriods } from '../../utils/calculateDcaPeriods';
import { DcaPreview } from './DcaPreview';

interface PortfolioTableProps {
  portfolio: Stock[];
  portfolioInputMode: PortfolioInputMode;
  updateStock: (index: number, field: keyof Stock, value: string | number) => void;
  removeStock: (index: number) => void;
  startDate?: string;
  endDate?: string;
}

export const PortfolioTable: React.FC<PortfolioTableProps> = ({
  portfolio,
  portfolioInputMode,
  updateStock,
  removeStock,
  startDate,
  endDate,
}) => {
  const dcaAdjustedTotal = getDcaAdjustedTotal(portfolio, startDate, endDate);

  const calculateWeight = (stock: Stock): string => {
    if (!startDate || !endDate) {
      return 'N/A';
    }

    let stockTotalAmount = stock.amount;
    if (stock.investmentType === 'dca') {
      const dcaPeriods = calculateDcaPeriods(startDate, endDate, stock.dcaFrequency || 'monthly_1');
      stockTotalAmount = stock.amount * dcaPeriods;
    }

    return dcaAdjustedTotal > 0
      ? ((stockTotalAmount / dcaAdjustedTotal) * 100).toFixed(1)
      : '0.0';
  };

  const calculateTotalWeight = (): { weight: number; isValid: boolean; display: string } => {
    const totalWeight = portfolio.reduce((sum, stock) => {
      return sum + (typeof stock.weight === 'number' ? stock.weight : 0);
    }, 0);

    const isValid = Math.abs(totalWeight - 100) < 0.01;
    const display = totalWeight.toFixed(1);

    return { weight: totalWeight, isValid, display };
  };

  return (
    <div className="md:overflow-x-auto lg:overflow-x-visible">
      <div className="md:min-w-[900px] lg:min-w-0">
        <Table className="text-sm">
          <TableHeader>
            <TableRow>
              <TableHead className="w-64">
                <FinancialTermTooltip term="종목">
                  종목/자산
                </FinancialTermTooltip>
              </TableHead>
              <TableHead className="w-32">
                <FinancialTermTooltip term="투자 금액">
                  투자 금액 ($)
                </FinancialTermTooltip>
              </TableHead>
              <TableHead className="w-28">
                <FinancialTermTooltip term="투자 방식">
                  투자 방식
                </FinancialTermTooltip>
              </TableHead>
              <TableHead className="w-24">
                <FinancialTermTooltip term="자산">
                  자산 타입
                </FinancialTermTooltip>
              </TableHead>
              <TableHead className="w-24">
                <FinancialTermTooltip term="투자 비중">
                  비중 (%)
                </FinancialTermTooltip>
              </TableHead>
              <TableHead className="w-20">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {portfolio.map((stock, index) => (
              <TableRow key={`stock_${index}`}>
                <TableCell className="w-64">
                  <div className="space-y-2 max-w-full">
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
                            className="w-full"
                            autoComplete="off"
                          />
                        )}
                      </>
                    )}
                  </div>
                </TableCell>
                <TableCell className="w-32">
                  <Input
                    type="number"
                    value={stock.amount}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'amount', e.target.value)}
                    min="100"
                    step="100"
                    disabled={portfolioInputMode === 'weight'}
                    className="w-full"
                  />
                </TableCell>
                <TableCell className="w-28">
                  <div className="space-y-2">
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
                      <Select
                        value={stock.dcaFrequency || 'monthly_1'}
                        onValueChange={(value) => updateStock(index, 'dcaFrequency', value)}
                      >
                        <SelectTrigger className="w-full">
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
                    )}
                  </div>
                  {stock.investmentType === 'dca' && stock.dcaFrequency && (
                    <DcaPreview stock={stock} startDate={startDate} endDate={endDate} />
                  )}
                </TableCell>
                <TableCell className="w-24">
                  <div className="space-y-2">
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
                </TableCell>
                <TableCell className="w-24">
                  {portfolioInputMode === 'weight' ? (
                    <Input
                      type="number"
                      value={typeof stock.weight === 'number' ? stock.weight : ''}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'weight', Number(e.target.value))}
                      min="0"
                      max="100"
                      step="0.1"
                      className="w-20 px-2 py-1 text-sm"
                    />
                  ) : (
                    <span title="DCA를 포함한 총 투자금액 비율로 자동 계산됨. 비중을 직접 입력하려면 비중 기반 모드로 전환하세요.">
                      {calculateWeight(stock)}%
                    </span>
                  )}
                </TableCell>
                <TableCell className="w-20">
                  <Button
                    type="button"
                    onClick={() => removeStock(index)}
                    disabled={portfolio.length <= 1}
                    variant="destructive"
                    size="sm"
                  >
                    삭제
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableHead className="text-left font-medium">합계</TableHead>
              <TableHead className="text-left font-medium">${dcaAdjustedTotal.toLocaleString()}</TableHead>
              <TableHead className="text-left font-medium">-</TableHead>
              <TableHead className="text-left font-medium">-</TableHead>
              <TableHead className="text-left font-medium">
                {(() => {
                  if (portfolioInputMode === 'weight') {
                    const { isValid, display } = calculateTotalWeight();
                    return (
                      <span className={isValid ? 'text-foreground' : 'text-destructive font-bold'}>
                        {display}%
                      </span>
                    );
                  } else {
                    return '100.0%';
                  }
                })()}
              </TableHead>
              <TableHead className="text-left font-medium"></TableHead>
            </TableRow>
          </TableFooter>
        </Table>
      </div>
    </div>
  );
};
