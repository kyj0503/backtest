import React from 'react';
import { FormField, FinancialTermTooltip } from '@/shared/components';

export interface CommissionFormProps {
  rebalanceFrequency: string;
  setRebalanceFrequency: (frequency: string) => void;
  commission: number;
  setCommission: (commission: number) => void;
  stockCount?: number; // 포트폴리오 전체 자산 수 (주식 + 현금)
}

const CommissionForm: React.FC<CommissionFormProps> = ({
  rebalanceFrequency,
  setRebalanceFrequency,
  commission,
  setCommission,
  stockCount = 0
}) => {
  const rebalanceOptions = [
    { value: 'none', label: '리밸런싱 안함' },
    { value: 'monthly', label: '매월' },
    { value: 'quarterly', label: '분기별' },
    { value: 'annually', label: '연간' }
  ];

  const isRebalanceDisabled = stockCount < 2;
  const rebalanceHelpText = isRebalanceDisabled
    ? '리밸런싱은 2개 이상의 자산(주식 또는 현금)이 필요합니다'
    : '포트폴리오 비중을 다시 맞추는 주기';

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
        options={rebalanceOptions}
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
