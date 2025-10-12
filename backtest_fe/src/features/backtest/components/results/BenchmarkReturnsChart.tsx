/**
 * 벤치마크 일일 수익률 차트 컴포넌트
 * 
 * **역할**:
 * - S&P 500과 NASDAQ 일일 수익률을 별도 박스에 표시
 * - 버튼으로 S&P/NASDAQ 전환
 */
import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Button } from '@/shared/ui/button';

interface BenchmarkReturnsChartProps {
  sp500Data: any[];
  nasdaqData: any[];
}

const BenchmarkReturnsChart: React.FC<BenchmarkReturnsChartProps> = ({
  sp500Data,
  nasdaqData,
}) => {
  const [selectedIndex, setSelectedIndex] = useState<'sp500' | 'nasdaq'>('sp500');

  const currentData = selectedIndex === 'sp500' ? sp500Data : nasdaqData;
  const hasData = currentData && currentData.length > 0;

  const formatDateTick = (value: string) => {
    const date = new Date(value);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  if (!hasData && sp500Data.length === 0 && nasdaqData.length === 0) return null;

  return (
    <div className="space-y-3 rounded-2xl border border-border/40 bg-card/30 p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">일일 수익률 벤치마크</h3>
          <p className="text-sm text-muted-foreground">
            S&P 500과 NASDAQ 일일 수익률 비교
          </p>
        </div>
        <div className="flex gap-2">
          {sp500Data.length > 0 && (
            <Button
              variant={selectedIndex === 'sp500' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedIndex('sp500')}
            >
              S&P 500
            </Button>
          )}
          {nasdaqData.length > 0 && (
            <Button
              variant={selectedIndex === 'nasdaq' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedIndex('nasdaq')}
            >
              NASDAQ
            </Button>
          )}
        </div>
      </div>

      {hasData ? (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={currentData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDateTick} />
            <YAxis tickFormatter={(value: number) => `${value.toFixed(1)}%`} />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
              labelFormatter={(label: string) => `날짜: ${label}`}
            />
            <Line type="monotone" dataKey="return_pct" stroke="#ef4444" strokeWidth={1.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="text-center py-8 text-muted-foreground">
          선택한 지수의 데이터가 없습니다.
        </div>
      )}
    </div>
  );
};

export default BenchmarkReturnsChart;
