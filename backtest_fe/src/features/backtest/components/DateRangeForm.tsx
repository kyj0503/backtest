import React from 'react';
import { FormField } from '@/shared/components';

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
    <div className="grid gap-6 md:grid-cols-2">
      <FormField
        label="시작 날짜"
        type="date"
        value={startDate}
        onChange={(value) => setStartDate(value.toString())}
      />
      <FormField
        label="종료 날짜"
        type="date"
        value={endDate}
        onChange={(value) => setEndDate(value.toString())}
      />
    </div>
  );
};

export default DateRangeForm;
