import React from 'react';
import { Loader2, TrendingUp } from 'lucide-react';
import { BacktestRequest } from '../model/api-types';
import { ASSET_TYPES } from '../model/strategyConfig';
import DateRangeForm from './DateRangeForm';
import StrategyForm from './StrategyForm';
import CommissionForm from './CommissionForm';
import PortfolioForm from './PortfolioForm';
import { useBacktestForm } from '../hooks/useBacktestForm';
import { useFormValidation } from '@/shared/hooks/useFormValidation';
import { FormSection } from '@/shared/components';
import { Button } from '@/shared/ui/button';
import { Alert, AlertDescription } from '@/shared/ui/alert';

interface PortfolioBacktestFormProps {
  onSubmit: (request: BacktestRequest) => Promise<unknown>;
  loading?: boolean;
}

const PortfolioBacktestForm: React.FC<PortfolioBacktestFormProps> = ({ onSubmit, loading = false }) => {
  const { state, actions, helpers } = useBacktestForm();
  const { errors, validateForm, setErrors } = useFormValidation();

  const generateStrategyParams = () => {
    const strategyParams = state.strategy.strategyParams;
    return strategyParams;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    actions.setLoading(true);

    const isFormValid = validateForm(state);
    if (!isFormValid) {
      actions.setLoading(false);
      return;
    }

    try {
      // 포트폴리오 데이터 준비 (백엔드 API 스키마에 맞춘 변환)
      const portfolioData = state.portfolio.map(stock => ({
        symbol: stock.symbol.toUpperCase(),
        amount: stock.amount,
        // include optional weight if user provided it
        weight: typeof stock.weight === 'number' ? stock.weight : undefined,
        investment_type: stock.investmentType,
        dca_periods: stock.dcaPeriods || 12,
        asset_type: stock.assetType || ASSET_TYPES.STOCK
      }));

      const params = generateStrategyParams();
      await onSubmit({
        portfolio: portfolioData,
        start_date: state.dates.startDate,
        end_date: state.dates.endDate,
        strategy: state.strategy.selectedStrategy || 'buy_hold_strategy',
        strategy_params: params,
        commission: state.settings.commission / 100, // 퍼센트를 소수점으로 변환 (0.2 -> 0.002)
        rebalance_frequency: state.settings.rebalanceFrequency
      });
    } catch (error) {
      console.error('백테스트 실행 중 오류:', error);
      const errorMessage = error instanceof Error ? error.message : '백테스트 실행 중 오류가 발생했습니다.';
      setErrors([errorMessage]);
    } finally {
      actions.setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6">
      {(errors.length > 0 || state.ui.errors.length > 0) && (
        <Alert variant="destructive" className="mb-2">
          <AlertDescription>
            <h3 className="text-sm font-semibold">입력 오류</h3>
            <ul className="mt-2 space-y-1 text-sm">
              {[...errors, ...state.ui.errors].map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        <PortfolioForm
          portfolio={state.portfolio}
          updateStock={actions.updateStock}
          addStock={actions.addStock}
          addCash={actions.addCash}
          removeStock={actions.removeStock}
          getTotalAmount={helpers.getTotalAmount}
          portfolioInputMode={state.portfolioInputMode}
          setPortfolioInputMode={actions.setPortfolioInputMode}
          totalInvestment={state.totalInvestment}
          setTotalInvestment={actions.setTotalInvestment}
        />

        <FormSection
          title="백테스트 기간"
          description="실행할 기간을 지정하세요."
        >
          <DateRangeForm
            startDate={state.dates.startDate}
            setStartDate={actions.setStartDate}
            endDate={state.dates.endDate}
            setEndDate={actions.setEndDate}
          />
        </FormSection>

        <div className="grid gap-6 md:grid-cols-2">
          <FormSection
            title="전략 선택"
            description="적용할 투자 전략과 파라미터를 설정하세요."
          >
            <StrategyForm
              selectedStrategy={state.strategy.selectedStrategy}
              setSelectedStrategy={actions.setSelectedStrategy}
              strategyParams={state.strategy.strategyParams}
              updateStrategyParam={actions.updateStrategyParam}
            />
          </FormSection>
          <FormSection
            title="리밸런싱 & 수수료"
            description="리밸런싱 주기와 거래 수수료 비율을 입력하세요."
          >
            <CommissionForm
              rebalanceFrequency={state.settings.rebalanceFrequency}
              setRebalanceFrequency={actions.setRebalanceFrequency}
              commission={state.settings.commission}
              setCommission={actions.setCommission}
            />
          </FormSection>
        </div>

        {/* 제출 버튼 */}
        <div className="flex justify-end pt-4">
          <Button
            type="submit"
            disabled={loading || state.ui.isLoading}
            size="lg"
            className="min-w-[200px]"
          >
            {(loading || state.ui.isLoading) ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                백테스트 실행 중...
              </>
            ) : (
              <>
                <TrendingUp className="mr-2 h-4 w-4" />
                백테스트 실행
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default PortfolioBacktestForm;
