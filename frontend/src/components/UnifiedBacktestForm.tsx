import React from 'react';
import { UnifiedBacktestRequest } from '../types/api';
import { ASSET_TYPES } from '../constants/strategies';
import DateRangeForm from './DateRangeForm';
import StrategyForm from './StrategyForm';
import CommissionForm from './CommissionForm';
import PortfolioForm from './PortfolioForm';
import { useBacktestForm } from '../hooks/useBacktestForm';
import { useFormValidation } from '../hooks/useFormValidation';

interface UnifiedBacktestFormProps {
  onSubmit: (request: UnifiedBacktestRequest) => Promise<void>;
  loading?: boolean;
}

const UnifiedBacktestForm: React.FC<UnifiedBacktestFormProps> = ({ onSubmit, loading = false }) => {
  const { state, actions, helpers } = useBacktestForm();
  const { errors, validateForm, setErrors } = useFormValidation();

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
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 rounded-t-lg">
          <h4 className="text-xl font-semibold text-gray-800 mb-2">포트폴리오 백테스트</h4>
          <p className="text-sm text-gray-600">
            종목/자산별 투자 금액과 방식을 설정하여 포트폴리오 백테스트를 실행합니다.
          </p>
        </div>
        <div className="p-6">
          {(errors.length > 0 || state.ui.errors.length > 0) && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800 mb-2">입력 오류</h3>
                  <ul className="text-sm text-red-700 space-y-1">
                    {[...errors, ...state.ui.errors].map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
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

            {/* 실행 버튼 */}
            <div>
              <button
                type="submit"
                disabled={loading || state.ui.isLoading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg text-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UnifiedBacktestForm;
