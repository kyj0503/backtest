import React, { useState, memo, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter, ScatterChart } from "recharts";
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

interface TradeLog {
  EntryTime: string;
  ExitTime?: string;
  EntryPrice: number;
  ExitPrice?: number;
  Size: number;
  PnL?: number;
  ReturnPct?: number;
}

interface StockPriceChartProps {
  stocksData: StockData[];
  tickerInfo?: { [symbol: string]: TickerInfo };
  tradeLogs?: Record<string, TradeLog[]>;
  className?: string;
}

const StockPriceChart: React.FC<StockPriceChartProps> = memo(({ stocksData, tickerInfo = {}, tradeLogs = {}, className = "" }) => {
  // 성능 모니터링
  useRenderPerformance('StockPriceChart');

  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => stocksData[0]?.symbol || '');

  // 선택된 종목의 데이터 찾기
  const selectedStockData = stocksData.find(stock => stock.symbol === selectedSymbol);

  // 선택된 종목의 매매 신호 생성
  const tradeSignals = useMemo(() => {
    const logs = tradeLogs[selectedSymbol];
    if (!logs || !Array.isArray(logs)) return { buys: [], sells: [] };

    const buys: Array<{ date: string; price: number }> = [];
    const sells: Array<{ date: string; price: number }> = [];

    logs.forEach((trade) => {
      // 매수 신호
      if (trade.EntryTime && trade.EntryPrice) {
        const entryDate = trade.EntryTime.split(' ')[0]; // "2025-01-02 00:00:00" → "2025-01-02"
        buys.push({ date: entryDate, price: trade.EntryPrice });
      }

      // 매도 신호
      if (trade.ExitTime && trade.ExitPrice) {
        const exitDate = trade.ExitTime.split(' ')[0];
        sells.push({ date: exitDate, price: trade.ExitPrice });
      }
    });

    return { buys, sells };
  }, [selectedSymbol, tradeLogs]);

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
                {/* 매수 신호 (파란점) */}
                <Scatter
                  data={tradeSignals.buys}
                  fill="#3b82f6"
                  shape="circle"
                />
                {/* 매도 신호 (빨간점) */}
                <Scatter
                  data={tradeSignals.sells}
                  fill="#ef4444"
                  shape="circle"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 차트 하단 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
            <div>
              <small className="text-muted-foreground">
                시작: {selectedStockData.data[0]?.date} |
                종료: {selectedStockData.data[selectedStockData.data.length - 1]?.date}
              </small>
            </div>
            <div className="text-left md:text-center">
              <small className="text-muted-foreground">
                데이터 포인트: {selectedStockData.data.length}개
              </small>
            </div>
            {tradeSignals.buys.length > 0 || tradeSignals.sells.length > 0 ? (
              <div className="text-left md:text-right">
                <small className="text-muted-foreground">
                  <span className="text-blue-500">● 매수: {tradeSignals.buys.length}회</span>
                  {' | '}
                  <span className="text-red-500">● 매도: {tradeSignals.sells.length}회</span>
                </small>
              </div>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
});

StockPriceChart.displayName = 'StockPriceChart';

export default StockPriceChart;
