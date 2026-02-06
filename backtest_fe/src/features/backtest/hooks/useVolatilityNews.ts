import { useState, useEffect, useRef, useCallback } from 'react';
import {
  VolatilityEvent,
  NewsItem,
} from '../model/types/volatility-news-types';
import {
  getStockVolatilityNews,
  getNaverNews,
  getLatestTickerNews,
} from '../api/backtestApi';

interface UseVolatilityNewsParams {
  symbols: string[];
  startDate: string;
  endDate: string;
  enabled?: boolean;
  canViewNews?: boolean;
}

interface UseVolatilityNewsReturn {
  volatilityData: { [key: string]: VolatilityEvent[] };
  selectedStock: string;
  newsData: NewsItem[];
  showNewsModal: boolean;
  currentNewsEvent: VolatilityEvent | null;
  loading: boolean;
  newsLoading: boolean;
  error: string | null;
  actions: {
    setSelectedStock: (symbol: string) => void;
    openNewsModal: (date: string, event: VolatilityEvent) => Promise<void>;
    closeNewsModal: () => void;
    refetch: () => Promise<void>;
  };
}

/**
 * 주가 변동성 및 뉴스 데이터 관리를 위한 커스텀 훅
 * 변동성 이벤트 조회, 종목 선택, 뉴스 모달 상태 관리를 통합
 */
export const useVolatilityNews = ({
  symbols,
  startDate,
  endDate,
  enabled = true,
  canViewNews = true
}: UseVolatilityNewsParams): UseVolatilityNewsReturn => {
  const [volatilityData, setVolatilityData] = useState<{ [key: string]: VolatilityEvent[] }>({});
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [newsData, setNewsData] = useState<NewsItem[]>([]);
  const [showNewsModal, setShowNewsModal] = useState(false);
  const [currentNewsEvent, setCurrentNewsEvent] = useState<VolatilityEvent | null>(null);
  const [loading, setLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 현금이 아닌 유효한 심볼만 필터링
  const validSymbols = symbols.filter(symbol =>
    symbol.toUpperCase() !== 'CASH' && symbol !== '현금'
  );

  const fetchVolatilityData = useCallback(async () => {
    if (!enabled || validSymbols.length === 0) return;

    // 이전 요청 취소
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const results: { [key: string]: VolatilityEvent[] } = {};

      for (const symbol of validSymbols) {
        if (controller.signal.aborted) return;
        try {
          const response = await getStockVolatilityNews(symbol, startDate, endDate, 5.0, controller.signal);
          if (response.status === 'success' && response.data.volatility_events) {
            results[symbol] = response.data.volatility_events;
          } else {
            results[symbol] = [];
          }
        } catch (symbolError) {
          console.warn(`Failed to fetch volatility data for ${symbol}:`, symbolError);
          results[symbol] = [];
        }
      }

      if (controller.signal.aborted) return;

      setVolatilityData(results);

      // 첫 번째 유효한 종목을 선택
      if (validSymbols.length > 0 && !selectedStock && validSymbols[0]) {
        setSelectedStock(validSymbols[0]);
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      console.error('변동성 데이터 가져오기 실패:', err);
      setError('변동성 데이터를 가져오는 중 오류가 발생했습니다.');
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, [validSymbols.join(','), startDate, endDate, enabled]);

  const openNewsModal = async (_date: string, event: VolatilityEvent) => {
    if (!canViewNews) {
      return;
    }
    setCurrentNewsEvent(event);
    setShowNewsModal(true);
    setNewsLoading(true);

    try {
      // 1. 먼저 특정 날짜의 뉴스 조회 시도 (DB 캐싱 사용)
      const dateResponse = await getNaverNews(selectedStock, event.date, 50);

      if (dateResponse.status === 'success' && dateResponse.data && dateResponse.data.news_list && dateResponse.data.news_list.length > 0) {
        setNewsData(dateResponse.data.news_list);
      } else {
        // 2. 특정 날짜에 뉴스가 없으면 최신 뉴스로 fallback
        const latestResponse = await getLatestTickerNews(selectedStock, 15);

        if (latestResponse.status === 'success' && latestResponse.data && latestResponse.data.news_list) {
          setNewsData(latestResponse.data.news_list);
        } else {
          console.warn('최신 뉴스 검색 실패:', latestResponse);
          setNewsData([]);
        }
      }
    } catch (err) {
      console.error('뉴스 데이터 가져오기 실패:', err);
      setNewsData([]);
    } finally {
      setNewsLoading(false);
    }
  };

  const closeNewsModal = () => {
    setShowNewsModal(false);
    setCurrentNewsEvent(null);
    setNewsData([]);
  };

  useEffect(() => {
    fetchVolatilityData();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchVolatilityData]);

  return {
    volatilityData,
    selectedStock,
    newsData,
    showNewsModal,
    currentNewsEvent,
    loading,
    newsLoading,
    error,
    actions: {
      setSelectedStock,
      openNewsModal,
      closeNewsModal,
      refetch: fetchVolatilityData
    }
  };
};
