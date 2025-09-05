import React from 'react';

interface DateRangeFormProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
}

const DateRangeForm: React.FC<DateRangeFormProps> = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange
}) => {
  return (
    <div className="mb-8">
      <h5 className="text-lg font-semibold mb-4">백테스트 기간</h5>
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <label className="form-label">
            시작일
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onStartDateChange(e.target.value)}
            className="form-control"
            required
          />
        </div>
        <div>
          <label className="form-label">
            종료일
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onEndDateChange(e.target.value)}
            className="form-control"
            required
          />
        </div>
      </div>
    </div>
  );
};

export default DateRangeForm;
