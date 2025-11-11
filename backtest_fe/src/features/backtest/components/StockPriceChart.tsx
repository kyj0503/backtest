import React, { useState, memo, useMemo } from "react";
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter } from "recharts";
import { useRenderPerformance } from "@/shared/components";
import StockSymbolSelector from './results/StockSymbolSelector';
import { formatPriceWithCurrency } from "@/shared/lib/utils/numberUtils";
import { TickerInfo } from '../model/types/backtest-result-types';

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
  Type?: 'BUY' | 'SELL';  // 거래 타입 (리밸런싱용)
  PnL?: number;
  ReturnPct?: number;
}

interface StockPriceChartProps {
  stocksData: StockData[];
  tickerInfo?: { [symbol: string]: TickerInfo };
  tradeLogs?: Record<string, TradeLog[]>;
  aggregationType?: 'daily' | 'weekly' | 'monthly';
  className?: string;
}

// aggregation된 데이터에서 실제 거래 날짜에 가장 가까운 날짜를 찾는 함수
const findClosestAggregationDate = (
  tradeDate: string, 
  aggregatedData: Array<{ date: string; price: number }>, 
  aggregationType: 'daily' | 'weekly' | 'monthly'
): string | null => {
  const tradeDateTime = new Date(tradeDate).getTime();
  
  // daily aggregation이면 정확히 일치하는 날짜만 찾음
  if (aggregationType === 'daily') {
    const exactMatch = aggregatedData.find(d => d.date === tradeDate);
    return exactMatch ? tradeDate : null;
  }
  
  // weekly/monthly aggregation이면 기간 내에 포함되는 날짜 찾음
  for (const dataPoint of aggregatedData) {
    if (aggregationType === 'weekly') {
      // 주간 데이터: 해당 주의 마지막 날짜를 사용
      // 거래일이 해당 aggregation 기간 내에 있는지 확인
      const dataDate = new Date(dataPoint.date);
      const tradeDateObj = new Date(tradeDate);
      
      // 간단한 방법: 거래일이 aggregation 날짜와 같은 주에 있는지 확인
      const dataWeek = Math.floor(dataDate.getTime() / (7 * 24 * 60 * 60 * 1000));
      const tradeWeek = Math.floor(tradeDateObj.getTime() / (7 * 24 * 60 * 60 * 1000));
      
      if (dataWeek === tradeWeek) {
        return dataPoint.date;
      }
    } else if (aggregationType === 'monthly') {
      // 월간 데이터: 해당 월의 마지막 날짜를 사용
      const tradeMonth = new Date(tradeDate).getMonth();
      const tradeYear = new Date(tradeDate).getFullYear();
      const dataMonth = new Date(dataPoint.date).getMonth();
      const dataYear = new Date(dataPoint.date).getFullYear();
      
      if (tradeYear === dataYear && tradeMonth === dataMonth) {
        return dataPoint.date;
      }
    }
  }
  
  // 정확히 일치하지 않으면 가장 가까운 날짜 찾음 (fallback)
  let closestDate: string | null = null;
  let minDiff = Infinity;
  
  for (const dataPoint of aggregatedData) {
    const dataDateTime = new Date(dataPoint.date).getTime();
    const diff = Math.abs(dataDateTime - tradeDateTime);
    
    if (diff < minDiff) {
      minDiff = diff;
      closestDate = dataPoint.date;
    }
  }
  
  return closestDate;
};

