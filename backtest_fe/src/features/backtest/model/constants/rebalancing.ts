/**
 * 리밸런싱 설정 (Nth Weekday 방식)
 */

export const REBALANCE_OPTIONS = [
  { value: 'none', label: '리밸런싱 안함' },
  { value: 'weekly_1', label: '매주' },
  { value: 'weekly_2', label: '2주마다' },
  { value: 'monthly_1', label: '매월 (Nth 요일)' },
  { value: 'monthly_2', label: '2개월마다' },
  { value: 'monthly_3', label: '3개월마다 (분기)' },
  { value: 'monthly_6', label: '6개월마다 (반년)' },
  { value: 'monthly_12', label: '12개월마다 (1년)' }
];

export type RebalanceFrequency = 
  | 'none' 
  | 'weekly_1' 
  | 'weekly_2' 
  | 'monthly_1' 
  | 'monthly_2' 
  | 'monthly_3' 
  | 'monthly_6' 
  | 'monthly_12';

/**
 * DCA·리밸런싱은 buy_hold_strategy 전용이다.
 *
 * 백엔드 전략 경로(run_strategy_portfolio_backtest)는 종목별 일시금
 * 백테스트를 합산하는 구조라 두 설정을 구현하지 않으며, 함께 보내면
 * 422로 거부한다(A-02). 과거에는 조용히 무시되어 사용자가 설정하지 않은
 * 조건의 성과를 보고 있었다.
 */
export const supportsDcaAndRebalancing = (strategy?: string): boolean =>
  !strategy || strategy === 'buy_hold_strategy';

/**
 * 실제로 적용되는 리밸런싱 주기.
 *
 * 리밸런싱이 불가능한 조건(기술적 전략, 자산 2개 미만)에서 드롭다운은
 * 'none'을 보여 주지만 state에는 이전 선택값이 남는다. 화면과 전송값이
 * 어긋나지 않도록 표시·제출 모두 이 함수를 거친다.
 */
export const resolveRebalanceFrequency = (
  frequency: string,
  strategy: string | undefined,
  assetCount: number,
): string => (supportsDcaAndRebalancing(strategy) && assetCount >= 2 ? frequency : 'none');
