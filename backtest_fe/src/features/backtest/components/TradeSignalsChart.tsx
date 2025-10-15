/**
 * 매매신호 차트 컴포넌트
 * 
 * **역할**:
 * - 백테스트 거래 내역(trade_markers)을 시각화
 * - 매수(entry) 및 매도(exit) 신호를 시간순으로 표시
 * - 각 거래의 수익률(PnL %)을 함께 표시
 * 
 * **표시 정보**:
 * - 날짜(X축): 거래 발생 시점
 * - 가격(Y축): 체결 가격
 * - 신호 타입: 매수(초록), 매도(빨강)
 * - 수익률: 매도 시 PnL % 표시
 * 
 * **사용 사례**:
 * - 전략의 매매 타이밍 분석
 * - 거래 빈도 확인
 * - 가격 대비 진입/청산 포인트 평가
 */
import React, { memo, useMemo } from 'react';
import { ResponsiveContainer, ScatterChart, CartesianGrid, XAxis, YAxis, Tooltip, Scatter, Legend } from 'recharts';
import { TradeMarker } from '../model/backtest-result-types';
import { formatPrice } from '@/shared/lib/utils/numberUtils';

interface TradeSignalsChartProps {
  trades: TradeMarker[];
}

const TradeSignalsChart: React.FC<TradeSignalsChartProps> = memo(({ trades }) => {
  // 매수 신호와 매도 신호 분리
  const { entrySignals, exitSignals } = useMemo(() => {
    const entries = trades
      .filter(t => t.type === 'entry')
      .map(t => ({
        date: t.date,
        price: t.price || 0,
        side: t.side,
        quantity: t.quantity || 0,
        type: '매수' as const,
      }));

    const exits = trades
      .filter(t => t.type === 'exit')
      .map(t => ({
        date: t.date,
        price: t.price || 0,
        side: t.side,
        quantity: t.quantity || 0,
        pnl_pct: t.pnl_pct,
        type: '매도' as const,
      }));

    return { entrySignals: entries, exitSignals: exits };
  }, [trades]);

  // 날짜 포맷터
  const formatDateTick = (value: string) => {
    const date = new Date(value);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  // 툴팁 커스텀 렌더러
  interface TooltipProps {
    active?: boolean;
    payload?: Array<{ payload: { date: string; price: number; type: string; quantity: number; pnl_pct?: number } }>;
  }

  const CustomTooltip = ({ active, payload }: TooltipProps) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg">
        <p className="font-semibold text-sm mb-1">{data.date}</p>
        <p className="text-sm">
          <span className={data.type === '매수' ? 'text-green-600' : 'text-red-600'}>
            {data.type} 신호
          </span>
        </p>
        <p className="text-sm">가격: ${formatPrice(data.price)}</p>
        <p className="text-sm">수량: {(data.quantity || 0).toFixed(2)}</p>
        {data.pnl_pct !== undefined && data.pnl_pct !== null && (
          <p className={`text-sm font-semibold ${data.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            수익률: {data.pnl_pct.toFixed(2)}%
          </p>
        )}
      </div>
    );
  };

  if (trades.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        거래 신호가 없습니다.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          type="category"
          allowDuplicatedCategory={false}
          tickFormatter={formatDateTick}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          dataKey="price"
          type="number"
          domain={['auto', 'auto']}
          tickFormatter={(value: number) => `$${formatPrice(value)}`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          verticalAlign="top"
          height={36}
          iconType="circle"
        />
        
        {/* 매수 신호 */}
        <Scatter
          name="매수 신호"
          data={entrySignals}
          fill="#10B981"
          shape="triangle"
          line={false}
        />
        
        {/* 매도 신호 */}
        <Scatter
          name="매도 신호"
          data={exitSignals}
          fill="#EF4444"
          shape="cross"
          line={false}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
});

TradeSignalsChart.displayName = 'TradeSignalsChart';

export default TradeSignalsChart;
