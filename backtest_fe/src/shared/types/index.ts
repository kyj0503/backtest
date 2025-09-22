/**
 * 공통 타입 정의
 * 애플리케이션 전반에서 사용되는 기본 타입들
 */

export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export interface User extends BaseEntity {
  username: string;
  email: string;
  profileImage?: string;
  investmentType?: 'conservative' | 'moderate' | 'balanced' | 'aggressive' | 'speculative';
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  content: T[];
  page: {
    number: number;
    size: number;
    totalElements: number;
    totalPages: number;
  };
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

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

// 테마 관련 타입
export interface ThemeConfig {
  name: string;
  colors: Record<string, string>;
  isDark: boolean;
}

// 라우터 관련 타입
export interface RouteConfig {
  path: string;
  label: string;
  description?: string;
  protected?: boolean;
}