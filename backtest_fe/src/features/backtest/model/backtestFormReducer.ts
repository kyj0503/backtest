import { ASSET_TYPES } from './strategyConfig';
import { BacktestFormState, BacktestFormAction, Stock } from './backtest-form-types';

export function backtestFormReducer(state: BacktestFormState, action: BacktestFormAction): BacktestFormState {
  // 비중 기반 모드에서 amount 자동 계산
  const recalcAmountsByWeight = (portfolio: Stock[], totalInvestment: number) => {
    return portfolio.map(s =>
      typeof s.weight === 'number'
        ? { ...s, amount: Math.round((s.weight / 100) * totalInvestment) }
        : s
    );
  };

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
        if (state.portfolioInputMode === 'weight') {
          // 비중 기반 모드: weight만 수정 가능, amount는 자동 계산
          if (field === 'weight') {
            return { ...stock, weight: Number(value) };
          }
          // 나머지 필드는 그대로
          return { ...stock, [field]: value };
        } else {
          // 금액 기반 모드: amount 직접 수정, weight는 undefined로 초기화
          if (field === 'amount') {
            return { ...stock, amount: Number(value), weight: undefined };
          }
          if (field === 'weight') {
            return { ...stock, weight: Number(value) };
          }
          return { ...stock, [field]: value };
        }
      });
      // 비중 기반 모드면 amount 자동 계산
      if (state.portfolioInputMode === 'weight') {
        updatedPortfolio = recalcAmountsByWeight(updatedPortfolio, state.totalInvestment);
      } else {
        // 금액 기반 모드에서 weight가 하나라도 있으면 amount를 weight 기준으로 동기화
        const hasAnyWeight = updatedPortfolio.some(s => typeof s.weight === 'number');
        if (hasAnyWeight) {
          const totalBudget = backtestFormHelpers.getTotalAmount(updatedPortfolio);
          updatedPortfolio = backtestFormHelpers.applyWeightsToAmounts(updatedPortfolio, totalBudget);
        }
      }
      return {
        ...state,
        portfolio: updatedPortfolio
      };
    }
    case 'SET_PORTFOLIO_INPUT_MODE': {
      // 모드 전환 시 상태 변환: 금액→비중, 비중→금액
      let updatedPortfolio = state.portfolio;
      if (action.payload === 'weight') {
        // 금액→비중: 현재 금액 비율로 weight 세팅
        const total = backtestFormHelpers.getTotalAmount(state.portfolio);
        updatedPortfolio = state.portfolio.map(s => ({
          ...s,
          weight: total > 0 ? Number(((s.amount / total) * 100).toFixed(2)) : 0
        }));
        // amount는 totalInvestment 기준으로 재계산
        updatedPortfolio = recalcAmountsByWeight(updatedPortfolio, state.totalInvestment);
      } else {
        // 비중→금액: weight를 undefined로 초기화
        updatedPortfolio = state.portfolio.map(s => ({ ...s, weight: undefined }));
      }
      return {
        ...state,
        portfolioInputMode: action.payload,
        portfolio: updatedPortfolio
      };
    }

    case 'SET_TOTAL_INVESTMENT': {
      // 전체 투자금액 변경 시 비중 기반 모드면 amount 자동 계산
      let updatedPortfolio = state.portfolio;
      if (state.portfolioInputMode === 'weight') {
        updatedPortfolio = recalcAmountsByWeight(state.portfolio, action.payload);
      }
      return {
        ...state,
        totalInvestment: action.payload,
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
          selectedStrategy: 'buy_hold_strategy',
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
