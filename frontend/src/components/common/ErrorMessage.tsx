import React from 'react';

export interface ErrorMessageProps {
  type?: 'error' | 'warning' | 'info' | 'success';
  title?: string;
  message: string;
  onClose?: () => void;
  dismissible?: boolean;
  className?: string;
  showIcon?: boolean;
}

// SVG 아이콘 컴포넌트들
const AlertCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const AlertTriangleIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const InfoIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const typeConfig = {
  error: {
    containerClass: 'bg-destructive/10 border-destructive/20 text-destructive',
    iconClass: 'text-destructive/60',
    titleClass: 'text-destructive',
    messageClass: 'text-destructive/90',
    icon: AlertCircleIcon
  },
  warning: {
    containerClass: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    iconClass: 'text-yellow-400',
    titleClass: 'text-yellow-800',
    messageClass: 'text-yellow-700',
    icon: AlertTriangleIcon
  },
  info: {
    containerClass: 'bg-accent/50 border-accent text-accent-foreground',
    iconClass: 'text-accent-foreground/60',
    titleClass: 'text-accent-foreground',
    messageClass: 'text-accent-foreground/90',
    icon: InfoIcon
  },
  success: {
    containerClass: 'bg-green-50 border-green-200 text-green-800',
    iconClass: 'text-green-400',
    titleClass: 'text-green-800',
    messageClass: 'text-green-700',
    icon: InfoIcon
  }
} as const;

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  type = 'error',
  title,
  message,
  onClose,
  dismissible = false,
  className = '',
  showIcon = true
}) => {
  const config = typeConfig[type];
  const IconComponent = config.icon;

  return (
    <div
      className={`
        border rounded-md p-4 ${config.containerClass} ${className}
      `}
      role="alert"
    >
      <div className="flex">
        {showIcon && (
          <div className="flex-shrink-0">
            <IconComponent 
              className={`w-5 h-5 ${config.iconClass}`}
              aria-hidden="true"
            />
          </div>
        )}
        
        <div className={showIcon ? "ml-3" : ""}>
          {title && (
            <h3 className={`text-sm font-medium ${config.titleClass}`}>
              {title}
            </h3>
          )}
          
          <div className={`text-sm ${title ? 'mt-2' : ''} ${config.messageClass}`}>
            {message}
          </div>
        </div>

        {(dismissible || onClose) && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={onClose}
                className={`
                  inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2
                  hover:bg-muted/20
                  ${config.iconClass}
                `}
                aria-label="닫기"
              >
                <XIcon className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 간단한 인라인 에러 메시지 (폼 필드용)
export const FieldError: React.FC<{ message: string; className?: string }> = ({ 
  message, 
  className = '' 
}) => (
  <div className={`text-sm text-destructive mt-1 ${className}`} role="alert">
    {message}
  </div>
);

// 토스트 스타일 알림
export const ToastMessage: React.FC<ErrorMessageProps> = (props) => (
  <ErrorMessage
    {...props}
    className={`
      fixed top-4 right-4 max-w-sm shadow-lg z-50 
      transform transition-all duration-300 ease-in-out
      ${props.className || ''}
    `}
    dismissible={true}
  />
);
