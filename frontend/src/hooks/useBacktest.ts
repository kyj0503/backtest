import { useState } from 'react';
import { UnifiedBacktestRequest } from '../types/api';
import { backtestApiService } from '../services/api';

export interface UseBacktestReturn {
  results: any;
  loading: boolean;
  error: string | null;
  isPortfolio: boolean;
  runBacktest: (request: UnifiedBacktestRequest) => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
}

export const useBacktest = (): UseBacktestReturn => {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPortfolio, setIsPortfolio] = useState(false);

  const runBacktest = async (request: UnifiedBacktestRequest) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setIsPortfolio(request.portfolio.length > 1);

    try {
      const result = await backtestApiService.runBacktest(request);
      setResults(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResults(null);
    setIsPortfolio(false);
  };

  const clearError = () => {
    setError(null);
  };

  return {
    results,
    loading,
    error,
    isPortfolio,
    runBacktest,
    clearResults,
    clearError,
  };
};
