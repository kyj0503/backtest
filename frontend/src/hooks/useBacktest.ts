import { useState } from 'react';
import { UnifiedBacktestRequest } from '../types/api';
import { backtestApiService, ApiError } from '../services/api';

export interface UseBacktestReturn {
  results: any;
  loading: boolean;
  error: string | null;
  errorType: string | null;
  errorId: string | null;
  isPortfolio: boolean;
  runBacktest: (request: UnifiedBacktestRequest) => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
}

export const useBacktest = (): UseBacktestReturn => {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<string | null>(null);
  const [errorId, setErrorId] = useState<string | null>(null);
  const [isPortfolio, setIsPortfolio] = useState(false);

  const runBacktest = async (request: UnifiedBacktestRequest) => {
    setLoading(true);
    setError(null);
    setErrorType(null);
    setErrorId(null);
    setResults(null);
    setIsPortfolio(request.portfolio.length > 1);

    try {
      const result = await backtestApiService.runBacktest(request);
      setResults(result);
    } catch (err) {
      if (err && typeof err === 'object' && 'message' in err) {
        const apiError = err as ApiError;
        setError(apiError.message);
        setErrorType(apiError.type || 'unknown');
        setErrorId(apiError.errorId || null);
      } else {
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        setError(errorMessage);
        setErrorType('unknown');
      }
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
    setErrorType(null);
    setErrorId(null);
  };

  return {
    results,
    loading,
    error,
    errorType,
    errorId,
    isPortfolio,
    runBacktest,
    clearResults,
    clearError,
  };
};
