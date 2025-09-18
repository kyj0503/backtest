export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

const getApiBase = () => (import.meta as any)?.env?.VITE_API_BASE_URL?.replace(/\/$/, '') || '';

export async function register(payload: RegisterPayload) {
  const res = await fetch(`${getApiBase()}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('auth_user', JSON.stringify({ id: data.user_id, username: data.username, email: data.email }));
  return data;
}

export async function login(payload: LoginPayload) {
  const res = await fetch(`${getApiBase()}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('auth_user', JSON.stringify({ id: data.user_id, username: data.username, email: data.email }));
  return data;
}

export function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

export function logout() {
  const token = getAuthToken();
  return fetch(`${getApiBase()}/api/v1/auth/logout`, {
    method: 'POST',
    headers: {
      'Authorization': token ? `Bearer ${token}` : ''
    }
  }).finally(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  });
}
