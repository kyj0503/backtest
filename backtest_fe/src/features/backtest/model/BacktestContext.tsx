import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { BacktestFormState, initialBacktestFormState, Stock } from './backtest-form-types';
import { backtestFormReducer } from './backtestFormReducer';

interface BacktestContextType {
  state: BacktestFormState;
  actions: {
    // 포트폴리오 관련
    updateStock: (index: number, field: keyof Stock, value: string | number) => void;
    addStock: () => void;
    addCash: () => void;
    removeStock: (index: number) => void;
    
    // 날짜 관련
    setStartDate: (date: string) => void;
    setEndDate: (date: string) => void;
    
    // 전략 관련
    setSelectedStrategy: (strategy: string) => void;
    updateStrategyParam: (key: string, value: string) => void;
    
    // 설정 관련
    setRebalanceFrequency: (frequency: string) => void;
    setCommission: (commission: number) => void;
    
    // UI 관련
    setErrors: (errors: string[]) => void;
    setLoading: (loading: boolean) => void;
    resetForm: () => void;
  };
}

const BacktestContext = createContext<BacktestContextType | undefined>(undefined);

interface BacktestProviderProps {
  children: ReactNode;
  initialState?: Partial<BacktestFormState>;
}

export const BacktestProvider: React.FC<BacktestProviderProps> = ({ 
  children, 
  initialState 
}) => {
  const [state, dispatch] = useReducer(
    backtestFormReducer,
    { ...initialBacktestFormState, ...initialState }
  );

  const actions = {
    // 포트폴리오 관련
    updateStock: (index: number, field: keyof Stock, value: string | number) => {
      dispatch({ type: 'UPDATE_STOCK', payload: { index, field, value } });
    },

    addStock: () => {
      const newStock: Stock = {
        symbol: '',
        amount: 10000,
        investmentType: 'lump_sum',
        dcaPeriods: 12
      };
      dispatch({ type: 'ADD_STOCK', payload: newStock });
    },

    addCash: () => {
      const newCash: Stock = {
        symbol: 'CASH',
        amount: 10000,
        investmentType: 'lump_sum',
        dcaPeriods: 12
      };
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

  const value: BacktestContextType = {
    state,
    actions
  };

  return (
    <BacktestContext.Provider value={value}>
      {children}
    </BacktestContext.Provider>
  );
};

export const useBacktestContext = (): BacktestContextType => {
  const context = useContext(BacktestContext);
  if (context === undefined) {
    throw new Error('useBacktestContext must be used within a BacktestProvider');
  }
  return context;
};
