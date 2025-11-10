import React, { memo, useMemo } from 'react';
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, Line, Area, ReferenceLine } from 'recharts';
import { CustomTooltip } from './shared';
import { useRenderPerformance } from '@/shared/components';

interface EquityChartData {
  date: string;
  return_pct: number;
  drawdown_pct: number;
  [key: string]: string | number;
}

interface EquityChartProps {
  data: EquityChartData[];
}

// 차트 설정 상수 (컴포넌트 외부로 이동하여 재생성 방지)
const CHART_CONFIG = {
  margin: { top: 20, right: 30, left: 20, bottom: 5 },
  strokeWidth: 2,
  fillOpacity: 0.3,
} as const;

const EquityChart: React.FC<EquityChartProps> = memo(({ data }) => {
  // 성능 모니터링
  useRenderPerformance('EquityChart');

  // 데이터 안전성 검사 (샘플링은 useChartData에서 처리됨)
  const processedData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];

    return data.map(item => ({
      ...item,
      return_pct: Number(item.return_pct) || 0,
      drawdown_pct: Number(item.drawdown_pct) || 0
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={320} debounce={300}>
      <ComposedChart data={processedData} margin={CHART_CONFIG.margin} syncId="equityChart">
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
          strokeWidth={CHART_CONFIG.strokeWidth}
          dot={false}
          name="수익률 (%)"
          isAnimationActive={false}
          connectNulls={true}
        />
        <Area
          yAxisId="drawdown"
          type="monotone"
          dataKey="drawdown_pct"
          stroke="#dc3545"
          fill="#dc3545"
          fillOpacity={CHART_CONFIG.fillOpacity}
          name="드로우다운 (%)"
          isAnimationActive={false}
        />
        <ReferenceLine yAxisId="return" y={0} stroke="#6c757d" strokeDasharray="2 2" />
      </ComposedChart>
    </ResponsiveContainer>
  );
});

EquityChart.displayName = 'EquityChart';

export default EquityChart;
