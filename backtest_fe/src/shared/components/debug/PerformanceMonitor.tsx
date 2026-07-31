import React, { useEffect, useRef } from 'react';

interface PerformanceMonitorProps {
  componentName: string;
  enabled?: boolean;
}

/**
 * 컴포넌트 렌더링 성능을 모니터링하는 HOC
 */
export const withPerformanceMonitor = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentName: string
) => {
  return React.memo((props: P) => {
    const renderStartTime = useRef<number | undefined>(undefined);
    const renderCount = useRef<number>(0);

    useEffect(() => {
      if (process.env.NODE_ENV === 'development') {
        renderCount.current += 1;
        const renderEndTime = performance.now();
        const renderDuration = renderEndTime - (renderStartTime.current || renderEndTime);
        
        console.log(`[Performance] ${componentName}:`, {
          renderCount: renderCount.current,
          renderDuration: `${renderDuration.toFixed(2)}ms`,
          timestamp: new Date().toISOString()
        });
      }
    });

    // 렌더링 시작 시간 기록
    if (process.env.NODE_ENV === 'development') {
      renderStartTime.current = performance.now();
    }

    return <WrappedComponent {...props} />;
  });
};

/**
 * 성능 프로파일러 컴포넌트
 */
const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ 
  componentName, 
  enabled = process.env.NODE_ENV === 'development' 
}) => {
  useEffect(() => {
    if (!enabled) return;

    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'measure' && entry.name.includes(componentName)) {
          console.log(`[Performance Measure] ${entry.name}:`, {
            duration: `${entry.duration.toFixed(2)}ms`,
            startTime: entry.startTime
          });
        }
      });
    });

    observer.observe({ entryTypes: ['measure'] });

    return () => {
      observer.disconnect();
    };
  }, [componentName, enabled]);

  return null;
};

/**
 * 메모리 사용량 모니터링 훅
 */
export const useMemoryMonitor = (componentName: string) => {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    const checkMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        console.log(`💾 [Memory] ${componentName}:`, {
          used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
          total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
          limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`,
          timestamp: new Date().toISOString()
        });
      }
    };

    const interval = setInterval(checkMemory, 5000); // 5초마다 체크

    return () => {
      clearInterval(interval);
    };
  }, [componentName]);
};

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

export default PerformanceMonitor;
