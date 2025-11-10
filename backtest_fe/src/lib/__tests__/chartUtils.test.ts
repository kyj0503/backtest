/**
 * Chart 유틸리티 함수 테스트
 * 
 * **테스트 범위**:
 * - 날짜 포맷 변환
 * - 데이터 정규화
 * - 빈 데이터 처리
 */

import { describe, it, expect } from 'vitest'

/**
 * 날짜 문자열을 차트 표시용 포맷으로 변환
 */
const formatChartDate = (dateString: string, format: 'short' | 'long' = 'short'): string => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  
  if (isNaN(date.getTime())) {
    return dateString // 유효하지 않은 날짜면 원본 반환
  }
  
  if (format === 'short') {
    // 짧은 형식: MM/DD
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`
  } else {
    // 긴 형식: YYYY-MM-DD
    return date.toISOString().split('T')[0]
  }
}

/**
 * OHLC 데이터 배열을 정규화
 */
const normalizeOhlcData = (data: any[]): any[] => {
  if (!data || data.length === 0) return []
  
  return data.map(item => ({
    date: item.date,
    open: Number(item.open) || 0,
    high: Number(item.high) || 0,
    low: Number(item.low) || 0,
    close: Number(item.close) || 0,
    volume: Number(item.volume) || 0,
  }))
}

/**
 * 가격 범위 계산
 */
const getPriceRange = (data: any[]): { min: number; max: number } => {
  if (!data || data.length === 0) {
    return { min: 0, max: 0 }
  }
  
  const prices = data.flatMap(item => [item.high, item.low])
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  
  // 상하 여백 5% 추가
  const padding = (max - min) * 0.05
  
  return {
    min: Math.floor(min - padding),
    max: Math.ceil(max + padding),
  }
}

/**
 * 숫자를 통화 형식으로 변환
 */
const formatCurrency = (value: number, currency: string = 'USD'): string => {
  if (isNaN(value)) return 'N/A'
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * 퍼센트 값 포맷
 */
const formatPercent = (value: number, decimals: number = 2): string => {
  if (isNaN(value)) return 'N/A'
  
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

describe('chartUtils', () => {
  describe('formatChartDate', () => {
    it('짧은 형식으로 날짜를 변환한다', () => {
      expect(formatChartDate('2023-01-15', 'short')).toBe('01/15')
      expect(formatChartDate('2023-12-31', 'short')).toBe('12/31')
    })

    it('긴 형식으로 날짜를 변환한다', () => {
      expect(formatChartDate('2023-01-15', 'long')).toBe('2023-01-15')
      expect(formatChartDate('2023-12-31', 'long')).toBe('2023-12-31')
    })

    it('빈 문자열을 처리한다', () => {
      expect(formatChartDate('')).toBe('')
    })

    it('유효하지 않은 날짜를 원본 그대로 반환한다', () => {
      expect(formatChartDate('invalid-date')).toBe('invalid-date')
    })

    it('기본값은 짧은 형식이다', () => {
      expect(formatChartDate('2023-01-15')).toBe('01/15')
    })
  })

  describe('normalizeOhlcData', () => {
    it('OHLC 데이터를 정규화한다', () => {
      const rawData = [
        { date: '2023-01-01', open: '100', high: '105', low: '99', close: '103', volume: '1000000' },
        { date: '2023-01-02', open: 103, high: 108, low: 102, close: 107, volume: 1200000 },
      ]

      const normalized = normalizeOhlcData(rawData)

      expect(normalized).toEqual([
        { date: '2023-01-01', open: 100, high: 105, low: 99, close: 103, volume: 1000000 },
        { date: '2023-01-02', open: 103, high: 108, low: 102, close: 107, volume: 1200000 },
      ])
    })

    it('빈 배열을 처리한다', () => {
      expect(normalizeOhlcData([])).toEqual([])
    })

    it('null/undefined를 처리한다', () => {
      expect(normalizeOhlcData(null as any)).toEqual([])
      expect(normalizeOhlcData(undefined as any)).toEqual([])
    })

    it('유효하지 않은 숫자를 0으로 변환한다', () => {
      const rawData = [
        { date: '2023-01-01', open: 'invalid', high: null, low: undefined, close: NaN, volume: '' },
      ]

      const normalized = normalizeOhlcData(rawData)

      expect(normalized).toEqual([
        { date: '2023-01-01', open: 0, high: 0, low: 0, close: 0, volume: 0 },
      ])
    })
  })

  describe('getPriceRange', () => {
    it('가격 범위를 계산한다', () => {
      const data = [
        { high: 105, low: 99 },
        { high: 110, low: 103 },
        { high: 108, low: 102 },
      ]

      const range = getPriceRange(data)

      // 최저: 99, 최고: 110, 범위: 11, 패딩: 0.55
      // min = 99 - 0.55 = 98.45 → 98
      // max = 110 + 0.55 = 110.55 → 111
      expect(range.min).toBe(98)
      expect(range.max).toBe(111)
    })

    it('빈 배열은 0을 반환한다', () => {
      expect(getPriceRange([])).toEqual({ min: 0, max: 0 })
    })

    it('null/undefined를 처리한다', () => {
      expect(getPriceRange(null as any)).toEqual({ min: 0, max: 0 })
      expect(getPriceRange(undefined as any)).toEqual({ min: 0, max: 0 })
    })
  })

  describe('formatCurrency', () => {
    it('통화 형식으로 변환한다', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56')
      expect(formatCurrency(1234.56, 'USD')).toBe('$1,234.56')
    })

    it('음수를 처리한다', () => {
      expect(formatCurrency(-1234.56)).toBe('-$1,234.56')
    })

    it('0을 처리한다', () => {
      expect(formatCurrency(0)).toBe('$0.00')
    })

    it('NaN을 처리한다', () => {
      expect(formatCurrency(NaN)).toBe('N/A')
    })

    it('큰 숫자를 처리한다', () => {
      expect(formatCurrency(1234567.89)).toBe('$1,234,567.89')
    })
  })

  describe('formatPercent', () => {
    it('퍼센트 값을 포맷한다', () => {
      expect(formatPercent(12.34)).toBe('+12.34%')
      expect(formatPercent(-5.67)).toBe('-5.67%')
    })

    it('양수에 + 기호를 추가한다', () => {
      expect(formatPercent(5)).toBe('+5.00%')
    })

    it('0을 처리한다', () => {
      expect(formatPercent(0)).toBe('+0.00%')
    })

    it('소수점 자릿수를 조정할 수 있다', () => {
      expect(formatPercent(12.3456, 1)).toBe('+12.3%')
      expect(formatPercent(12.3456, 3)).toBe('+12.346%')
    })

    it('NaN을 처리한다', () => {
      expect(formatPercent(NaN)).toBe('N/A')
    })
  })
})
