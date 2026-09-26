import { useState, useCallback } from 'react';
import { BacktestFormState } from '../model/types/backtest-form-types';
import { backtestFormHelpers } from '../model/backtestFormReducer';
import { ASSET_TYPES, VALIDATION_RULES, supportsDcaAndRebalancing } from '../model/strategyConfig';

export interface UseFormValidationReturn {
  errors: string[];
  isValid: boolean;
  validateForm: (formState: BacktestFormState) => boolean;
  addError: (error: string) => void;
  removeError: (error: string) => void;
  clearErrors: () => void;
  setErrors: (errors: string[]) => void;
}

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/**
 * 'YYYY-MM-DD' 두 날짜 사이의 일수(종료일 - 시작일).
 * 백엔드 엔드포인트의 `(end_date - start_date).days`와 같은 정의다 — 예를 들어
 * 2023-01-01 ~ 2023-01-31은 30일. 로컬 시간대/서머타임 영향을 받지 않도록 UTC 자정으로
 * 해석한다. 형식이 잘못됐으면 null.
 */
export function getBacktestPeriodDays(startDate: string, endDate: string): number | null {
  const toUtcMs = (value: string): number | null => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
    if (!match) return null;
    const ms = Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    return Number.isNaN(ms) ? null : ms;
  };
  const start = toUtcMs(startDate);
  const end = toUtcMs(endDate);
  if (start === null || end === null) return null;
  return Math.round((end - start) / MS_PER_DAY);
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

  // 기술적 전략은 분할 매수를 지원하지 않는다 (백엔드가 422로 거부 — A-02)
  if (!supportsDcaAndRebalancing(formState.strategy.selectedStrategy)) {
    const dcaSymbols = formState.portfolio
      .filter(stock => stock.investmentType === 'dca' && stock.assetType !== ASSET_TYPES.CASH)
      .map(stock => stock.symbol.toUpperCase() || '(빈 종목)');
    if (dcaSymbols.length > 0) {
      errors.push(
        `기술적 전략에서는 분할 매수(DCA)를 사용할 수 없습니다: ${dcaSymbols.join(', ')}. ` +
        '일시불로 바꾸거나 Buy & Hold 전략을 선택해주세요.'
      );
    }
  }

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
  } else if (formState.dates.startDate && formState.dates.endDate) {
    // 최소 기간 (A-17). 백엔드가 422로 거부하기 전에 같은 규칙·같은 문구로 막는다.
    // 문구는 backtest_be_fast/app/api/v1/endpoints/backtest.py의 ValidationError와 맞춘다.
    const periodDays = getBacktestPeriodDays(formState.dates.startDate, formState.dates.endDate);
    const minDays = VALIDATION_RULES.MIN_BACKTEST_PERIOD_DAYS;
    if (periodDays !== null && periodDays < minDays) {
      errors.push(`백테스트 기간이 너무 짧습니다: ${periodDays}일 (최소 ${minDays}일 필요)`);
    }
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
