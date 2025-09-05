import { ASSET_TYPES } from '../constants/strategies';
import { BacktestFormState, BacktestFormAction, Stock } from '../types/backtest-form';

export function backtestFormReducer(state: BacktestFormState, action: BacktestFormAction): BacktestFormState {
  switch (action.type) {
    case 'SET_PORTFOLIO':
      return {
        ...state,
        portfolio: action.payload
      };

    case 'ADD_STOCK':
      return {
        ...state,
        portfolio: [...state.portfolio, action.payload]
      };

    case 'UPDATE_STOCK':
      const { index, field, value } = action.payload;
      const updatedPortfolio = state.portfolio.map((stock, i) => 
        i === index ? { ...stock, [field]: value } : stock
      );
      return {
        ...state,
        portfolio: updatedPortfolio
      };

    case 'REMOVE_STOCK':
      return {
        ...state,
        portfolio: state.portfolio.filter((_, index) => index !== action.payload)
      };

    case 'SET_START_DATE':
      return {
        ...state,
        dates: {
          ...state.dates,
          startDate: action.payload
        }
      };

    case 'SET_END_DATE':
      return {
        ...state,
        dates: {
          ...state.dates,
          endDate: action.payload
        }
      };

    case 'SET_STRATEGY':
      return {
        ...state,
        strategy: {
          ...state.strategy,
          selectedStrategy: action.payload
        }
      };

    case 'SET_STRATEGY_PARAMS':
      return {
        ...state,
        strategy: {
          ...state.strategy,
          strategyParams: action.payload
        }
      };

    case 'UPDATE_STRATEGY_PARAM':
      return {
        ...state,
        strategy: {
          ...state.strategy,
          strategyParams: {
            ...state.strategy.strategyParams,
            [action.payload.key]: action.payload.value
          }
        }
      };

    case 'SET_REBALANCE_FREQUENCY':
      return {
        ...state,
        settings: {
          ...state.settings,
          rebalanceFrequency: action.payload
        }
      };

    case 'SET_COMMISSION':
      return {
        ...state,
        settings: {
          ...state.settings,
          commission: action.payload
        }
      };

    case 'SET_ERRORS':
      return {
        ...state,
        ui: {
          ...state.ui,
          errors: action.payload
        }
      };

    case 'SET_LOADING':
      return {
        ...state,
        ui: {
          ...state.ui,
          isLoading: action.payload
        }
      };

    case 'RESET_FORM':
      return {
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
        }
      };

    default:
      return state;
  }
}

// 헬퍼 함수들
export const backtestFormHelpers = {
  addStock: (): Stock => ({
    symbol: '',
    amount: 10000,
    investmentType: 'lump_sum',
    dcaPeriods: 12,
    assetType: ASSET_TYPES.STOCK
  }),

  addCash: (): Stock => ({
    symbol: 'CASH',
    amount: 10000,
    investmentType: 'lump_sum',
    dcaPeriods: 12,
    assetType: ASSET_TYPES.CASH
  }),

  getTotalAmount: (portfolio: Stock[]): number => {
    return portfolio.reduce((sum, stock) => sum + stock.amount, 0);
  },

  validatePortfolio: (portfolio: Stock[]): string[] => {
    const errors: string[] = [];
    
    if (portfolio.length === 0) {
      errors.push('최소 하나의 종목을 추가해야 합니다.');
      return errors;
    }

    portfolio.forEach((stock, index) => {
      if (!stock.symbol.trim()) {
        errors.push(`${index + 1}번째 종목의 심볼을 입력해주세요.`);
      }
      if (stock.amount < 100) {
        errors.push(`${index + 1}번째 종목의 투자 금액은 최소 $100 이상이어야 합니다.`);
      }
      if (stock.investmentType === 'dca' && (!stock.dcaPeriods || stock.dcaPeriods < 1)) {
        errors.push(`${index + 1}번째 종목의 DCA 기간을 설정해주세요.`);
      }
    });

    return errors;
  }
};
