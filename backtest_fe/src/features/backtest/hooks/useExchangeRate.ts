import { useState, useEffect, useRef, useCallback } from 'react';
import { getExchangeRate } from '../api/backtestApi';

interface ExchangeRateData {
  date: string;
  rate: number;
  volume?: number;
}

interface UseExchangeRateParams {
  startDate: string;
  endDate: string;
  enabled?: boolean;
}

interface UseExchangeRateReturn {
  exchangeData: ExchangeRateData[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * 환율 데이터 페칭을 위한 커스텀 훅
 * USD/KRW 환율 데이터를 가져오고 캐싱 기능 제공
 */
export const useExchangeRate = ({
  startDate,
  endDate,
  enabled = true
}: UseExchangeRateParams): UseExchangeRateReturn => {
  const [exchangeData, setExchangeData] = useState<ExchangeRateData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchExchangeRate = useCallback(async () => {
    if (!enabled || !startDate || !endDate) return;

    // 이전 요청 취소
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const response = await getExchangeRate(startDate, endDate, controller.signal);

      if (controller.signal.aborted) return;

      if (response.status === 'success' && response.data.exchange_rates) {
        setExchangeData(response.data.exchange_rates);
      } else {
        setError(response.message || '환율 데이터를 가져올 수 없습니다.');
        setExchangeData([]);
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      console.error('환율 데이터 조회 실패:', err);
      setError('환율 데이터 조회에 실패했습니다.');
      setExchangeData([]);
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, [startDate, endDate, enabled]);

  useEffect(() => {
    fetchExchangeRate();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchExchangeRate]);

  return {
    exchangeData,
    loading,
    error,
    refetch: fetchExchangeRate
  };
};
