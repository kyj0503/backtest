import React from 'react';
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, Line, Area, ReferenceLine } from 'recharts';
import CustomTooltip from './CustomTooltip';

const EquityChart: React.FC<{ data: any[] }> = ({ data }) => {
  const safeData = data || [];

  return (
    <div>
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={safeData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="return" orientation="left" />
          <YAxis yAxisId="drawdown" orientation="right" />
          <RechartsTooltip content={<CustomTooltip />} />
          <Legend />
          <Line yAxisId="return" type="monotone" dataKey="return_pct" stroke="#198754" strokeWidth={2} dot={false} name="수익률 (%)" />
          <Area yAxisId="drawdown" type="monotone" dataKey="drawdown_pct" stroke="#dc3545" fill="#dc3545" fillOpacity={0.3} name="드로우다운 (%)" />
          <ReferenceLine yAxisId="return" y={0} stroke="#6c757d" strokeDasharray="2 2" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EquityChart;
