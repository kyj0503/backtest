import { AssetType } from './strategyConfig';

export interface Stock {
  symbol: string;
  amount: number;
  // Optional allocation weight in percent (0-100). If provided, UI will treat allocation as weight-based
  weight?: number;
  investmentType: 'lump_sum' | 'dca';
  dcaPeriods?: number;
  assetType?: AssetType;
}

export type PortfolioInputMode = 'amount' | 'weight';

export interface BacktestFormState {
  portfolio: Stock[];
  dates: {
    startDate: string;
    endDate: string;
  };
  strategy: {
    selectedStrategy: string;
    strategyParams: Record<string, any>;
  };
  settings: {
    rebalanceFrequency: string;
    commission: number;
  };
  ui: {
    errors: string[];
    isLoading: boolean;
  };
  portfolioInputMode: PortfolioInputMode;
  totalInvestment: number;
}

export type BacktestFormAction =
  | { type: 'SET_PORTFOLIO'; payload: Stock[] }
  | { type: 'ADD_STOCK'; payload: Stock }
  | { type: 'UPDATE_STOCK'; payload: { index: number; field: keyof Stock; value: string | number } }
  | { type: 'REMOVE_STOCK'; payload: number }
  | { type: 'SET_START_DATE'; payload: string }
  | { type: 'SET_END_DATE'; payload: string }
  | { type: 'SET_STRATEGY'; payload: string }
  | { type: 'SET_STRATEGY_PARAMS'; payload: Record<string, any> }
  | { type: 'UPDATE_STRATEGY_PARAM'; payload: { key: string; value: string } }
  | { type: 'SET_REBALANCE_FREQUENCY'; payload: string }
  | { type: 'SET_COMMISSION'; payload: number }
  | { type: 'SET_ERRORS'; payload: string[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_PORTFOLIO_INPUT_MODE'; payload: PortfolioInputMode }
  | { type: 'SET_TOTAL_INVESTMENT'; payload: number }
  | { type: 'RESET_FORM' };

export const initialBacktestFormState: BacktestFormState = {
  portfolio: [{ 
    symbol: '', 
    amount: 10000, 
    investmentType: 'lump_sum',
    dcaPeriods: 12 
  }],
  dates: {
    startDate: '2023-01-01',
    endDate: '2024-12-31'
  },
  strategy: {
    selectedStrategy: 'buy_and_hold',
    strategyParams: {}
  },
  settings: {
    rebalanceFrequency: 'monthly',
    commission: 0.2
  },
  ui: {
    errors: [],
    isLoading: false
  },
  portfolioInputMode: 'amount',
  totalInvestment: 10000
};
