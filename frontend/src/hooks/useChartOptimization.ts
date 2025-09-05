import { useMemo, useCallback } from 'react';

/**
 * 차트 성능 최적화를 위한 커스텀 훅
 */
export const useChartOptimization = () => {
  // 차트 색상 설정 메모이제이션
  const chartColors = useMemo(() => ({
    primary: '#0d6efd',
    success: '#198754',
    danger: '#dc3545',
    warning: '#fd7e14',
    info: '#0dcaf0',
    secondary: '#6c757d',
    light: '#f8f9fa',
    dark: '#212529',
    positive: '#198754',
    negative: '#dc3545',
    neutral: '#6c757d'
  }), []);

  // 차트 기본 설정 메모이제이션
  const chartConfig = useMemo(() => ({
    margin: { top: 20, right: 30, left: 20, bottom: 5 },
    strokeWidth: {
      thin: 1,
      normal: 1.5,
      thick: 2,
      bold: 3
    },
    opacity: {
      low: 0.1,
      medium: 0.3,
      high: 0.6,
      full: 1.0
    },
    heights: {
      small: 200,
      medium: 300,
      large: 400,
      xlarge: 500
    }
  }), []);

  // 데이터 포맷터 함수들 메모이제이션
  const formatters = useMemo(() => ({
    currency: (value: number): string => {
      if (value >= 1e9) {
        return `${(value / 1e9).toFixed(1)}B`;
      } else if (value >= 1e6) {
        return `${(value / 1e6).toFixed(1)}M`;
      } else if (value >= 1e3) {
        return `${(value / 1e3).toFixed(1)}K`;
      }
      return value.toLocaleString();
    },
    
    percentage: (value: number): string => {
      return `${(value * 100).toFixed(2)}%`;
    },
    
    number: (value: number, decimals: number = 2): string => {
      return value.toFixed(decimals);
    },
    
    date: (dateString: string): string => {
      const date = new Date(dateString);
      return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
    }
  }), []);

  // 차트 데이터 변환 함수 메모이제이션
  const transformChartData = useCallback((data: any[], transformFn?: (item: any) => any) => {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map(item => {
      const baseItem = {
        ...item,
        // 숫자 데이터 안전성 보장
        ...(item.value !== undefined && { value: Number(item.value) || 0 }),
        ...(item.price !== undefined && { price: Number(item.price) || 0 }),
        ...(item.volume !== undefined && { volume: Number(item.volume) || 0 }),
        ...(item.return_pct !== undefined && { return_pct: Number(item.return_pct) || 0 }),
        ...(item.drawdown_pct !== undefined && { drawdown_pct: Number(item.drawdown_pct) || 0 })
      };
      
      return transformFn ? transformFn(baseItem) : baseItem;
    });
  }, []);

  // 색상 선택 함수 메모이제이션
  const getColorByValue = useCallback((value: number, neutralValue: number = 0) => {
    if (value > neutralValue) return chartColors.positive;
    if (value < neutralValue) return chartColors.negative;
    return chartColors.neutral;
  }, [chartColors]);

  // 데이터 필터링 함수 메모이제이션
  const filterDataByDateRange = useCallback((
    data: any[], 
    startDate?: string, 
    endDate?: string
  ) => {
    if (!startDate && !endDate) return data;
    
    return data.filter(item => {
      const itemDate = new Date(item.date);
      const start = startDate ? new Date(startDate) : new Date(0);
      const end = endDate ? new Date(endDate) : new Date();
      
      return itemDate >= start && itemDate <= end;
    });
  }, []);

  // 차트 애니메이션 설정 메모이제이션
  const animationConfig = useMemo(() => ({
    duration: 500,
    easing: 'ease-in-out',
    delay: 0
  }), []);

  return {
    chartColors,
    chartConfig,
    formatters,
    transformChartData,
    getColorByValue,
    filterDataByDateRange,
    animationConfig
  };
};
