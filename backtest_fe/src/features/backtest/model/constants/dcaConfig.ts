/**
 * DCA (Dollar Cost Averaging) 관련 설정
 */

// DCA 주기 프리셋 (Nth Weekday 방식)
export type DcaFrequency = 'weekly_1' | 'weekly_2' | 'monthly_1' | 'monthly_2' | 'monthly_3' | 'monthly_6' | 'monthly_12';

export const DCA_FREQUENCY_OPTIONS = [
  { value: 'weekly_1', label: '매주', type: 'weekly', interval: 1 },
  { value: 'weekly_2', label: '2주마다', type: 'weekly', interval: 2 },
  { value: 'monthly_1', label: '매월 (Nth 요일)', type: 'monthly', interval: 1 },
  { value: 'monthly_2', label: '2개월마다', type: 'monthly', interval: 2 },
  { value: 'monthly_3', label: '3개월마다 (분기)', type: 'monthly', interval: 3 },
  { value: 'monthly_6', label: '6개월마다 (반년)', type: 'monthly', interval: 6 },
  { value: 'monthly_12', label: '12개월마다 (1년)', type: 'monthly', interval: 12 }
] as const;

/**
 * DCA 주기 정보를 가져오는 헬퍼 함수
 */
export const getDcaPeriodInfo = (frequency: DcaFrequency): { type: string; interval: number } => {
  const option = DCA_FREQUENCY_OPTIONS.find(opt => opt.value === frequency);
  return { type: option?.type || 'monthly', interval: option?.interval || 1 };
};

