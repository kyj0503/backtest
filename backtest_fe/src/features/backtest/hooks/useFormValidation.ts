import { useState, useCallback } from 'react';
import { BacktestFormState } from '../model/types/backtest-form-types';
import { backtestFormHelpers } from '../model/backtestFormReducer';

export interface UseFormValidationReturn {
  errors: string[];
  isValid: boolean;
  validateForm: (formState: BacktestFormState) => boolean;
  addError: (error: string) => void;
  removeError: (error: string) => void;
  clearErrors: () => void;
  setErrors: (errors: string[]) => void;
}

/**
 * 백테스트 폼 전체 검증을 수행합니다.
 * backtestFormHelpers.validatePortfolio()에 위임하여 포트폴리오 검증을 수행하고,
 * 날짜/수수료 검증을 추가합니다.
 */
export function validateBacktestForm(formState: BacktestFormState): string[] {
  const errors: string[] = [];

  // 포트폴리오 검증 (중복/빈값/금액/DCA/비중 합계)
  errors.push(...backtestFormHelpers.validatePortfolio(formState.portfolio));

  // 날짜 검증
  if (!formState.dates.startDate) {
    errors.push('시작 날짜를 선택해주세요.');
  }
  if (!formState.dates.endDate) {
    errors.push('종료 날짜를 선택해주세요.');
  }
  if (formState.dates.startDate && formState.dates.endDate &&
      formState.dates.startDate >= formState.dates.endDate) {
    errors.push('시작 날짜는 종료 날짜보다 이전이어야 합니다.');
  }

  // 수수료 검증
  if (formState.settings.commission < 0 || formState.settings.commission > 5) {
    errors.push('수수료는 0% ~ 5% 사이여야 합니다.');
  }

  return errors;
}

export const useFormValidation = (): UseFormValidationReturn => {
  const [errors, setErrorsState] = useState<string[]>([]);

  const validateForm = useCallback((formState: BacktestFormState): boolean => {
    const newErrors = validateBacktestForm(formState);
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
