export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

const disabledError = () => new Error('인증 기능은 현재 비활성화되어 있습니다.');

export async function register(_payload: RegisterPayload) {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  return Promise.reject(disabledError());
}

export async function login(_payload: LoginPayload) {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  return Promise.reject(disabledError());
}

export function getAuthToken(): string | null {
  const token = localStorage.getItem('auth_token');
  if (token) {
    localStorage.removeItem('auth_token');
  }
  return null;
}

export function logout() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  return Promise.resolve();
}
