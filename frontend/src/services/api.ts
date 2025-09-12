// API 호출을 담당하는 서비스 클래스
import { BacktestRequest } from '../types/api';

export interface ApiError {
  message: string;
  status: number;
  errorId?: string;
  type?: 'network' | 'validation' | 'server' | 'data_not_found' | 'rate_limit';
}

export class BacktestApiService {
  private getApiBaseUrl(): string {
    // 1) 환경변수 우선 (Vite)
    const envBase = (import.meta as any)?.env?.VITE_API_BASE_URL as string | undefined;
    if (envBase && typeof envBase === 'string') {
      return envBase.replace(/\/$/, '');
    }

    // 2) 기본: 상대 경로 사용 -> dev에서는 vite proxy(/api), prod에서는 동일 오리진
    return '';
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

  async runBacktest(request: BacktestRequest) {
    try {
      // 새로운 통합 엔드포인트 사용 - 백엔드에서 요구하는 형식으로 변환
      const unifiedRequest = {
        portfolio: request.portfolio.map(stock => ({
          symbol: stock.symbol,
          amount: stock.amount,
          investment_type: stock.investment_type || 'lump_sum',
          dca_periods: stock.dca_periods,
          asset_type: stock.asset_type || 'stock'
        })),
        start_date: request.start_date,
        end_date: request.end_date,
        strategy: request.strategy,
        strategy_params: request.strategy_params || {},
        commission: request.commission || 0.002,
        rebalance_frequency: request.rebalance_frequency || 'monthly'
      };

      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(unifiedRequest),
      });

      if (!response.ok) {
        const apiError = await this.handleApiError(response);
        throw apiError;
      }

      const result = await response.json();
      
      // 통합 API 응답 처리 - 표준화된 형식 반환
      if (result.status === 'success') {
        return {
          ...result.data,
          backtest_type: result.backtest_type, // 백테스트 유형 정보 포함
          api_version: 'unified' // 통합 API 사용 표시
        };
      }
      
      return result;
    } catch (error) {
      if (error && typeof error === 'object' && 'message' in error) {
        throw error; // 이미 처리된 ApiError
      }
      throw this.createApiError(error);
    }
  }



  // 레거시 로직 (필요시 사용)
  async runBacktestLegacy(request: BacktestRequest) {
    // 현금 자산이 포함된 경우 항상 포트폴리오 API 사용
    const hasCashAsset = request.portfolio.some(stock => stock.asset_type === 'cash');
    
    if (request.portfolio.length === 1 && !hasCashAsset) {
      // 단일 종목 (현금 자산이 아닌 경우만)
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
      // 포트폴리오 (현금 자산이 포함된 경우 포함)
      const portfolioRequest = {
        portfolio: request.portfolio.map(stock => ({
          symbol: stock.asset_type === 'cash' ? 'CASH' : stock.symbol, // 백엔드에서는 여전히 CASH 심볼 사용
          amount: stock.amount,
          investment_type: stock.investment_type,
          dca_periods: stock.dca_periods,
          asset_type: stock.asset_type || 'stock'  // 자산 타입 추가
        })),
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

  async getStockData(ticker: string, startDate: string, endDate: string) {
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/stock-data/${ticker}?start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
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

  async getExchangeRate(startDate: string, endDate: string) {
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/exchange-rate?start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
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

  async getStockVolatilityNews(ticker: string, startDate: string, endDate: string, threshold: number = 5.0) {
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/backtest/stock-volatility-news/${ticker}?start_date=${startDate}&end_date=${endDate}&threshold=${threshold}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
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

  async getNaverNews(ticker: string, date: string, display: number = 10) {
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/naver-news/ticker/${ticker}/date?start_date=${date}&end_date=${date}&display=${display}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
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

  async searchNews(query: string, display: number = 15) {
    try {
      const response = await fetch(`${this.getApiBaseUrl()}/api/v1/naver-news/search?query=${encodeURIComponent(query)}&display=${display}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
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
}

// 싱글톤 인스턴스 export
export const backtestApiService = new BacktestApiService();
