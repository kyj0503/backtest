import React, { useState } from 'react';
import { Loader2, Settings2, CheckCircle2 } from 'lucide-react';
import { BacktestRequest } from '../types/api';
import { ASSET_TYPES } from '../constants/strategies';
import DateRangeForm from './DateRangeForm';
import StrategyForm from './StrategyForm';
import CommissionForm from './CommissionForm';
import PortfolioForm from './PortfolioForm';
import AdvancedSettingsForm, { AdvancedStockSettings } from './AdvancedSettingsForm';
import { useBacktestForm } from '../hooks/useBacktestForm';
import { useFormValidation } from '../hooks/useFormValidation';
import { FormSection } from './common';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';

interface BacktestFormProps {
  onSubmit: (request: BacktestRequest) => Promise<void>;
  loading?: boolean;
}

const BacktestForm: React.FC<BacktestFormProps> = ({ onSubmit, loading = false }) => {
  const { state, actions, helpers } = useBacktestForm();
  const { errors, validateForm, setErrors } = useFormValidation();
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [advancedSettings, setAdvancedSettings] = useState<AdvancedStockSettings[]>([]);

  const generateStrategyParams = () => {
    const strategyParams = state.strategy.strategyParams;
    const params: Record<string, any> = {};
    Object.entries(strategyParams).forEach(([key, value]) => {
      params[key] = typeof value === 'string' ? parseInt(value) || value : value;
    });
    return params;
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
        strategy: state.strategy.selectedStrategy || 'buy_and_hold',
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
      <section className="space-y-6 rounded-[32px] border border-border/40 bg-card/40 p-8 shadow-sm">
        <div className="space-y-2">
          <h4 className="text-2xl font-semibold text-foreground">포트폴리오 백테스트</h4>
          <p className="text-sm text-muted-foreground">
            자산 구성과 전략, 리밸런싱 정책을 선택해 백테스트를 실행하세요.
          </p>
        </div>

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
              description="실행할 기간을 지정하세요. 종목별 커스텀 기간은 고급 설정에서 조정할 수 있습니다."
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

            <FormSection
              title="종목별 고급 설정"
              description="포트폴리오에 종목을 추가한 후 개별 전략과 기간을 조정할 수 있습니다."
            >
              <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
                <Button
                  type="button"
                  variant={advancedSettings.length > 0 ? 'secondary' : 'outline'}
                  onClick={() => setShowAdvancedSettings(true)}
                  disabled={state.portfolio.length === 0}
                  className="w-full rounded-full sm:w-auto"
                >
                  <Settings2 className="mr-2 h-4 w-4" />
                  고급 설정 열기
                </Button>
                <div className="text-xs text-muted-foreground">
                  {state.portfolio.length === 0 && '포트폴리오에 종목을 추가하면 고급 설정을 사용할 수 있습니다.'}
                  {state.portfolio.length > 0 && advancedSettings.length === 0 && '필요 시 종목별 전략과 기간을 세밀하게 조정하세요.'}
                  {advancedSettings.length > 0 && (
                    <span className="inline-flex items-center gap-1 text-emerald-600">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      개별 설정이 적용되었습니다.
                    </span>
                  )}
                </div>
              </div>
            </FormSection>

            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={loading || state.ui.isLoading}
                className="w-full rounded-full text-base font-semibold sm:w-auto sm:px-8"
                size="lg"
              >
                {loading || state.ui.isLoading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    백테스트 실행 중...
                  </span>
                ) : (
                  '포트폴리오 백테스트 실행'
                )}
              </Button>
            </div>
        </form>

        <AdvancedSettingsForm
          portfolio={state.portfolio}
          isVisible={showAdvancedSettings}
          onClose={() => setShowAdvancedSettings(false)}
          onApply={setAdvancedSettings}
        />
      </section>
    </div>
  );
};

export default BacktestForm;
