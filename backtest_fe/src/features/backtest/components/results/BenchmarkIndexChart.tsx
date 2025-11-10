/**
 * 벤치마크 지수 차트 컴포넌트
 *
 * **역할**:
 * - S&P 500과 NASDAQ 지수와 포트폴리오 누적 수익률 비교
 * - 시작점을 100으로 normalize하여 직관적 비교
 * - 범례 클릭으로 개별 라인 토글 가능
 */
import React, { useState, useMemo, memo, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { CARD_STYLES, HEADING_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';
import { useRenderPerformance } from '@/shared/components/PerformanceMonitor';

interface BenchmarkIndexChartProps {
  sp500Data: any[];
  nasdaqData: any[];
  portfolioEquityData: any[];  // 포트폴리오 equity curve 데이터
}

const BenchmarkIndexChart: React.FC<BenchmarkIndexChartProps> = memo(({
  sp500Data,
  nasdaqData,
  portfolioEquityData,
}) => {
  // 성능 모니터링
  useRenderPerformance('BenchmarkIndexChart');

  // 각 라인의 표시 여부를 관리하는 상태
  const [visibleLines, setVisibleLines] = useState<Record<string, boolean>>({
    portfolio: true,
    sp500: true,
    nasdaq: true,
  });

  // 데이터를 시작점 100으로 normalize하는 함수 (샘플링은 useChartData에서 처리됨)
  const normalizeData = (data: any[], valueKey: string) => {
    if (!data || data.length === 0) return [];
    const startValue = data[0][valueKey];
    if (!startValue || startValue === 0) return [];

    return data.map((point: any) => ({
      date: point.date,
      normalized: (point[valueKey] / startValue) * 100,
    }));
  };

  // S&P 500과 NASDAQ 데이터를 normalize
  const normalizedSp500 = useMemo(
    () => normalizeData(sp500Data, 'close'),
    [sp500Data]
  );

  const normalizedNasdaq = useMemo(
    () => normalizeData(nasdaqData, 'close'),
    [nasdaqData]
  );

  // ============================================================
  // 포트폴리오 누적 가치를 정규화 (equity value 기반)
  // ============================================================
  //
  // **목적: DCA(분할 매수) 전략과 벤치마크 지수를 공정하게 비교**
  // - DCA는 시간에 따라 투자금이 증가하므로 절대 금액(equity curve)으로는 비교 불가
  // - equity value를 시작점 100으로 정규화하여 상대적 성과를 비교
  // - 시작점을 100으로 normalize하여 직관적 비교 가능
  //
  // **왜 return_pct가 아닌 value를 사용하는가?**
  // - return_pct: 일간/주간/4주간 수익률 (집계 타입에 따라 다름)
  // - 장기간 백테스트 시 return_pct는 이미 복리 수익률임
  // - 이를 다시 복리로 누적하면 중복 계산 발생!
  // - value: 실제 포트폴리오 가치 (이미 모든 복리 효과가 반영됨)
  //
  // **정규화 공식:**
  // - normalized = (현재 value / 시작 value) × 100
  //
  // **관련 파일:**
  // - 백엔드: portfolio_service.py의 API 응답 생성
  // - 프론트엔드: useChartData.ts에서 샘플링 및 복리 집계
  // ============================================================
  const normalizedPortfolio = useMemo(() => {
    if (!portfolioEquityData || portfolioEquityData.length === 0) return [];

    const startValue = portfolioEquityData[0].value;
    if (!startValue || startValue === 0) return [];

    return portfolioEquityData.map((point) => ({
      date: point.date,
      normalized: (point.value / startValue) * 100,
    }));
  }, [portfolioEquityData]);

  // 세 데이터를 날짜별로 병합
  const mergedData = useMemo(() => {
    const dataMap = new Map<string, any>();

    // 포트폴리오 데이터 추가
    normalizedPortfolio.forEach(p => {
      dataMap.set(p.date, {
        date: p.date,
        portfolio: p.normalized,
      });
    });

    // S&P 500 데이터 추가
    normalizedSp500.forEach(item => {
      const existing = dataMap.get(item.date) || { date: item.date };
      existing.sp500 = item.normalized;
      dataMap.set(item.date, existing);
    });

    // NASDAQ 데이터 추가
    normalizedNasdaq.forEach(item => {
      const existing = dataMap.get(item.date) || { date: item.date };
      existing.nasdaq = item.normalized;
      dataMap.set(item.date, existing);
    });

    // 날짜순으로 정렬
    return Array.from(dataMap.values()).sort((a, b) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [normalizedSp500, normalizedNasdaq, normalizedPortfolio]);

  // Y축 범위 계산 (표시된 라인만 고려)
  const yAxisDomain = useMemo(() => {
    if (mergedData.length === 0) return ['auto', 'auto'];

    let allValues: number[] = [];
    
    mergedData.forEach(item => {
      if (visibleLines.portfolio && item.portfolio !== undefined) {
        allValues.push(item.portfolio);
      }
      if (visibleLines.sp500 && item.sp500 !== undefined) {
        allValues.push(item.sp500);
      }
      if (visibleLines.nasdaq && item.nasdaq !== undefined) {
        allValues.push(item.nasdaq);
      }
    });

    if (allValues.length === 0) return ['auto', 'auto'];

    const min = Math.min(...allValues);
    const max = Math.max(...allValues);

    return [min, max];
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
        <h3 className={HEADING_STYLES.h3}>벤치마크 비교</h3>
        <p className={TEXT_STYLES.caption}>
          포트폴리오와 지수의 누적 성과 비교 (시작점 = 100)
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320} debounce={300}>
        <LineChart data={mergedData} syncId="benchmarkChart">
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDateTick}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            domain={yAxisDomain}
            tickFormatter={(value: number) => value.toFixed(0)}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                portfolio: '내 포트폴리오',
                sp500: 'S&P 500',
                nasdaq: 'NASDAQ',
              };
              return [value.toFixed(2), labels[name] || name];
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
          {portfolioEquityData.length > 0 && (
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

BenchmarkIndexChart.displayName = 'BenchmarkIndexChart';

export default BenchmarkIndexChart;
