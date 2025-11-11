import React, { useState } from 'react';
import { Loader2, TrendingUp, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { BacktestRequest } from '../model/types/api-types';
import { ASSET_TYPES } from '../model/strategyConfig';
import DateRangeForm from './DateRangeForm';
import StrategyForm from './StrategyForm';
import CommissionForm from './CommissionForm';
import PortfolioForm from './PortfolioForm';
import { useBacktestForm } from '../hooks/useBacktestForm';
import { useFormValidation } from '@/shared/hooks/useFormValidation';
import { FormSection } from '@/shared/components';
import { Button } from '@/shared/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog';

interface PortfolioBacktestFormProps {
  onSubmit: (request: BacktestRequest) => Promise<unknown>;
  loading?: boolean;
}

const PortfolioBacktestForm: React.FC<PortfolioBacktestFormProps> = ({ onSubmit, loading = false }) => {
  const { state, actions } = useBacktestForm();
  const { errors, validateForm, setErrors } = useFormValidation();
  const [showErrorModal, setShowErrorModal] = useState(false);

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
      setShowErrorModal(true);  // 에러 모달 표시
      return;
    }

    try {
      // 포트폴리오 데이터 준비 (백엔드 API 스키마에 맞춘 변환)
      const portfolioData = state.portfolio.map(stock => {
        return {
          symbol: stock.symbol.toUpperCase(),
          amount: stock.amount,  // 항상 amount를 전송 (비중 모드에서도 reducer가 계산함)
          investment_type: stock.investmentType,
          dca_frequency: stock.dcaFrequency || 'monthly_1',
          asset_type: stock.assetType || ASSET_TYPES.STOCK
        };
      });

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
      
      // 백엔드 검증 에러 메시지 추출
      let errorMessages: string[] = [];
      
      if (axios.isAxiosError(error) && error.response) {
        const responseData = error.response.data;
        
        // Pydantic ValidationError 처리
        if (responseData?.detail) {
          if (Array.isArray(responseData.detail)) {
            // Pydantic validation errors
            errorMessages = responseData.detail.map((err: any) => {
              if (err.msg) {
                return err.msg;
              }
              return JSON.stringify(err);
            });
          } else if (typeof responseData.detail === 'string') {
            errorMessages = [responseData.detail];
          }
        } else if (responseData?.message) {
          errorMessages = [responseData.message];
        } else if (responseData?.error) {
          errorMessages = [responseData.error];
        }
      }
      
      // 에러 메시지가 없으면 기본 메시지
      if (errorMessages.length === 0) {
        const defaultMessage = error instanceof Error ? error.message : '백테스트 실행 중 오류가 발생했습니다.';
        errorMessages = [defaultMessage];
      }
      
      setErrors(errorMessages);
      setShowErrorModal(true);  // 에러 모달 표시
    } finally {
      actions.setLoading(false);
    }
  };

  const allErrors = [...errors, ...state.ui.errors];

  // 포트폴리오 전체 자산 수 계산 (주식 + 현금)
  const stockCount = state.portfolio.length;

  return (
    <div className="mx-auto flex w-full lg:max-w-[1600px] flex-col gap-4 sm:gap-6">
      {/* 에러 모달 */}
      <Dialog open={showErrorModal} onOpenChange={setShowErrorModal}>
        <DialogContent className="max-w-[95vw] sm:max-w-lg mx-3">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-destructive text-2xl">
              <div className="p-2 rounded-xl bg-destructive/10">
                <AlertCircle className="h-6 w-6" />
              </div>
              입력 오류
            </DialogTitle>
            <DialogDescription asChild>
              <div className="mt-6">
                <div className="rounded-xl bg-destructive/5 p-5 border-2 border-destructive/20">
                  <ul className="space-y-3 text-sm text-foreground">
                    {allErrors.map((error, index) => (
                      <li key={index} className="flex items-start gap-3">
                        <span className="text-destructive font-bold text-base mt-0.5">•</span>
                        <span className="leading-relaxed">{error}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="mt-8 flex justify-end">
                  <Button size="lg" onClick={() => setShowErrorModal(false)}>
                    확인
                  </Button>
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>

      <form onSubmit={handleSubmit} className="space-y-8">
        <PortfolioForm
          portfolio={state.portfolio}
          updateStock={actions.updateStock}
          addStock={actions.addStock}
          addCash={actions.addCash}
          removeStock={actions.removeStock}
          portfolioInputMode={state.portfolioInputMode}
          setPortfolioInputMode={actions.setPortfolioInputMode}
          totalInvestment={state.totalInvestment}
          setTotalInvestment={actions.setTotalInvestment}
          startDate={state.dates.startDate}
          endDate={state.dates.endDate}
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
              stockCount={stockCount}
              selectedStrategy={state.strategy.selectedStrategy}
            />
          </FormSection>
        </div>

        {/* 제출 버튼 */}
        <div className="flex justify-end pt-6">
          <Button
            type="submit"
            disabled={loading || state.ui.isLoading}
            size="lg"
            className="min-w-[240px] shadow-md hover:shadow-xl"
          >
            {(loading || state.ui.isLoading) ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                백테스트 실행 중...
              </>
            ) : (
              <>
                <TrendingUp className="mr-2 h-5 w-5" />
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
