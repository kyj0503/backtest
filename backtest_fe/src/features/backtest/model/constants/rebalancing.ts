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
