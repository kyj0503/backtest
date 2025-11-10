/**
 * 벤치마크 일일 수익률 비교 차트 컴포넌트
 * 
 * **역할**:
 * - 포트폴리오, S&P 500, NASDAQ 일일 수익률을 한 그래프에 겹쳐서 표시
 * - 각 라인을 다른 색상으로 구분하여 비교 용이
 * - 범례 클릭으로 개별 라인 토글 가능
 */
import React, { useMemo, useState, memo, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { CARD_STYLES, HEADING_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';
import { useRenderPerformance } from '@/shared/components/PerformanceMonitor';

interface BenchmarkReturnsChartProps {
  sp500Data: any[];
  nasdaqData: any[];
  portfolioDailyReturns?: Record<string, number>;
  aggregationType?: 'daily' | 'weekly' | 'monthly';
}

const BenchmarkReturnsChart: React.FC<BenchmarkReturnsChartProps> = memo(({
  sp500Data,
  nasdaqData,
  portfolioDailyReturns,
  aggregationType = 'daily',
}) => {
  // 성능 모니터링
  useRenderPerformance('BenchmarkReturnsChart');

  // 집계 타입에 따른 라벨
  const periodLabel = {
    daily: '일일',
    weekly: '주간',
    monthly: '월간',
  }[aggregationType];

  // 각 라인의 표시 여부를 관리하는 상태
  const [visibleLines, setVisibleLines] = useState<Record<string, boolean>>({
    portfolio: true,
    sp500: true,
    nasdaq: true,
  });

  // 모든 데이터를 날짜 기준으로 병합 (샘플링은 useChartData에서 처리됨)
  const mergedData = useMemo(() => {
    const dataMap = new Map<string, any>();

    // 포트폴리오 일일 수익률 추가
    if (portfolioDailyReturns) {
      Object.entries(portfolioDailyReturns).forEach(([date, returnPct]) => {
        dataMap.set(date, {
          date,
          portfolio: returnPct,
        });
      });
    }

    // S&P 500 데이터 추가
    sp500Data.forEach(item => {
      const existing = dataMap.get(item.date) || { date: item.date };
      existing.sp500 = item.return_pct;
      dataMap.set(item.date, existing);
    });

    // NASDAQ 데이터 추가
    nasdaqData.forEach(item => {
      const existing = dataMap.get(item.date) || { date: item.date };
      existing.nasdaq = item.return_pct;
      dataMap.set(item.date, existing);
    });

    // 날짜순으로 정렬
    return Array.from(dataMap.values()).sort((a, b) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [sp500Data, nasdaqData, portfolioDailyReturns]);

  // Y축 범위 계산 (표시된 라인만 고려) - 효율적인 계산
  const yAxisDomain = useMemo(() => {
    if (mergedData.length === 0) return ['auto', 'auto'];

    // 표시된 라인에 따라 필요한 값들만 추출
    const allValues: number[] = mergedData.flatMap(item => {
      const values: number[] = [];
      if (visibleLines.portfolio && item.portfolio !== undefined) {
        values.push(item.portfolio);
      }
      if (visibleLines.sp500 && item.sp500 !== undefined) {
        values.push(item.sp500);
      }
      if (visibleLines.nasdaq && item.nasdaq !== undefined) {
        values.push(item.nasdaq);
      }
      return values;
    });

    if (allValues.length === 0) return ['auto', 'auto'];

    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    
    return [minValue, maxValue];
  }, [mergedData, visibleLines]);

  const hasData = mergedData.length > 0;

  const formatDateTick = (value: string) => {
    const date = new Date(value);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  const handleLegendClick = useCallback((data: any) => {
    const dataKey = data.dataKey;
    if (dataKey && typeof dataKey === 'string') {
      setVisibleLines(prev => ({
        ...prev,
        [dataKey]: !prev[dataKey],
      }));
    }
  }, []);

  if (!hasData) return null;

  return (
    <div className={CARD_STYLES.base}>
      <div className={`${SPACING.itemCompact} ${SPACING.contentGap}`}>
        <h3 className={HEADING_STYLES.h3}>{periodLabel} 수익률 벤치마크 비교</h3>
        <p className={TEXT_STYLES.caption}>
          포트폴리오와 주요 지수의 {periodLabel} 수익률을 비교하세요
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320} debounce={300}>
        <LineChart data={mergedData} syncId="benchmarkReturnsChart">
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDateTick}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            domain={yAxisDomain}
            tickFormatter={(value: number) => `${value.toFixed(1)}%`}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                portfolio: '내 포트폴리오',
                sp500: 'S&P 500',
                nasdaq: 'NASDAQ',
              };
              return [`${value.toFixed(2)}%`, labels[name] || name];
            }}
            labelFormatter={(label: string) => `날짜: ${label}`}
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ccc',
              borderRadius: '8px',
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '10px', cursor: 'pointer' }}
            onClick={handleLegendClick}
            formatter={(value: string) => {
              const labels: Record<string, string> = {
                portfolio: '내 포트폴리오',
                sp500: 'S&P 500',
                nasdaq: 'NASDAQ',
              };
              const isVisible = visibleLines[value];
              return (
                <span style={{ opacity: isVisible ? 1 : 0.5 }}>
                  {labels[value] || value}
                </span>
              );
            }}
          />

          {/* 포트폴리오 라인 */}
          {portfolioDailyReturns && (
            <Line
              type="monotone"
              dataKey="portfolio"
              stroke="#6366f1"
              strokeWidth={2}
              dot={false}
              name="portfolio"
              hide={!visibleLines.portfolio}
              isAnimationActive={false}
              connectNulls={true}
            />
          )}

          {/* S&P 500 라인 */}
          {sp500Data.length > 0 && (
            <Line
              type="monotone"
              dataKey="sp500"
              stroke="#10b981"
              strokeWidth={1.5}
              dot={false}
              strokeDasharray="5 5"
              name="sp500"
              hide={!visibleLines.sp500}
              isAnimationActive={false}
              connectNulls={true}
            />
          )}

          {/* NASDAQ 라인 */}
          {nasdaqData.length > 0 && (
            <Line
              type="monotone"
              dataKey="nasdaq"
              stroke="#f97316"
              strokeWidth={1.5}
              dot={false}
              strokeDasharray="3 3"
              name="nasdaq"
              hide={!visibleLines.nasdaq}
              isAnimationActive={false}
              connectNulls={true}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
});

BenchmarkReturnsChart.displayName = 'BenchmarkReturnsChart';

export default BenchmarkReturnsChart;
