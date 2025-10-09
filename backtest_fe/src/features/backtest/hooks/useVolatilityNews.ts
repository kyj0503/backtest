import { useState, useEffect } from 'react';
import {
  VolatilityEvent,
  NewsItem,
} from '../model/volatility-news-types';
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

  // 현금이 아닌 유효한 심볼만 필터링
  const validSymbols = symbols.filter(symbol => 
    symbol.toUpperCase() !== 'CASH' && symbol !== '현금'
  );

  const fetchVolatilityData = async () => {
    if (!enabled || validSymbols.length === 0) return;

    setLoading(true);
    setError(null);
    
    try {
      const results: { [key: string]: VolatilityEvent[] } = {};
      
      for (const symbol of validSymbols) {
        try {
          const response = await getStockVolatilityNews(symbol, startDate, endDate);
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
      
      setVolatilityData(results);
      
      // 첫 번째 유효한 종목을 선택
      if (validSymbols.length > 0 && !selectedStock) {
        setSelectedStock(validSymbols[0]);
      }
    } catch (err) {
      console.error('변동성 데이터 가져오기 실패:', err);
      setError('변동성 데이터를 가져오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const openNewsModal = async (_date: string, event: VolatilityEvent) => {
    if (!canViewNews) {
      return;
    }
    setCurrentNewsEvent(event);
    setShowNewsModal(true);
    setNewsLoading(true);

    try {
      console.log(`뉴스 검색 시작: ${selectedStock}, 날짜: ${event.date}`);

      // 1. 먼저 특정 날짜의 뉴스 조회 시도 (DB 캐싱 사용)
      const dateResponse = await getNaverNews(selectedStock, event.date, 50);

      if (dateResponse.status === 'success' && dateResponse.data && dateResponse.data.news_list && dateResponse.data.news_list.length > 0) {
        console.log(`${selectedStock}의 ${event.date} 뉴스 ${dateResponse.data.news_list.length}개를 찾았습니다. (캐시 사용: ${dateResponse.data.from_cache || false})`);
        setNewsData(dateResponse.data.news_list);
      } else {
        // 2. 특정 날짜에 뉴스가 없으면 최신 뉴스로 fallback
        console.log(`${selectedStock}의 ${event.date} 뉴스가 없습니다. 최신 뉴스를 가져옵니다.`);

        const latestResponse = await getLatestTickerNews(selectedStock, 15);

        if (latestResponse.status === 'success' && latestResponse.data && latestResponse.data.news_list) {
          console.log(`${selectedStock}의 최신 뉴스 ${latestResponse.data.news_list.length}개를 찾았습니다.`);
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
  }, [validSymbols.join(','), startDate, endDate, enabled]);

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
