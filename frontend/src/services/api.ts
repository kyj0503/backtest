// API 호출을 담당하는 서비스 클래스
import { UnifiedBacktestRequest } from '../types/api';

export class BacktestApiService {
  private getApiBaseUrl(): string {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      const protocol = window.location.protocol;
      
      // 프로덕션 환경 (도메인 사용)
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return `${protocol}//backtest-be.yeonjae.kr`;
      }
    }
    // 개발 환경
    return 'http://localhost:8001';
  }

  async runSingleStockBacktest(request: {
    ticker: string;
    start_date: string;
    end_date: string;
    initial_cash: number;
    strategy: string;
    strategy_params: Record<string, any>;
  }) {
    const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/chart-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async runPortfolioBacktest(request: {
    portfolio: any[];
    start_date: string;
    end_date: string;
    commission: number;
    rebalance_frequency: string;
    strategy: string;
    strategy_params: Record<string, any>;
  }) {
    const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/portfolio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async runBacktest(request: UnifiedBacktestRequest) {
    if (request.portfolio.length === 1) {
      // 단일 종목
      const singleStockRequest = {
        ticker: request.portfolio[0].symbol,
        start_date: request.start_date,
        end_date: request.end_date,
        initial_cash: request.portfolio[0].amount,
        strategy: request.strategy,
        strategy_params: request.strategy_params || {}
      };
      
      return this.runSingleStockBacktest(singleStockRequest);
    } else {
      // 포트폴리오
      const portfolioRequest = {
        portfolio: request.portfolio,
        start_date: request.start_date,
        end_date: request.end_date,
        commission: request.commission || 0.002,
        rebalance_frequency: request.rebalance_frequency || 'monthly',
        strategy: request.strategy,
        strategy_params: request.strategy_params || {}
      };
      
      const result = await this.runPortfolioBacktest(portfolioRequest);
      
      // 포트폴리오 API 응답 처리
      if (result.status === 'success' && result.data) {
        return result.data;
      }
      return result;
    }
  }
}

// 싱글톤 인스턴스 export
export const backtestApiService = new BacktestApiService();
