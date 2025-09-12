export interface UseBacktestFormReturn {
  state: BacktestFormState;
  actions: {
    updateStock: (index: number, field: keyof Stock, value: string | number) => void;
    addStock: () => void;
    addCash: () => void;
    removeStock: (index: number) => void;
    setStartDate: (date: string) => void;
    setEndDate: (date: string) => void;
    setSelectedStrategy: (strategy: string) => void;
    updateStrategyParam: (key: string, value: string) => void;
    setRebalanceFrequency: (frequency: string) => void;
    setCommission: (commission: number) => void;
    setErrors: (errors: string[]) => void;
    setLoading: (loading: boolean) => void;
    resetForm: () => void;
    setPortfolioInputMode: (mode: 'amount' | 'weight') => void;
    setTotalInvestment: (amount: number) => void;
  };
  helpers: {
    getTotalAmount: () => number;
    validateForm: () => string[];
  };
}
import { useReducer, useEffect } from 'react';
import { STRATEGY_CONFIGS } from '../constants/strategies';
import { BacktestFormState, Stock, initialBacktestFormState } from '../types/backtest-form';
import { backtestFormReducer, backtestFormHelpers } from '../reducers/backtestFormReducer';


export const useBacktestForm = (initialState?: Partial<BacktestFormState>): UseBacktestFormReturn => {
  const [state, dispatch] = useReducer(
    backtestFormReducer, 
    { ...initialBacktestFormState, ...initialState }
  );

  // 전략 변경 시 기본 파라미터 설정
  useEffect(() => {
    const config = STRATEGY_CONFIGS[state.strategy.selectedStrategy as keyof typeof STRATEGY_CONFIGS];
    if (config && config.parameters) {
      const defaultParams: Record<string, any> = {};
      Object.entries(config.parameters).forEach(([key, param]) => {
        defaultParams[key] = (param as any).default;
      });
      dispatch({ type: 'SET_STRATEGY_PARAMS', payload: defaultParams });
    } else {
      dispatch({ type: 'SET_STRATEGY_PARAMS', payload: {} });
    }
  }, [state.strategy.selectedStrategy]);

  const actions = {
    setPortfolioInputMode: (mode: 'amount' | 'weight') => {
      dispatch({ type: 'SET_PORTFOLIO_INPUT_MODE', payload: mode });
    },
    setTotalInvestment: (amount: number) => {
      dispatch({ type: 'SET_TOTAL_INVESTMENT', payload: amount });
    },
    updateStock: (index: number, field: keyof Stock, value: string | number) => {
      dispatch({ type: 'UPDATE_STOCK', payload: { index, field, value } });
    },

    addStock: () => {
      const newStock = backtestFormHelpers.addStock();
      dispatch({ type: 'ADD_STOCK', payload: newStock });
    },

    addCash: () => {
      const newCash = backtestFormHelpers.addCash();
      dispatch({ type: 'ADD_STOCK', payload: newCash });
    },

    removeStock: (index: number) => {
      dispatch({ type: 'REMOVE_STOCK', payload: index });
    },

    // 날짜 관련
    setStartDate: (date: string) => {
      dispatch({ type: 'SET_START_DATE', payload: date });
    },
    setEndDate: (date: string) => {
      dispatch({ type: 'SET_END_DATE', payload: date });
    },

    // 전략 관련
    setSelectedStrategy: (strategy: string) => {
      dispatch({ type: 'SET_STRATEGY', payload: strategy });
    },

    updateStrategyParam: (key: string, value: string) => {
      dispatch({ type: 'UPDATE_STRATEGY_PARAM', payload: { key, value } });
    },

    // 설정 관련
    setRebalanceFrequency: (frequency: string) => {
      dispatch({ type: 'SET_REBALANCE_FREQUENCY', payload: frequency });
    },

    setCommission: (commission: number) => {
      dispatch({ type: 'SET_COMMISSION', payload: commission });
    },

    // UI 관련
    setErrors: (errors: string[]) => {
      dispatch({ type: 'SET_ERRORS', payload: errors });
    },

    setLoading: (loading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: loading });
    },

    resetForm: () => {
      dispatch({ type: 'RESET_FORM' });
    }
  };

  const helpers = {
    getTotalAmount: () => backtestFormHelpers.getTotalAmount(state.portfolio),
    
    validateForm: () => {
      const errors: string[] = [];
      
      // 포트폴리오 검증
      const portfolioErrors = backtestFormHelpers.validatePortfolio(state.portfolio);
      errors.push(...portfolioErrors);
      
      // 날짜 검증
      if (!state.dates.startDate) {
        errors.push('시작 날짜를 선택해주세요.');
      }
      if (!state.dates.endDate) {
        errors.push('종료 날짜를 선택해주세요.');
      }
      if (state.dates.startDate && state.dates.endDate && state.dates.startDate >= state.dates.endDate) {
        errors.push('시작 날짜는 종료 날짜보다 이전이어야 합니다.');
      }
      
      // 수수료 검증
      if (state.settings.commission < 0 || state.settings.commission > 5) {
        errors.push('수수료는 0% ~ 5% 사이여야 합니다.');
      }

      return errors;
    }
  };

  return {
    state,
    actions,
    helpers
  };
};
