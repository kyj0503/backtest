import React, { memo, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart } from 'recharts';
import { 
  ChartData, 
  PortfolioData
} from '../../types/backtest-results';

interface EnhancedChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const EnhancedChartsSection: React.FC<EnhancedChartsSectionProps> = memo(({ data, isPortfolio }) => {
  // 화폐 포맷터 함수 메모이제이션
  const formatCurrency = useMemo(() => (value: number): string => {
    if (value >= 1e9) {
      return `${(value / 1e9).toFixed(1)}B`;
    } else if (value >= 1e6) {
      return `${(value / 1e6).toFixed(1)}M`;
    } else if (value >= 1e3) {
      return `${(value / 1e3).toFixed(1)}K`;
    }
    return value.toLocaleString();
  }, []);

  // 환율 데이터 차트
  const renderExchangeRateChart = () => {
    const exchangeRates = (data as any).exchange_rates;
    if (!exchangeRates || exchangeRates.length === 0) {
      return null;
    }

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h5 className="text-lg font-semibold">원/달러 환율</h5>
          <p className="text-sm text-gray-600">백테스트 기간 동안의 원달러 환율 변화</p>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={exchangeRates}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value: any) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value: number) => `₩${value.toFixed(0)}`}
              />
              <Tooltip 
                formatter={(value: number) => [`₩${value.toFixed(2)}`, '환율']}
                labelFormatter={(label: any) => `날짜: ${label}`}
              />
              <Line 
                type="monotone" 
                dataKey="rate" 
                stroke="#10b981" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  // S&P 500 벤치마크 차트
  const renderSP500BenchmarkChart = () => {
    const sp500Data = (data as any).sp500_benchmark;
    if (!sp500Data || sp500Data.length === 0) {
      return null;
    }

    // 수익률 계산
    const benchmarkWithReturns = sp500Data.map((item: any, index: number) => {
      if (index === 0) {
        return { ...item, return_pct: 0 };
      }
      const prevClose = sp500Data[index - 1].close;
      const returnPct = ((item.close - prevClose) / prevClose) * 100;
      return { ...item, return_pct: returnPct };
    });

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h5 className="text-lg font-semibold">S&P 500 지수</h5>
          <p className="text-sm text-gray-600">동기간 S&P 500 지수 변화 (벤치마크)</p>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={benchmarkWithReturns}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value: any) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis yAxisId="left" orientation="left" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
              <Tooltip 
                formatter={(value: number, name: string) => {
                  if (name === 'close') return [value.toFixed(2), 'S&P 500'];
                  if (name === 'return_pct') return [`${value.toFixed(2)}%`, '일일 수익률'];
                  return [value, name];
                }}
                labelFormatter={(label: any) => `날짜: ${label}`}
              />
              <Area 
                yAxisId="left"
                type="monotone" 
                dataKey="close" 
                stroke="#3b82f6" 
                fill="#3b82f6"
                fillOpacity={0.1}
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="return_pct" 
                stroke="#ef4444" 
                strokeWidth={1}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  // 나스닥 벤치마크 차트
  const renderNasdaqBenchmarkChart = () => {
    const nasdaqData = (data as any).nasdaq_benchmark;
    if (!nasdaqData || nasdaqData.length === 0) {
      return null;
    }

    // 수익률 계산
    const benchmarkWithReturns = nasdaqData.map((item: any, index: number) => {
      if (index === 0) {
        return { ...item, return_pct: 0 };
      }
      const prevClose = nasdaqData[index - 1].close;
      const returnPct = ((item.close - prevClose) / prevClose) * 100;
      return { ...item, return_pct: returnPct };
    });

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h5 className="text-lg font-semibold">나스닥 지수</h5>
          <p className="text-sm text-gray-600">동기간 나스닥 지수 변화 (벤치마크)</p>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={benchmarkWithReturns}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value: any) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis yAxisId="left" orientation="left" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
              <Tooltip 
                formatter={(value: number, name: string) => {
                  if (name === 'close') return [value.toFixed(2), '나스닥'];
                  if (name === 'return_pct') return [`${value.toFixed(2)}%`, '일일 수익률'];
                  return [value, name];
                }}
                labelFormatter={(label: any) => `날짜: ${label}`}
              />
              <Area 
                yAxisId="left"
                type="monotone" 
                dataKey="close" 
                stroke="#8b5cf6" 
                fill="#8b5cf6"
                fillOpacity={0.1}
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="return_pct" 
                stroke="#f59e0b" 
                strokeWidth={1}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  // 거래 신호 차트 (단일 종목용)
  const renderTradeSignalsChart = () => {
    if (isPortfolio) return null;
    
    const chartData = data as ChartData;
    const tradeMarkers = chartData.trade_markers || [];
    const ohlcData = chartData.ohlc_data || [];

    if (tradeMarkers.length === 0 || ohlcData.length === 0) {
      return null;
    }

    // OHLC 데이터에 거래 신호 추가
    const dataWithSignals = ohlcData.map(item => {
      const buySignal = tradeMarkers.find(trade => 
        trade.date === item.date && trade.type === 'entry'
      );
      const sellSignal = tradeMarkers.find(trade => 
        trade.date === item.date && trade.type === 'exit'
      );

      return {
        ...item,
        buySignal: buySignal ? buySignal.price : null,
        sellSignal: sellSignal ? sellSignal.price : null
      };
    });

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h5 className="text-lg font-semibold">매매 신호</h5>
          <p className="text-sm text-gray-600">백테스트 전략의 매수/매도 신호 ({tradeMarkers.length}개 거래)</p>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={dataWithSignals}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value: any) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                formatter={(value: number, name: string) => {
                  if (name === 'close') return [`$${value.toFixed(2)}`, '종가'];
                  if (name === 'buySignal') return [`$${value.toFixed(2)}`, '매수 신호'];
                  if (name === 'sellSignal') return [`$${value.toFixed(2)}`, '매도 신호'];
                  return [value, name];
                }}
                labelFormatter={(label: any) => `날짜: ${label}`}
              />
              <Line 
                type="monotone" 
                dataKey="close" 
                stroke="#6b7280" 
                strokeWidth={1}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="buySignal" 
                stroke="#10b981" 
                strokeWidth={0}
                dot={{ r: 6, fill: '#10b981' }}
              />
              <Line 
                type="monotone" 
                dataKey="sellSignal" 
                stroke="#ef4444" 
                strokeWidth={0}
                dot={{ r: 6, fill: '#ef4444' }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* 환율 데이터 */}
      {renderExchangeRateChart()}

      {/* 벤치마크 데이터 */}
      {renderSP500BenchmarkChart()}
      {renderNasdaqBenchmarkChart()}

      {/* 매매 신호 차트 (단일 종목만) */}
      {renderTradeSignalsChart()}
    </div>
  );
});

EnhancedChartsSection.displayName = 'EnhancedChartsSection';

export default EnhancedChartsSection;