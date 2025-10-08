
import { useState, useCallback } from 'react';
import { useAsync } from '@/shared/hooks/useAsync';
import { BacktestService } from '../services/backtestService';
import { OptimizationRequest, OptimizationResult } from '../model/api-types';

export function useOptimization() {
  const [lastRequest, setLastRequest] = useState<OptimizationRequest | null>(null);
  
  const {
    data: result,
    isLoading,
    error,
    execute: executeOptimization,
    reset,
  } = useAsync<OptimizationResult>(
    () => BacktestService.runOptimization(lastRequest!),
    [lastRequest],
    { immediate: false }
  );

  const runOptimization = useCallback(async (request: OptimizationRequest) => {
    setLastRequest(request);
    return executeOptimization();
  }, [executeOptimization]);

  return {
    result,
    isLoading,
    error,
    runOptimization,
    reset,
    lastRequest,
  };
}
