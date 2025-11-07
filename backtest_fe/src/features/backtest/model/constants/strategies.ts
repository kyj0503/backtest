/**
 * 투자 전략 설정 및 파라미터 정의
 */

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
