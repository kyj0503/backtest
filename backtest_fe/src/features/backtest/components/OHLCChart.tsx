import React, { memo, useMemo, useCallback } from 'react';
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

interface OHLCData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  [key: string]: any;
}

interface Indicator {
  name: string;
  color: string;
  data?: Array<{ date: string; value: number }>;
}

interface Trade {
  date: string;
  type: 'entry' | 'exit';
  price?: number;
}

interface OHLCChartProps {
  data: OHLCData[];
  indicators: Indicator[];
  trades: Trade[];
}

const OHLCChart: React.FC<OHLCChartProps> = memo(({ data, indicators, trades }) => {
  // 데이터 안전성 검사 및 메모이제이션
  const safeData = useMemo(() => data || [], [data]);
  const safeIndicators = useMemo(() => indicators || [], [indicators]);
  const safeTrades = useMemo(() => trades || [], [trades]);

  // 데이터 병합 로직 메모이제이션
  const mergedData = useMemo(() => {
    return safeData.map(ohlc => {
      const point: any = { 
        ...ohlc,
        open: Number(ohlc.open) || 0,
        high: Number(ohlc.high) || 0,
        low: Number(ohlc.low) || 0,
        close: Number(ohlc.close) || 0,
        volume: Number(ohlc.volume) || 0
      };
      
      safeIndicators.forEach(indicator => {
        const indicatorPoint = indicator.data?.find((d: any) => d.date === ohlc.date);
        if (indicatorPoint) {
          point[indicator.name] = Number(indicatorPoint.value) || 0;
        }
      });
      return point;
    });
  }, [safeData, safeIndicators]);

  // 차트 설정 메모이제이션
  const chartConfig = useMemo(() => ({
    margin: { top: 20, right: 30, left: 20, bottom: 5 },
    strokeWidth: {
      main: 2,
      indicator: 1.5
    },
    opacity: {
      volume: 0.3,
      grid: 0.3
    }
  }), []);

  // 인디케이터 라인 렌더링 콜백 메모이제이션
  const renderIndicatorLines = useCallback(() => {
    return safeIndicators.map((indicator, index) => (
      <Line
        key={indicator.name}
        yAxisId="price"
        type="monotone"
        dataKey={indicator.name}
        stroke={indicator.color}
        strokeWidth={chartConfig.strokeWidth.indicator}
        dot={false}
        name={indicator.name}
        strokeDasharray={index % 2 === 1 ? '5 5' : undefined}
      />
    ));
  }, [safeIndicators, chartConfig.strokeWidth.indicator]);

  // 거래 마크 렌더링 콜백 메모이제이션
  const renderTradeMarks = useCallback(() => {
    return safeTrades.map((trade, index) => (
      <ReferenceLine
        key={`${trade.date}-${index}`}
        yAxisId="price"
        x={trade.date}
        stroke={trade.type === 'entry' ? '#198754' : '#dc3545'}
        strokeWidth={2}
        strokeDasharray="2 2"
      />
    ));
  }, [safeTrades]);

  return (
    <div>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={mergedData} margin={chartConfig.margin}>
          <CartesianGrid strokeDasharray="3 3" opacity={chartConfig.opacity.grid} />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
          <YAxis yAxisId="price" orientation="right" />
          <YAxis yAxisId="volume" orientation="left" />
          <RechartsTooltip content={<CustomTooltip />} />
          <Legend />
          <Bar 
            yAxisId="volume" 
            dataKey="volume" 
            fill="#6c757d" 
            opacity={chartConfig.opacity.volume} 
            name="거래량" 
          />
          <Line 
            yAxisId="price" 
            type="monotone" 
            dataKey="close" 
            stroke="#0d6efd" 
            strokeWidth={chartConfig.strokeWidth.main} 
            dot={false} 
            name="종가" 
          />
          {renderIndicatorLines()}
          {renderTradeMarks()}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
});

OHLCChart.displayName = 'OHLCChart';

export default OHLCChart;
