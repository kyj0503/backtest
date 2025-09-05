import { useCallback } from 'react';
import { Stock } from '../types/backtest-form';
import { ASSET_TYPES } from '../constants/strategies';

export interface UsePortfolioReturn {
  addStock: () => Stock;
  addCash: () => Stock;
  updateStock: (stocks: Stock[], index: number, field: keyof Stock, value: string | number) => Stock[];
  removeStock: (stocks: Stock[], index: number) => Stock[];
  getTotalAmount: (stocks: Stock[]) => number;
  getPortfolioWeights: (stocks: Stock[]) => { symbol: string; weight: number }[];
  validatePortfolio: (stocks: Stock[]) => string[];
}

export const usePortfolio = (): UsePortfolioReturn => {
  const addStock = useCallback((): Stock => ({
    symbol: '',
    amount: 10000,
    investmentType: 'lump_sum',
    dcaPeriods: 12,
    assetType: ASSET_TYPES.STOCK
  }), []);

  const addCash = useCallback((): Stock => ({
    symbol: 'CASH',
    amount: 10000,
    investmentType: 'lump_sum',
    dcaPeriods: 12,
    assetType: ASSET_TYPES.CASH
  }), []);

  const updateStock = useCallback((
    stocks: Stock[], 
    index: number, 
    field: keyof Stock, 
    value: string | number
  ): Stock[] => {
    return stocks.map((stock, i) => 
      i === index ? { ...stock, [field]: value } : stock
    );
  }, []);

  const removeStock = useCallback((stocks: Stock[], index: number): Stock[] => {
    return stocks.filter((_, i) => i !== index);
  }, []);

  const getTotalAmount = useCallback((stocks: Stock[]): number => {
    return stocks.reduce((sum, stock) => sum + stock.amount, 0);
  }, []);

  const getPortfolioWeights = useCallback((stocks: Stock[]): { symbol: string; weight: number }[] => {
    const total = getTotalAmount(stocks);
    return stocks.map(stock => ({
      symbol: stock.symbol,
      weight: total > 0 ? (stock.amount / total) * 100 : 0
    }));
  }, [getTotalAmount]);

  const validatePortfolio = useCallback((stocks: Stock[]): string[] => {
    const errors: string[] = [];
    
    if (stocks.length === 0) {
      errors.push('최소 하나의 종목을 추가해야 합니다.');
      return errors;
    }

    stocks.forEach((stock, index) => {
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

    // 중복 종목 검사 (현금 제외)
    const symbols = stocks
      .filter(stock => stock.assetType !== ASSET_TYPES.CASH)
      .map(stock => stock.symbol.toUpperCase());
    const duplicates = symbols.filter((symbol, index) => symbols.indexOf(symbol) !== index);
    
    if (duplicates.length > 0) {
      errors.push(`중복된 종목이 있습니다: ${[...new Set(duplicates)].join(', ')}`);
    }

    return errors;
  }, []);

  return {
    addStock,
    addCash,
    updateStock,
    removeStock,
    getTotalAmount,
    getPortfolioWeights,
    validatePortfolio
  };
};
