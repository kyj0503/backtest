import React, { memo, useMemo, useCallback } from 'react';
import { ScatterChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Scatter, Cell, ReferenceLine } from 'recharts';
import { TrendingUp } from 'lucide-react';

interface Trade {
  date: string;
  type: 'entry' | 'exit';
  pnl_pct?: number;
  price?: number;
  [key: string]: any;
}

interface TradesChartProps {
  trades: Trade[];
}

const TradesChart: React.FC<TradesChartProps> = memo(({ trades }) => {
  // 출구 거래 필터링 및 메모이제이션
  const exitTrades = useMemo(() => {
    if (!trades || !Array.isArray(trades)) return [];
    
    return trades
      .filter(t => t.type === 'exit' && t.pnl_pct !== undefined)
      .map(trade => ({
        ...trade,
        pnl_pct: Number(trade.pnl_pct) || 0
      }));
  }, [trades]);

  // 차트 설정 메모이제이션
  const chartConfig = useMemo(() => ({
    margin: { top: 20, right: 30, left: 20, bottom: 5 },
    colors: {
      positive: '#198754',
      negative: '#dc3545',
      reference: '#6c757d',
      default: '#0d6efd'
    },
    opacity: {
      grid: 0.3
    }
  }), []);

  // 셀 색상 결정 콜백 메모이제이션
  const getCellColor = useCallback((pnlPct: number) => {
    return pnlPct >= 0 ? chartConfig.colors.positive : chartConfig.colors.negative;
  }, [chartConfig.colors]);

  // 셀 렌더링 메모이제이션
  const renderCells = useCallback(() => {
    return exitTrades.map((trade, index) => (
      <Cell 
        key={`${trade.date}-${index}`} 
        fill={getCellColor(trade.pnl_pct || 0)} 
      />
    ));
  }, [exitTrades, getCellColor]);

  // 빈 데이터 처리
  if (exitTrades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <TrendingUp className="h-8 w-8 mb-2 opacity-50" />
        <p>표시할 거래 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div>
      <ResponsiveContainer width="100%" height={250}>
        <ScatterChart data={exitTrades} margin={chartConfig.margin}>
          <CartesianGrid 
            strokeDasharray="3 3" 
            opacity={chartConfig.opacity.grid} 
          />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }} 
          />
          <YAxis 
            dataKey="pnl_pct" 
            tick={{ fontSize: 12 }}
            label={{ 
              value: 'P&L (%)', 
              angle: -90, 
              position: 'insideLeft' 
            }}
          />
          <Scatter 
            dataKey="pnl_pct" 
            fill={chartConfig.colors.default}
          >
            {renderCells()}
          </Scatter>
          <ReferenceLine 
            y={0} 
            stroke={chartConfig.colors.reference} 
            strokeDasharray="2 2" 
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
});

TradesChart.displayName = 'TradesChart';

export default TradesChart;
