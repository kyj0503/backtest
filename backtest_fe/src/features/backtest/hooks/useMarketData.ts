
import { useCallback } from 'react';
import { useAsync } from '@/shared/hooks/useAsync';
import { BacktestService } from '../services/backtestService';

export function useMarketData() {
  const newsState = useAsync(
    () => BacktestService.searchNews('주식 시장'),
    [],
    { immediate: false }
  );

  const exchangeRateState = useAsync(
    () => BacktestService.getExchangeRate(),
    [],
    { immediate: false }
  );

  const volatilityState = useAsync(
    () => BacktestService.getVolatilityData(['AAPL', 'GOOGL', 'MSFT']),
    [],
    { immediate: false }
  );

  const loadNews = useCallback((query: string) => {
    return BacktestService.searchNews(query);
  }, []);

  const loadVolatilityData = useCallback((symbols: string[]) => {
    return BacktestService.getVolatilityData(symbols);
  }, []);

  return {
    news: newsState,
    exchangeRate: exchangeRateState,
    volatility: volatilityState,
    loadNews,
    loadVolatilityData,
  };
}
