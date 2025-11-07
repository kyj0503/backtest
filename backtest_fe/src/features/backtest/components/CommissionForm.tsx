import React from 'react';
import { FormField, FinancialTermTooltip } from '@/shared/components';
import { REBALANCE_OPTIONS } from '../model/strategyConfig';

export interface CommissionFormProps {
  rebalanceFrequency: string;
  setRebalanceFrequency: (frequency: string) => void;
  commission: number;
  setCommission: (commission: number) => void;
  stockCount?: number; // 포트폴리오 전체 자산 수 (주식 + 현금)
  selectedStrategy?: string; // 선택된 전략
}

const CommissionForm: React.FC<CommissionFormProps> = ({
  rebalanceFrequency,
  setRebalanceFrequency,
  commission,
  setCommission,
  stockCount = 0,
  selectedStrategy = 'buy_hold_strategy'
}) => {
  // 기술적 전략 목록 (리밸런싱 불가)
  const technicalStrategies = [
    'sma_strategy',
    'rsi_strategy',
    'macd_strategy',
    'ema_strategy',
    'bollinger_strategy'
  ];

  const isTechnicalStrategy = technicalStrategies.includes(selectedStrategy);
  const isRebalanceDisabled = stockCount < 2 || isTechnicalStrategy;

  // 비활성화 이유를 명확히 안내
  const rebalanceHelpText = (() => {
    if (isTechnicalStrategy) {
      return '기술적 전략은 매수/매도 신호를 따르므로 리밸런싱이 지원되지 않습니다';
    }
    if (stockCount < 2) {
      return '리밸런싱은 2개 이상의 자산(주식 또는 현금)이 필요합니다';
    }
    return '포트폴리오 비중을 다시 맞추는 주기';
  })();

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <FormField
        label={
          <FinancialTermTooltip term="리밸런싱 주기">
            리밸런싱 주기
          </FinancialTermTooltip>
        }
        type="select"
        value={isRebalanceDisabled ? 'none' : rebalanceFrequency}
        onChange={(value) => setRebalanceFrequency(value as string)}
        options={REBALANCE_OPTIONS}
        disabled={isRebalanceDisabled}
        helpText={rebalanceHelpText}
      />

      <FormField
        label={
          <FinancialTermTooltip term="거래 수수료">
            거래 수수료 (%)
          </FinancialTermTooltip>
        }
        type="number"
        value={commission}
        onChange={(value) => setCommission(value as number)}
        min={0}
        max={5}
        step={0.01}
        helpText="예: 0.2 (0.2% 수수료)"
      />
    </div>
  );
};

export default CommissionForm;
