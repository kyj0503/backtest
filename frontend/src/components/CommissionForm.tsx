import React, { ChangeEvent } from 'react';

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
  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* 리밸런싱 주기 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">리밸런싱 주기</label>
        <select
          value={rebalanceFrequency}
          onChange={(e: ChangeEvent<HTMLSelectElement>) => setRebalanceFrequency(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="never">리밸런싱 안함</option>
          <option value="monthly">매월</option>
          <option value="quarterly">분기별</option>
          <option value="yearly">연간</option>
        </select>
        <p className="text-xs text-gray-500 mt-1">
          포트폴리오 비중을 다시 맞추는 주기
        </p>
      </div>

      {/* 거래 수수료 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">거래 수수료 (%)</label>
        <input
          type="number"
          value={commission}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setCommission(Number(e.target.value))}
          min="0"
          max="5"
          step="0.01"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">
          예: 0.2 (0.2% 수수료)
        </p>
      </div>
    </div>
  );
};

export default CommissionForm;
