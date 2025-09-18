import { useState, useEffect } from 'react';
import { getStockData } from '../api/backtestApi';
import { StockDataItem } from '../model/backtest-result-types';

interface UseStockDataParams {
  symbols: string[];
  startDate: string;
  endDate: string;
  enabled?: boolean;
}

interface UseStockDataReturn {
  stocksData: StockDataItem[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * 주가 데이터 페칭을 위한 커스텀 훅
 * 여러 종목의 주가 데이터를 병렬로 가져오고 캐싱 기능 제공
 */
export const useStockData = ({ 
  symbols, 
  startDate, 
  endDate, 
  enabled = true 
}: UseStockDataParams): UseStockDataReturn => {
  const [stocksData, setStocksData] = useState<StockDataItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 현금 자산이 아닌 유효한 심볼만 필터링
  const validSymbols = symbols.filter(symbol => 
    symbol.toUpperCase() !== 'CASH' && symbol !== '현금'
  );

  const fetchStockData = async () => {
    if (!enabled || validSymbols.length === 0) return;

    setLoading(true);
    setError(null);
    
    try {
      const stockDataResults: StockDataItem[] = [];

      // 병렬로 모든 종목 데이터 가져오기
      const fetchPromises = validSymbols.map(async (symbol) => {
        try {
          const response = await getStockData(symbol, startDate, endDate);
          if (response.status === 'success' && response.data.price_data.length > 0) {
            return {
              symbol: symbol,
              data: response.data.price_data
            };
          }
          return null;
        } catch (error) {
          console.error(`주가 데이터 가져오기 실패 (${symbol}):`, error);
          return null;
        }
      });

      const results = await Promise.all(fetchPromises);
      
      // null이 아닌 결과만 필터링
      results.forEach(result => {
        if (result) {
          stockDataResults.push(result);
        }
      });

      setStocksData(stockDataResults);
    } catch (err) {
      console.error('주가 데이터 가져오기 전체 실패:', err);
      setError('주가 데이터를 가져오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStockData();
  }, [validSymbols.join(','), startDate, endDate, enabled]);

  return {
    stocksData,
    loading,
    error,
    refetch: fetchStockData
  };
};
