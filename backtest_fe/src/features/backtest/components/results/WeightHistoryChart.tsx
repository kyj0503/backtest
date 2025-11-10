import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';
import { WeightHistoryPoint } from '../../model/types/backtest-result-types';
import { getStockDisplayName } from '../../model/strategyConfig';
import { TEXT_STYLES } from '@/shared/styles/design-tokens';

interface RebalanceEvent {
  date: string;
  trades: Array<any>;
  weights_before: Record<string, number>;
  weights_after: Record<string, number>;
}

interface WeightHistoryChartProps {
  weightHistory: WeightHistoryPoint[];
  portfolioComposition: Array<{ symbol: string }>;
  rebalanceHistory?: RebalanceEvent[];
}

// 색상 팔레트
const COLORS = [
  '#6366f1', // indigo
  '#f97316', // orange
  '#10b981', // emerald
  '#8b5cf6', // violet
  '#f59e0b', // amber
  '#ef4444', // red
  '#06b6d4', // cyan
  '#ec4899', // pink
  '#84cc16', // lime
  '#14b8a6', // teal
];

const WeightHistoryChart: React.FC<WeightHistoryChartProps> = ({
  weightHistory,
  portfolioComposition,
  rebalanceHistory
}) => {
  const symbols = useMemo(() => {
    // portfolioComposition에서 symbol 추출 (중복 제거)
    return Array.from(new Set(portfolioComposition.map(stock => stock.symbol)));
  }, [portfolioComposition]);

  // symbol -> 표시 이름 매핑
  const symbolDisplayNames = useMemo(() => {
    const mapping: Record<string, string> = {};
    symbols.forEach(symbol => {
      mapping[symbol] = getStockDisplayName(symbol);
    });
    return mapping;
  }, [symbols]);

  const chartData = useMemo(() => {
    return weightHistory.map(point => {
      const dataPoint: Record<string, any> = {
        date: point.date,
      };
      symbols.forEach(symbol => {
        dataPoint[symbol] = ((point[symbol] as number) || 0) * 100; // 비중을 퍼센트로 변환
      });
      return dataPoint;
    });
  }, [weightHistory, symbols]);

  if (!weightHistory || weightHistory.length === 0) {
    return (
      <div className={`text-center py-12 ${TEXT_STYLES.caption}`}>
        <p>비중 변화 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400} debounce={300}>
      <AreaChart data={chartData} syncId="weightHistoryChart">
        <defs>
          {symbols.map((symbol, index) => (
            <linearGradient key={symbol} id={`color${index}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0.8} />
              <stop offset="95%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0.1} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          tickFormatter={(value: string) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()}`;
          }}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(value: number) => `${value.toFixed(0)}%`}
          domain={[0, 100]}
        />
        <Tooltip
          formatter={(value: number, name: string) => [`${value.toFixed(2)}%`, symbolDisplayNames[name] || name]}
          labelFormatter={(label: string) => `날짜: ${label}`}
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #ccc',
            borderRadius: '8px',
          }}
        />
        <Legend
          wrapperStyle={{ paddingTop: '20px' }}
          iconType="square"
          formatter={(value: string) => symbolDisplayNames[value] || value}
        />
        {/* 리밸런싱 마커 */}
        {rebalanceHistory && rebalanceHistory.length > 0 && rebalanceHistory.map((event, idx) => (
          <ReferenceLine
            key={idx}
            x={event.date}
            stroke="#f97316"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: '⚖️',
              position: 'top',
              fontSize: 16,
            }}
          />
        ))}
        {symbols.map((symbol, index) => (
          <Area
            key={symbol}
            type="monotone"
            dataKey={symbol}
            stackId="1"
            stroke={COLORS[index % COLORS.length]}
            fill={`url(#color${index})`}
            strokeWidth={2}
            isAnimationActive={false}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default WeightHistoryChart;
