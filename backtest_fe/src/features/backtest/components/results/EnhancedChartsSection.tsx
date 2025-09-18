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
} from '../../model/backtest-result-types';
import { FormLegend } from '@/shared/components';

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

  const FeatureBlock: React.FC<{
    title: string;
    description?: string;
    actions?: React.ReactNode;
    children: React.ReactNode;
  }> = ({ title, description, actions, children }) => (
    <div className="space-y-3 rounded-2xl border border-border/40 bg-card/30 p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
          {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
      <div>{children}</div>
    </div>
  );

  const sections: Array<{ key: string; node: React.ReactNode; fullWidth?: boolean }> = [];

  if (exchangeRates && exchangeRates.length > 0) {
    sections.push({
      key: 'exchange',
      node: (
        <FeatureBlock
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
        </FeatureBlock>
      ),
    });
  }

  const addBenchmarkSection = (key: string, title: string, points?: BenchmarkPoint[]) => {
    if (!points || !points.length) return;
    sections.push({
      key,
      node: (
        <FeatureBlock
          title={title}
          description="지수 수준과 일일 수익률을 함께 확인하세요"
          actions={<FormLegend items={[{ label: '좌측: 지수 · 우측: 일일 수익률', tone: 'muted' }]} />}
        >
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={withBenchmarkReturn(points)}>
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
              <Area yAxisId="left" type="monotone" dataKey="close" stroke="#3b82f6" fillOpacity={0.15} fill="#3b82f6" />
              <Line yAxisId="right" type="monotone" dataKey="return_pct" stroke="#ef4444" strokeWidth={1.5} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </FeatureBlock>
      ),
    });
  };

  addBenchmarkSection('sp500', 'S&P 500 벤치마크', sp500Benchmark);
  addBenchmarkSection('nasdaq', 'NASDAQ 벤치마크', nasdaqBenchmark);

  if (!isPortfolio && tradeMarkers?.length && ohlcData?.length) {
    const dataWithSignals = ohlcData.map(item => {
      const buySignal = tradeMarkers.find(trade => trade.date === item.date && trade.type === 'entry');
      const sellSignal = tradeMarkers.find(trade => trade.date === item.date && trade.type === 'exit');
      return {
        ...item,
        buySignal: buySignal ? buySignal.price : undefined,
        sellSignal: sellSignal ? sellSignal.price : undefined,
      };
    });

    sections.push({
      key: 'trade-signals',
      fullWidth: true,
      node: (
        <FeatureBlock
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
              <Line type="monotone" dataKey="buySignal" stroke="#10b981" strokeWidth={0} dot={{ r: 5, fill: '#10b981' }} />
              <Line type="monotone" dataKey="sellSignal" stroke="#ef4444" strokeWidth={0} dot={{ r: 5, fill: '#ef4444' }} />
            </ComposedChart>
          </ResponsiveContainer>
        </FeatureBlock>
      ),
    });
  }

  if (!sections.length) return null;

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      {sections.map(({ key, node, fullWidth }) => (
        <div key={key} className={fullWidth ? 'xl:col-span-2' : undefined}>
          {node}
        </div>
      ))}
    </div>
  );
});

EnhancedChartsSection.displayName = 'EnhancedChartsSection';

export default EnhancedChartsSection;
