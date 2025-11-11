import React from 'react';
import { FormField, FinancialTermTooltip } from '@/shared/components';

export interface DateRangeFormProps {
  startDate: string;
  setStartDate: (date: string) => void;
  endDate: string;
  setEndDate: (date: string) => void;
}

const DateRangeForm: React.FC<DateRangeFormProps> = ({
  startDate,
  setStartDate,
  endDate,
  setEndDate
}) => {
  return (
    <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2">
      <div className="w-full overflow-hidden">
        <FormField
          label={
            <FinancialTermTooltip term="백테스트 기간">
              시작 날짜
            </FinancialTermTooltip>
          }
          type="date"
          value={startDate}
          onChange={(value) => setStartDate(value.toString())}
          helpText="백테스트를 시작할 날짜"
          className="[&>input]:max-w-full [&>input]:box-border"
        />
      </div>
      <div className="w-full overflow-hidden">
        <FormField
          label={
            <FinancialTermTooltip term="백테스트 기간">
              종료 날짜
            </FinancialTermTooltip>
          }
          type="date"
          value={endDate}
          onChange={(value) => setEndDate(value.toString())}
          helpText="백테스트를 종료할 날짜"
          className="[&>input]:max-w-full [&>input]:box-border"
        />
      </div>
    </div>
  );
};

export default DateRangeForm;
