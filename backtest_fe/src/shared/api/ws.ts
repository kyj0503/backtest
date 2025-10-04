import { getApiBaseUrl } from './base';

export const buildWebSocketUrl = (): string => {
  const base = getApiBaseUrl();
  
  // API base URL이 상대 경로인 경우 (예: '/api')
  // 현재 window.location을 기반으로 WebSocket URL 생성
  if (base.startsWith('/')) {
    if (typeof window !== 'undefined' && window.location) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      console.log('[WebSocket] Building URL from relative API base:', { base, wsUrl });
      return wsUrl;
    }
    // SSR 환경이거나 window가 없는 경우 기본값
    console.warn('[WebSocket] No window object, using fallback URL');
    return 'ws://localhost:8080/ws';
  }
  
  // API base URL이 절대 URL인 경우
  try {
    if (base.startsWith('http://') || base.startsWith('https://')) {
      const url = new URL(base);
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${url.host}/ws`;
      console.log('[WebSocket] Building URL from absolute API base:', { base, wsUrl });
      return wsUrl;
    }
  } catch (error) {
    console.warn('[WebSocket] Failed to parse API base URL:', error);
  }

  // fallback
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    console.log('[WebSocket] Using fallback URL:', wsUrl);
    return wsUrl;
  }

  console.warn('[WebSocket] All methods failed, using hardcoded fallback');
  return 'ws://localhost:8080/ws';
};
