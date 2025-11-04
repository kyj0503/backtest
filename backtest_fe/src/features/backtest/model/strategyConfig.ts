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
  buy_hold_strategy: {
    name: '매수 후 보유',
    description: '매수 후 보유 전략 - 파라미터 없음',
    parameters: {}
  },
  sma_strategy: {
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
  bollinger_strategy: {
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
  },
  ema_strategy: {
    name: 'EMA 교차',
    description: '지수 이동평균선 교차 기반 매매',
    parameters: {
      fast_window: {
        type: 'int',
        default: 12,
        min: 5,
        max: 50,
        description: '단기 EMA 기간'
      },
      slow_window: {
        type: 'int',
        default: 26,
        min: 10,
        max: 200,
        description: '장기 EMA 기간'
      }
    }
  }
};

// 미리 정의된 종목 목록
export const PREDEFINED_STOCKS = [
  { value: 'CUSTOM', label: '직접 입력' },

  // 미국 주식 및 ETF (20개)
  { value: 'AAPL', label: 'AAPL - Apple Inc.' },
  { value: 'GOOGL', label: 'GOOGL - Alphabet Inc.' },
  { value: 'MSFT', label: 'MSFT - Microsoft Corp.' },
  { value: 'TSLA', label: 'TSLA - Tesla Inc.' },
  { value: 'AMZN', label: 'AMZN - Amazon.com Inc.' },
  { value: 'NVDA', label: 'NVDA - NVIDIA Corp.' },
  { value: 'META', label: 'META - Meta Platforms Inc.' },
  { value: 'NFLX', label: 'NFLX - Netflix Inc.' },
  { value: 'JPM', label: 'JPM - JPMorgan Chase & Co.' },
  { value: 'V', label: 'V - Visa Inc.' },
  { value: 'JNJ', label: 'JNJ - Johnson & Johnson' },
  { value: 'WMT', label: 'WMT - Walmart Inc.' },
  { value: 'PG', label: 'PG - Procter & Gamble Co.' },
  { value: 'DIS', label: 'DIS - Walt Disney Co.' },
  { value: 'BAC', label: 'BAC - Bank of America Corp.' },
  { value: 'CSCO', label: 'CSCO - Cisco Systems Inc.' },
  { value: 'INTC', label: 'INTC - Intel Corp.' },
  { value: 'AMD', label: 'AMD - Advanced Micro Devices Inc.' },
  { value: 'SPY', label: 'SPY - SPDR S&P 500 ETF' },
  { value: 'QQQ', label: 'QQQ - Invesco QQQ Trust' },
  { value: 'VTI', label: 'VTI - Vanguard Total Stock Market ETF' },

  // 한국 주식 (20개)
  { value: '005930.KS', label: '005930.KS - 삼성전자' },
  { value: '000660.KS', label: '000660.KS - SK하이닉스' },
  { value: '005380.KS', label: '005380.KS - 현대자동차' },
  { value: '000270.KS', label: '000270.KS - 기아' },
  { value: '035420.KS', label: '035420.KS - NAVER' },
  { value: '051910.KS', label: '051910.KS - LG화학' },
  { value: '006400.KS', label: '006400.KS - 삼성SDI' },
  { value: '035720.KS', label: '035720.KS - 카카오' },
  { value: '003550.KS', label: '003550.KS - LG' },
  { value: '017670.KS', label: '017670.KS - SK텔레콤' },
  { value: '096770.KS', label: '096770.KS - SK이노베이션' },
  { value: '034730.KS', label: '034730.KS - SK' },
  { value: '028260.KS', label: '028260.KS - 삼성물산' },
  { value: '012330.KS', label: '012330.KS - 현대모비스' },
  { value: '068270.KS', label: '068270.KS - 셀트리온' },
  { value: '207940.KS', label: '207940.KS - 삼성바이오로직스' },
  { value: '105560.KS', label: '105560.KS - KB금융' },
  { value: '055550.KS', label: '055550.KS - 신한지주' },
  { value: '086790.KS', label: '086790.KS - 하나금융지주' },
  { value: '015760.KS', label: '015760.KS - 한국전력' }
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

// DCA 주기 프리셋
export type DcaFrequency = 'monthly' | 'bimonthly' | 'quarterly' | 'semiannually' | 'annually';

export const DCA_FREQUENCY_OPTIONS = [
  { value: 'monthly', label: '매달 투자', months: 1 },
  { value: 'bimonthly', label: '격달로 투자', months: 2 },
  { value: 'quarterly', label: '매 분기 투자', months: 3 },
  { value: 'semiannually', label: '반년마다 투자', months: 6 },
  { value: 'annually', label: '매년 투자', months: 12 }
] as const;

// DCA 주기(개월)를 가져오는 헬퍼 함수
export const getDcaMonths = (frequency: DcaFrequency): number => {
  const option = DCA_FREQUENCY_OPTIONS.find(opt => opt.value === frequency);
  return option?.months || 1;
};

// 유효성 검증 규칙
export const VALIDATION_RULES = {
  MIN_AMOUNT: 100,
  MAX_AMOUNT: 1000000,
  MAX_PORTFOLIO_SIZE: 10,
  MIN_COMMISSION: 0,
  MAX_COMMISSION: 5,
  SYMBOL_MAX_LENGTH: 10
};

// 주식 심볼에서 표시 이름 추출
export const getStockDisplayName = (symbol: string): string => {
  // PREDEFINED_STOCKS에서 해당 심볼 찾기
  const stock = PREDEFINED_STOCKS.find(s => s.value.toUpperCase() === symbol.toUpperCase());

  if (stock && stock.value !== 'CUSTOM') {
    // "AAPL - Apple Inc." -> "Apple Inc."
    // "005930.KS - 삼성전자" -> "삼성전자"
    const parts = stock.label.split(' - ');
    if (parts.length > 1) {
      const name = parts[1].trim();
      // "Apple Inc."는 "Apple"로 짧게, 한국 주식은 그대로
      if (name.includes('Inc.') || name.includes('Corp.') || name.includes('Co.')) {
        return name.split(/\s+(Inc\.|Corp\.|Co\.)/)[0];
      }
      return name;
    }
  }

  // 매핑이 없으면 원래 심볼 반환
  return symbol;
};

// 기본값
export const DEFAULT_VALUES = {
  START_DATE: '2023-01-01',
  END_DATE: '2024-12-31',
  INITIAL_AMOUNT: 10000,
  COMMISSION: 0.2, // 퍼센트
  DCA_FREQUENCY: 'monthly' as DcaFrequency,
  REBALANCE_FREQUENCY: 'monthly',
  STRATEGY: 'buy_hold_strategy'
};
