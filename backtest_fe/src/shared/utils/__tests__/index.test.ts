/**
 * 공통 유틸리티 함수 테스트
 */

import { describe, it, expect } from 'vitest'
import {
  formatDate,
  formatNumber,
  truncate,
  capitalize,
  kebabCase,
  camelCase,
  omit,
  pick,
  isEmpty,
  groupBy,
  unique,
  sortBy,
  debounce,
  generateId,
  buildUrl,
  getErrorMessage,
} from '@/shared/utils'

describe('Date Utils', () => {
  it('should format date correctly', () => {
    const date = new Date('2023-12-25T10:30:00Z')
    
    expect(formatDate(date, 'short')).toMatch(/2023/)
    expect(formatDate(date, 'iso')).toBe('2023-12-25')
    expect(formatDate('invalid', 'short')).toBe('Invalid Date')
  })
})

describe('Number Utils', () => {
  it('should format numbers correctly', () => {
    expect(formatNumber(1234.56)).toBe('1,234.56')
    expect(formatNumber(0.15, { percentage: true })).toMatch(/%/)
    expect(formatNumber(1000000, { currency: true })).toMatch(/₩/)
    expect(formatNumber(1500, { compact: true })).toBe('1.5천')
  })

  it('should handle NaN values', () => {
    expect(formatNumber(NaN)).toBe('0')
  })
})

describe('String Utils', () => {
  it('should truncate text correctly', () => {
    expect(truncate('Hello World', 5)).toBe('He...')
    expect(truncate('Hi', 10)).toBe('Hi')
  })

  it('should capitalize text', () => {
    expect(capitalize('hello world')).toBe('Hello world')
    expect(capitalize('HELLO')).toBe('Hello')
  })

  it('should convert to kebab-case', () => {
    expect(kebabCase('helloWorld')).toBe('hello-world')
    expect(kebabCase('Hello World')).toBe('hello-world')
  })

  it('should convert to camelCase', () => {
    expect(camelCase('hello-world')).toBe('helloWorld')
    expect(camelCase('Hello World')).toBe('helloWorld')
  })
})

describe('Object Utils', () => {
  const testObj = { a: 1, b: 2, c: 3 }

  it('should omit keys correctly', () => {
    expect(omit(testObj, ['b'])).toEqual({ a: 1, c: 3 })
  })

  it('should pick keys correctly', () => {
    expect(pick(testObj, ['a', 'c'])).toEqual({ a: 1, c: 3 })
  })

  it('should check if value is empty', () => {
    expect(isEmpty(null)).toBe(true)
    expect(isEmpty('')).toBe(true)
    expect(isEmpty([])).toBe(true)
    expect(isEmpty({})).toBe(true)
    expect(isEmpty('hello')).toBe(false)
    expect(isEmpty([1])).toBe(false)
    expect(isEmpty({ a: 1 })).toBe(false)
  })
})

describe('Array Utils', () => {
  it('should group array by key', () => {
    const items = [
      { type: 'fruit', name: 'apple' },
      { type: 'fruit', name: 'banana' },
      { type: 'vegetable', name: 'carrot' },
    ]
    
    const grouped = groupBy(items, item => item.type)
    expect(grouped.fruit).toHaveLength(2)
    expect(grouped.vegetable).toHaveLength(1)
  })

  it('should remove duplicates', () => {
    expect(unique([1, 2, 2, 3])).toEqual([1, 2, 3])
    
    const items = [
      { id: 1, name: 'a' },
      { id: 2, name: 'b' },
      { id: 1, name: 'c' },
    ]
    expect(unique(items, item => item.id)).toHaveLength(2)
  })

  it('should sort array', () => {
    const items = [{ value: 3 }, { value: 1 }, { value: 2 }]
    const sorted = sortBy(items, item => item.value)
    
    expect(sorted[0].value).toBe(1)
    expect(sorted[2].value).toBe(3)
  })
})

describe('Utility Functions', () => {
  it('should generate unique IDs', () => {
    const id1 = generateId('test_')
    const id2 = generateId('test_')
    
    expect(id1).toMatch(/^test_/)
    expect(id1).not.toBe(id2)
  })

  it('should build URLs with params', () => {
    const url = buildUrl('/api/test', { page: 1, size: 10 })
    expect(url).toContain('page=1')
    expect(url).toContain('size=10')
  })

  it('should extract error messages', () => {
    expect(getErrorMessage('Simple error')).toBe('Simple error')
    expect(getErrorMessage({ message: 'Object error' })).toBe('Object error')
    expect(getErrorMessage({})).toBe('알 수 없는 오류가 발생했습니다.')
  })
})

describe('Debounce', () => {
  it('should debounce function calls', async () => {
    let counter = 0
    const increment = () => counter++
    const debouncedIncrement = debounce(increment, 100)

    debouncedIncrement()
    debouncedIncrement()
    debouncedIncrement()

    expect(counter).toBe(0)

    await new Promise(resolve => setTimeout(resolve, 150))
    expect(counter).toBe(1)
  })
})