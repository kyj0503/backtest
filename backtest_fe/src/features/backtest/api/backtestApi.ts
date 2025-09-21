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
    // First try JSON parsing (most APIs). If that fails, fall back to text.
    const text = await response.text();
    if (!text) {
      message = response.statusText || message;
    } else {
      try {
        const data = JSON.parse(text);
        if (typeof data?.detail === 'string') {
          message = data.detail;
          errorId = extractErrorId(data.detail);
        } else if (typeof data?.message === 'string') {
          message = data.message;
        } else if (typeof data === 'string') {
          message = data;
        } else {
          // fallback to raw text when JSON doesn't contain expected fields
          message = text;
        }
      } catch (jsonErr) {
        // not JSON, use raw text
        message = text;
      }
    }
  } catch (error) {
    console.warn('Failed to read API error payload', error);
    message = response.statusText || message;
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

// FastAPI 백테스트 서버는 인증이 필요 없으므로 직접 호출
// Vite 프록시를 통해 /api/v1/backtest -> http://localhost:8000/api/v1/backtest 로 라우팅됨
export const backtestApi = {
  async executeBacktest(request: BacktestRequest) {
    try {
      // TEMP DEBUG: log outgoing payload shape to help match backend Pydantic model
      try {
        // eslint-disable-next-line no-console
        console.debug('[backtestApi] executeBacktest outgoing payload:', JSON.parse(JSON.stringify(request)));
      } catch (e) {
        // eslint-disable-next-line no-console
        console.debug('[backtestApi] failed stringify payload for debug', e);
      }

      const response = await fetch('/api/v1/backtest/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw await parseErrorResponse(response);
      }

      // TEMP DEBUG: log raw response body to trace what the UI receives
      try {
        const text = await response.text();
        try {
          // try parsing JSON for pretty logging
          // eslint-disable-next-line no-console
          console.debug('[backtestApi] raw response (parsed):', JSON.parse(text));
        } catch (e) {
          // eslint-disable-next-line no-console
          console.debug('[backtestApi] raw response (text):', text);
        }

        // return parsed JSON if possible, otherwise text
        try {
          return JSON.parse(text);
        } catch (e) {
          // if backend returned non-JSON body unexpectedly, return as text
          // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
          return text as unknown as Record<string, unknown>;
        }
      } catch (e) {
        // if reading body fails, fallback to default json() (may throw)
        // eslint-disable-next-line no-console
        console.warn('[backtestApi] failed to read response body for debug', e);
        return response.json();
      }
    } catch (error) {
      if (error && typeof error === 'object' && 'message' in (error as Record<string, unknown>)) {
        throw error as ApiError;
      }
      throw createNetworkError(error);
    }
  },
};

// Convenience named export for backward compatibility with previous imports
export const runBacktest = (request: BacktestRequest) => backtestApi.executeBacktest(request);

export const getStockData = async (ticker: string, startDate: string, endDate: string) => {
  try {
    const response = await fetch(
      `/api/v1/backtest/stock-data/${ticker}?start_date=${startDate}&end_date=${endDate}`,
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
      `/api/v1/backtest/exchange-rate?start_date=${startDate}&end_date=${endDate}`,
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
      `/api/v1/backtest/stock-volatility-news/${ticker}?start_date=${startDate}&end_date=${endDate}&threshold=${threshold}`,
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
      `/api/v1/naver-news/ticker/${ticker}/date?start_date=${date}&end_date=${date}&display=${display}`,
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
      `/api/v1/naver-news/search?query=${encodeURIComponent(query)}&display=${display}`,
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
