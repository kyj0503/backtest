import React from 'react';
import { FormField, FinancialTermTooltip } from '@/shared/components';

export interface CommissionFormProps {
  rebalanceFrequency: string;
  setRebalanceFrequency: (frequency: string) => void;
  commission: number;
  setCommission: (commission: number) => void;
}

const CommissionForm: React.FC<CommissionFormProps> = ({
  rebalanceFrequency,
  setRebalanceFrequency,
  commission,
  setCommission
}) => {
  const rebalanceOptions = [
    { value: 'never', label: '리밸런싱 안함' },
    { value: 'monthly', label: '매월' },
    { value: 'quarterly', label: '분기별' },
    { value: 'yearly', label: '연간' }
  ];

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <FormField
        label={
          <FinancialTermTooltip term="리밸런싱 주기">
            리밸런싱 주기
          </FinancialTermTooltip>
        }
        type="select"
        value={rebalanceFrequency}
        onChange={(value) => setRebalanceFrequency(value as string)}
        options={rebalanceOptions}
        helpText="포트폴리오 비중을 다시 맞추는 주기"
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
