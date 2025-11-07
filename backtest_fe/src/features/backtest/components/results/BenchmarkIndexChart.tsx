/**
 * 벤치마크 지수 차트 컴포넌트
 *
 * **역할**:
 * - S&P 500과 NASDAQ 지수와 포트폴리오 누적 수익률 비교
 * - 시작점을 100으로 normalize하여 직관적 비교
 * - 범례 클릭으로 개별 라인 토글 가능
 */
import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
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
  // 각 라인의 표시 여부를 관리하는 상태
  const [visibleLines, setVisibleLines] = useState<Record<string, boolean>>({
    portfolio: true,
    sp500: true,
    nasdaq: true,
  });

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
  // 포트폴리오 누적 수익률 계산 (일일 수익률 기반)
  // ============================================================
  //
  // **목적: DCA(분할 매수) 전략과 벤치마크 지수를 공정하게 비교**
  // - DCA는 시간에 따라 투자금이 증가하므로 절대 금액(equity curve)으로는 비교 불가
  // - 대신 일일 수익률을 복리로 누적하여 상대적 성과를 비교
  // - 시작점을 100으로 normalize하여 직관적 비교 가능
  //
  // **수익률 형식 변환:**
  // - API에서 받는 return_pct: 백분율 (2.5 = 2.5%)
  // - 복리 계산에 필요한 형식: 소수 (0.025 = 2.5%)
  // - 변환: dailyReturn / 100
  //
  // **복리 누적 공식:**
  // - 현재 가치 = 이전 가치 × (1 + 수익률)
  // - 예: 100 × (1 + 0.025) = 102.5 (첫날 2.5% 수익)
  // - 예: 102.5 × (1 + 0.03) = 105.575 (둘째날 3% 수익)
  //
  // **사용 예시:**
  // - 포트폴리오(DCA): 매달 $1000씩 10회 투자 → 총 투자금 $10,000, 최종 equity $12,000 (20% 수익)
  // - 벤치마크(지수): 지수는 "투자금" 개념 없이 시작 가격 100에서 종료 가격 110으로 상승 (10% 수익)
  // - 절대 equity 비교: $12,000 vs 110 (단위도 다르고, DCA 투자금 증가 효과 포함되어 무의미)
  // - 수익률 비교: 120 vs 110 (시작점 100 기준, 순수 성과만 비교 가능)
  //
  // **관련 파일:**
  // - 백엔드: portfolio_service.py:1494 (return_val * 100으로 백분율 변환)
  // - 이 파일: BenchmarkIndexChart.tsx:67 (dailyReturn / 100으로 소수 변환)
  // ============================================================
  const normalizedPortfolio = useMemo(() => {
    if (!portfolioEquityData || portfolioEquityData.length === 0) return [];

    let cumulativeValue = 100; // 시작점 = 100

    return portfolioEquityData.map((point, index) => {
      if (index === 0) {
        return { date: point.date, normalized: 100 };
      }

      // 일일 수익률을 누적: 현재 가치 = 이전 가치 × (1 + 수익률/100)
      // - dailyReturn: API에서 받은 백분율 (예: 2.5 = 2.5%)
      // - dailyReturn / 100: 복리 계산용 소수로 변환 (예: 2.5 / 100 = 0.025)
      // - (1 + 0.025): 수익률 승수 (1.025 = 2.5% 증가)
      const dailyReturn = point.return_pct || 0;
      cumulativeValue = cumulativeValue * (1 + dailyReturn / 100);

      return {
        date: point.date,
        normalized: cumulativeValue,
      };
    });
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

  if (!hasData) return null;

  return (
    <div className={CARD_STYLES.base}>
      <div className={`${SPACING.itemCompact} mb-4`}>
        <h3 className={HEADING_STYLES.h3}>벤치마크 비교</h3>
        <p className={TEXT_STYLES.caption}>
          포트폴리오와 지수의 누적 성과 비교 (시작점 = 100)
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={mergedData}>
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
            onClick={(e: { dataKey?: string }) => {
              const dataKey = e.dataKey;
              if (dataKey) {
                setVisibleLines(prev => ({
                  ...prev,
                  [dataKey]: !prev[dataKey],
                }));
              }
            }}
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
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BenchmarkIndexChart;
