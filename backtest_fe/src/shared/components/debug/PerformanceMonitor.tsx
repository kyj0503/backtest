import { useEffect, useRef } from 'react';

/**
 * 렌더링 성능 측정 훅
 */
export const useRenderPerformance = (componentName: string) => {
  const renderStartTime = useRef<number | undefined>(undefined);
  const renderCount = useRef<number>(0);

  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      renderCount.current += 1;
      const renderEndTime = performance.now();
      const renderDuration = renderEndTime - (renderStartTime.current || renderEndTime);

      // 성능 측정 마크 생성
      performance.mark(`${componentName}-render-end`);

      if (renderCount.current > 1) {
        performance.measure(
          `${componentName}-render`,
          `${componentName}-render-start`,
          `${componentName}-render-end`
        );
      }

      console.log(`[Render Performance] ${componentName}:`, {
        renderCount: renderCount.current,
        renderDuration: `${renderDuration.toFixed(2)}ms`,
        timestamp: new Date().toISOString()
      });
    }
  });

  // 렌더링 시작 마크
  if (process.env.NODE_ENV === 'development') {
    renderStartTime.current = performance.now();
    performance.mark(`${componentName}-render-start`);
  }
};
