import { getApiBaseUrl } from './base';

export const buildWebSocketUrl = (): string => {
  const base = getApiBaseUrl();
  try {
    if (base.startsWith('http://') || base.startsWith('https://')) {
      const url = new URL(base);
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${url.host}/ws`;
    }
  } catch (error) {
    console.warn('Failed to parse API base URL for websocket', error);
  }

  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws`;
  }

  return 'ws://localhost:8080/ws';
};
