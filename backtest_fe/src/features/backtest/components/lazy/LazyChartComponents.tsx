import { lazy } from 'react';

// 차트 컴포넌트들의 지연 로딩
export const LazyEquityChart = lazy(() => import('../EquityChart'));
export const LazyOHLCChart = lazy(() => import('../OHLCChart'));
export const LazyTradesChart = lazy(() => import('../TradesChart'));
export const LazyStockPriceChart = lazy(() => import('../StockPriceChart'));

// 뉴스 관련 컴포넌트 지연 로딩
export const LazyStockVolatilityNews = lazy(() => import('../StockVolatilityNews'));

// 통계 컴포넌트 지연 로딩
export const LazyStatsSummary = lazy(() => import('../StatsSummary'));

// 환율 차트 지연 로딩
export const LazyExchangeRateChart = lazy(() => import('../ExchangeRateChart'));
