import React from 'react';
import { CalendarRange } from 'lucide-react';
import { FormField, FormLegend } from './common';

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
    <div className="space-y-4">
      <FormLegend
        icon={<CalendarRange className="h-3.5 w-3.5" />}
        items={[
          { label: 'YYYY-MM-DD 형식', tone: 'muted' },
          { label: '시작은 종료보다 이전이어야 합니다', tone: 'accent' },
        ]}
      />
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
    </div>
  );
};

export default DateRangeForm;
