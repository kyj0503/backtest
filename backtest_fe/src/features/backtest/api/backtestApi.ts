import { apiClient, extractErrorMessage } from '@/shared/api/client';

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

const toApiError = (error: unknown): ApiError => {
  if (error && typeof error === 'object' && 'isAxiosError' in error) {
    const axiosErr = error as unknown as { response?: { status: number; data?: { detail?: string; message?: string } }; message: string };
    const status = axiosErr.response?.status ?? 0;
    const data = axiosErr.response?.data;

    if (status === 0) {
      return {
        message: '네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해주세요.',
        status: 0,
        type: 'network',
      };
    }

    const detail = data?.detail;
    const message = (typeof detail === 'string' ? detail : undefined)
      ?? data?.message
      ?? extractErrorMessage(error);

    return {
      message,
      status,
      errorId: extractErrorId(detail),
      type: mapStatusToType(status),
    };
  }

  if (error instanceof Error) {
    return { message: error.message, status: 500, type: 'server' };
  }

  return { message: '알 수 없는 오류가 발생했습니다.', status: 500, type: 'server' };
};

export const getStockData = async (ticker: string, startDate: string, endDate: string, signal?: AbortSignal) => {
  try {
    const { data } = await apiClient.get(
      `/api/v1/backtest/stock-data/${ticker}`,
      { params: { start_date: startDate, end_date: endDate }, signal },
    );
    return data;
  } catch (error) {
    throw toApiError(error);
  }
};

export const getExchangeRate = async (startDate: string, endDate: string, signal?: AbortSignal) => {
  try {
    const { data } = await apiClient.get(
      `/api/v1/backtest/exchange-rate`,
      { params: { start_date: startDate, end_date: endDate }, signal },
    );
    return data;
  } catch (error) {
    throw toApiError(error);
  }
};

export const getStockVolatilityNews = async (
  ticker: string,
  startDate: string,
  endDate: string,
  threshold = 5.0,
  signal?: AbortSignal,
) => {
  try {
    const { data } = await apiClient.get(
      `/api/v1/backtest/stock-volatility-news/${ticker}`,
      { params: { start_date: startDate, end_date: endDate, threshold }, signal },
    );
    return data;
  } catch (error) {
    throw toApiError(error);
  }
};

export const getNaverNews = async (ticker: string, date: string, display = 10, signal?: AbortSignal) => {
  try {
    const { data } = await apiClient.get(
      `/api/v1/naver-news/ticker/${ticker}/date`,
      { params: { start_date: date, end_date: date, display }, signal },
    );
    return data;
  } catch (error) {
    throw toApiError(error);
  }
};

export const getLatestTickerNews = async (ticker: string, display = 10, signal?: AbortSignal) => {
  try {
    const { data } = await apiClient.get(
      `/api/v1/naver-news/ticker/${ticker}`,
      { params: { display }, signal },
    );
    return data;
  } catch (error) {
    throw toApiError(error);
  }
};

export const searchNews = async (query: string, display = 15, signal?: AbortSignal) => {
  try {
    const { data } = await apiClient.get(
      `/api/v1/naver-news/search`,
      { params: { query, display }, signal },
    );
    return data;
  } catch (error) {
    throw toApiError(error);
  }
};
