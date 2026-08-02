import { useState, useCallback } from 'react';
import { BacktestService } from '../services/backtestService';
import { extractErrorMessage } from '@/shared/api/client';
import {
  BacktestRequest,
  UnifiedBacktestResponse,
} from '../model/types/api-types';

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
      // client.ts의 extractErrorMessage를 사용해 FastAPI의 실제 detail
      // 메시지(문자열 또는 Pydantic 검증 배열)를 노출한다. 이 훅이 페이지
      // 레벨 Alert의 유일한 에러 표시 경로다 — PortfolioBacktestForm의 모달은
      // 제출 전 클라이언트 측 검증 실패에만 사용되고, 백엔드 에러에 대해서는
      // 더 이상 중복으로 표시하지 않는다 (P2-29).
      setError(extractErrorMessage(err));
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

  return {
    result,
    isLoading,
    error,
    runBacktest,
    reset,
    lastRequest,
  };
}
