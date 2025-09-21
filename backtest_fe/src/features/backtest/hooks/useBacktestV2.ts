/**
 * 백테스트 관련 커스텀 훅
 */

import { useState, useCallback, useMemo } from 'react';
import { useAsync } from '@/shared/hooks/useAsync';
import { BacktestService } from '../services/backtestService';
import {
  BacktestRequest,
  UnifiedBacktestResponse,
  Strategy,
  OptimizationRequest,
  OptimizationResult,
} from '../model/api-types';

export function useBacktest() {
  const [lastRequest, setLastRequest] = useState<BacktestRequest | null>(null);
  
  const {
    data: result,
    isLoading,
    error,
    execute: executeBacktest,
    reset,
  } = useAsync<UnifiedBacktestResponse>(
    () => BacktestService.executeBacktest(lastRequest!),
    [lastRequest],
    { immediate: false }
  );

  const runBacktest = useCallback(async (request: BacktestRequest) => {
    setLastRequest(request);
    return executeBacktest();
  }, [executeBacktest]);

  const isPortfolioBacktest = useMemo(() => {
    return result?.backtest_type === 'portfolio';
  }, [result]);

  const isSingleStockBacktest = useMemo(() => {
    return result?.backtest_type === 'single_stock';
  }, [result]);

  return {
    result,
    isLoading,
    error,
    runBacktest,
    reset,
    lastRequest,
    isPortfolioBacktest,
    isSingleStockBacktest,
  };
}

export function useStrategies() {
  return useAsync<Strategy[]>(
    () => BacktestService.getStrategies(),
    [],
    {
      onError: (error) => {
        console.error('Failed to load strategies:', error);
      }
    }
  );
}

export function useStrategy(strategyName: string | null) {
  return useAsync<Strategy>(
    () => BacktestService.getStrategy(strategyName!),
    [strategyName],
    { 
      immediate: !!strategyName,
      onError: (error) => {
        console.error(`Failed to load strategy ${strategyName}:`, error);
      }
    }
  );
}

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

export function useMarketData() {
  const newsState = useAsync(
    () => BacktestService.searchNews('주식 시장'),
    [],
    { immediate: false }
  );

  const exchangeRateState = useAsync(
    () => BacktestService.getExchangeRate(),
    [],
    { immediate: false }
  );

  const volatilityState = useAsync(
    () => BacktestService.getVolatilityData(['AAPL', 'GOOGL', 'MSFT']),
    [],
    { immediate: false }
  );

  const loadNews = useCallback((query: string) => {
    return BacktestService.searchNews(query);
  }, []);

  const loadVolatilityData = useCallback((symbols: string[]) => {
    return BacktestService.getVolatilityData(symbols);
  }, []);

  return {
    news: newsState,
    exchangeRate: exchangeRateState,
    volatility: volatilityState,
    loadNews,
    loadVolatilityData,
  };
}