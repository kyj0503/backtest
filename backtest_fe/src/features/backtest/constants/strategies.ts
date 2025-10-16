/**
 * 백테스팅 전략 정의
 * 
 * 전략 목록은 자주 변경되지 않으므로 프론트엔드에 하드코딩하여
 * 불필요한 API 호출을 제거하고 성능을 개선합니다.
 */

export interface StrategyParameter {
  type: string;
  default: number;
  min: number;
  max: number;
  description: string;
}

export interface Strategy {
  name: string;
  displayName: string;
  description: string;
  parameters: Record<string, StrategyParameter>;
}

export const STRATEGIES: Strategy[] = [
  {
    name: 'buy_hold_strategy',
    displayName: 'Buy & Hold',
    description: '매수 후 보유 전략 - 초기에 매수하여 종료일까지 보유',
    parameters: {},
  },
  {
    name: 'sma_strategy',
    displayName: 'SMA 크로스오버',
    description: 'SMA 단기/장기 이동평균 교차 전략',
    parameters: {
      short_window: {
        type: 'int',
        default: 10,
        min: 2,
        max: 50,
        description: '단기 이동평균 기간',
      },
      long_window: {
        type: 'int',
        default: 20,
        min: 10,
        max: 200,
        description: '장기 이동평균 기간',
      },
    },
  },
  {
    name: 'rsi_strategy',
    displayName: 'RSI 전략',
    description: 'RSI 과매수/과매도 기반 전략',
    parameters: {
      rsi_period: {
        type: 'int',
        default: 14,
        min: 2,
        max: 50,
        description: 'RSI 계산 기간',
      },
      oversold: {
        type: 'int',
        default: 30,
        min: 10,
        max: 40,
        description: '과매도 임계값',
      },
      overbought: {
        type: 'int',
        default: 70,
        min: 60,
        max: 90,
        description: '과매수 임계값',
      },
    },
  },
  {
    name: 'bollinger_strategy',
    displayName: '볼린저 밴드',
    description: '볼린저 밴드 돌파 전략',
    parameters: {
      period: {
        type: 'int',
        default: 20,
        min: 5,
        max: 50,
        description: '이동평균 기간',
      },
      std_dev: {
        type: 'float',
        default: 2.0,
        min: 1.0,
        max: 3.0,
        description: '표준편차 배수',
      },
    },
  },
  {
    name: 'macd_strategy',
    displayName: 'MACD 전략',
    description: 'MACD 크로스오버 전략',
    parameters: {
      fast_period: {
        type: 'int',
        default: 12,
        min: 5,
        max: 50,
        description: '빠른 EMA 기간',
      },
      slow_period: {
        type: 'int',
        default: 26,
        min: 10,
        max: 100,
        description: '느린 EMA 기간',
      },
      signal_period: {
        type: 'int',
        default: 9,
        min: 5,
        max: 50,
        description: '시그널선 기간',
      },
    },
  },
  {
    name: 'ema_strategy',
    displayName: 'EMA 크로스오버',
    description: 'EMA 단기/장기 지수이동평균 교차 전략',
    parameters: {
      short_period: {
        type: 'int',
        default: 12,
        min: 2,
        max: 50,
        description: '단기 EMA 기간',
      },
      long_period: {
        type: 'int',
        default: 26,
        min: 10,
        max: 200,
        description: '장기 EMA 기간',
      },
    },
  },
];

/**
 * 전략 이름으로 전략 객체 찾기
 */
export function getStrategyByName(name: string): Strategy | undefined {
  return STRATEGIES.find(s => s.name === name);
}

/**
 * 전략의 기본 파라미터 값 가져오기
 */
export function getDefaultParameters(strategyName: string): Record<string, number> {
  const strategy = getStrategyByName(strategyName);
  if (!strategy) return {};

  const params: Record<string, number> = {};
  Object.entries(strategy.parameters).forEach(([key, param]) => {
    params[key] = param.default;
  });
  return params;
}
