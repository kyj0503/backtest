// 자주 사용되는 Tailwind CSS 클래스 조합
export const STYLE_CLASSES = {
  // 버튼 스타일
  BUTTON: {
    BASE: 'inline-flex items-center justify-center rounded-md border font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200',
    PRIMARY: 'border-transparent bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    SECONDARY: 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-blue-500',
    SUCCESS: 'border-transparent bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
    DANGER: 'border-transparent bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    WARNING: 'border-transparent bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500',
    GHOST: 'border-transparent bg-transparent text-gray-600 hover:bg-gray-100 focus:ring-gray-500',
    
    // 크기별
    SM: 'px-3 py-2 text-sm',
    MD: 'px-4 py-2 text-sm',
    LG: 'px-4 py-2 text-base',
    XL: 'px-6 py-3 text-base',
  },

  // 입력 필드 스타일
  INPUT: {
    BASE: 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
    ERROR: 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500',
    SUCCESS: 'border-green-300 focus:border-green-500 focus:ring-green-500',
    DISABLED: 'bg-gray-50 text-gray-500 cursor-not-allowed',
    
    // 크기별
    SM: 'px-3 py-1.5 text-sm',
    MD: 'px-3 py-2 text-sm',
    LG: 'px-4 py-2 text-base',
  },

  // 카드 스타일
  CARD: {
    BASE: 'bg-white overflow-hidden shadow rounded-lg',
    BORDERED: 'border border-gray-200',
    HOVER: 'hover:shadow-md transition-shadow duration-200',
    
    HEADER: 'px-4 py-5 sm:px-6 border-b border-gray-200',
    BODY: 'px-4 py-5 sm:p-6',
    FOOTER: 'px-4 py-4 sm:px-6 bg-gray-50 border-t border-gray-200',
  },

  // 테이블 스타일
  TABLE: {
    CONTAINER: 'overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg',
    BASE: 'min-w-full divide-y divide-gray-200',
    BORDERED: 'border border-gray-200 rounded-lg',
    
    HEADER: 'bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
    CELL: 'px-6 py-4 whitespace-nowrap text-sm text-gray-900',
    ROW_HOVER: 'hover:bg-gray-50',
    ROW_STRIPED: 'odd:bg-gray-50 even:bg-white',
  },

  // 폼 스타일
  FORM: {
    GROUP: 'space-y-2',
    LABEL: 'block text-sm font-medium text-gray-700',
    REQUIRED: 'text-red-500 ml-1',
    HELP_TEXT: 'text-sm text-gray-500',
    ERROR_TEXT: 'text-sm text-red-600',
    
    GRID_2: 'grid grid-cols-1 gap-4 sm:grid-cols-2',
    GRID_3: 'grid grid-cols-1 gap-4 sm:grid-cols-3',
    GRID_4: 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4',
  },

  // 알림/메시지 스타일
  ALERT: {
    BASE: 'border rounded-md p-4',
    
    SUCCESS: 'bg-green-50 border-green-200 text-green-800',
    ERROR: 'bg-red-50 border-red-200 text-red-800',
    WARNING: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    INFO: 'bg-blue-50 border-blue-200 text-blue-800',
    
    TITLE: 'text-sm font-medium',
    MESSAGE: 'text-sm',
    ICON: 'w-5 h-5 flex-shrink-0',
  },

  // 배지 스타일
  BADGE: {
    BASE: 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
    
    SUCCESS: 'bg-green-100 text-green-800',
    ERROR: 'bg-red-100 text-red-800',
    WARNING: 'bg-yellow-100 text-yellow-800',
    INFO: 'bg-blue-100 text-blue-800',
    GRAY: 'bg-gray-100 text-gray-800',
    
    // 크기별
    SM: 'px-2 py-0.5 text-xs',
    MD: 'px-2.5 py-0.5 text-xs',
    LG: 'px-3 py-0.5 text-sm',
  },

  // 레이아웃 스타일
  LAYOUT: {
    CONTAINER: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
    SECTION: 'py-8',
    DIVIDER: 'border-t border-gray-200',
    
    FLEX_CENTER: 'flex items-center justify-center',
    FLEX_BETWEEN: 'flex items-center justify-between',
    FLEX_COL: 'flex flex-col',
    
    GRID_AUTO: 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3',
  },

  // 로딩 상태
  LOADING: {
    SPINNER: 'animate-spin',
    PULSE: 'animate-pulse',
    SKELETON: 'bg-gray-200 rounded animate-pulse',
  },

  // 유틸리티
  UTILITY: {
    SCREEN_READER_ONLY: 'sr-only',
    TRUNCATE: 'truncate',
    TRANSITION: 'transition-all duration-200 ease-in-out',
    FOCUS_RING: 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
  },
} as const;

// 자주 사용되는 클래스 조합 함수들
export const getButtonClasses = (
  variant: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'ghost' = 'primary',
  size: 'sm' | 'md' | 'lg' | 'xl' = 'md',
  disabled = false
) => {
  const baseClasses = STYLE_CLASSES.BUTTON.BASE;
  const variantClasses = STYLE_CLASSES.BUTTON[variant.toUpperCase() as keyof typeof STYLE_CLASSES.BUTTON];
  const sizeClasses = STYLE_CLASSES.BUTTON[size.toUpperCase() as keyof typeof STYLE_CLASSES.BUTTON];
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';
  
  return `${baseClasses} ${variantClasses} ${sizeClasses} ${disabledClasses}`.trim();
};

export const getInputClasses = (
  state: 'default' | 'error' | 'success' = 'default',
  size: 'sm' | 'md' | 'lg' = 'md',
  disabled = false
) => {
  const baseClasses = STYLE_CLASSES.INPUT.BASE;
  const stateClasses = state === 'error' ? STYLE_CLASSES.INPUT.ERROR : 
                      state === 'success' ? STYLE_CLASSES.INPUT.SUCCESS : '';
  const sizeClasses = STYLE_CLASSES.INPUT[size.toUpperCase() as keyof typeof STYLE_CLASSES.INPUT];
  const disabledClasses = disabled ? STYLE_CLASSES.INPUT.DISABLED : '';
  
  return `${baseClasses} ${stateClasses} ${sizeClasses} ${disabledClasses}`.trim();
};

export const getAlertClasses = (type: 'success' | 'error' | 'warning' | 'info') => {
  const baseClasses = STYLE_CLASSES.ALERT.BASE;
  const typeClasses = STYLE_CLASSES.ALERT[type.toUpperCase() as keyof typeof STYLE_CLASSES.ALERT];
  
  return `${baseClasses} ${typeClasses}`.trim();
};

export const getBadgeClasses = (
  variant: 'success' | 'error' | 'warning' | 'info' | 'gray' = 'gray',
  size: 'sm' | 'md' | 'lg' = 'md'
) => {
  const baseClasses = STYLE_CLASSES.BADGE.BASE;
  const variantClasses = STYLE_CLASSES.BADGE[variant.toUpperCase() as keyof typeof STYLE_CLASSES.BADGE];
  const sizeClasses = STYLE_CLASSES.BADGE[size.toUpperCase() as keyof typeof STYLE_CLASSES.BADGE];
  
  return `${baseClasses} ${variantClasses} ${sizeClasses}`.trim();
};
