import React, { useState, memo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useRenderPerformance } from "@/shared/components/PerformanceMonitor";
import StockSymbolSelector from './results/StockSymbolSelector';
import { formatPriceWithCurrency } from "@/shared/lib/utils/numberUtils";
import { TickerInfo } from '../model/backtest-result-types';

interface StockData {
  symbol: string;
  data: Array<{
    date: string;
    price: number;
    volume?: number;
  }>;
}

interface StockPriceChartProps {
  stocksData: StockData[];
  tickerInfo?: { [symbol: string]: TickerInfo };
  className?: string;
}

const StockPriceChart: React.FC<StockPriceChartProps> = memo(({ stocksData, tickerInfo = {}, className = "" }) => {
  // 성능 모니터링
  useRenderPerformance('StockPriceChart');

  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => stocksData[0]?.symbol || '');

  // 선택된 종목의 데이터 찾기
  const selectedStockData = stocksData.find(stock => stock.symbol === selectedSymbol);

  if (!stocksData || stocksData.length === 0) {
    return (
      <div className={`bg-card border border-border rounded-lg shadow-sm ${className}`}>
        <div className="px-6 py-4 text-center">
          <p className="text-muted-foreground">표시할 주가 데이터가 없습니다.</p>
        </div>
      </div>
    );
  }

  // 날짜 포맷팅 함수
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
  };

  // 가격 포맷팅 함수
  const formatPrice = (value: number) => {
    return formatPriceWithCurrency(value, tickerInfo[selectedSymbol]?.currency || 'USD');
  };

  return (
    <div className={className}>
      {/* 종목 선택 버튼들 */}
      <StockSymbolSelector
        symbols={stocksData.map(s => s.symbol)}
        selectedSymbol={selectedSymbol}
        onSelectSymbol={setSelectedSymbol}
        className="mb-4"
      />

      {/* 차트 */}
      {selectedStockData && (
        <>
          <div style={{ width: '100%', height: '400px' }}>
            <ResponsiveContainer>
              <LineChart data={selectedStockData.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={{ fontSize: 12 }}
                  interval={Math.max(1, Math.floor(selectedStockData.data.length / 8))}
                />
                <YAxis
                  tickFormatter={formatPrice}
                  domain={['dataMin - 5', 'dataMax + 5']}
                />
                <Tooltip
                  labelFormatter={(label: any) => `날짜: ${label}`}
                  formatter={(value: number) => [formatPrice(value), '주가']}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 차트 하단 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
            <div>
              <small className="text-muted-foreground">
                시작: {selectedStockData.data[0]?.date} |
                종료: {selectedStockData.data[selectedStockData.data.length - 1]?.date}
              </small>
            </div>
            <div className="text-left md:text-right">
              <small className="text-muted-foreground">
                데이터 포인트: {selectedStockData.data.length}개
              </small>
            </div>
          </div>
        </>
      )}
    </div>
  );
});

StockPriceChart.displayName = 'StockPriceChart';

export default StockPriceChart;
