/**
 * 폼 상태 관리를 위한 커스텀 훅
 */

import { useState, useCallback, useMemo } from 'react';
import { FormState } from '@/shared/types';

type ValidationRule<T> = {
  [K in keyof T]?: (value: T[K]) => string | null;
};

export function useForm<T extends Record<string, unknown>>(
  initialData: T,
  validationRules: ValidationRule<T> = {}
) {
  const [formState, setFormState] = useState<FormState<T>>({
    data: initialData,
    errors: {},
    isSubmitting: false,
    isValid: true,
  });

  // 필드 값 업데이트
  const setFieldValue = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setFormState(prev => {
      const newData = { ...prev.data, [field]: value };
      const fieldError = validationRules[field]?.(value);
      const newErrors = { ...prev.errors };
      
      if (fieldError) {
        newErrors[field] = fieldError;
      } else {
        delete newErrors[field];
      }

      const isValid = Object.keys(newErrors).length === 0;

      return {
        ...prev,
        data: newData,
        errors: newErrors,
        isValid,
      };
    });
  }, [validationRules]);

  // 필드 에러 설정
  const setFieldError = useCallback(<K extends keyof T>(field: K, error: string) => {
    setFormState(prev => ({
      ...prev,
      errors: { ...prev.errors, [field]: error },
      isValid: false,
    }));
  }, []);

  // 전체 폼 검증
  const validateForm = useCallback(() => {
    const errors: Partial<Record<keyof T, string>> = {};
    
    Object.keys(validationRules).forEach(field => {
      const rule = validationRules[field as keyof T];
      if (rule) {
        const error = rule(formState.data[field as keyof T]);
        if (error) {
          errors[field as keyof T] = error;
        }
      }
    });

    const isValid = Object.keys(errors).length === 0;
    
    setFormState(prev => ({
      ...prev,
      errors,
      isValid,
    }));

    return isValid;
  }, [formState.data, validationRules]);

  // 폼 리셋
  const resetForm = useCallback(() => {
    setFormState({
      data: initialData,
      errors: {},
      isSubmitting: false,
      isValid: true,
    });
  }, [initialData]);

  // 제출 상태 설정
  const setSubmitting = useCallback((isSubmitting: boolean) => {
    setFormState(prev => ({ ...prev, isSubmitting }));
  }, []);

  // 전체 데이터 설정
  const setFormData = useCallback((data: T) => {
    setFormState(prev => ({ ...prev, data }));
  }, []);

  // 폼 핸들러 생성
  const createChangeHandler = useCallback(<K extends keyof T>(field: K) => {
    return (value: T[K]) => setFieldValue(field, value);
  }, [setFieldValue]);

  // 입력 핸들러 (이벤트 기반)
  const createInputHandler = useCallback(<K extends keyof T>(field: K) => {
    return (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const value = event.target.value as T[K];
      setFieldValue(field, value);
    };
  }, [setFieldValue]);

  // 체크박스 핸들러
  const createCheckboxHandler = useCallback(<K extends keyof T>(field: K) => {
    return (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.checked as T[K];
      setFieldValue(field, value);
    };
  }, [setFieldValue]);

  // 제출 핸들러
  const handleSubmit = useCallback((onSubmit: (data: T) => Promise<void> | void) => {
    return async (event?: React.FormEvent) => {
      event?.preventDefault();
      
      if (!validateForm()) {
        return;
      }

      setSubmitting(true);
      try {
        await onSubmit(formState.data);
      } finally {
        setSubmitting(false);
      }
    };
  }, [formState.data, validateForm, setSubmitting]);

  // 계산된 값들
  const computed = useMemo(() => ({
    hasErrors: Object.keys(formState.errors).length > 0,
    isDirty: JSON.stringify(formState.data) !== JSON.stringify(initialData),
    canSubmit: formState.isValid && !formState.isSubmitting,
  }), [formState.data, formState.errors, formState.isValid, formState.isSubmitting, initialData]);

  return {
    ...formState,
    ...computed,
    setFieldValue,
    setFieldError,
    validateForm,
    resetForm,
    setSubmitting,
    setFormData,
    createChangeHandler,
    createInputHandler,
    createCheckboxHandler,
    handleSubmit,
  };
}