import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { authStorage } from '@/shared/api/auth-storage';
import {
  getCurrentUser,
  login as loginService,
  logout as logoutService,
  register as registerService,
} from '../services/auth';
import { LoginPayload, RegisterPayload } from '../services/auth';
import { extractErrorMessage } from '@/shared/api/client';
import { AuthUser } from '../types';
export type { AuthUser } from '../types';

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: AuthUser | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const storedTokens = authStorage.getTokens();
        const storedUser = authStorage.getUser();
        if (!storedTokens || !storedUser) {
          authStorage.clearAll();
          setUser(null);
          return;
        }
        setUser(storedUser);
        const me = await getCurrentUser();
        setUser(me);
      } catch (error) {
        console.error('Failed to restore session', error);
        authStorage.clearAll();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    void bootstrap();
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    try {
      const loggedIn = await loginService(payload);
      setUser(loggedIn);
    } catch (err) {
      throw new Error(extractErrorMessage(err));
    }
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    try {
      const registered = await registerService(payload);
      setUser(registered);
    } catch (err) {
      throw new Error(extractErrorMessage(err));
    }
  }, []);

  const logout = useCallback(async () => {
    await logoutService();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      isLoading,
      login,
      register,
      logout,
      setUser,
    }),
    [isLoading, login, logout, register, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
