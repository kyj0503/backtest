import { AuthUser } from '@/features/auth/types';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  accessExpiresAt: string;
  refreshTokenExpiresAt: string;
}

const TOKEN_STORAGE_KEY = 'auth.tokens';
const USER_STORAGE_KEY = 'auth.user';

export const authStorage = {
  getTokens(): AuthTokens | null {
    try {
      const raw = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw) as AuthTokens;
    } catch {
      return null;
    }
  },

  setTokens(tokens: AuthTokens | null) {
    if (!tokens) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      return;
    }
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
  },

  clearTokens() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  },

  getUser(): AuthUser | null {
    try {
      const raw = localStorage.getItem(USER_STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  },

  setUser(user: AuthUser | null) {
    if (!user) {
      localStorage.removeItem(USER_STORAGE_KEY);
      return;
    }
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  },

  clearAll() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  },
};

export const persistAuthState = (user: AuthUser, tokens: AuthTokens) => {
  authStorage.setTokens(tokens);
  authStorage.setUser(user);
};

export const isTokenExpired = (expiryIso: string | undefined | null, bufferMs = 30_000): boolean => {
  if (!expiryIso) return true;
  const expiry = Date.parse(expiryIso);
  if (Number.isNaN(expiry)) return true;
  return expiry - Date.now() <= bufferMs;
};

export const tokensAvailable = (): boolean => {
  const tokens = authStorage.getTokens();
  return !!(tokens && tokens.accessToken && tokens.refreshToken);
};
