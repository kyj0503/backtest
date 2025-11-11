import React, { ChangeEvent } from 'react';
import { FormSection, FinancialTermTooltip } from '@/shared/components';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip';
import { Card, CardContent } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table';
import { Stock, PortfolioInputMode } from '../model/types/backtest-form-types';
import { PREDEFINED_STOCKS, ASSET_TYPES, DCA_FREQUENCY_OPTIONS, VALIDATION_RULES } from '../model/strategyConfig';
import { TEXT_STYLES } from '@/shared/styles/design-tokens';
import { getDcaAdjustedTotal } from '../utils/portfolioCalculations';
import { calculateDcaPeriods } from '../utils/calculateDcaPeriods';
import { Trash2 } from 'lucide-react';

// DCA 프리뷰 컴포넌트
const DcaPreview: React.FC<{ stock: Stock; startDate?: string; endDate?: string }> = ({ stock, startDate, endDate }) => {
  const periodAmount = stock.amount || 0;  // 입력한 금액이 회당 투자 금액
  const frequencyLabel = DCA_FREQUENCY_OPTIONS.find(opt => opt.value === stock.dcaFrequency)?.label || '';

  // 백테스트 기간 계산 (DCA 횟수)
  let dcaPeriods = 1;
  let totalAmount = periodAmount;

  if (startDate && endDate) {
    // calculateDcaPeriods를 사용하여 중복 제거
    dcaPeriods = calculateDcaPeriods(startDate, endDate, stock.dcaFrequency || 'monthly_1');
    totalAmount = periodAmount * dcaPeriods;
  }

  return (
    <p className={`${TEXT_STYLES.captionSmall} mt-1`}>
      {frequencyLabel}: 총 {dcaPeriods}회, 회당 ${periodAmount.toLocaleString()} (총 ${totalAmount.toLocaleString()})
    </p>
  );
};

export interface PortfolioFormProps {
  portfolio: Stock[];
  updateStock: (index: number, field: keyof Stock, value: string | number) => void;
  addStock: () => void;
  addCash: () => void;
  removeStock: (index: number) => void;
  portfolioInputMode: PortfolioInputMode;
  setPortfolioInputMode: (mode: PortfolioInputMode) => void;
  totalInvestment: number;
  setTotalInvestment: (amount: number) => void;
  startDate?: string;
  endDate?: string;
}

