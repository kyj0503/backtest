/**
 * 공통 타입 정의
 * 애플리케이션 전반에서 사용되는 기본 타입들
 */

// 공통 UI 상태 타입
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface AsyncState<T> extends LoadingState {
  data: T | null;
}

// 폼 관련 공통 타입
export interface FormState<T> {
  data: T;
  errors: Partial<Record<keyof T, string>>;
  isSubmitting: boolean;
  isValid: boolean;
}