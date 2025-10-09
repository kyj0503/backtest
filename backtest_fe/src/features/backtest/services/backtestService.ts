/**
 * 리팩터링된 백테스트 서비스
 * 타입 안전성과 에러 처리 개선
 */

import { apiClient } from '@/shared/api/client';
import {
  BacktestRequest,
  UnifiedBacktestResponse,
  Strategy,
  NewsResponse,
  ExchangeRateData,
  VolatilityData,
  OptimizationRequest,
  OptimizationResult,
} from '../model/api-types';

export class BacktestService {
  /**
   * 백테스트 실행 (단일 종목 또는 포트폴리오)
   */
  static async executeBacktest(request: BacktestRequest): Promise<UnifiedBacktestResponse> {
    const response = await apiClient.post<UnifiedBacktestResponse>('/v1/backtest/portfolio', request);
    return response.data;
  }

  /**
   * 이용 가능한 전략 목록 조회
   */
  static async getStrategies(): Promise<Strategy[]> {
    const response = await apiClient.get<Strategy[]>('/v1/strategies');
    return response.data;
  }

  /**
   * 특정 전략 정보 조회
   */
  static async getStrategy(strategyName: string): Promise<Strategy> {
    const response = await apiClient.get<Strategy>(`/v1/strategies/${strategyName}`);
    return response.data;
  }

  /**
   * 최적화 실행
   */
  static async runOptimization(request: OptimizationRequest): Promise<OptimizationResult> {
    const response = await apiClient.post<OptimizationResult>('/v1/optimize/run', request);
    return response.data;
  }

  /**
   * 뉴스 검색
   */
  static async searchNews(query: string, display = 10): Promise<NewsResponse> {
    const response = await apiClient.get<NewsResponse>('/v1/naver-news/search', { 
      params: { query, display } 
    });
    return response.data;
  }

  /**
   * 환율 정보 조회
   */
  static async getExchangeRate(): Promise<ExchangeRateData> {
    const response = await apiClient.get<ExchangeRateData>('/v1/yfinance/exchange-rate');
    return response.data;
  }

  /**
   * 변동성 데이터 조회
   */
  static async getVolatilityData(symbols: string[]): Promise<VolatilityData[]> {
    const response = await apiClient.get<VolatilityData[]>('/v1/volatility', { 
      params: { symbols: symbols.join(',') } 
    });
    return response.data;
  }

  /**
   * 시스템 상태 조회
   */
  static async getSystemInfo() {
    const response = await apiClient.get('/v1/system/info');
    return response.data;
  }
}

export default BacktestService;