/**
 * 리밸런싱 설정 (주 단위)
 */

export const REBALANCE_OPTIONS = [
  { value: 'none', label: '리밸런싱 안함' },
  { value: 'weekly_1', label: '매주' },
  { value: 'weekly_2', label: '2주마다' },
  { value: 'weekly_4', label: '4주마다 (약 1달)' },
  { value: 'weekly_8', label: '8주마다 (약 2달)' },
  { value: 'weekly_12', label: '12주마다 (약 1분기)' },
  { value: 'weekly_24', label: '24주마다 (약 반년)' },
  { value: 'weekly_48', label: '48주마다 (약 1년)' }
];

export type RebalanceFrequency = 
  | 'none' 
  | 'weekly_1' 
  | 'weekly_2' 
  | 'weekly_4' 
  | 'weekly_8' 
  | 'weekly_12' 
  | 'weekly_24' 
  | 'weekly_48';
