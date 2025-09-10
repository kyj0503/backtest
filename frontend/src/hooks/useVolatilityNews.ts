import { useState, useEffect } from 'react';
import { backtestApiService } from '../services/api';
import { 
  VolatilityEvent, 
  NewsItem, 
  getCompanyName
} from '../types/volatility-news';

interface UseVolatilityNewsParams {
  symbols: string[];
  startDate: string;
  endDate: string;
  enabled?: boolean;
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
  enabled = true 
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
          const response = await backtestApiService.getStockVolatilityNews(symbol, startDate, endDate);
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
    // _date 매개변수는 호환성을 위해 유지하지만, 현재는 회사명만으로 검색
    setCurrentNewsEvent(event);
    setShowNewsModal(true);
    setNewsLoading(true);
    
    try {
      const companyName = getCompanyName(selectedStock);
      
      // backtestApiService를 통해 뉴스 검색 (간단한 검색 사용)
      console.log(`뉴스 검색 시작: ${companyName} (${selectedStock})`);
      
      const response = await backtestApiService.searchNews(companyName, 15);
      
      if (response.status === 'success' && response.data && response.data.news_list) {
        console.log(`${companyName}에 대한 뉴스 ${response.data.news_list.length}개를 찾았습니다.`);
        setNewsData(response.data.news_list);
      } else {
        console.warn('뉴스 검색 실패:', response);
        setNewsData([]);
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
