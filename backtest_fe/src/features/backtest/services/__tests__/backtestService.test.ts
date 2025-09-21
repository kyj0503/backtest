/**
 * BacktestService 테스트
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BacktestService } from '../backtestService'
import { apiClient } from '@/shared/api/client'
import { createMockBacktestResult, createMockStrategy, mockApiResponse } from '@/test/utils'

// API 클라이언트 모킹
vi.mock('@/shared/api/client')

const mockedApiClient = vi.mocked(apiClient)

describe('BacktestService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('executeBacktest', () => {
    it('should execute backtest successfully', async () => {
      const mockResult = createMockBacktestResult()
      mockedApiClient.post.mockResolvedValue(mockApiResponse(mockResult))

      const request = {
        portfolio: [{ symbol: 'AAPL', amount: 1000 }],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        strategy: 'buy_and_hold',
      }

      const result = await BacktestService.executeBacktest(request)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/v1/backtest/execute', request)
      expect(result).toEqual(mockResult)
    })

    it('should handle backtest execution error', async () => {
      const error = new Error('Backtest failed')
      mockedApiClient.post.mockRejectedValue(error)

      const request = {
        portfolio: [{ symbol: 'AAPL', amount: 1000 }],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        strategy: 'buy_and_hold',
      }

      await expect(BacktestService.executeBacktest(request)).rejects.toThrow('Backtest failed')
    })
  })

  describe('getStrategies', () => {
    it('should fetch strategies successfully', async () => {
      const mockStrategies = [createMockStrategy()]
      mockedApiClient.get.mockResolvedValue(mockApiResponse(mockStrategies))

      const result = await BacktestService.getStrategies()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/strategies')
      expect(result).toEqual(mockStrategies)
    })
  })

  describe('getStrategy', () => {
    it('should fetch specific strategy', async () => {
      const mockStrategy = createMockStrategy()
      mockedApiClient.get.mockResolvedValue(mockApiResponse(mockStrategy))

      const result = await BacktestService.getStrategy('buy_and_hold')

      expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/strategies/buy_and_hold')
      expect(result).toEqual(mockStrategy)
    })
  })

  describe('searchNews', () => {
    it('should search news with default display count', async () => {
      const mockNews = {
        lastBuildDate: '2023-12-01',
        total: 100,
        start: 1,
        display: 10,
        items: []
      }
      mockedApiClient.get.mockResolvedValue(mockApiResponse(mockNews))

      const result = await BacktestService.searchNews('AAPL')

      expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/naver-news/search', {
        params: { query: 'AAPL', display: 10 }
      })
      expect(result).toEqual(mockNews)
    })

    it('should search news with custom display count', async () => {
      const mockNews = {
        lastBuildDate: '2023-12-01',
        total: 100,
        start: 1,
        display: 20,
        items: []
      }
      mockedApiClient.get.mockResolvedValue(mockApiResponse(mockNews))

      await BacktestService.searchNews('AAPL', 20)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/naver-news/search', {
        params: { query: 'AAPL', display: 20 }
      })
    })
  })

  describe('getExchangeRate', () => {
    it('should fetch exchange rate', async () => {
      const mockExchangeRate = {
        date: '2023-12-01',
        usd_krw: 1300.5,
        change_rate: 0.5,
        trend: 'up' as const
      }
      mockedApiClient.get.mockResolvedValue(mockApiResponse(mockExchangeRate))

      const result = await BacktestService.getExchangeRate()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/yfinance/exchange-rate')
      expect(result).toEqual(mockExchangeRate)
    })
  })

  describe('getVolatilityData', () => {
    it('should fetch volatility data for multiple symbols', async () => {
      const mockVolatilityData = [
        {
          symbol: 'AAPL',
          period: '1M',
          volatility: 0.25,
          price_change: 5.2,
          volume_change: -10.5,
          last_updated: '2023-12-01T10:00:00Z'
        }
      ]
      mockedApiClient.get.mockResolvedValue(mockApiResponse(mockVolatilityData))

      const result = await BacktestService.getVolatilityData(['AAPL', 'GOOGL'])

      expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/volatility', {
        params: { symbols: 'AAPL,GOOGL' }
      })
      expect(result).toEqual(mockVolatilityData)
    })
  })

  describe('runOptimization', () => {
    it('should run optimization successfully', async () => {
      const mockOptimizationResult = {
        best_params: { param1: 10, param2: 20 },
        best_score: 1.5,
        results: []
      }
      mockedApiClient.post.mockResolvedValue(mockApiResponse(mockOptimizationResult))

      const request = {
        ticker: 'AAPL',
        strategy: 'sma_cross',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        parameter_ranges: {
          short_window: { min: 5, max: 20, step: 5 },
          long_window: { min: 20, max: 50, step: 10 }
        },
        objective: 'sharpe' as const
      }

      const result = await BacktestService.runOptimization(request)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/v1/optimize/run', request)
      expect(result).toEqual(mockOptimizationResult)
    })
  })

  describe('getSystemInfo', () => {
    it('should fetch system info', async () => {
      const mockSystemInfo = {
        version: '1.0.0',
        environment: 'production',
        last_updated: '2023-12-01T10:00:00Z'
      }
      mockedApiClient.get.mockResolvedValue(mockApiResponse(mockSystemInfo))

      const result = await BacktestService.getSystemInfo()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/system/info')
      expect(result).toEqual(mockSystemInfo)
    })
  })
})