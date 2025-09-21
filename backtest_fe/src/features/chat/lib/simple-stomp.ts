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
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        const lines = ['CONNECT', 'accept-version:1.2', 'heart-beat:0,0'];
        Object.entries(headers).forEach(([key, value]) => {
          lines.push(`${key}:${value}`);
        });
        lines.push('', '');
        this.ws?.send(lines.join('\n'));
      };

      this.ws.onmessage = (event) => {
        const data = typeof event.data === 'string' ? event.data : '';
        const frames = parseFrames(data);
        frames.forEach((frame) => {
          if (frame.command === 'CONNECTED') {
            this.connected = true;
            resolve();
            return;
          }
          if (frame.command === 'MESSAGE') {
            const handler = this.messageHandlers.get(frame.headers.subscription ?? '');
            handler?.(frame);
          }
          if (frame.command === 'ERROR') {
            reject(new Error(frame.body || 'STOMP ERROR'));
          }
        });
      };

      this.ws.onerror = (event) => {
        reject(event instanceof ErrorEvent ? event.error : new Error('WebSocket error'));
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
