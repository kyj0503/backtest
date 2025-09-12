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

    case 'UPDATE_STOCK': {
      const { index, field, value } = action.payload;
      let updatedPortfolio = state.portfolio.map((stock, i) => {
        if (i !== index) return stock;
        // amount를 직접 수정하면 weight를 undefined로 초기화(자동계산 모드)
        if (field === 'amount') {
          return { ...stock, amount: Number(value), weight: undefined };
        }
        // weight를 직접 수정하면 amount는 weight에서 계산됨(수동 비중 모드)
        if (field === 'weight') {
          return { ...stock, weight: Number(value) };
        }
        return { ...stock, [field]: value };
      });

      // weight가 하나라도 있으면 amount를 weight 기준으로 동기화
      const hasAnyWeight = updatedPortfolio.some(s => typeof s.weight === 'number');
      if (hasAnyWeight) {
        const totalBudget = backtestFormHelpers.getTotalAmount(updatedPortfolio);
        updatedPortfolio = backtestFormHelpers.applyWeightsToAmounts(updatedPortfolio, totalBudget);
      }
      return {
        ...state,
        portfolio: updatedPortfolio
      };
    }

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
    weight: undefined,
    investmentType: 'lump_sum',
    dcaPeriods: 12,
    assetType: ASSET_TYPES.STOCK
  }),

  addCash: (): Stock => ({
    symbol: 'CASH',
    amount: 10000,
    weight: undefined,
    investmentType: 'lump_sum',
    dcaPeriods: 12,
    assetType: ASSET_TYPES.CASH
  }),

  getTotalAmount: (portfolio: Stock[]): number => {
    return portfolio.reduce((sum, stock) => sum + stock.amount, 0);
  },

  // If weights are provided by the user (not undefined), convert them to amounts based on total budget
  applyWeightsToAmounts: (portfolio: Stock[], totalBudget?: number): Stock[] => {
    const hasWeights = portfolio.some(s => typeof s.weight === 'number');
    if (!hasWeights) return portfolio;
    const budget = typeof totalBudget === 'number' ? totalBudget : backtestFormHelpers.getTotalAmount(portfolio);
    if (budget <= 0) return portfolio;
    return portfolio.map(s => ({ ...s, amount: typeof s.weight === 'number' ? Math.round((s.weight! / 100) * budget) : s.amount }));
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

    // If user provided weights, validate they sum to ~100
    const weights = portfolio.map(s => typeof s.weight === 'number' ? s.weight! : 0);
    const hasAnyWeight = weights.some(w => w > 0);
    if (hasAnyWeight) {
      const totalWeight = weights.reduce((a, b) => a + b, 0);
      if (Math.abs(totalWeight - 100) > 0.5) {
        errors.push(`포트폴리오 비중 합계가 100%가 아닙니다 (현재 ${totalWeight.toFixed(1)}%).`);
      }
    }

    return errors;
  }
};
