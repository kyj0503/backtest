import React, { memo, useMemo } from 'react';
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, Line, Area, ReferenceLine } from 'recharts';
import CustomTooltip from './CustomTooltip';

interface EquityChartData {
  date: string;
  return_pct: number;
  drawdown_pct: number;
  [key: string]: any;
}

interface EquityChartProps {
  data: EquityChartData[];
}

const EquityChart: React.FC<EquityChartProps> = memo(({ data }) => {
  // 데이터 안전성 검사 및 메모이제이션
  const safeData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map(item => ({
      ...item,
      return_pct: Number(item.return_pct) || 0,
      drawdown_pct: Number(item.drawdown_pct) || 0
    }));
  }, [data]);

  // 차트 설정 메모이제이션
  const chartConfig = useMemo(() => ({
    margin: { top: 20, right: 30, left: 20, bottom: 5 },
    strokeWidth: 2,
    fillOpacity: 0.3
  }), []);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={safeData} margin={chartConfig.margin}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis yAxisId="return" orientation="left" />
        <YAxis yAxisId="drawdown" orientation="right" />
        <RechartsTooltip content={<CustomTooltip />} />
        <Legend />
        <Line 
          yAxisId="return" 
          type="monotone" 
          dataKey="return_pct" 
          stroke="#198754" 
          strokeWidth={chartConfig.strokeWidth} 
          dot={false} 
          name="수익률 (%)" 
        />
        <Area 
          yAxisId="drawdown" 
          type="monotone" 
          dataKey="drawdown_pct" 
          stroke="#dc3545" 
          fill="#dc3545" 
          fillOpacity={chartConfig.fillOpacity} 
          name="드로우다운 (%)" 
        />
        <ReferenceLine yAxisId="return" y={0} stroke="#6c757d" strokeDasharray="2 2" />
      </ComposedChart>
    </ResponsiveContainer>
  );
});

EquityChart.displayName = 'EquityChart';

export default EquityChart;
