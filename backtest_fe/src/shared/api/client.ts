import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getApiBaseUrl } from './base';
import { authStorage, AuthTokens, isTokenExpired, persistAuthState, tokensAvailable } from './auth-storage';
import { AuthUser } from '@/features/auth/types';

interface AuthResponseDTO {
  user: {
    id: number;
    username: string;
    email: string;
    profileImage: string | null;
    investmentType: string | null;
    emailVerified: boolean;
  };
  tokens: {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    accessExpiresAt: string;
    refreshTokenExpiresAt: string;
  };
}

const baseURL = getApiBaseUrl();

export const apiClient = axios.create({
  baseURL,
});

let refreshPromise: Promise<AuthTokens | null> | null = null;

const plainClient = axios.create({
  baseURL,
});

const toAuthUser = (dto: AuthResponseDTO['user']): AuthUser => ({
  id: dto.id,
  username: dto.username,
  email: dto.email,
  profileImage: dto.profileImage ?? undefined,
  investmentType: dto.investmentType ?? undefined,
  emailVerified: dto.emailVerified,
});

const toAuthTokens = (dto: AuthResponseDTO['tokens']): AuthTokens => ({
  accessToken: dto.accessToken,
  refreshToken: dto.refreshToken,
  tokenType: dto.tokenType,
  accessExpiresAt: dto.accessExpiresAt,
  refreshTokenExpiresAt: dto.refreshTokenExpiresAt,
});

const requestTokenRefresh = async (): Promise<AuthTokens | null> => {
  const tokens = authStorage.getTokens();
  if (!tokens) return null;
  if (isTokenExpired(tokens.refreshTokenExpiresAt, 0)) {
    authStorage.clearAll();
    return null;
  }
  try {
    const response = await plainClient.post<AuthResponseDTO>('/v1/auth/token/refresh', {
      refreshToken: tokens.refreshToken,
    });
    const newTokens = toAuthTokens(response.data.tokens);
    const user = toAuthUser(response.data.user);
    persistAuthState(user, newTokens);
    return newTokens;
  } catch (error) {
    authStorage.clearAll();
    throw error;
  }
};

const ensureFreshAccessToken = async (): Promise<AuthTokens | null> => {
  const tokens = authStorage.getTokens();
  if (!tokens) return null;
  if (!isTokenExpired(tokens.refreshTokenExpiresAt, 0) && isTokenExpired(tokens.accessExpiresAt)) {
    if (!refreshPromise) {
      refreshPromise = requestTokenRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    return refreshPromise;
  }
  return tokens;
};

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const clonedConfig = { ...config };
  const headers = clonedConfig.headers ?? {};
  const tokens = tokensAvailable() ? await ensureFreshAccessToken() : authStorage.getTokens();
  if (tokens && headers) {
    headers['Authorization'] = `${tokens.tokenType ?? 'Bearer'} ${tokens.accessToken}`;
    clonedConfig.headers = headers;
  }
  return clonedConfig;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status !== 401 || !error.config) {
      throw error;
    }

    // Prevent infinite loop
    if ((error.config as any)._retry) {
      authStorage.clearAll();
      throw error;
    }

    try {
      if (!refreshPromise) {
        refreshPromise = requestTokenRefresh().finally(() => {
          refreshPromise = null;
        });
      }
      const tokens = await refreshPromise;
      if (!tokens) {
        throw error;
      }
      (error.config as any)._retry = true;
      error.config.headers = {
        ...error.config.headers,
        Authorization: `${tokens.tokenType ?? 'Bearer'} ${tokens.accessToken}`,
      };
      return apiClient.request(error.config);
    } catch (refreshError) {
      authStorage.clearAll();
      throw refreshError;
    }
  }
);

export const extractErrorMessage = (err: unknown): string => {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: string; error?: string } | undefined;
    return data?.message || data?.error || err.message || '요청 처리 중 오류가 발생했습니다.';
  }
  if (err instanceof Error) {
    return err.message;
  }
  return '요청 처리 중 알 수 없는 오류가 발생했습니다.';
};
