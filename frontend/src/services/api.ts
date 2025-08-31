// API 호출을 담당하는 서비스 클래스
import { UnifiedBacktestRequest } from '../types/api';

export interface ApiError {
  message: string;
  status: number;
  errorId?: string;
  type?: 'network' | 'validation' | 'server' | 'data_not_found' | 'rate_limit';
}

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

  private async handleApiError(response: Response): Promise<ApiError> {
    let errorMessage = `HTTP error! status: ${response.status}`;
    let errorType: ApiError['type'] = 'server';
    let errorId: string | undefined;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
      
      // 에러 ID 추출 (백엔드에서 제공하는 경우)
      if (typeof errorData.detail === 'string' && errorData.detail.includes('오류 ID:')) {
        const idMatch = errorData.detail.match(/오류 ID:\s*([a-zA-Z0-9]+)/);
        if (idMatch) {
          errorId = idMatch[1];
        }
      }

      // HTTP 상태 코드에 따른 에러 타입 분류
      switch (response.status) {
        case 404:
          errorType = 'data_not_found';
          break;
        case 422:
          errorType = 'validation';
          break;
        case 429:
          errorType = 'rate_limit';
          break;
        case 400:
          errorType = 'validation';
          break;
        default:
          errorType = 'server';
      }
    } catch (parseError) {
      // JSON 파싱 실패 시 기본 메시지 사용
      console.warn('Error parsing API error response:', parseError);
    }

    return {
      message: errorMessage,
      status: response.status,
      errorId,
      type: errorType
    };
  }

  private createApiError(error: Error | any): ApiError {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return {
        message: '네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해주세요.',
        status: 0,
        type: 'network'
      };
    }

    return {
      message: error.message || '알 수 없는 오류가 발생했습니다.',
      status: 500,
      type: 'server'
    };
  }

  async runSingleStockBacktest(request: {
    ticker: string;
    start_date: string;
    end_date: string;
    initial_cash: number;
    strategy: string;
    strategy_params: Record<string, any>;
  }) {
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/chart-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const apiError = await this.handleApiError(response);
        throw apiError;
      }

      return await response.json();
    } catch (error) {
      if (error && typeof error === 'object' && 'message' in error) {
        throw error; // 이미 처리된 ApiError
      }
      throw this.createApiError(error);
    }
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
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const apiError = await this.handleApiError(response);
        throw apiError;
      }

      return await response.json();
    } catch (error) {
      if (error && typeof error === 'object' && 'message' in error) {
        throw error; // 이미 처리된 ApiError
      }
      throw this.createApiError(error);
    }
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

  async getServerInfo() {
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/system/info`);
      
      if (!response.ok) {
        const apiError = await this.handleApiError(response);
        throw apiError;
      }
      
      return await response.json();
    } catch (error) {
      if (error && typeof error === 'object' && 'message' in error) {
        throw error; // 이미 처리된 ApiError
      }
      throw this.createApiError(error);
    }
  }
}

// 싱글톤 인스턴스 export
export const backtestApiService = new BacktestApiService();
