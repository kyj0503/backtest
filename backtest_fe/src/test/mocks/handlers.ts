/**
 * MSW API 모킹 핸들러
 */

import { http, HttpResponse } from 'msw'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const handlers = [
  // 백테스트 실행 API (통합 엔드포인트)
  http.post(`${API_BASE_URL}/api/v1/backtest/portfolio`, () => {
    return HttpResponse.json({
      status: 'success',
      backtest_type: 'single_stock',
      data: {
        ticker: 'AAPL',
        strategy: 'buy_and_hold',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        ohlc_data: [
          { date: '2023-01-01', open: 100, high: 105, low: 99, close: 103, volume: 1000000 },
          { date: '2023-06-01', open: 110, high: 115, low: 108, close: 112, volume: 1200000 },
          { date: '2023-12-31', open: 120, high: 125, low: 118, close: 123, volume: 1300000 },
        ],
        equity_data: [
          { date: '2023-01-01', equity: 10000 },
          { date: '2023-06-01', equity: 11000 },
          { date: '2023-12-31', equity: 11550 },
        ],
        trade_markers: [
          { date: '2023-01-01', type: 'buy', price: 100 },
          { date: '2023-12-31', type: 'sell', price: 123 },
        ],
        indicators: [],
        summary_stats: {
          total_return_pct: 15.5,
          total_trades: 2,
          win_rate_pct: 100,
          max_drawdown_pct: -5.2,
          sharpe_ratio: 1.2,
          profit_factor: 2.1,
        }
      }
    })
  }),

  // 백테스트 히스토리 조회
  http.get(`${API_BASE_URL}/api/v1/backtest/history`, () => {
    return HttpResponse.json([
      {
        id: 1,
        ticker: 'AAPL',
        strategy: 'buy_and_hold',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        total_return_pct: 15.5,
        created_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        ticker: 'GOOGL',
        strategy: 'sma_cross',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        total_return_pct: -5.2,
        created_at: '2024-01-02T00:00:00Z'
      }
    ])
  }),

  // 헬스체크
  http.get(`${API_BASE_URL}/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString()
    })
  }),

  // 전략 목록 조회
  http.get(`${API_BASE_URL}/api/v1/strategies`, () => {
    return HttpResponse.json([
      {
        name: 'buy_and_hold',
        description: 'Simple buy and hold strategy',
        parameters: [],
        category: 'basic'
      },
      {
        name: 'sma_cross',
        description: 'Simple Moving Average Crossover',
        parameters: [
          { name: 'short_window', type: 'integer', default: 20 },
          { name: 'long_window', type: 'integer', default: 50 }
        ],
        category: 'technical'
      }
    ])
  }),
]
