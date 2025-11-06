import React, { useState, memo, useMemo } from "react";
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter } from "recharts";
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

  // 선택된 종목의 매매 신호를 주가 데이터에 merge
  const chartDataWithSignals = useMemo(() => {
    if (!selectedStockData) return [];

    const logs = tradeLogs[selectedSymbol];
    if (!logs || !Array.isArray(logs)) {
      return selectedStockData.data.map(d => ({ ...d }));
    }

    console.log('🔍 [StockPriceChart] Processing trades for', selectedSymbol);
    console.log('🔍 [StockPriceChart] Trade logs:', logs);
    console.log('🔍 [StockPriceChart] First stock data point:', selectedStockData.data[0]);

    // 날짜별 매매 신호 세트 생성 (날짜만 저장)
    const buyDates = new Set<string>();
    const sellDates = new Set<string>();

    logs.forEach((trade, index) => {
      console.log(`📝 [Trade ${index + 1}]`, trade);

      if (trade.EntryTime) {
        // ISO 8601 형식 처리: "2020-01-06T00:00:00" → "2020-01-06"
        const entryDate = trade.EntryTime.split('T')[0].split(' ')[0];
        buyDates.add(entryDate);
        console.log(`  ✅ Buy date: ${entryDate}`);
      }
      if (trade.ExitTime) {
        // ISO 8601 형식 처리: "2020-01-06T00:00:00" → "2020-01-06"
        const exitDate = trade.ExitTime.split('T')[0].split(' ')[0];
        sellDates.add(exitDate);
        console.log(`  ✅ Sell date: ${exitDate}`);
      }
    });

    console.log('📊 [StockPriceChart] Buy dates:', Array.from(buyDates));
    console.log('📊 [StockPriceChart] Sell dates:', Array.from(sellDates));
    console.log('📊 [StockPriceChart] stock data dates (first 5):', selectedStockData.data.slice(0, 5).map(d => d.date));

    // 주가 데이터에 매매 신호 merge (해당 날짜의 실제 주가를 사용)
    const mergedData = selectedStockData.data.map(point => ({
      ...point,
      buySignal: buyDates.has(point.date) ? point.price : undefined,
      sellSignal: sellDates.has(point.date) ? point.price : undefined,
    }));

    // 디버깅: 매매 신호가 있는 데이터만 필터링해서 출력
    const signalPoints = mergedData.filter(d => d.buySignal || d.sellSignal);
    console.log('📍 [StockPriceChart] Signal points count:', signalPoints.length);
    console.log('📍 [StockPriceChart] Signal points:', signalPoints);

    return mergedData;
  }, [selectedSymbol, selectedStockData, tradeLogs]);

  // 매매 횟수 계산
  const tradeCount = useMemo(() => {
    const logs = tradeLogs[selectedSymbol];
    if (!logs || !Array.isArray(logs)) return { buys: 0, sells: 0 };

    const buys = logs.filter(t => t.EntryTime && t.EntryPrice).length;
    const sells = logs.filter(t => t.ExitTime && t.ExitPrice).length;

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
              <ComposedChart data={chartDataWithSignals}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={{ fontSize: 12 }}
                  interval={Math.max(1, Math.floor(chartDataWithSignals.length / 8))}
                />
                <YAxis
                  tickFormatter={formatPrice}
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  labelFormatter={(label: any) => `날짜: ${label}`}
                  formatter={(value: any, name: string) => {
                    if (!value) return null;
                    if (name === 'price') return [formatPrice(value), '주가'];
                    if (name === 'buySignal') return [formatPrice(value), '매수'];
                    if (name === 'sellSignal') return [formatPrice(value), '매도'];
                    return [value, name];
                  }}
                />
                {/* 주가 라인 */}
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 6 }}
                  isAnimationActive={false}
                />
                {/* 매수 신호 (파란점) */}
                <Scatter
                  name="매수"
                  dataKey="buySignal"
                  fill="#3b82f6"
                  shape="circle"
                  isAnimationActive={false}
                  r={8}
                />
                {/* 매도 신호 (빨간점) */}
                <Scatter
                  name="매도"
                  dataKey="sellSignal"
                  fill="#ef4444"
                  shape="circle"
                  isAnimationActive={false}
                  r={8}
                />
              </ComposedChart>
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
            {tradeCount.buys > 0 || tradeCount.sells > 0 ? (
              <div className="text-left md:text-right">
                <small className="text-muted-foreground">
                  <span className="text-blue-500">● 매수: {tradeCount.buys}회</span>
                  {' | '}
                  <span className="text-red-500">● 매도: {tradeCount.sells}회</span>
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
