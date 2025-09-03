import React from 'react';
import {
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Bar,
  Line,
  ReferenceLine
} from 'recharts';
import CustomTooltip from './CustomTooltip';

const OHLCChart: React.FC<{ data: any[]; indicators: any[]; trades: any[] }> = ({ data, indicators, trades }) => {
  const safeData = data || [];
  const safeIndicators = indicators || [];
  const safeTrades = trades || [];

  const mergedData = safeData.map(ohlc => {
    const point: any = { ...ohlc };
    safeIndicators.forEach(indicator => {
      const indicatorPoint = indicator.data?.find((d: any) => d.date === ohlc.date);
      if (indicatorPoint) {
        point[indicator.name] = indicatorPoint.value;
      }
    });
    return point;
  });

  return (
    <div>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={mergedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
          <YAxis yAxisId="price" orientation="right" />
          <YAxis yAxisId="volume" orientation="left" />
          <RechartsTooltip content={<CustomTooltip />} />
          <Legend />
          <Bar yAxisId="volume" dataKey="volume" fill="#6c757d" opacity={0.3} name="거래량" />
          <Line yAxisId="price" type="monotone" dataKey="close" stroke="#0d6efd" strokeWidth={2} dot={false} name="종가" />
          {safeIndicators.map((indicator, index) => (
            <Line
              key={indicator.name}
              yAxisId="price"
              type="monotone"
              dataKey={indicator.name}
              stroke={indicator.color}
              strokeWidth={1.5}
              dot={false}
              name={indicator.name}
              strokeDasharray={index % 2 === 1 ? '5 5' : undefined}
            />
          ))}
          {safeTrades.map((trade, index) => (
            <ReferenceLine
              key={index}
              yAxisId="price"
              x={trade.date}
              stroke={trade.type === 'entry' ? '#198754' : '#dc3545'}
              strokeWidth={2}
              strokeDasharray="2 2"
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default OHLCChart;
