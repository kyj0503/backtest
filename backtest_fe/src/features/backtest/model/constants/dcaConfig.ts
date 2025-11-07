/**
 * DCA (Dollar Cost Averaging) 관련 설정
 */

// DCA 주기 프리셋 (주 단위)
export type DcaFrequency = 'weekly_1' | 'weekly_2' | 'weekly_4' | 'weekly_8' | 'weekly_12' | 'weekly_24' | 'weekly_48';

export const DCA_FREQUENCY_OPTIONS = [
  { value: 'weekly_1', label: '1주마다', weeks: 1 },
  { value: 'weekly_2', label: '2주마다', weeks: 2 },
  { value: 'weekly_4', label: '4주마다', weeks: 4 },
  { value: 'weekly_8', label: '8주마다', weeks: 8 },
  { value: 'weekly_12', label: '12주마다', weeks: 12 },
  { value: 'weekly_24', label: '24주마다', weeks: 24 },
  { value: 'weekly_48', label: '48주마다', weeks: 48 }
] as const;

/**
 * DCA 주기(주)를 가져오는 헬퍼 함수
 */
export const getDcaWeeks = (frequency: DcaFrequency): number => {
  const option = DCA_FREQUENCY_OPTIONS.find(opt => opt.value === frequency);
  return option?.weeks || 1;
};
