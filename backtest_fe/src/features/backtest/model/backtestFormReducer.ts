import { ASSET_TYPES, getDcaWeeks } from './strategyConfig';
import { BacktestFormState, BacktestFormAction, Stock } from './backtest-form-types';

export function backtestFormReducer(state: BacktestFormState, action: BacktestFormAction): BacktestFormState {
  // 비중 기반 모드에서 amount 자동 계산 (DCA 고려)
  const recalcAmountsByWeight = (portfolio: Stock[], totalInvestment: number, startDate?: string, endDate?: string) => {
    if (!startDate || !endDate || totalInvestment === 0) {
      // 날짜 정보 없으면 기본 계산
      return portfolio.map(s =>
        typeof s.weight === 'number'
          ? { ...s, amount: Math.round((s.weight / 100) * totalInvestment) }
          : s
      );
    }

    const start = new Date(startDate);
    const end = new Date(endDate);
    const timeDiff = end.getTime() - start.getTime();
    const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
    const weeks = Math.floor(days / 7);

    // Step 1: weight 항목들의 인덱스 찾기
    const weightIndices: number[] = [];
    portfolio.forEach((s, index) => {
      if (typeof s.weight === 'number') {
        weightIndices.push(index);
      }
    });

    if (weightIndices.length === 0) return portfolio;

    // Step 2: 각 weight 항목의 amount 계산
    const perPeriodAmounts: (number | null)[] = new Array(portfolio.length).fill(null);
    let accumulatedTotalAmount = 0;  // 비 DCA 종목들의 누적 투자액

    weightIndices.forEach((index, pos) => {
      const s = portfolio[index];
      const weightPercent = s.weight || 0;
      const totalAmountForStock = (weightPercent / 100) * totalInvestment;
      const isLastWeightItem = pos === weightIndices.length - 1;

      if (s.investmentType === 'dca') {
        const intervalWeeks = getDcaWeeks(s.dcaFrequency || 'weekly_4');
        const dcaPeriods = Math.max(1, Math.floor(weeks / intervalWeeks) + 1);
        
        if (isLastWeightItem) {
          // 마지막 DCA 항목: 정확한 오차 보정
          // remainingTotal = 총액 - (이전 종목들의 실제 투자액)
          const remainingTotal = totalInvestment - accumulatedTotalAmount;
          // 회당 금액 = 남은 총액 / 기간 (버림으로 보수적 계산)
          const perPeriodAmount = Math.floor(remainingTotal / dcaPeriods);
          perPeriodAmounts[index] = perPeriodAmount;
        } else {
          // 일반 DCA 항목
          const perPeriodAmount = Math.round(totalAmountForStock / dcaPeriods);
          perPeriodAmounts[index] = perPeriodAmount;
          accumulatedTotalAmount += Math.round(totalAmountForStock);
        }
      } else {
        // 일시불 항목
        const amount = Math.round(totalAmountForStock);
        perPeriodAmounts[index] = amount;
        if (!isLastWeightItem) {
          accumulatedTotalAmount += amount;
        } else {
          // 마지막 일시불 항목: 오차 보정
          const remainingTotal = totalInvestment - accumulatedTotalAmount;
          perPeriodAmounts[index] = remainingTotal;
        }
      }
    });

    // Step 3: 최종 결과 반영
    return portfolio.map((s, index) => {
      if (perPeriodAmounts[index] !== null) {
        return { ...s, amount: perPeriodAmounts[index]! };
      }
      return s;
    });
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
          // DCA 주기 변경시에도 amount 자동 계산 필요
          if (field === 'dcaFrequency' || field === 'investmentType') {
            return { ...stock, [field]: value };
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
      // 비중 기반 모드면 amount 자동 계산 (DCA 고려)
      if (state.portfolioInputMode === 'weight') {
        updatedPortfolio = recalcAmountsByWeight(
          updatedPortfolio,
          state.totalInvestment,
          state.dates.startDate,
          state.dates.endDate
        );
      } else {
        // 금액 기반 모드에서 weight가 하나라도 있으면 amount를 weight 기준으로 동기화
        const hasAnyWeight = updatedPortfolio.some((s) => typeof s.weight === 'number');
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
        updatedPortfolio = state.portfolio.map((s) => ({
          ...s,
          weight: total > 0 ? Number(((s.amount / total) * 100).toFixed(2)) : 0
        }));
        // amount는 totalInvestment 기준으로 재계산 (DCA 고려)
        updatedPortfolio = recalcAmountsByWeight(
          updatedPortfolio,
          state.totalInvestment,
          state.dates.startDate,
          state.dates.endDate
        );
      } else {
        // 비중→금액: weight를 undefined로 초기화
        updatedPortfolio = state.portfolio.map((s) => ({ ...s, weight: undefined }));
      }
      return {
        ...state,
        portfolioInputMode: action.payload,
        portfolio: updatedPortfolio
      };
    }

    case 'SET_TOTAL_INVESTMENT': {
      // 전체 투자금액 변경 시 비중 기반 모드면 amount 자동 계산 (DCA 고려)
      let updatedPortfolio = state.portfolio;
      if (state.portfolioInputMode === 'weight') {
        updatedPortfolio = recalcAmountsByWeight(
          state.portfolio,
          action.payload,
          state.dates.startDate,
          state.dates.endDate
        );
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

    case 'SET_START_DATE': {
      const newDates = {
        ...state.dates,
        startDate: action.payload
      };
      // 비중 기반 모드일 때 날짜 변경 시 amount 재계산 (DCA 기간이 바뀔 수 있음)
      let updatedPortfolio = state.portfolio;
      if (state.portfolioInputMode === 'weight') {
        updatedPortfolio = recalcAmountsByWeight(
          state.portfolio,
          state.totalInvestment,
          action.payload,
          state.dates.endDate
        );
      }
      return {
        ...state,
        dates: newDates,
        portfolio: updatedPortfolio
      };
    }

    case 'SET_END_DATE': {
      const newDates = {
        ...state.dates,
        endDate: action.payload
      };
      // 비중 기반 모드일 때 날짜 변경 시 amount 재계산 (DCA 기간이 바뀔 수 있음)
      let updatedPortfolio = state.portfolio;
      if (state.portfolioInputMode === 'weight') {
        updatedPortfolio = recalcAmountsByWeight(
          state.portfolio,
          state.totalInvestment,
          state.dates.startDate,
          action.payload
        );
      }
      return {
        ...state,
        dates: newDates,
        portfolio: updatedPortfolio
      };
    }

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
          dcaFrequency: 'weekly_4'
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
          rebalanceFrequency: 'weekly_4',
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
    dcaFrequency: 'weekly_4',
    assetType: ASSET_TYPES.STOCK
  }),

  addCash: (): Stock => ({
    symbol: 'CASH',
    amount: 10000,
    weight: undefined,
    investmentType: 'lump_sum',
    dcaFrequency: 'weekly_4',
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

    // 중복 종목 검증 (현금 제외)
    const symbolCounts = new Map<string, number>();
    portfolio.forEach(stock => {
      if (stock.assetType !== ASSET_TYPES.CASH && stock.symbol.trim()) {
        const normalizedSymbol = stock.symbol.trim().toUpperCase();
        symbolCounts.set(normalizedSymbol, (symbolCounts.get(normalizedSymbol) || 0) + 1);
      }
    });
    
    symbolCounts.forEach((count, symbol) => {
      if (count > 1) {
        errors.push(`종목 ${symbol}이(가) ${count}번 중복되었습니다. 같은 종목은 한 번만 추가할 수 있습니다.`);
      }
    });

    portfolio.forEach((stock, index) => {
      if (!stock.symbol.trim()) {
        errors.push(`${index + 1}번째 종목의 심볼을 입력해주세요.`);
      }
      if (stock.amount < 100) {
        errors.push(`${index + 1}번째 종목의 투자 금액은 최소 $100 이상이어야 합니다.`);
      }
      if (stock.investmentType === 'dca' && !stock.dcaFrequency) {
        errors.push(`${index + 1}번째 종목의 DCA 투자 주기를 선택해주세요.`);
      }
    });

    // If user provided weights, validate they sum to ~100
    const weights = portfolio.map(s => typeof s.weight === 'number' ? s.weight! : 0);
    const hasAnyWeight = weights.some(w => w > 0);
    if (hasAnyWeight) {
      const totalWeight = weights.reduce((a, b) => a + b, 0);
      // 비중 합계 검증: 100% ± 5% 범위 허용 (반올림 오차 대비)
      // 예: 50% + 50% = 100% OK
      //     50.1% + 49.9% = 100% OK
      //     60% + 40% = 100% OK
      //     52.5% + 52.5% = 105% NG (5% 초과)
      if (totalWeight < 95 || totalWeight > 105) {
        errors.push(`포트폴리오 비중 합계가 100%에 가까워야 합니다 (95~105% 범위). 현재 ${totalWeight.toFixed(1)}%.`);
      }
    }

    return errors;
  }
};
