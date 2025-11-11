// 공통 컴포넌트 통합 내보내기

// Layout Components
export { default as ErrorBoundary } from './layout/ErrorBoundary';
export { default as Header } from './layout/Header';
export { default as Footer } from './layout/Footer';
export { default as ThemeSelector } from './layout/ThemeSelector';

// Form Components
export { FormField } from './form/FormField';
export type { FormFieldProps } from './form/FormField';

export { FormSection } from './form/FormSection';
export type { FormSectionProps } from './form/FormSection';

export { FormLegend } from './form/FormLegend';

// Loading Components
export { LoadingSpinner, InlineSpinner, ButtonSpinner } from './loading/LoadingSpinner';
export type { LoadingSpinnerProps } from './loading/LoadingSpinner';
export { default as ChartLoading } from './loading/ChartLoading';

// Feedback Components
export { ErrorMessage, FieldError, ToastMessage } from './feedback/ErrorMessage';
export type { ErrorMessageProps } from './feedback/ErrorMessage';

// Tooltip Components
export { default as FinancialTermTooltip } from './tooltip/FinancialTermTooltip';

// Debug Components
export { default as PerformanceMonitor, useRenderPerformance } from './debug/PerformanceMonitor';