const PortfolioForm: React.FC<PortfolioFormProps> = ({
  portfolio,
  startDate,
  endDate,
  updateStock,
  addStock,
  addCash,
  removeStock,
  portfolioInputMode,
  setPortfolioInputMode,
  totalInvestment,
  setTotalInvestment,
}) => {
  // 모바일 카드 레이아웃 렌더링
  const renderMobileCard = (stock: Stock, index: number) => {
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
          {/* 헤더: 자산 번호 + 삭제 버튼 */}
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

          {/* 종목/자산 선택 */}
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

          {/* 2열 그리드: 투자금액 + 자산타입 */}
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

          {/* 투자 방식 */}
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

          {/* 비중 표시 */}
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

  return (
    <FormSection
      title="포트폴리오 구성"
      description={`투자할 자산과 비중을 설정하세요. 최대 ${VALIDATION_RULES.MAX_PORTFOLIO_SIZE}개의 자산을 추가할 수 있습니다.`}
      contentClassName="md:overflow-x-auto"
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
                min={1}
                step={0.01}
                value={totalInvestment}
                onChange={e => setTotalInvestment(Number(e.target.value))}
                className="h-8 w-28 rounded-full border-0 bg-background text-right text-sm shadow-none focus-visible:ring-1"
              />
            </div>
          )}
        </div>
      }
      footer={
        <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2 sm:items-center">
          <Button
            type="button"
            onClick={addStock}
            disabled={portfolio.length >= 10}
            variant="outline"
            className="rounded-full w-full sm:w-auto"
            size="sm"
          >
            + 종목 추가
          </Button>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                onClick={addCash}
                disabled={portfolio.length >= 10}
                variant="outline"
                className="rounded-full border-green-300 text-green-700 hover:bg-green-50 w-full sm:w-auto"
                size="sm"
              >
                현금 추가
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>현금을 포트폴리오에 추가 (무위험 자산)</p>
            </TooltipContent>
          </Tooltip>
          <span className="text-xs text-muted-foreground sm:ml-auto">
            {portfolio.length}/{VALIDATION_RULES.MAX_PORTFOLIO_SIZE} 자산
          </span>
        </div>
      }
    >
      {/* 모바일 카드 레이아웃 (md 이하) */}
      <div className="md:hidden space-y-3">
        {portfolio.map((stock, index) => renderMobileCard(stock, index))}
        
        {/* 모바일 합계 카드 */}
        <Card className="bg-muted/30">
          <CardContent className="p-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">합계</span>
                <span className="text-lg font-bold">${(() => {
                  const dcaAdjustedTotal = getDcaAdjustedTotal(portfolio, startDate, endDate);
                  return dcaAdjustedTotal.toLocaleString();
                })()}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">총 비중</span>
                {(() => {
                  if (portfolioInputMode === 'weight') {
                    const totalWeight = portfolio.reduce((sum, stock) => {
                      return sum + (typeof stock.weight === 'number' ? stock.weight : 0);
                    }, 0);
                    const isValid = Math.abs(totalWeight - 100) < 0.01;
                    const displayWeight = totalWeight.toFixed(1);
                    return (
                      <Badge variant={isValid ? "secondary" : "destructive"} className="font-bold">
                        {displayWeight}%
                      </Badge>
                    );
                  } else {
                    return <Badge variant="secondary" className="font-bold">100.0%</Badge>;
                  }
                })()}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 데스크톱 테이블 레이아웃 (md 이상) */}
      <div className="hidden md:block">
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
                    {/* 자산 타입 배지(위험자산/무위험) 노출 제거 */}
                  </div>
                </TableCell>
                <TableCell className="w-24">
                  {/* 비중(%) 입력: weight 기반 모드면 직접 입력, 금액 기반 모드면 자동 계산 (DCA 고려) */}
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
                      {(() => {
                        // 날짜가 설정되지 않으면 가중치 계산 불가
                        if (!startDate || !endDate) {
                          return 'N/A';
                        }

                        const dcaAdjustedTotal = getDcaAdjustedTotal(portfolio, startDate, endDate);
                        
                        // 각 종목의 실제 총 투자액 계산
                        let stockTotalAmount = stock.amount;
                        if (stock.investmentType === 'dca') {
                          // DCA: 회당 금액 × 투자 횟수
                          const dcaPeriods = calculateDcaPeriods(startDate, endDate, stock.dcaFrequency || 'monthly_1');
                          stockTotalAmount = stock.amount * dcaPeriods;
                        }
                        // 일시불: 입력한 금액 그대로
                        
                        return dcaAdjustedTotal > 0 
                          ? ((stockTotalAmount / dcaAdjustedTotal) * 100).toFixed(1)
                          : '0.0';
                      })()}%
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
                <TableHead className="text-left font-medium">${(() => {
                  const dcaAdjustedTotal = getDcaAdjustedTotal(portfolio, startDate, endDate);
                  return dcaAdjustedTotal.toLocaleString();
                })()}</TableHead>
                <TableHead className="text-left font-medium">-</TableHead>
                <TableHead className="text-left font-medium">-</TableHead>
                <TableHead className="text-left font-medium">
                  {(() => {
                    // 실제 비중 합계 계산
                    if (portfolioInputMode === 'weight') {
                      const totalWeight = portfolio.reduce((sum, stock) => {
                        return sum + (typeof stock.weight === 'number' ? stock.weight : 0);
                      }, 0);
                      
                      const isValid = Math.abs(totalWeight - 100) < 0.01; // 반올림 오차 허용
                      const displayWeight = totalWeight.toFixed(1);
                      
                      return (
                        <span className={isValid ? 'text-foreground' : 'text-destructive font-bold'}>
                          {displayWeight}%
                        </span>
                      );
                    } else {
                      // 금액 기준 모드에서는 항상 100%
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
      </div>
    </FormSection>
  );
};

export default PortfolioForm;
