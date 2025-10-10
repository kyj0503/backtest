export const getApiBaseUrl = (): string => {
  const envBase = (import.meta as any)?.env?.VITE_API_BASE_URL;
  if (typeof envBase === 'string' && envBase.length > 0) {
    return envBase.replace(/\/$/, '');
  }
  // 빈 문자열 반환: backtestService.ts에서 전체 경로(/api/v1/...)를 사용
  return '';
};

export const buildApiUrl = (path: string): string => {
  const base = getApiBaseUrl();
  if (!path.startsWith('/')) {
    return `${base}/${path}`;
  }
  return `${base}${path}`;
};
