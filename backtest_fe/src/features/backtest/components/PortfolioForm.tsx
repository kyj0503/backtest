import React, { ChangeEvent } from 'react';
import { FormSection, FinancialTermTooltip } from '@/shared/components';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { ScrollArea } from '@/shared/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip';
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table';
import { Stock, PortfolioInputMode } from '../model/backtest-form-types';
import { PREDEFINED_STOCKS, ASSET_TYPES } from '../model/strategyConfig';

export interface PortfolioFormProps {
  portfolio: Stock[];
  updateStock: (index: number, field: keyof Stock, value: string | number) => void;
  addStock: () => void;
  addCash: () => void;
  removeStock: (index: number) => void;
  getTotalAmount: () => number;
  portfolioInputMode: PortfolioInputMode;
  setPortfolioInputMode: (mode: PortfolioInputMode) => void;
  totalInvestment: number;
  setTotalInvestment: (amount: number) => void;
}

const PortfolioForm: React.FC<PortfolioFormProps> = ({
  portfolio,
  updateStock,
  addStock,
  addCash,
  removeStock,
  getTotalAmount,
  portfolioInputMode,
  setPortfolioInputMode,
  totalInvestment,
  setTotalInvestment,
}) => {
  return (
    <FormSection
      title="포트폴리오 구성"
      description="투자할 자산과 비중을 설정하세요. 최대 10개의 자산을 추가할 수 있습니다."
      actions={
        <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <div className="inline-flex items-center gap-1 rounded-full border border-border/70 bg-background p-1 shadow-sm">
            <Button
              type="button"
              onClick={() => setPortfolioInputMode('amount')}
              variant={portfolioInputMode === 'amount' ? 'secondary' : 'ghost'}
              className="rounded-full px-4 py-1 text-sm"
            >
              금액 기준
            </Button>
            <Button
              type="button"
              onClick={() => setPortfolioInputMode('weight')}
              variant={portfolioInputMode === 'weight' ? 'secondary' : 'ghost'}
              className="rounded-full px-4 py-1 text-sm"
            >
              비중 기준
            </Button>
          </div>
          {portfolioInputMode === 'weight' && (
            <div className="flex items-center gap-2 rounded-full bg-muted/40 px-3 py-1.5">
              <Label className="text-xs font-medium text-muted-foreground">
                <FinancialTermTooltip term="투자 금액">
                  전체 투자금액($)
                </FinancialTermTooltip>
              </Label>
              <Input
                type="number"
                min={1000}
                step={100}
                value={totalInvestment}
                onChange={e => setTotalInvestment(Number(e.target.value))}
                className="h-8 w-28 rounded-full border-0 bg-background text-right text-sm shadow-none focus-visible:ring-1"
              />
            </div>
          )}
        </div>
      }
      footer={
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            onClick={addStock}
            disabled={portfolio.length >= 10}
            variant="outline"
            className="rounded-full"
          >
            + 종목 추가
          </Button>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  onClick={addCash}
                  disabled={portfolio.length >= 10}
                  variant="outline"
                  className="rounded-full border-green-300 text-green-700 hover:bg-green-50"
                >
                  현금 추가
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>현금을 포트폴리오에 추가 (무위험 자산)</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <span className="text-xs text-muted-foreground">
            {portfolio.length}/10 자산
          </span>
        </div>
      }
    >
      <ScrollArea className="w-full">
        <div className="min-w-[820px]">
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
              <TableHead className="w-28">투자 방식</TableHead>
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
                  <div className="space-y-2 max-w-full overflow-hidden">
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
                          <SelectContent>
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
                      <Input
                        type="number"
                        value={stock.dcaPeriods || 12}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'dcaPeriods', e.target.value)}
                        min="1"
                        max="60"
                        placeholder="개월 수"
                        className="w-full"
                      />
                    )}
                  </div>
                  {stock.investmentType === 'dca' && stock.dcaPeriods && (
                    <p className="text-xs text-muted-foreground mt-1">
                      월 ${Math.round(stock.amount / stock.dcaPeriods)}씩 {stock.dcaPeriods}개월
                    </p>
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
                    {/* 자산 타입 배지(위험자산/무위험) 노출 제거 */}
                  </div>
                </TableCell>
                <TableCell className="w-24">
                  {/* 비중(%) 입력: weight 기반 모드면 직접 입력, 금액 기반 모드면 자동 계산 */}
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
                    <span title="투자 금액 비율로 자동 계산됨. 비중을 직접 입력하려면 비중 기반 모드로 전환하세요.">
                      {((stock.amount / getTotalAmount()) * 100).toFixed(1)}%
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
                <TableHead className="text-left font-medium">${getTotalAmount().toLocaleString()}</TableHead>
                <TableHead className="text-left font-medium">-</TableHead>
                <TableHead className="text-left font-medium">-</TableHead>
                <TableHead className="text-left font-medium">100.0%</TableHead>
                <TableHead className="text-left font-medium"></TableHead>
              </TableRow>
            </TableFooter>
          </Table>
        </div>
      </ScrollArea>
    </FormSection>
  );
};

export default PortfolioForm;
