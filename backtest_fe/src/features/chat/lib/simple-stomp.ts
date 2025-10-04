export interface StompFrame {
  command: string;
  headers: Record<string, string>;
  body: string;
}

type MessageHandler = (frame: StompFrame) => void;

const TERMINATOR = '\0';

const parseFrames = (raw: string): StompFrame[] => {
  const frames: StompFrame[] = [];
  const parts = raw.split(TERMINATOR).filter(Boolean);
  for (const part of parts) {
    const [headerSection, ...bodyParts] = part.split(/\n\n/);
    const body = bodyParts.join('\n\n');
    const headerLines = headerSection.split('\n');
    const command = headerLines.shift()?.trim() ?? '';
    const headers: Record<string, string> = {};
    headerLines.forEach((line) => {
      const [key, ...valueParts] = line.split(':');
      if (!key) return;
      headers[key.trim()] = valueParts.join(':').trim();
    });
    frames.push({ command, headers, body });
  }
  return frames;
};

export class SimpleStompClient {
  private ws: WebSocket | null = null;
  private readonly url: string;
  private connected = false;
  private connectPromise: Promise<void> | null = null;
  private messageHandlers = new Map<string, MessageHandler>();
  private subscriptionSeq = 0;

  constructor(url: string) {
    this.url = url;
  }

  isConnected(): boolean {
    return this.connected;
  }

  connect(headers: Record<string, string> = {}): Promise<void> {
    if (this.connected) return Promise.resolve();
    if (this.connectPromise) return this.connectPromise;

    this.connectPromise = new Promise((resolve, reject) => {
      // WebSocket이 이미 연결 중이거나 연결된 경우 재사용
      if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
        if (this.connected) {
          resolve();
          return;
        }
        // 연결 중이면 기다림 (이미 onmessage 핸들러가 resolve 호출할 것)
        return;
      }

      console.log('[STOMP] Connecting to:', this.url);
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('[STOMP] WebSocket connection opened');
        const lines = ['CONNECT', 'accept-version:1.2', 'heart-beat:0,0'];
        Object.entries(headers).forEach(([key, value]) => {
          lines.push(`${key}:${value}`);
        });
        lines.push('', '');
        console.log('[STOMP] Sending CONNECT frame');
        this.ws?.send(lines.join('\n'));
      };

      this.ws.onmessage = (event) => {
        const data = typeof event.data === 'string' ? event.data : '';
        const frames = parseFrames(data);
        frames.forEach((frame) => {
          console.log('[STOMP] Received frame:', frame.command);
          if (frame.command === 'CONNECTED') {
            console.log('[STOMP] Connection established');
            this.connected = true;
            resolve();
            return;
          }
          if (frame.command === 'MESSAGE') {
            const handler = this.messageHandlers.get(frame.headers.subscription ?? '');
            handler?.(frame);
          }
          if (frame.command === 'ERROR') {
            console.error('[STOMP] Error frame received:', frame.body);
            reject(new Error(frame.body || 'STOMP ERROR'));
          }
        });
      };

      this.ws.onerror = (event) => {
        console.error('[STOMP] WebSocket error:', event);
        // React Strict Mode에서 발생하는 불필요한 에러 로그 억제
        // 연결이 아직 완료되지 않은 경우에만 reject
        if (!this.connected) {
          reject(new Error('WebSocket connection failed'));
        }
        // 이미 연결된 경우 에러 무시 (재연결 로직이 필요하면 여기에 추가)
      };

      this.ws.onclose = () => {
        this.connected = false;
        this.connectPromise = null;
      };
    });

    return this.connectPromise;
  }

  subscribe(destination: string, handler: MessageHandler): () => void {
    if (!this.ws) {
      throw new Error('STOMP client is not connected');
    }
    const id = `sub-${++this.subscriptionSeq}`;
    this.messageHandlers.set(id, handler);
    const frame = [`SUBSCRIBE`, `id:${id}`, `destination:${destination}`, '', ''].join('\n');
    this.ws.send(frame);
    return () => this.unsubscribe(id);
  }

  unsubscribe(id: string) {
    if (!this.ws) return;
    this.messageHandlers.delete(id);
    const frame = [`UNSUBSCRIBE`, `id:${id}`, '', ''].join('\n');
    this.ws.send(frame);
  }

  disconnect() {
    if (!this.ws) return;
    
    // 연결 상태일 때만 DISCONNECT 프레임 전송
    if (this.connected && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(['DISCONNECT', '', ''].join('\n'));
      } catch (error) {
        console.warn('Failed to send STOMP disconnect frame', error);
      }
    }
    
    this.ws.close();
    this.connected = false;
    this.connectPromise = null;
    this.messageHandlers.clear();
  }
}
