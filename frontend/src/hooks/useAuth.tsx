import { useEffect, useState, useCallback, useContext, createContext, ReactNode } from 'react';
import { logout as apiLogout } from '../services/auth';

export interface AuthUser {
	id: number;
	username: string;
	email: string;
}

interface AuthContextType {
	user: AuthUser | null;
	setUser: (user: AuthUser | null) => void;
	logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
	const [user, setUser] = useState<AuthUser | null>(null);

	useEffect(() => {
		try {
			const raw = localStorage.getItem('auth_user');
			if (raw) setUser(JSON.parse(raw));
		} catch {}
		const onStorage = (e: StorageEvent) => {
			if (e.key === 'auth_user') {
				try { setUser(e.newValue ? JSON.parse(e.newValue) : null); } catch { setUser(null); }
			}
		};
		window.addEventListener('storage', onStorage);
		return () => window.removeEventListener('storage', onStorage);
	}, []);

	const logout = useCallback(async () => {
		try { await apiLogout(); } catch {}
		localStorage.removeItem('auth_token');
		localStorage.removeItem('auth_user');
		setUser(null);
	}, []);

	return (
		<AuthContext.Provider value={{ user, setUser, logout }}>
			{children}
		</AuthContext.Provider>
	);
}

export function useAuth() {
	const ctx = useContext(AuthContext);
	if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
	return ctx;
}
