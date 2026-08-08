import { useState, useCallback, useRef, useEffect } from 'react';
import { BacktestService } from '../services/backtestService';
import { extractErrorMessage, setActiveRequestSignal } from '@/shared/api/client';
import {
  BacktestRequest,
  UnifiedBacktestResponse,
} from '../model/types/api-types';

export function useBacktest() {
  const [lastRequest, setLastRequest] = useState<BacktestRequest | null>(null);
  const [result, setResult] = useState<UnifiedBacktestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 진행 중인 요청의 컨트롤러. 언마운트되거나 새 제출이 이전 요청을
  // 대체(supersede)할 때 실제로 취소하는 데 쓴다 (P2-30). ref이므로 클로저가
  // 항상 최신 값을 본다.
  const activeControllerRef = useRef<AbortController | null>(null);

  const runBacktest = useCallback(async (request: BacktestRequest) => {
    // 이전 요청이 아직 끝나지 않았다면 새 제출이 그것을 대체한다 — 취소해서
    // 나중에 도착하는 오래된 응답이 최신 상태를 덮어쓰지 못하게 막는다.
    activeControllerRef.current?.abort();
    const controller = new AbortController();
    activeControllerRef.current = controller;
    setActiveRequestSignal(controller.signal);

    setLastRequest(request);
    setIsLoading(true);
    setError(null);

    try {
      const data = await BacktestService.executeBacktest(request);
      // 이 요청이 이미 대체되었다면(새 요청이 activeControllerRef를 넘겨받음)
      // 최신 요청이 상태를 소유하므로 여기서는 갱신하지 않는다.
      if (activeControllerRef.current === controller) {
        setResult(data);
      }
      return data;
    } catch (err) {
      if (activeControllerRef.current === controller) {
        // client.ts의 extractErrorMessage를 사용해 FastAPI의 실제 detail
        // 메시지(문자열 또는 Pydantic 검증 배열)를 노출한다. 이 훅이 페이지
        // 레벨 Alert의 유일한 에러 표시 경로다 — PortfolioBacktestForm의 모달은
        // 제출 전 클라이언트 측 검증 실패에만 사용되고, 백엔드 에러에 대해서는
        // 더 이상 중복으로 표시하지 않는다 (P2-29).
        //
        // 대체되거나 언마운트되어 취소된 요청의 실패는 공유 상태에 반영하지
        // 않는다 — 이미 최신 요청(또는 사라진 컴포넌트)이 그 책임을 넘겨받았다.
        setError(extractErrorMessage(err));
      }
      throw err;
    } finally {
      if (activeControllerRef.current === controller) {
        activeControllerRef.current = null;
        setActiveRequestSignal(undefined);
        setIsLoading(false);
      }
    }
  }, []);

  // 언마운트 시 진행 중인 요청을 취소한다 — 화면을 떠나도 백엔드에 계속
  // 부하를 주거나, 이미 사라진 컴포넌트를 위해 응답을 기다리지 않는다.
  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
      activeControllerRef.current = null;
    };
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