const StockPriceChart: React.FC<StockPriceChartProps> = memo(({ stocksData, tickerInfo = {}, tradeLogs = {}, aggregationType = 'daily', className = "" }) => {
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

    // 날짜별 매매 신호 세트 생성 (날짜만 저장)
    const buyDates = new Set<string>();
    const sellDates = new Set<string>();

    logs.forEach((trade) => {
      // 실제 거래 날짜 추출
      let tradeDates: string[] = [];
      
      if (trade.Type) {
        // Type 필드가 있으면 (리밸런싱, DCA 등)
        if (trade.EntryTime) {
          const entryDate = trade.EntryTime.split('T')[0].split(' ')[0];
          tradeDates.push(entryDate);
        }
      } else {
        // 기존 로직 (하위 호환성)
        if (trade.EntryTime) {
          const entryDate = trade.EntryTime.split('T')[0].split(' ')[0];
          tradeDates.push(entryDate);
        }
        if (trade.ExitTime) {
          const exitDate = trade.ExitTime.split('T')[0].split(' ')[0];
          tradeDates.push(exitDate);
        }
      }

      // 각 거래 날짜를 aggregation된 데이터의 날짜에 매핑
      tradeDates.forEach(tradeDate => {
        const mappedDate = findClosestAggregationDate(tradeDate, selectedStockData.data, aggregationType);
        if (mappedDate) {
          if (trade.Type === 'BUY' || (!trade.Type && trade.EntryTime)) {
            buyDates.add(mappedDate);
          } else if (trade.Type === 'SELL' || (!trade.Type && trade.ExitTime)) {
            sellDates.add(mappedDate);
          }
        }
      });
    });

    // 주가 데이터에 매매 신호 merge (해당 날짜의 실제 주가를 사용)
    const mergedData = selectedStockData.data.map(point => ({
      ...point,
      buySignal: buyDates.has(point.date) ? point.price : undefined,
      sellSignal: sellDates.has(point.date) ? point.price : undefined,
    }));

    return mergedData;
  }, [selectedSymbol, selectedStockData, tradeLogs, aggregationType]);

  // Y축 도메인 계산 (메모이제이션)
  const yAxisDomain = useMemo<[number, number]>(() => {
    const prices = chartDataWithSignals
      .map((d: any) => d.price)
      .filter((price): price is number => typeof price === 'number' && !isNaN(price));
    
    if (prices.length === 0) return [0, 100];
    
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    
    return [minPrice, maxPrice];
  }, [chartDataWithSignals]);

  // 매매 횟수 계산
  const tradeCount = useMemo(() => {
    const logs = tradeLogs[selectedSymbol];
    if (!logs || !Array.isArray(logs)) return { buys: 0, sells: 0 };

    let buys = 0;
    let sells = 0;

    logs.forEach(t => {
      // Type 필드가 있으면 타입으로 카운트
      if (t.Type) {
        if (t.Type === 'BUY') buys++;
        if (t.Type === 'SELL') sells++;
      } else {
        // Type 필드가 없으면 기존 로직 (하위 호환성)
        if (t.EntryTime && t.EntryPrice) buys++;
        if (t.ExitTime && t.ExitPrice) sells++;
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
            <ResponsiveContainer debounce={300}>
              <ComposedChart 
                data={chartDataWithSignals} 
                syncId="stockPriceChart"
                margin={{ top: 5, right: 20, left: 10, bottom: typeof window !== 'undefined' && window.innerWidth < 640 ? 60 : 30 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={{ fontSize: 11 }}
                  interval={Math.max(1, Math.floor(chartDataWithSignals.length / (typeof window !== 'undefined' && window.innerWidth < 640 ? 4 : 8)))}
                  angle={typeof window !== 'undefined' && window.innerWidth < 640 ? -45 : 0}
                  textAnchor={typeof window !== 'undefined' && window.innerWidth < 640 ? 'end' : 'middle'}
                />
                <YAxis
                  tickFormatter={formatPrice}
                  domain={yAxisDomain}
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
                  connectNulls={true}
                />
                {/* 매수 신호 (빨간점) */}
                <Scatter
                  name="매수"
                  dataKey="buySignal"
                  fill="#ef4444"
                  shape="circle"
                  isAnimationActive={false}
                  r={8}
                />
                {/* 매도 신호 (파란점) */}
                <Scatter
                  name="매도"
                  dataKey="sellSignal"
                  fill="#3b82f6"
                  shape="circle"
                  isAnimationActive={false}
                  r={8}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* 차트 하단 정보 */}
          <div className="flex flex-col gap-2">
            {/* 윗줄: 시작/종료/데이터 포인트 */}
            <div className="text-center">
              <small className="text-muted-foreground">
                시작: {selectedStockData.data[0]?.date} | 
                종료: {selectedStockData.data[selectedStockData.data.length - 1]?.date} | 
                데이터 포인트: {selectedStockData.data.length}개
              </small>
            </div>
            
            {/* 아랫줄: 매수/매도 횟수 (거래가 있는 경우에만) */}
            {(tradeCount.buys > 0 || tradeCount.sells > 0) && (
              <div className="text-center">
                <small className="text-muted-foreground">
                  <span className="text-red-500">● 매수: {tradeCount.buys}회</span>
                  {' | '}
                  <span className="text-blue-500">● 매도: {tradeCount.sells}회</span>
                </small>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
});

StockPriceChart.displayName = 'StockPriceChart';

export default StockPriceChart;
