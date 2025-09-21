/**
 * 비동기 상태 관리를 위한 커스텀 훅
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { AsyncState } from '@/shared/types';

interface UseAsyncOptions<T> {
  initialData?: T;
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: string) => void;
}

export function useAsync<T>(
  asyncFn: () => Promise<T>,
  deps: React.DependencyList = [],
  options: UseAsyncOptions<T> = {}
) {
  const { initialData = null, immediate = true, onSuccess, onError } = options;
  
  const [state, setState] = useState<AsyncState<T>>({
    data: initialData,
    isLoading: immediate,
    error: null,
  });

  const mountedRef = useRef(true);
  const latestAsyncFn = useRef(asyncFn);
  
  // 최신 함수 참조 유지
  useEffect(() => {
    latestAsyncFn.current = asyncFn;
  }, [asyncFn]);

  // 컴포넌트 언마운트 추적
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(async () => {
    if (!mountedRef.current) return;
    
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const data = await latestAsyncFn.current();
      
      if (!mountedRef.current) return;
      
      setState(prev => ({ ...prev, data, isLoading: false }));
      onSuccess?.(data);
    } catch (error) {
      if (!mountedRef.current) return;
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }));
      onError?.(errorMessage);
    }
  }, [onSuccess, onError]);

  const reset = useCallback(() => {
    setState({
      data: initialData,
      isLoading: false,
      error: null,
    });
  }, [initialData]);

  const setData = useCallback((data: T) => {
    setState(prev => ({ ...prev, data }));
  }, []);

  const setError = useCallback((error: string) => {
    setState(prev => ({ ...prev, error, isLoading: false }));
  }, []);

  // 초기 실행
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [...deps, execute, immediate]);

  return {
    ...state,
    execute,
    reset,
    setData,
    setError,
    isIdle: !state.isLoading && !state.error && !state.data,
    isSuccess: !state.isLoading && !state.error && state.data !== null,
    isError: !!state.error,
  };
}