import React from 'react';
import { ScatterChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Scatter, Cell, ReferenceLine } from 'recharts';

const TradesChart: React.FC<{ trades: any[] }> = ({ trades }) => {
  const exitTrades = (trades || []).filter(t => t.type === 'exit' && t.pnl_pct !== undefined);

  return (
    <div>
      <ResponsiveContainer width="100%" height={250}>
        <ScatterChart data={exitTrades} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis dataKey="pnl_pct" />
          <Scatter dataKey="pnl_pct" fill="#0d6efd">
            {exitTrades.map((trade, index) => (
              <Cell key={index} fill={trade.pnl_pct >= 0 ? '#198754' : '#dc3545'} />
            ))}
          </Scatter>
          <ReferenceLine y={0} stroke="#6c757d" strokeDasharray="2 2" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TradesChart;
