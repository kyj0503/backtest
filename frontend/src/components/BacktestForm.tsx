import React, { useState } from 'react';
import { BacktestRequest } from '../types/api';
import { ASSET_TYPES } from '../constants/strategies';
import DateRangeForm from './DateRangeForm';
import StrategyForm from './StrategyForm';
import CommissionForm from './CommissionForm';
import PortfolioForm from './PortfolioForm';
import AdvancedSettingsForm, { AdvancedStockSettings } from './AdvancedSettingsForm';
import { useBacktestForm } from '../hooks/useBacktestForm';
import { useFormValidation } from '../hooks/useFormValidation';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Card, CardContent, CardHeader } from './ui/card';

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
      console.log('Portfolio data being sent:', portfolioData);
      console.log('Strategy params being sent:', params);

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
    <div className="max-w-6xl mx-auto">
      <Card>
        <CardHeader>
          <h4 className="text-xl font-semibold text-foreground mb-2">포트폴리오 백테스트</h4>
          <p className="text-sm text-muted-foreground">
            종목/자산별 투자 금액과 방식을 설정하여 포트폴리오 백테스트를 실행합니다.
          </p>
        </CardHeader>
        <CardContent>
          {(errors.length > 0 || state.ui.errors.length > 0) && (
            <Alert variant="destructive" className="mb-6">
              <AlertDescription>
                <h3 className="text-sm font-medium mb-2">입력 오류</h3>
                <ul className="text-sm space-y-1">
                    {[...errors, ...state.ui.errors].map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            {/* 포트폴리오 구성 */}
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

            {/* 백테스트 설정 */}
            <div className="mb-8">
              <h5 className="text-lg font-semibold mb-4">백테스트 설정</h5>
              <DateRangeForm
                startDate={state.dates.startDate}
                setStartDate={actions.setStartDate}
                endDate={state.dates.endDate}
                setEndDate={actions.setEndDate}
              />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <StrategyForm
                selectedStrategy={state.strategy.selectedStrategy}
                setSelectedStrategy={actions.setSelectedStrategy}
                strategyParams={state.strategy.strategyParams}
                updateStrategyParam={actions.updateStrategyParam}
              />
              <CommissionForm
                rebalanceFrequency={state.settings.rebalanceFrequency}
                setRebalanceFrequency={actions.setRebalanceFrequency}
                commission={state.settings.commission}
                setCommission={actions.setCommission}
              />
            </div>

            {/* 고급 설정 버튼 */}
            <div className="mb-4">
              <Button
                type="button"
                variant={advancedSettings.length > 0 ? "default" : "outline"}
                onClick={() => setShowAdvancedSettings(true)}
                disabled={state.portfolio.length === 0}
                className={`w-full py-2 px-4 text-sm font-medium ${
                  advancedSettings.length > 0 
                    ? 'bg-blue-600 text-white hover:bg-blue-700' 
                    : ''
                }`}
              >
                {advancedSettings.length > 0 ? '✓' : '🔧'} 고급 사용자 설정 
                {advancedSettings.length > 0 && 
                  ` (${advancedSettings.filter(s => s.startDate || s.endDate || s.strategy !== 'buy_and_hold').length}개 종목 개별 설정됨)`
                }
              </Button>
              {state.portfolio.length === 0 ? (
                <p className="text-xs text-muted-foreground mt-1 text-center">
                  포트폴리오에 종목을 추가한 후 고급 설정을 사용할 수 있습니다.
                </p>
              ) : advancedSettings.length > 0 && (
                <p className="text-xs text-green-600 mt-1 text-center">
                  고급 설정이 적용되었습니다. 각 종목별로 개별 날짜와 전략이 설정됩니다.
                </p>
              )}
            </div>

            {/* 실행 버튼 */}
            <div>
              <Button
                type="submit"
                disabled={loading || state.ui.isLoading}
                className="w-full py-3 px-6 text-lg font-semibold"
                size="lg"
              >
                {loading || state.ui.isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    포트폴리오 백테스트 실행 중...
                  </span>
                ) : (
                  '포트폴리오 백테스트 실행'
                )}
              </Button>
            </div>
          </form>

          {/* 고급 설정 모달 */}
          <AdvancedSettingsForm
            portfolio={state.portfolio}
            isVisible={showAdvancedSettings}
            onClose={() => setShowAdvancedSettings(false)}
            onApply={setAdvancedSettings}
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default BacktestForm;
