export const getApiBaseUrl = (): string => {
  const envBase = (import.meta as any)?.env?.VITE_API_BASE_URL;
  if (typeof envBase === 'string' && envBase.length > 0) {
    return envBase.replace(/\/$/, '');
  }
  return '';
};

export const buildApiUrl = (path: string): string => {
  const base = getApiBaseUrl();
  if (!path.startsWith('/')) {
    return `${base}/${path}`;
  }
  return `${base}${path}`;
};
