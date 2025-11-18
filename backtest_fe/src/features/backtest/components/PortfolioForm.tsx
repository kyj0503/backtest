import React from 'react';
import { FormSection } from '@/shared/components';
import { Button } from '@/shared/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip';
import { Stock, PortfolioInputMode } from '../model/types/backtest-form-types';
import { VALIDATION_RULES } from '../model/strategyConfig';
import {
  PortfolioInputModeToggle,
  PortfolioMobileCard,
  PortfolioSummary,
  PortfolioTable,
} from './portfolio-form';

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
  return (
    <FormSection
      title="포트폴리오 구성"
      description={`투자할 자산과 비중을 설정하세요. 최대 ${VALIDATION_RULES.MAX_PORTFOLIO_SIZE}개의 자산을 추가할 수 있습니다.`}
      contentClassName="md:overflow-x-auto"
      actions={
        <PortfolioInputModeToggle
          mode={portfolioInputMode}
          onModeChange={setPortfolioInputMode}
        />
      }
      footer={
        <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2 sm:items-center">
          <Button
            type="button"
            onClick={addStock}
            disabled={portfolio.length >= VALIDATION_RULES.MAX_PORTFOLIO_SIZE}
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
                disabled={portfolio.length >= VALIDATION_RULES.MAX_PORTFOLIO_SIZE}
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
      <div className="md:hidden space-y-3">
        {portfolio.map((stock, index) => (
          <PortfolioMobileCard
            key={`stock_mobile_${index}`}
            stock={stock}
            index={index}
            portfolio={portfolio}
            portfolioInputMode={portfolioInputMode}
            updateStock={updateStock}
            removeStock={removeStock}
            startDate={startDate}
            endDate={endDate}
          />
        ))}
        <PortfolioSummary
          portfolio={portfolio}
          portfolioInputMode={portfolioInputMode}
          totalInvestment={totalInvestment}
          setTotalInvestment={setTotalInvestment}
          startDate={startDate}
          endDate={endDate}
        />
      </div>

      <div className="hidden md:block">
        <PortfolioTable
          portfolio={portfolio}
          portfolioInputMode={portfolioInputMode}
          updateStock={updateStock}
          removeStock={removeStock}
          startDate={startDate}
          endDate={endDate}
        />
      </div>
    </FormSection>
  );
};

export default PortfolioForm;
