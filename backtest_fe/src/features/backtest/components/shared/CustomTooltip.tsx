import React from 'react';

interface TooltipPayload {
  color?: string;
  dataKey?: string;
  value?: number | string;
  name?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border rounded shadow-sm">
        <p className="fw-bold mb-1">{`날짜: ${label}`}</p>
        {payload.map((entry: TooltipPayload, index: number) => (
          <p key={index} style={{ color: entry.color }} className="mb-0">
            {`${entry.dataKey}: ${typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default CustomTooltip;
