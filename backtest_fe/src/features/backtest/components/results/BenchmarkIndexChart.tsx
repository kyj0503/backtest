/**
 * 벤치마크 지수 차트 컴포넌트
 *
 * **역할**:
 * - S&P 500과 NASDAQ 지수와 포트폴리오 누적 수익률 비교
 * - 시작점을 100으로 normalize하여 직관적 비교
 * - 버튼으로 S&P/NASDAQ 전환
 */
import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Button } from '@/shared/ui/button';
import { CARD_STYLES, HEADING_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';

interface BenchmarkIndexChartProps {
  sp500Data: any[];
  nasdaqData: any[];
  portfolioEquityData: any[];  // 포트폴리오 equity curve 데이터
}

const BenchmarkIndexChart: React.FC<BenchmarkIndexChartProps> = ({
  sp500Data,
  nasdaqData,
  portfolioEquityData,
}) => {
  const [selectedIndex, setSelectedIndex] = useState<'sp500' | 'nasdaq'>('sp500');

  const currentBenchmarkData = selectedIndex === 'sp500' ? sp500Data : nasdaqData;
  const hasData = currentBenchmarkData && currentBenchmarkData.length > 0;

  // 데이터를 시작점 100으로 normalize하는 함수
  const normalizeData = (data: any[], valueKey: string) => {
    if (!data || data.length === 0) return [];
    const startValue = data[0][valueKey];
    if (!startValue || startValue === 0) return [];

    return data.map((point: any) => ({
      date: point.date,
      normalized: (point[valueKey] / startValue) * 100,
    }));
  };

  // 벤치마크와 포트폴리오 데이터를 normalize
  const normalizedBenchmark = useMemo(
    () => normalizeData(currentBenchmarkData, 'close'),
    [currentBenchmarkData]
  );

  const normalizedPortfolio = useMemo(
    () => normalizeData(portfolioEquityData, 'value'),
    [portfolioEquityData]
  );

  // 두 데이터를 날짜별로 병합
  const mergedData = useMemo(() => {
    if (normalizedBenchmark.length === 0) return [];

    const portfolioMap = new Map(
      normalizedPortfolio.map(p => [p.date, p.normalized])
    );

    return normalizedBenchmark.map(b => ({
      date: b.date,
      benchmark: b.normalized,
      portfolio: portfolioMap.get(b.date) || null,
    }));
  }, [normalizedBenchmark, normalizedPortfolio]);

  // Y축 범위 계산 (normalize된 데이터 기준)
  const yAxisDomain = useMemo(() => {
    if (mergedData.length === 0) return undefined;

    const allValues = mergedData.flatMap(d =>
      [d.benchmark, d.portfolio].filter(v => v !== null) as number[]
    );

    if (allValues.length === 0) return undefined;

    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    const padding = (max - min) * 0.1; // 10% 패딩

    return [Math.max(0, min - padding), max + padding];
  }, [mergedData]);

  const formatDateTick = (value: string) => {
    const date = new Date(value);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  if (!hasData && sp500Data.length === 0 && nasdaqData.length === 0) return null;

  return (
    <div className={CARD_STYLES.base}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className={SPACING.itemCompact}>
          <h3 className={HEADING_STYLES.h3}>벤치마크 비교</h3>
          <p className={TEXT_STYLES.caption}>
            포트폴리오와 지수의 누적 성과 비교 (시작점 = 100)
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
          <LineChart data={mergedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDateTick} />
            <YAxis
              domain={yAxisDomain}
              tickFormatter={(value: number) => value.toFixed(0)}
            />
            <Tooltip
              formatter={(value: number, name: string) => {
                const label = name === 'benchmark'
                  ? (selectedIndex === 'sp500' ? 'S&P 500' : 'NASDAQ')
                  : '내 포트폴리오';
                return [value.toFixed(2), label];
              }}
              labelFormatter={(label: string) => `날짜: ${label}`}
            />
            <Legend
              formatter={(value: string) => {
                if (value === 'benchmark') {
                  return selectedIndex === 'sp500' ? 'S&P 500' : 'NASDAQ';
                }
                return '내 포트폴리오';
              }}
            />
            <Line
              type="monotone"
              dataKey="portfolio"
              stroke="#6366f1"
              strokeWidth={2.5}
              dot={false}
              name="portfolio"
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="benchmark"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              name="benchmark"
            />
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

export default BenchmarkIndexChart;
