
import { useAsync } from '@/shared/hooks/useAsync';
import { BacktestService } from '../services/backtestService';
import { Strategy } from '../model/api-types';

export function useStrategies() {
  return useAsync<Strategy[]>(
    () => BacktestService.getStrategies(),
    [],
    {
      onError: (error) => {
        console.error('Failed to load strategies:', error);
      }
    }
  );
}

export function useStrategy(strategyName: string | null) {
  return useAsync<Strategy>(
    () => BacktestService.getStrategy(strategyName!),
    [strategyName],
    { 
      immediate: !!strategyName,
      onError: (error) => {
        console.error(`Failed to load strategy ${strategyName}:`, error);
      }
    }
  );
}
