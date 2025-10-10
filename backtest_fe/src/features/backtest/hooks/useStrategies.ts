/**
 * 전략 관련 훅
 * 
 * 전략 목록은 constants/strategies.ts에 하드코딩되어 있으므로
 * API 호출 없이 즉시 반환합니다.
 */

import { useMemo } from 'react';
import { STRATEGIES, getStrategyByName } from '../constants/strategies';

export function useStrategies() {
  const data = useMemo(() => STRATEGIES, []);
  
  return {
    data,
    loading: false,
    error: null,
    execute: () => Promise.resolve(data),
  };
}

export function useStrategy(strategyName: string | null) {
  const data = useMemo(
    () => (strategyName ? getStrategyByName(strategyName) : undefined),
    [strategyName]
  );
  
  return {
    data,
    loading: false,
    error: null,
    execute: () => Promise.resolve(data),
  };
}
