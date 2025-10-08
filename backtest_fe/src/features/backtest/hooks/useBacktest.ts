import { useState, useCallback, useMemo } from 'react';
import { BacktestService } from '../services/backtestService';
import {
  BacktestRequest,
  UnifiedBacktestResponse,
} from '../model/api-types';

export function useBacktest() {
  const [lastRequest, setLastRequest] = useState<BacktestRequest | null>(null);
  const [result, setResult] = useState<UnifiedBacktestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runBacktest = useCallback(async (request: BacktestRequest) => {
    setLastRequest(request);
    setIsLoading(true);
    setError(null);

    try {
      const data = await BacktestService.executeBacktest(request);
      setResult(data);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setIsLoading(false);
  }, []);

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