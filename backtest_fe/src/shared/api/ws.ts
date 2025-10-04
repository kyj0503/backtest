import { getApiBaseUrl } from './base';

export const buildWebSocketUrl = (): string => {
  const base = getApiBaseUrl();
  
  // API base URL이 상대 경로인 경우 (예: '/api')
  if (base.startsWith('/')) {
    if (typeof window !== 'undefined' && window.location) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      
      // 개발 환경: Vite 프록시가 WebSocket 경로를 제대로 전달하지 못하는 문제 우회
      // localhost:5173에서 실행 중이면 직접 백엔드 포트(8080)로 연결
      if (window.location.host === 'localhost:5173') {
        const wsUrl = `${protocol}//localhost:8080/ws`;
        console.log('[WebSocket] Dev mode - connecting directly to backend:', wsUrl);
        return wsUrl;
      }
      
      // 프로덕션 또는 Vite 프록시 사용
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
