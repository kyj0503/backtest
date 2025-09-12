import { useState } from 'react';
import { BacktestRequest } from '../types/api';
import { backtestApiService, ApiError } from '../services/api';

export interface UseBacktestReturn {
  results: any;
  loading: boolean;
  error: string | null;
  errorType: string | null;
  errorId: string | null;
  isPortfolio: boolean;
  runBacktest: (request: BacktestRequest) => Promise<void>;
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

  const runBacktest = async (request: BacktestRequest) => {
    setLoading(true);
    setError(null);
    setErrorType(null);
    setErrorId(null);
    setResults(null);

    try {
      const result = await backtestApiService.runBacktest(request);
      
      // 통합 API 응답 처리
      if (result.backtest_type) {
        setIsPortfolio(result.backtest_type === 'portfolio');
        console.log(`백테스트 유형: ${result.backtest_type}, 통합 API 사용`);
      } else {
        // 레거시 API 응답 처리 (fallback)
        setIsPortfolio(request.portfolio.length > 1 || request.portfolio.some(stock => stock.asset_type === 'cash'));
      }
      
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
