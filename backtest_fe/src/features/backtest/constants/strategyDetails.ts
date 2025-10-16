/**
 * 투자 전략 상세 정보
 */

export interface StrategyDetail {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: '초급' | '중급' | '고급';
  overview: string;
  howItWorks: string[];
  advantages: string[];
  disadvantages: string[];
  bestFor: string[];
  parameters?: {
    name: string;
    description: string;
    defaultValue: number;
    range: string;
  }[];
  example?: string;
  relatedStrategies?: string[];
}

export const STRATEGY_DETAILS: Record<string, StrategyDetail> = {
  buy_hold_strategy: {
    id: 'buy_hold_strategy',
    name: '매수 후 보유 (Buy & Hold)',
    description: '자산을 매수한 후 장기간 보유하는 가장 기본적인 투자 전략',
    category: '기본 전략',
    difficulty: '초급',
    overview: `매수 후 보유 전략은 투자의 가장 기본이 되는 전략으로, 자산을 매수한 후 시장의 단기 변동에 관계없이 장기간 보유하는 방식입니다.

시장 타이밍을 맞추려 하지 않고, 장기적으로 시장이 상승할 것이라는 믿음을 바탕으로 합니다. 워렌 버핏이 추천하는 전략으로, 역사적으로 S&P 500 지수는 장기적으로 연평균 약 10%의 수익률을 보여왔습니다.`,
    howItWorks: [
      '1. 투자할 자산을 선정하고 매수합니다',
      '2. 시장의 단기 변동을 무시하고 장기간 보유합니다',
      '3. 목표 기간 도달 시 또는 필요 시에만 매도합니다',
      '4. 배당금이 있다면 재투자하여 복리 효과를 극대화합니다',
    ],
    advantages: [
      '✓ 간단하고 이해하기 쉬움',
      '✓ 거래 수수료가 최소화됨',
      '✓ 시장 타이밍에 대한 스트레스 없음',
      '✓ 세금 효율적 (장기 보유 시 세금 우대)',
      '✓ 복리 효과로 장기적으로 높은 수익 가능',
      '✓ 시간과 노력이 적게 듦',
    ],
    disadvantages: [
      '✗ 단기 하락장에서도 보유해야 하는 심리적 어려움',
      '✗ 시장 상황에 따라 큰 손실을 볼 수 있음',
      '✗ 기회비용 발생 가능 (다른 전략이 더 나을 수 있음)',
      '✗ 자산 선택이 매우 중요 (잘못 선택하면 장기 손실)',
    ],
    bestFor: [
      '장기 투자자 (10년 이상)',
      '시장 타이밍을 맞추기 어려운 일반 투자자',
      '안정적인 자산(지수 ETF, 우량주)에 투자하려는 사람',
      '복잡한 전략보다 단순함을 선호하는 투자자',
      '은퇴 자금 등 장기 목표를 위한 투자자',
    ],
    example: `예시: 2010년 1월 1일에 S&P 500 지수(SPY)에 1,000만원을 투자했다면?

- 2020년 1월 1일: 약 2,500만원 (연평균 약 9.6%)
- 2024년 1월 1일: 약 3,800만원 (연평균 약 9.5%)

중간에 코로나19 폭락(-34%, 2020년 3월)이 있었지만, 계속 보유했다면 결국 큰 수익을 얻었을 것입니다.`,
    relatedStrategies: ['dca_strategy', 'value_averaging'],
  },

  sma_strategy: {
    id: 'sma_strategy',
    name: '단순이동평균 교차 (SMA Crossover)',
    description: '두 개의 이동평균선이 교차할 때 매매 신호를 생성하는 추세 추종 전략',
    category: '기술적 분석',
    difficulty: '중급',
    overview: `단순이동평균(SMA) 교차 전략은 단기와 장기 이동평균선의 교차점을 매매 신호로 활용하는 기술적 분석 기법입니다.

단기 이동평균선이 장기 이동평균선을 상향 돌파하면(골든 크로스) 매수하고, 하향 돌파하면(데드 크로스) 매도합니다. 시장의 추세를 따라가는 전략으로, 강한 추세장에서 효과적입니다.`,
    howItWorks: [
      '1. 단기 SMA(예: 10일)와 장기 SMA(예: 20일)를 계산합니다',
      '2. 단기 SMA가 장기 SMA를 상향 돌파 → 골든크로스 → 매수',
      '3. 단기 SMA가 장기 SMA를 하향 돌파 → 데드크로스 → 매도',
      '4. 추세가 지속되는 동안 포지션 유지',
    ],
    advantages: [
      '✓ 명확한 매매 신호',
      '✓ 강한 추세장에서 큰 수익 가능',
      '✓ 감정적 판단 배제',
      '✓ 자동화하기 쉬움',
      '✓ 다양한 자산에 적용 가능',
    ],
    disadvantages: [
      '✗ 횡보장(박스권)에서 잦은 손실 발생',
      '✗ 후행 지표라 최적의 진입/청산점을 놓침',
      '✗ 잦은 거래로 인한 수수료 부담',
      '✗ 급격한 변동성에 취약',
      '✗ 잘못된 신호(Whipsaw) 발생 가능',
    ],
    bestFor: [
      '추세가 뚜렷한 시장에 투자하는 사람',
      '명확한 규칙을 원하는 투자자',
      '단기~중기 트레이더',
      '기술적 분석을 선호하는 투자자',
    ],
    parameters: [
      {
        name: 'short_window',
        description: '단기 이동평균 기간',
        defaultValue: 10,
        range: '5~50일',
      },
      {
        name: 'long_window',
        description: '장기 이동평균 기간',
        defaultValue: 20,
        range: '10~100일',
      },
    ],
    example: `일반적인 조합:
- 단기: 5~20일, 장기: 20~50일 → 단기 트레이딩
- 단기: 50일, 장기: 200일 → 장기 투자 (골든크로스/데드크로스)`,
    relatedStrategies: ['ema_strategy', 'macd_strategy'],
  },

  rsi_strategy: {
    id: 'rsi_strategy',
    name: 'RSI 전략 (Relative Strength Index)',
    description: '상대강도지수를 사용하여 과매수/과매도 구간에서 역추세 매매를 하는 전략',
    category: '기술적 분석',
    difficulty: '중급',
    overview: `RSI(상대강도지수)는 가격의 상승 압력과 하락 압력을 비교하여 0~100 사이의 값으로 나타내는 모멘텀 지표입니다.

일반적으로 RSI가 70 이상이면 과매수(Overbought), 30 이하면 과매도(Oversold) 상태로 판단합니다. 과매도 구간에서 매수하고, 과매수 구간에서 매도하여 평균 회귀를 노리는 역추세 전략입니다.`,
    howItWorks: [
      '1. RSI 지표를 계산합니다 (일반적으로 14일 기준)',
      '2. RSI가 과매도 수준(30 이하)에 도달 → 매수 신호',
      '3. RSI가 과매수 수준(70 이상)에 도달 → 매도 신호',
      '4. RSI가 중립 구간으로 돌아올 때까지 포지션 유지',
    ],
    advantages: [
      '✓ 과매수/과매도 구간을 명확히 식별',
      '✓ 박스권 장세에서 효과적',
      '✓ 다이버전스로 추세 전환 예측 가능',
      '✓ 범용성이 높음 (주식, 코인, 외환 등)',
      '✓ 단기 반등 기회 포착에 유리',
    ],
    disadvantages: [
      '✗ 강한 추세장에서는 계속 과매수/과매도 상태 유지 가능',
      '✗ 잘못된 신호가 많을 수 있음',
      '✗ 다른 지표와 함께 사용해야 정확도 향상',
      '✗ RSI만으로는 추세 방향 파악 어려움',
    ],
    bestFor: [
      '박스권 장세를 노리는 단기 트레이더',
      '평균 회귀를 믿는 투자자',
      '변동성이 큰 자산 거래자',
      '데이 트레이더 또는 스윙 트레이더',
    ],
    parameters: [
      {
        name: 'rsi_period',
        description: 'RSI 계산 기간',
        defaultValue: 14,
        range: '5~30일',
      },
      {
        name: 'rsi_overbought',
        description: '과매수 기준선',
        defaultValue: 70,
        range: '60~90',
      },
      {
        name: 'rsi_oversold',
        description: '과매도 기준선',
        defaultValue: 30,
        range: '10~40',
      },
    ],
    example: `전형적인 설정:
- RSI 기간: 14일
- 과매수: 70 이상 → 매도
- 과매도: 30 이하 → 매수

공격적인 설정:
- 과매수: 80, 과매도: 20 (더 극단적인 상황에서만 진입)`,
    relatedStrategies: ['stochastic_strategy', 'bollinger_strategy'],
  },

  bollinger_strategy: {
    id: 'bollinger_strategy',
    name: '볼린저 밴드 (Bollinger Bands)',
    description: '가격의 변동성을 기준으로 매매 구간을 설정하는 전략',
    category: '기술적 분석',
    difficulty: '중급',
    overview: `볼린저 밴드는 이동평균선을 중심으로 표준편차를 이용해 상한선과 하한선을 그린 지표입니다.

가격이 밴드의 상단에 닿으면 과매수, 하단에 닿으면 과매도로 판단하여 평균 회귀를 노립니다. 변동성이 확대되면 밴드가 넓어지고, 축소되면 밴드가 좁아져 변동성 변화를 시각적으로 파악할 수 있습니다.`,
    howItWorks: [
      '1. 중심선(20일 이동평균)을 계산합니다',
      '2. 상단밴드 = 중심선 + (표준편차 × 2)',
      '3. 하단밴드 = 중심선 - (표준편차 × 2)',
      '4. 가격이 하단밴드에 닿으면 매수, 상단밴드에 닿으면 매도',
      '5. 밴드 폭이 좁아지면 큰 변동성 임박 신호',
    ],
    advantages: [
      '✓ 변동성을 시각적으로 쉽게 파악',
      '✓ 과매수/과매도 구간 명확',
      '✓ 밴드 수축은 큰 움직임의 전조',
      '✓ 다양한 시장 상황에 적응 가능',
      '✓ 다른 지표와 결합하기 좋음',
    ],
    disadvantages: [
      '✗ 추세장에서는 밴드를 따라 움직여 잘못된 신호',
      '✗ 밴드 터치만으로는 신호 부족',
      '✗ 급격한 변동성 확대 시 대응 어려움',
      '✗ 표준편차 배수 설정이 중요',
    ],
    bestFor: [
      '박스권 또는 약한 추세장 투자자',
      '변동성 거래를 선호하는 트레이더',
      '평균 회귀 전략을 사용하는 투자자',
      '중단기 스윙 트레이더',
    ],
    parameters: [
      {
        name: 'period',
        description: '이동평균 기간',
        defaultValue: 20,
        range: '10~50일',
      },
      {
        name: 'std_dev',
        description: '표준편차 배수',
        defaultValue: 2.0,
        range: '1.0~3.0',
      },
    ],
    example: `표준 설정:
- 기간: 20일
- 표준편차: 2배

공격적 설정 (좁은 밴드):
- 표준편차: 1.5배 → 더 자주 신호 발생

보수적 설정 (넓은 밴드):
- 표준편차: 2.5배 → 극단적 상황에서만 신호`,
    relatedStrategies: ['rsi_strategy', 'keltner_channel'],
  },

  macd_strategy: {
    id: 'macd_strategy',
    name: 'MACD 전략 (Moving Average Convergence Divergence)',
    description: '이동평균 수렴/확산을 이용한 추세 및 모멘텀 분석 전략',
    category: '기술적 분석',
    difficulty: '중급',
    overview: `MACD는 단기 EMA와 장기 EMA의 차이를 나타내는 선(MACD선)과 그것의 이동평균(시그널선)을 사용하는 지표입니다.

MACD선이 시그널선을 상향 돌파하면 매수, 하향 돌파하면 매도 신호로 판단합니다. 히스토그램으로 두 선의 차이를 시각화하여 모멘텀의 강도를 파악할 수 있습니다.`,
    howItWorks: [
      '1. MACD선 = 12일 EMA - 26일 EMA',
      '2. 시그널선 = MACD선의 9일 EMA',
      '3. 히스토그램 = MACD선 - 시그널선',
      '4. MACD선이 시그널선을 상향 돌파 → 매수',
      '5. MACD선이 시그널선을 하향 돌파 → 매도',
      '6. 히스토그램 증가 → 추세 강화, 감소 → 추세 약화',
    ],
    advantages: [
      '✓ 추세와 모멘텀을 동시에 파악',
      '✓ 다이버전스로 추세 전환 조기 포착',
      '✓ 명확한 매매 신호',
      '✓ 히스토그램으로 추세 강도 확인',
      '✓ 널리 사용되어 신뢰도 높음',
    ],
    disadvantages: [
      '✗ 후행 지표로 신호가 늦음',
      '✗ 횡보장에서 잘못된 신호 빈발',
      '✗ 급격한 변동에 민감',
      '✗ 단독 사용 시 정확도 낮음',
    ],
    bestFor: [
      '추세 추종 전략을 선호하는 투자자',
      '중기 투자자 (수주~수개월)',
      '기술적 분석에 익숙한 트레이더',
      '다이버전스 패턴을 활용하는 투자자',
    ],
    parameters: [
      {
        name: 'fast_period',
        description: '빠른 EMA 기간',
        defaultValue: 12,
        range: '5~20일',
      },
      {
        name: 'slow_period',
        description: '느린 EMA 기간',
        defaultValue: 26,
        range: '20~50일',
      },
      {
        name: 'signal_period',
        description: '시그널 라인 기간',
        defaultValue: 9,
        range: '5~15일',
      },
    ],
    example: `표준 설정 (Gerald Appel의 원안):
- 빠른 EMA: 12
- 느린 EMA: 26
- 시그널: 9

단기 트레이딩:
- 빠른 EMA: 5, 느린 EMA: 13, 시그널: 5

장기 투자:
- 빠른 EMA: 19, 느린 EMA: 39, 시그널: 9`,
    relatedStrategies: ['sma_strategy', 'ema_strategy'],
  },

  ema_strategy: {
    id: 'ema_strategy',
    name: 'EMA 교차 (Exponential Moving Average)',
    description: '지수이동평균선의 교차를 이용한 추세 추종 전략',
    category: '기술적 분석',
    difficulty: '중급',
    overview: `EMA(지수이동평균)는 최근 가격에 더 큰 가중치를 부여하는 이동평균입니다. SMA보다 가격 변화에 빠르게 반응하여 추세 전환을 조기에 포착할 수 있습니다.

단기 EMA가 장기 EMA를 돌파할 때 매매 신호를 생성하며, SMA 교차 전략과 유사하지만 더 민감하게 반응합니다.`,
    howItWorks: [
      '1. 단기 EMA(예: 12일)와 장기 EMA(예: 26일) 계산',
      '2. 단기 EMA가 장기 EMA 상향 돌파 → 매수',
      '3. 단기 EMA가 장기 EMA 하향 돌파 → 매도',
      '4. EMA가 가격 지지/저항선 역할',
    ],
    advantages: [
      '✓ 최근 가격에 더 민감하게 반응',
      '✓ 추세 전환을 SMA보다 빠르게 포착',
      '✓ 잘못된 신호 감소',
      '✓ 동적 지지/저항선으로 활용',
      '✓ MACD 등 다른 지표의 기반',
    ],
    disadvantages: [
      '✗ 너무 민감하여 소음(noise)에 취약',
      '✗ 횡보장에서 잦은 매매 발생',
      '✗ SMA보다 계산이 복잡',
      '✗ 변동성 큰 시장에서 오신호 가능',
    ],
    bestFor: [
      '단기~중기 트레이더',
      '빠른 추세 전환 포착을 원하는 투자자',
      '변동성 있는 시장에서 거래하는 사람',
      '데이 트레이딩 또는 스윙 트레이딩',
    ],
    parameters: [
      {
        name: 'fast_window',
        description: '단기 EMA 기간',
        defaultValue: 12,
        range: '5~50일',
      },
      {
        name: 'slow_window',
        description: '장기 EMA 기간',
        defaultValue: 26,
        range: '10~200일',
      },
    ],
    example: `단기 트레이딩:
- 빠른 EMA: 8, 느린 EMA: 21

중기 트레이딩 (MACD 기본):
- 빠른 EMA: 12, 느린 EMA: 26

장기 투자:
- 빠른 EMA: 50, 느린 EMA: 200`,
    relatedStrategies: ['sma_strategy', 'macd_strategy'],
  },
};
