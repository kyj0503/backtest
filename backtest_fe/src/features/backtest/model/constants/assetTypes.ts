/**
 * 자산 타입 정의
 */

export const ASSET_TYPES = {
  STOCK: 'stock',
  CASH: 'cash'
} as const;

export type AssetType = typeof ASSET_TYPES[keyof typeof ASSET_TYPES];

// 투자 방식 옵션
export const INVESTMENT_TYPE_OPTIONS = [
  { value: 'lump_sum', label: '일시 투자' },
  { value: 'dca', label: '분할 매수 (DCA)' }
];
