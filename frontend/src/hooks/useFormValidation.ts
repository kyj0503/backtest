import { useState, useCallback } from 'react';
import { BacktestFormState } from '../types/backtest-form';

export interface UseFormValidationReturn {
  errors: string[];
  isValid: boolean;
  validateForm: (formState: BacktestFormState) => boolean;
  addError: (error: string) => void;
  removeError: (error: string) => void;
  clearErrors: () => void;
  setErrors: (errors: string[]) => void;
}

export const useFormValidation = (): UseFormValidationReturn => {
  const [errors, setErrorsState] = useState<string[]>([]);

  const validateForm = useCallback((formState: BacktestFormState): boolean => {
    const newErrors: string[] = [];
    
    // 포트폴리오 검증
    if (formState.portfolio.length === 0) {
      newErrors.push('최소 하나의 종목을 추가해야 합니다.');
    }

    formState.portfolio.forEach((stock, index) => {
      if (!stock.symbol.trim()) {
        newErrors.push(`${index + 1}번째 종목의 심볼을 입력해주세요.`);
      }
      if (stock.amount < 100) {
        newErrors.push(`${index + 1}번째 종목의 투자 금액은 최소 $100 이상이어야 합니다.`);
      }
      if (stock.investmentType === 'dca' && (!stock.dcaPeriods || stock.dcaPeriods < 1)) {
        newErrors.push(`${index + 1}번째 종목의 DCA 기간을 설정해주세요.`);
      }
    });
    
    // 날짜 검증
    if (!formState.dates.startDate) {
      newErrors.push('시작 날짜를 선택해주세요.');
    }
    if (!formState.dates.endDate) {
      newErrors.push('종료 날짜를 선택해주세요.');
    }
    if (formState.dates.startDate && formState.dates.endDate && 
        formState.dates.startDate >= formState.dates.endDate) {
      newErrors.push('시작 날짜는 종료 날짜보다 이전이어야 합니다.');
    }
    
    // 수수료 검증
    if (formState.settings.commission < 0 || formState.settings.commission > 5) {
      newErrors.push('수수료는 0% ~ 5% 사이여야 합니다.');
    }

    // 총 투자 금액 검증
    const totalAmount = formState.portfolio.reduce((sum, stock) => sum + stock.amount, 0);
    if (totalAmount < 1000) {
      newErrors.push('총 투자 금액은 최소 $1,000 이상이어야 합니다.');
    }

    setErrorsState(newErrors);
    return newErrors.length === 0;
  }, []);

  const addError = useCallback((error: string) => {
    setErrorsState(prev => [...prev.filter(e => e !== error), error]);
  }, []);

  const removeError = useCallback((error: string) => {
    setErrorsState(prev => prev.filter(e => e !== error));
  }, []);

  const clearErrors = useCallback(() => {
    setErrorsState([]);
  }, []);

  const setErrors = useCallback((newErrors: string[]) => {
    setErrorsState(newErrors);
  }, []);

  return {
    errors,
    isValid: errors.length === 0,
    validateForm,
    addError,
    removeError,
    clearErrors,
    setErrors
  };
};
