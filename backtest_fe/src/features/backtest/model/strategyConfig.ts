// 투자 전략 관련 상수와 설정
export interface StrategyParameter {
  type: 'int' | 'float';
  default: number;
  min: number;
  max: number;
  step?: number;
  description?: string;
}

export interface StrategyConfig {
  name: string;
  description: string;
  parameters: Record<string, StrategyParameter>;
}

export const STRATEGY_CONFIGS: Record<string, StrategyConfig> = {
  buy_and_hold: {
    name: '매수 후 보유',
    description: '매수 후 보유 전략 - 파라미터 없음',
    parameters: {}
  },
  sma_crossover: {
    name: '단순이동평균 교차',
    description: '단기/장기 이동평균선 교차 기반 매매',
    parameters: {
      short_window: {
        type: 'int',
        default: 10,
        min: 5,
        max: 50,
        description: '단기 이동평균 기간'
      },
      long_window: {
        type: 'int',
        default: 20,
        min: 10,
        max: 100,
        description: '장기 이동평균 기간'
      }
    }
  },
  rsi_strategy: {
    name: 'RSI 전략',
    description: 'RSI 과매수/과매도 기반 매매',
    parameters: {
      rsi_period: {
        type: 'int',
        default: 14,
        min: 5,
        max: 30,
        description: 'RSI 계산 기간'
      },
      rsi_oversold: {
        type: 'int',
        default: 30,
        min: 10,
        max: 40,
        description: 'RSI 과매도 기준'
      },
      rsi_overbought: {
        type: 'int',
        default: 70,
        min: 60,
        max: 90,
        description: 'RSI 과매수 기준'
      }
    }
  },
  bollinger_bands: {
    name: '볼린저 밴드',
    description: '볼린저 밴드 기반 매매',
    parameters: {
      period: {
        type: 'int',
        default: 20,
        min: 10,
        max: 50,
        description: '이동평균 기간'
      },
      std_dev: {
        type: 'float',
        default: 2.0,
        min: 1.0,
        max: 3.0,
        step: 0.1,
        description: '표준편차 배수'
      }
    }
  },
  macd_strategy: {
    name: 'MACD 전략',
    description: 'MACD 교차 기반 매매',
    parameters: {
      fast_period: {
        type: 'int',
        default: 12,
        min: 5,
        max: 20,
        description: '빠른 EMA 기간'
      },
      slow_period: {
        type: 'int',
        default: 26,
        min: 20,
        max: 50,
        description: '느린 EMA 기간'
      },
      signal_period: {
        type: 'int',
        default: 9,
        min: 5,
        max: 15,
        description: '시그널 라인 기간'
      }
    }
  }
};

// 미리 정의된 종목 목록
export const PREDEFINED_STOCKS = [
  { value: 'CUSTOM', label: '직접 입력' },
  { value: 'AAPL', label: 'AAPL - Apple Inc.' },
  { value: 'GOOGL', label: 'GOOGL - Alphabet Inc.' },
  { value: 'MSFT', label: 'MSFT - Microsoft Corp.' },
  { value: 'TSLA', label: 'TSLA - Tesla Inc.' },
  { value: 'AMZN', label: 'AMZN - Amazon.com Inc.' },
  { value: 'NVDA', label: 'NVDA - NVIDIA Corp.' },
  { value: 'META', label: 'META - Meta Platforms Inc.' },
  { value: 'NFLX', label: 'NFLX - Netflix Inc.' },
  { value: 'SPY', label: 'SPY - SPDR S&P 500 ETF' },
  { value: 'QQQ', label: 'QQQ - Invesco QQQ Trust' },
  { value: 'VTI', label: 'VTI - Vanguard Total Stock Market ETF' }
];

// 자산 타입 정의
export const ASSET_TYPES = {
  STOCK: 'stock',
  CASH: 'cash'
} as const;

export type AssetType = typeof ASSET_TYPES[keyof typeof ASSET_TYPES];

// 리밸런싱 옵션
export const REBALANCE_OPTIONS = [
  { value: 'never', label: '리밸런싱 안함' },
  { value: 'monthly', label: '매월' },
  { value: 'quarterly', label: '분기별' },
  { value: 'yearly', label: '연간' }
];

// 투자 방식 옵션
export const INVESTMENT_TYPE_OPTIONS = [
  { value: 'lump_sum', label: '일시 투자' },
  { value: 'dca', label: '분할 매수 (DCA)' }
];

// 유효성 검증 규칙
export const VALIDATION_RULES = {
  MIN_AMOUNT: 100,
  MAX_AMOUNT: 1000000,
  MIN_DCA_PERIODS: 1,
  MAX_DCA_PERIODS: 60,
  MAX_PORTFOLIO_SIZE: 10,
  MIN_COMMISSION: 0,
  MAX_COMMISSION: 5,
  SYMBOL_MAX_LENGTH: 10
};

// 기본값
export const DEFAULT_VALUES = {
  START_DATE: '2023-01-01',
  END_DATE: '2024-12-31',
  INITIAL_AMOUNT: 10000,
  COMMISSION: 0.2, // 퍼센트
  DCA_PERIODS: 12,
  REBALANCE_FREQUENCY: 'monthly',
  STRATEGY: 'buy_and_hold'
};
