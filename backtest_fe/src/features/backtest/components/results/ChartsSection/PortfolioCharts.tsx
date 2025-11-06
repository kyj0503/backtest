/**
 * 포트폴리오 차트 컴포넌트
 * 누적 자산 가치, 일일 수익률, 개별 자산 주가 차트
 */

import React, { Suspense, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import { LazyStockPriceChart } from '../../lazy/LazyChartComponents';
import ChartLoading from '@/shared/components/ChartLoading';
import { ResultBlock } from '../../shared';
import { EquityPoint, PortfolioData } from '../../../model/types';
import { formatCurrency, formatDateShort } from '../../../utils';

interface PortfolioChartsProps {
  portfolioData: PortfolioData;
  portfolioEquityData: EquityPoint[];
  stocksData: Array<{ symbol: string; data: any[] }>;
  tickerInfo: Record<string, any>;
  tradeLogs: Record<string, any[]>;
  loadingStockData?: boolean;
}

export const PortfolioCharts: React.FC<PortfolioChartsProps> = ({
  portfolioData,
  portfolioEquityData,
  stocksData,
  tickerInfo,
  tradeLogs,
  loadingStockData = false,
}) => {
  const { portfolio_composition, rebalance_history } = portfolioData;
  const isMultipleStocks = portfolio_composition.length > 1;

  // 일일 수익률 Y축 도메인 계산 (메모이제이션)
  const dailyReturnYAxisDomain = useMemo<[number, number]>(() => {
    const returnValues = portfolioEquityData
      .map((d: any) => d.return_pct || 0)
      .filter((value): value is number => typeof value === 'number' && !isNaN(value));
    
    if (returnValues.length === 0) return [0, 100];
    
    const minValue = Math.min(...returnValues);
    const maxValue = Math.max(...returnValues);
    
    return [minValue, maxValue];
  }, [portfolioEquityData]);

  return (
    <>
      {/* 누적 자산 가치 */}
      <ResultBlock
        title="누적 자산 가치"
        description="기간 동안 누적 자산 가치 변화를 확인하세요 (리밸런싱 시점 표시)"
      >
        <ResponsiveContainer width="100%" height={360}>
          <AreaChart data={portfolioEquityData}>
            <defs>
              <linearGradient id="portfolioValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDateShort} />
            <YAxis tickFormatter={(value: number) => formatCurrency(value)} />
            <Tooltip
              formatter={(value: number) => [
                formatCurrency(value),
                isMultipleStocks ? '포트폴리오 가치' : '자산 가치',
              ]}
              labelFormatter={(label: string) => `날짜: ${label}`}
            />
            {/* 리밸런싱 마커 */}
            {rebalance_history?.map((event, idx) => (
              <ReferenceLine
                key={idx}
                x={event.date}
                stroke="#f97316"
                strokeWidth={2}
                strokeDasharray="5 5"
                label={{
                  value: '⚖️',
                  position: 'top',
                  fontSize: 16,
                }}
              />
            ))}
            <Area type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} fill="url(#portfolioValue)" />
          </AreaChart>
        </ResponsiveContainer>
      </ResultBlock>

      {/* 일일 수익률 */}
      <ResultBlock title="일일 수익률" description="일별 수익률 변동을 살펴보며 변동성을 파악하세요">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={portfolioEquityData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDateShort} />
            <YAxis 
              domain={dailyReturnYAxisDomain}
              tickFormatter={(value: number) => `${value.toFixed(1)}%`} 
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
              labelFormatter={(label: string) => `날짜: ${label}`}
            />
            <Line type="monotone" dataKey="return_pct" stroke="#f97316" strokeWidth={1.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ResultBlock>

      {/* 개별 자산 주가 */}
      <ResultBlock title="개별 자산 주가" description="포트폴리오 구성 자산들의 가격 흐름">
        {loadingStockData ? (
          <div className="flex flex-col items-center gap-3 py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">자산 데이터를 불러오는 중입니다...</p>
          </div>
        ) : stocksData.length > 0 ? (
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyStockPriceChart stocksData={stocksData} tickerInfo={tickerInfo} tradeLogs={tradeLogs} />
          </Suspense>
        ) : (
          <p className="text-sm text-muted-foreground">표시할 자산 데이터가 없습니다.</p>
        )}
      </ResultBlock>
    </>
  );
};
