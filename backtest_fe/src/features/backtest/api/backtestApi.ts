import { buildApiUrl } from '@/shared/api/base';
import { BacktestRequest } from '../model/api-types';

export interface ApiError {
  message: string;
  status: number;
  errorId?: string;
  type?: 'network' | 'validation' | 'server' | 'data_not_found' | 'rate_limit';
}

const extractErrorId = (detail: unknown): string | undefined => {
  if (typeof detail !== 'string') {
    return undefined;
  }
  const match = detail.match(/오류 ID:\s*([a-zA-Z0-9]+)/);
  return match?.[1];
};

const mapStatusToType = (status: number): ApiError['type'] => {
  switch (status) {
    case 400:
    case 422:
      return 'validation';
    case 404:
      return 'data_not_found';
    case 429:
      return 'rate_limit';
    default:
      return 'server';
  }
};

const parseErrorResponse = async (response: Response): Promise<ApiError> => {
  let message = `HTTP error! status: ${response.status}`;
  let errorId: string | undefined;

  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') {
      message = data.detail;
      errorId = extractErrorId(data.detail);
    } else if (typeof data?.message === 'string') {
      message = data.message;
    }
  } catch (error) {
    console.warn('Failed to parse API error payload', error);
  }

  return {
    message,
    status: response.status,
    errorId,
    type: mapStatusToType(response.status),
  };
};

const createNetworkError = (error: unknown): ApiError => {
  if (error instanceof Error && error.name === 'TypeError' && /fetch/i.test(error.message)) {
    return {
      message: '네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해주세요.',
      status: 0,
      type: 'network',
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      status: 500,
      type: 'server',
    };
  }

  return {
    message: '알 수 없는 오류가 발생했습니다.',
    status: 500,
    type: 'server',
  };
};

export const runBacktest = async (request: BacktestRequest) => {
  const unifiedRequest = {
    portfolio: request.portfolio.map((stock) => ({
      symbol: stock.symbol,
      amount: stock.amount,
      weight: (stock as any).weight,
      investment_type: stock.investment_type || 'lump_sum',
      dca_periods: stock.dca_periods,
      asset_type: stock.asset_type || 'stock',
    })),
    start_date: request.start_date,
    end_date: request.end_date,
    strategy: request.strategy,
    strategy_params: request.strategy_params || {},
    commission: request.commission ?? 0.002,
    rebalance_frequency: request.rebalance_frequency || 'monthly',
  };

  try {
    const response = await fetch(buildApiUrl('/api/v1/backtest/execute'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(unifiedRequest),
    });

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    const result = await response.json();

    if (result?.status === 'success') {
      return {
        ...result.data,
        backtest_type: result.backtest_type,
        api_version: 'unified',
      };
    }

    return result;
  } catch (error) {
    if (error && typeof error === 'object' && 'message' in (error as Record<string, unknown>)) {
      throw error as ApiError;
    }
    throw createNetworkError(error);
  }
};

export const getStockData = async (ticker: string, startDate: string, endDate: string) => {
  try {
    const response = await fetch(
      buildApiUrl(`/api/v1/backtest/stock-data/${ticker}?start_date=${startDate}&end_date=${endDate}`),
      { headers: { 'Content-Type': 'application/json' } },
    );

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    return response.json();
  } catch (error) {
    if (error && typeof error === 'object' && 'message' in (error as Record<string, unknown>)) {
      throw error as ApiError;
    }
    throw createNetworkError(error);
  }
};

export const getExchangeRate = async (startDate: string, endDate: string) => {
  try {
    const response = await fetch(
      buildApiUrl(`/api/v1/backtest/exchange-rate?start_date=${startDate}&end_date=${endDate}`),
      { headers: { 'Content-Type': 'application/json' } },
    );

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    return response.json();
  } catch (error) {
    if (error && typeof error === 'object' && 'message' in (error as Record<string, unknown>)) {
      throw error as ApiError;
    }
    throw createNetworkError(error);
  }
};

export const getStockVolatilityNews = async (
  ticker: string,
  startDate: string,
  endDate: string,
  threshold = 5.0,
) => {
  try {
    const response = await fetch(
      buildApiUrl(
        `/api/v1/backtest/stock-volatility-news/${ticker}?start_date=${startDate}&end_date=${endDate}&threshold=${threshold}`,
      ),
      { headers: { 'Content-Type': 'application/json' } },
    );

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    return response.json();
  } catch (error) {
    if (error && typeof error === 'object' && 'message' in (error as Record<string, unknown>)) {
      throw error as ApiError;
    }
    throw createNetworkError(error);
  }
};

export const getNaverNews = async (ticker: string, date: string, display = 10) => {
  try {
    const response = await fetch(
      buildApiUrl(`/api/v1/naver-news/ticker/${ticker}/date?start_date=${date}&end_date=${date}&display=${display}`),
      { headers: { 'Content-Type': 'application/json' } },
    );

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    return response.json();
  } catch (error) {
    if (error && typeof error === 'object' && 'message' in (error as Record<string, unknown>)) {
      throw error as ApiError;
    }
    throw createNetworkError(error);
  }
};

export const searchNews = async (query: string, display = 15) => {
  try {
    const response = await fetch(
      buildApiUrl(`/api/v1/naver-news/search?query=${encodeURIComponent(query)}&display=${display}`),
      { headers: { 'Content-Type': 'application/json' } },
    );

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    return response.json();
  } catch (error) {
    if (error && typeof error === 'object' && 'message' in (error as Record<string, unknown>)) {
      throw error as ApiError;
    }
    throw createNetworkError(error);
  }
};
