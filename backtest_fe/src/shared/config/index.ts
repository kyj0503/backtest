/**
 * 환경 변수 및 애플리케이션 설정
 */

interface AppConfig {
  readonly API_BASE_URL: string;
  readonly WS_BASE_URL: string;
  readonly NODE_ENV: 'development' | 'production' | 'test';
  readonly IS_DEVELOPMENT: boolean;
  readonly IS_PRODUCTION: boolean;
  readonly IS_TEST: boolean;
  readonly APP_VERSION: string;
  readonly BUILD_TIME: string;
}

// 환경 변수 검증 및 기본값 설정
const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key] || defaultValue;
  if (!value) {
    throw new Error(`Required environment variable ${key} is not defined`);
  }
  return value;
};

// API URL 빌드 함수
const buildApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL;
  
  // 상대 경로인 경우 현재 origin 사용
  if (baseUrl?.startsWith('/')) {
    return `${window.location.origin}${baseUrl}`;
  }
  
  // 절대 URL인 경우 그대로 사용
  if (baseUrl?.startsWith('http')) {
    return baseUrl;
  }
  
  // 기본값: 현재 origin의 /api
  return `${window.location.origin}/api`;
};

// WebSocket URL 빌드 함수
const buildWsUrl = (): string => {
  const baseUrl = buildApiUrl();
  return baseUrl.replace(/^http/, 'ws') + '/ws';
};

export const config: AppConfig = {
  API_BASE_URL: buildApiUrl(),
  WS_BASE_URL: buildWsUrl(),
  NODE_ENV: (import.meta.env.MODE as AppConfig['NODE_ENV']) || 'development',
  IS_DEVELOPMENT: import.meta.env.MODE === 'development',
  IS_PRODUCTION: import.meta.env.MODE === 'production',
  IS_TEST: import.meta.env.MODE === 'test',
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  BUILD_TIME: import.meta.env.VITE_BUILD_TIME || new Date().toISOString(),
};

// 개발 모드에서만 설정 정보 출력
if (config.IS_DEVELOPMENT) {
  console.log('App Config:', config);
}

export default config;