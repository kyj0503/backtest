import React, { ChangeEvent } from 'react';

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
    <div className="grid md:grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">시작 날짜</label>
        <input
          type="date"
          value={startDate}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setStartDate(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">종료 날짜</label>
        <input
          type="date"
          value={endDate}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setEndDate(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  );
};

export default DateRangeForm;
