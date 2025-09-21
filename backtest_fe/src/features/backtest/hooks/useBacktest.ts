import { useState } from 'react';
import { BacktestRequest } from '../model/api-types';
import { runBacktest as executeBacktest, ApiError } from '../api/backtestApi';

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
      const result = await executeBacktest(request);

      // 통합 API 응답 처리: 서버가 wrapper { backtest_type, data, ... } 형태로 반환할 수 있음
      let normalized = result as any;
      if (normalized && typeof normalized === 'object' && 'data' in normalized) {
        // use inner `data` as the shape expected by result components
        normalized = normalized.data;
      }

      // 백테스트 유형은 wrapper 레벨에서 결정되므로 원본 `result`를 참조
      if (result && typeof result === 'object' && 'backtest_type' in (result as any)) {
        setIsPortfolio((result as any).backtest_type === 'portfolio');
        // eslint-disable-next-line no-console
        console.log(`백테스트 유형: ${(result as any).backtest_type}, 통합 API 사용`);
      } else {
        // 레거시 API 응답 처리 (fallback)
        setIsPortfolio(request.portfolio.length > 1 || request.portfolio.some(stock => stock.asset_type === 'cash'));
      }

      setResults(normalized);
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
