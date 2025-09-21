import { apiClient, extractErrorMessage } from '@/shared/api/client';
import { authStorage, AuthTokens, persistAuthState } from '@/shared/api/auth-storage';
import { AuthUser } from '../types';

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  investmentType?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

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

interface UserProfileDTO {
  id: number;
  username: string;
  email: string;
  profileImage: string | null;
  investmentType: string | null;
  emailVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

const toAuthUser = (dto: AuthResponseDTO['user']): AuthUser => ({
  id: dto.id,
  username: dto.username,
  email: dto.email,
  profileImage: dto.profileImage ?? undefined,
  investmentType: dto.investmentType ?? undefined,
  emailVerified: dto.emailVerified,
});

const toTokens = (dto: AuthResponseDTO['tokens']): AuthTokens => ({
  accessToken: dto.accessToken,
  refreshToken: dto.refreshToken,
  tokenType: dto.tokenType,
  accessExpiresAt: dto.accessExpiresAt,
  refreshTokenExpiresAt: dto.refreshTokenExpiresAt,
});

const persistAuthResponse = (response: AuthResponseDTO): AuthUser => {
  const user = toAuthUser(response.user);
  const tokens = toTokens(response.tokens);
  persistAuthState(user, tokens);
  return user;
};

export const register = async (payload: RegisterPayload): Promise<AuthUser> => {
  try {
    const { data } = await apiClient.post<AuthResponseDTO>('/v1/auth/signup', {
      username: payload.username,
      email: payload.email,
      password: payload.password,
      investmentType: payload.investmentType ?? null,
    });
    return persistAuthResponse(data);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const login = async (payload: LoginPayload): Promise<AuthUser> => {
  try {
    const { data } = await apiClient.post<AuthResponseDTO>('/v1/auth/login', payload);
    return persistAuthResponse(data);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const refreshTokens = async (): Promise<AuthUser | null> => {
  const tokens = authStorage.getTokens();
  if (!tokens) return null;
  try {
    const { data } = await apiClient.post<AuthResponseDTO>('/v1/auth/token/refresh', {
      refreshToken: tokens.refreshToken,
    });
    return persistAuthResponse(data);
  } catch (err) {
    authStorage.clearAll();
    return null;
  }
};

export const getCurrentUser = async (): Promise<AuthUser> => {
  try {
    const { data } = await apiClient.get<UserProfileDTO>('/v1/users/me');
    const user: AuthUser = {
      id: data.id,
      username: data.username,
      email: data.email,
      profileImage: data.profileImage ?? undefined,
      investmentType: data.investmentType ?? undefined,
      emailVerified: data.emailVerified,
    };
    authStorage.setUser(user);
    return user;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const logout = async () => {
  authStorage.clearAll();
};
