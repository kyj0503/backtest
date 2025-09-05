// UI 상수 - 색상, 크기, 애니메이션 등
export const UI_CONSTANTS = {
  // 색상 팔레트
  COLORS: {
    PRIMARY: '#3B82F6',   // blue-500
    SUCCESS: '#10B981',   // green-500
    WARNING: '#F59E0B',   // yellow-500
    DANGER: '#EF4444',    // red-500
    INFO: '#6366F1',      // indigo-500
    GRAY: '#6B7280',      // gray-500
    WHITE: '#FFFFFF',
    BLACK: '#000000',
  },

  // 차트 색상
  CHART_COLORS: {
    EQUITY: '#3B82F6',
    BENCHMARK: '#10B981',
    TRADES_BUY: '#10B981',
    TRADES_SELL: '#EF4444',
    CANDLESTICK_UP: '#10B981',
    CANDLESTICK_DOWN: '#EF4444',
    VOLUME: '#6B7280',
    SMA: '#F59E0B',
    EMA: '#8B5CF6',
    RSI: '#EC4899',
    OVERBOUGHT: '#EF4444',
    OVERSOLD: '#10B981',
  },

  // 크기
  SIZES: {
    XS: '0.75rem',    // 12px
    SM: '0.875rem',   // 14px
    MD: '1rem',       // 16px
    LG: '1.125rem',   // 18px
    XL: '1.25rem',    // 20px
    '2XL': '1.5rem',  // 24px
  },

  // 간격
  SPACING: {
    XS: '0.25rem',    // 4px
    SM: '0.5rem',     // 8px
    MD: '1rem',       // 16px
    LG: '1.5rem',     // 24px
    XL: '2rem',       // 32px
    '2XL': '3rem',    // 48px
  },

  // 경계선 반지름
  BORDER_RADIUS: {
    SM: '0.125rem',   // 2px
    MD: '0.375rem',   // 6px
    LG: '0.5rem',     // 8px
    XL: '0.75rem',    // 12px
    FULL: '9999px',
  },

  // 그림자
  SHADOWS: {
    SM: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    MD: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    LG: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    XL: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },

  // 애니메이션 지속시간
  ANIMATION: {
    FAST: '150ms',
    NORMAL: '300ms',
    SLOW: '500ms',
  },

  // 브레이크포인트
  BREAKPOINTS: {
    SM: '640px',
    MD: '768px',
    LG: '1024px',
    XL: '1280px',
    '2XL': '1536px',
  },

  // Z-Index 레이어
  Z_INDEX: {
    DROPDOWN: 10,
    STICKY: 20,
    MODAL_BACKDROP: 40,
    MODAL: 50,
    POPOVER: 60,
    TOOLTIP: 70,
    NOTIFICATION: 80,
  },
} as const;

// 타입 안전성을 위한 타입 추출
export type UIColor = keyof typeof UI_CONSTANTS.COLORS;
export type ChartColor = keyof typeof UI_CONSTANTS.CHART_COLORS;
export type UISize = keyof typeof UI_CONSTANTS.SIZES;
export type UISpacing = keyof typeof UI_CONSTANTS.SPACING;
