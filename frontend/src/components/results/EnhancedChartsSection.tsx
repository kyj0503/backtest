import React, { memo, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import {
  BenchmarkPoint,
  ChartData,
  ExchangeRatePoint,
  PortfolioData,
  TradeMarker,
  OhlcPoint,
} from '../../types/backtest-results';
import { SectionCard, FormLegend } from '../common';

interface EnhancedChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const EnhancedChartsSection: React.FC<EnhancedChartsSectionProps> = memo(({ data, isPortfolio }) => {
  const exchangeRates = useMemo<ExchangeRatePoint[] | undefined>(
    () => (data as ChartData).exchange_rates ?? (data as PortfolioData).exchange_rates,
    [data],
  );

  const sp500Benchmark = useMemo<BenchmarkPoint[] | undefined>(
    () => (data as ChartData).sp500_benchmark ?? (data as PortfolioData).sp500_benchmark,
    [data],
  );

  const nasdaqBenchmark = useMemo<BenchmarkPoint[] | undefined>(
    () => (data as ChartData).nasdaq_benchmark ?? (data as PortfolioData).nasdaq_benchmark,
    [data],
  );

  const tradeMarkers = useMemo<TradeMarker[] | undefined>(
    () => (!isPortfolio ? (data as ChartData).trade_markers : undefined),
    [data, isPortfolio],
  );

  const ohlcData = useMemo<OhlcPoint[] | undefined>(
    () => (!isPortfolio ? (data as ChartData).ohlc_data : undefined),
    [data, isPortfolio],
  );

  const formatDateTick = (value: string) => {
    const date = new Date(value);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  const withBenchmarkReturn = (points?: BenchmarkPoint[]) =>
    points?.map((point, index) => {
      if (index === 0) {
        return { ...point, return_pct: 0 };
      }
      const prev = points[index - 1];
      const returnPct = ((point.close - prev.close) / prev.close) * 100;
      return { ...point, return_pct: returnPct };
    }) ?? [];

  const renderTradeSignals = () => {
    if (isPortfolio || !tradeMarkers?.length || !ohlcData?.length) return null;

    const dataWithSignals = ohlcData.map(item => {
      const buySignal = tradeMarkers.find(trade => trade.date === item.date && trade.type === 'entry');
      const sellSignal = tradeMarkers.find(trade => trade.date === item.date && trade.type === 'exit');

      return {
        ...item,
        buySignal: buySignal ? buySignal.price : undefined,
        sellSignal: sellSignal ? sellSignal.price : undefined,
      };
    });

    return (
      <SectionCard
        title="매매 신호"
        description="전략이 실행한 매수/매도 시점을 확인하세요"
        actions={<FormLegend items={[{ label: `${tradeMarkers.length}개 거래`, tone: 'accent' }]} />}
      >
        <ResponsiveContainer width="100%" height={360}>
          <ComposedChart data={dataWithSignals}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDateTick} />
            <YAxis />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (name === 'close') return [`$${value.toFixed(2)}`, '종가'];
                if (name === 'buySignal') return [`$${value?.toFixed(2)}`, '매수 신호'];
                if (name === 'sellSignal') return [`$${value?.toFixed(2)}`, '매도 신호'];
                return [value, name];
              }}
              labelFormatter={(label: string) => `날짜: ${label}`}
            />
            <Line type="monotone" dataKey="close" stroke="#6b7280" strokeWidth={1.5} dot={false} />
            <Line
              type="monotone"
              dataKey="buySignal"
              stroke="#10b981"
              strokeWidth={0}
              dot={{ r: 5, fill: '#10b981' }}
            />
            <Line
              type="monotone"
              dataKey="sellSignal"
              stroke="#ef4444"
              strokeWidth={0}
              dot={{ r: 5, fill: '#ef4444' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </SectionCard>
    );
  };

  return (
    <div className="space-y-6">
      {exchangeRates && exchangeRates.length > 0 && (
        <SectionCard
          title="환율 추이"
          description="백테스트 기간 동안의 원/달러 변동"
          actions={<FormLegend items={[{ label: `${exchangeRates.length}포인트`, tone: 'muted' }]} />}
        >
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={exchangeRates}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDateTick} />
              <YAxis tickFormatter={(value: number) => `₩${value.toFixed(0)}`} />
              <Tooltip
                formatter={(value: number) => [`₩${value.toFixed(2)}`, '환율']}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Line type="monotone" dataKey="rate" stroke="#f97316" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </SectionCard>
      )}

      {sp500Benchmark && sp500Benchmark.length > 0 && (
        <SectionCard
          title="S&P 500 벤치마크"
          description="동일 기간 S&P 500 지수 흐름"
          actions={<FormLegend items={[{ label: '좌측: 지수 · 우측: 일일 수익률', tone: 'muted' }]} />}
        >
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={withBenchmarkReturn(sp500Benchmark)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDateTick} />
              <YAxis yAxisId="left" orientation="left" />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => `${value.toFixed(1)}%`} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === 'close') return [value.toFixed(2), '지수'];
                  if (name === 'return_pct') return [`${value.toFixed(2)}%`, '일일 수익률'];
                  return [value, name];
                }}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Area yAxisId="left" type="monotone" dataKey="close" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
              <Line yAxisId="right" type="monotone" dataKey="return_pct" stroke="#ef4444" strokeWidth={1.5} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </SectionCard>
      )}

      {nasdaqBenchmark && nasdaqBenchmark.length > 0 && (
        <SectionCard
          title="NASDAQ 벤치마크"
          description="동일 기간 나스닥 지수 흐름"
          actions={<FormLegend items={[{ label: '좌측: 지수 · 우측: 일일 수익률', tone: 'muted' }]} />}
        >
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={withBenchmarkReturn(nasdaqBenchmark)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDateTick} />
              <YAxis yAxisId="left" orientation="left" />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => `${value.toFixed(1)}%`} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === 'close') return [value.toFixed(2), '지수'];
                  if (name === 'return_pct') return [`${value.toFixed(2)}%`, '일일 수익률'];
                  return [value, name];
                }}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Area yAxisId="left" type="monotone" dataKey="close" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.15} />
              <Line yAxisId="right" type="monotone" dataKey="return_pct" stroke="#f59e0b" strokeWidth={1.5} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </SectionCard>
      )}

      {renderTradeSignals()}
    </div>
  );
});

EnhancedChartsSection.displayName = 'EnhancedChartsSection';

export default EnhancedChartsSection;
