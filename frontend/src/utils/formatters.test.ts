import { describe, it, expect } from 'vitest'
import { 
  formatCurrency, 
  formatPercent, 
  formatNumber,
  formatDate,
  getStatVariant,
  getTradeColor,
  calculateTotalAmount,
  calculateWeight
} from '../utils/formatters'

describe('formatters', () => {
  describe('formatCurrency', () => {
    it('should format positive numbers correctly', () => {
      expect(formatCurrency(1234)).toBe('US$1,234')
      expect(formatCurrency(1000000)).toBe('US$1,000,000')
    })

    it('should format negative numbers correctly', () => {
      expect(formatCurrency(-1234)).toBe('-US$1,234')
    })

    it('should handle zero', () => {
      expect(formatCurrency(0)).toBe('US$0')
    })

    it('should handle invalid inputs', () => {
      expect(formatCurrency(NaN)).toBe('N/A')
    })
  })

  describe('formatPercent', () => {
    it('should format positive percentages correctly', () => {
      expect(formatPercent(25.678)).toBe('25.68%')
      expect(formatPercent(100)).toBe('100.00%')
    })

    it('should format negative percentages correctly', () => {
      expect(formatPercent(-15.5)).toBe('-15.50%')
    })

    it('should handle zero', () => {
      expect(formatPercent(0)).toBe('0.00%')
    })

    it('should handle invalid inputs', () => {
      expect(formatPercent(undefined)).toBe('N/A')
      expect(formatPercent(null)).toBe('N/A')
      expect(formatPercent(NaN)).toBe('N/A')
    })
  })

  describe('formatNumber', () => {
    it('should format numbers with specified decimals', () => {
      expect(formatNumber(3.14159, 2)).toBe('3.14')
      expect(formatNumber(3.14159, 4)).toBe('3.1416')
    })

    it('should handle invalid inputs', () => {
      expect(formatNumber(undefined)).toBe('N/A')
      expect(formatNumber(null)).toBe('N/A')
      expect(formatNumber(NaN)).toBe('N/A')
    })
  })

  describe('getStatVariant', () => {
    it('should return correct variants for return type', () => {
      expect(getStatVariant(10, 'return')).toBe('success')
      expect(getStatVariant(-10, 'return')).toBe('danger')
      expect(getStatVariant(0, 'return')).toBe('success')
    })

    it('should return correct variants for sharpe type', () => {
      expect(getStatVariant(1.5, 'sharpe')).toBe('success')
      expect(getStatVariant(0.7, 'sharpe')).toBe('warning')
      expect(getStatVariant(0.3, 'sharpe')).toBe('danger')
    })

    it('should return correct variants for drawdown type', () => {
      expect(getStatVariant(-3, 'drawdown')).toBe('success')
      expect(getStatVariant(-10, 'drawdown')).toBe('warning')
      expect(getStatVariant(-20, 'drawdown')).toBe('danger')
    })

    it('should return correct variants for winRate type', () => {
      expect(getStatVariant(70, 'winRate')).toBe('success')
      expect(getStatVariant(50, 'winRate')).toBe('warning')
      expect(getStatVariant(30, 'winRate')).toBe('danger')
    })
  })

  describe('getTradeColor', () => {
    it('should return correct colors for entry trades', () => {
      expect(getTradeColor('entry', 'buy')).toBe('#198754')
      expect(getTradeColor('entry', 'sell')).toBe('#dc3545')
    })

    it('should return correct color for exit trades', () => {
      expect(getTradeColor('exit')).toBe('#ffc107')
    })
  })

  describe('calculateTotalAmount', () => {
    it('should calculate total amount correctly', () => {
      const portfolio = [
        { amount: 1000 },
        { amount: 2000 },
        { amount: 500 }
      ]
      expect(calculateTotalAmount(portfolio)).toBe(3500)
    })

    it('should handle empty portfolio', () => {
      expect(calculateTotalAmount([])).toBe(0)
    })
  })

  describe('calculateWeight', () => {
    it('should calculate weight correctly', () => {
      expect(calculateWeight(1000, 5000)).toBe(20)
      expect(calculateWeight(2500, 5000)).toBe(50)
    })

    it('should handle zero total amount', () => {
      expect(calculateWeight(1000, 0)).toBe(0)
    })
  })
})
