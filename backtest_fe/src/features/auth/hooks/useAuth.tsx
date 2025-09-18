import { useEffect, useState, useCallback, useContext, createContext, ReactNode } from 'react';

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
		localStorage.removeItem('auth_token');
		localStorage.removeItem('auth_user');
		setUser(null);
	}, []);

	const logout = useCallback(async () => {
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
