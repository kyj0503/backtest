import { useState, useCallback, ChangeEvent } from 'react';

interface UseFormInputOptions {
  initialValue?: string | number;
  validate?: (value: string | number) => string | null;
  transform?: (value: string) => string | number;
}

interface UseFormInputReturn {
  value: string | number;
  error: string | null;
  hasError: boolean;
  setValue: (value: string | number) => void;
  handleChange: (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
  handleBlur: () => void;
  reset: () => void;
  validate: () => boolean;
}

/**
 * 폼 입력 필드를 위한 커스텀 훅
 * 값 관리, 검증, 에러 처리를 통합적으로 제공
 */
export const useFormInput = ({
  initialValue = '',
  validate,
  transform
}: UseFormInputOptions = {}): UseFormInputReturn => {
  const [value, setValue] = useState<string | number>(initialValue);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  const validateValue = useCallback((val: string | number): string | null => {
    if (validate) {
      return validate(val);
    }
    return null;
  }, [validate]);

  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    let newValue: string | number = e.target.value;
    
    // 변환 함수가 있으면 적용
    if (transform) {
      newValue = transform(newValue);
    }
    
    setValue(newValue);
    
    // 터치된 상태에서만 즉시 검증
    if (touched) {
      const validationError = validateValue(newValue);
      setError(validationError);
    }
  }, [transform, touched, validateValue]);

  const handleBlur = useCallback(() => {
    setTouched(true);
    const validationError = validateValue(value);
    setError(validationError);
  }, [value, validateValue]);

  const setValueDirectly = useCallback((newValue: string | number) => {
    setValue(newValue);
    if (touched) {
      const validationError = validateValue(newValue);
      setError(validationError);
    }
  }, [touched, validateValue]);

  const reset = useCallback(() => {
    setValue(initialValue);
    setError(null);
    setTouched(false);
  }, [initialValue]);

  const validateInput = useCallback((): boolean => {
    const validationError = validateValue(value);
    setError(validationError);
    setTouched(true);
    return validationError === null;
  }, [value, validateValue]);

  return {
    value,
    error,
    hasError: error !== null,
    setValue: setValueDirectly,
    handleChange,
    handleBlur,
    reset,
    validate: validateInput
  };
};
