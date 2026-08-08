import React, { memo, useEffect, useMemo, useState } from 'react';
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, Line, Area, ReferenceLine } from 'recharts';
import type { TextAnchor } from 'recharts';
import { CustomTooltip } from './shared';
import { useRenderPerformance } from '@/shared/components';
import type { EquityPoint } from '../model/types';

interface EquityChartProps {
  data: EquityPoint[];
}

// 뷰포트 너비를 추적하는 훅.
// 기존에는 useMemo 내부에서 렌더 시점에 window.innerWidth를 직접 읽어
// 리사이즈에 반응하지 않았다. resize 이벤트를 구독해 상태로 관리한다.
const useViewportWidth = (): number => {
  const [width, setWidth] = useState<number>(() =>
    typeof window !== 'undefined' ? window.innerWidth : 1024
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return width;
};

// 차트 설정 상수 (컴포넌트 외부로 이동하여 재생성 방지)
const CHART_CONFIG = {
  margin: { top: 20, right: 30, left: 20, bottom: 5 },
  strokeWidth: 2,
  fillOpacity: 0.3,
} as const;

// 화면 크기에 따른 X축 틱 간격 계산
const getXAxisInterval = (dataLength: number, width: number) => {
  if (width < 640) { // 모바일
    return Math.ceil(dataLength / 4); // 최대 4개 라벨
  } else if (width < 1024) { // 태블릿
    return Math.ceil(dataLength / 6); // 최대 6개 라벨
  }
  return Math.ceil(dataLength / 8); // 데스크톱, 최대 8개 라벨
};

const EquityChart: React.FC<EquityChartProps> = memo(({ data }) => {
  // 성능 모니터링
  useRenderPerformance('EquityChart');

  const viewportWidth = useViewportWidth();

  // 데이터 안전성 검사 (샘플링은 useChartData에서 처리됨)
  const processedData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];

    return data.map(item => ({
      ...item,
      return_pct: Number(item.return_pct) || 0,
      drawdown_pct: Number(item.drawdown_pct) || 0
    }));
  }, [data]);

  // 반응형 X축 설정
  const xAxisProps = useMemo(() => {
    const isMobile = viewportWidth < 640;
    const textAnchor: TextAnchor = isMobile ? 'end' : 'middle';
    return {
      interval: getXAxisInterval(processedData.length, viewportWidth),
      angle: isMobile ? -45 : 0,
      textAnchor,
      height: isMobile ? 60 : 30,
    };
  }, [processedData.length, viewportWidth]);

  return (
    <ResponsiveContainer width="100%" height={400} debounce={300}>
      <ComposedChart data={processedData} margin={{ ...CHART_CONFIG.margin, bottom: xAxisProps.height }} syncId="equityChart">
        {/* recharts v3: CartesianGrid의 yAxisId가 YAxis와 일치해야 가로 그리드가 눈금에 맞춰 그려진다. */}
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} yAxisId="return" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 11 }}
          interval={xAxisProps.interval}
          angle={xAxisProps.angle}
          textAnchor={xAxisProps.textAnchor}
        />
        <YAxis yAxisId="return" orientation="left" />
        <YAxis yAxisId="drawdown" orientation="right" />
        <RechartsTooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          yAxisId="return"
          type="monotone"
          dataKey="return_pct"
          stroke="#198754"
          strokeWidth={CHART_CONFIG.strokeWidth}
          dot={false}
          name="수익률 (%)"
          isAnimationActive={false}
          connectNulls={true}
        />
        <Area
          yAxisId="drawdown"
          type="monotone"
          dataKey="drawdown_pct"
          stroke="#dc3545"
          fill="#dc3545"
          fillOpacity={CHART_CONFIG.fillOpacity}
          name="드로우다운 (%)"
          isAnimationActive={false}
        />
        <ReferenceLine yAxisId="return" y={0} stroke="#6c757d" strokeDasharray="2 2" />
      </ComposedChart>
    </ResponsiveContainer>
  );
});

EquityChart.displayName = 'EquityChart';

export default EquityChart;
