import React, { useEffect, useRef, useState } from 'react';
import { getAuthToken } from '../services/auth';
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

const getApiBase = () => (import.meta as any)?.env?.VITE_API_BASE_URL?.replace(/\/$/, '') || '';

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Array<{user:string; message:string; type:string}>>([]);
  const [input, setInput] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;
    
    const base = getApiBase();
    let wsUrlBase: string;
    
    if (base && base.startsWith('http')) {
      // 명시적 API URL이 설정된 경우
      wsUrlBase = base.replace('http', 'ws');
    } else {
      // 환경변수가 없으면 현재 location 기반으로 WebSocket URL 생성
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const port = window.location.hostname === 'localhost' ? ':8001' : '';
      wsUrlBase = `${protocol}//${host}${port}`;
    }
    
    const url = `${wsUrlBase}/api/v1/chat/ws/general?token=${token}`;
    console.log('WebSocket 연결 시도:', url);
    
    const ws = new WebSocket(url);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('WebSocket 연결 성공');
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket 연결 종료:', event.code, event.reason);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket 연결 오류:', error);
    };
    
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setMessages(prev => [...prev, { user: data.user, message: data.message, type: data.type }]);
      } catch {
        // ignore non-JSON
      }
    };
    return () => { ws.close(); };
  }, []);

  const send = () => {
    if (
      wsRef.current &&
      wsRef.current.readyState === WebSocket.OPEN &&
      input.trim()
    ) {
      wsRef.current.send(input.trim());
      setInput('');
    } else if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN) {
      // 연결이 아직 안 됐거나 끊어진 경우 사용자에게 안내
      alert('채팅 서버와의 연결이 아직 완료되지 않았습니다. 잠시 후 다시 시도해 주세요.');
    }
  };

  return (
    <div className="container mx-auto px-4 py-10 max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle>채팅방</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border rounded p-4 h-80 overflow-auto bg-background">
            {messages.map((m, i) => (
              <div key={i} className="text-sm">
                <strong>{m.user}</strong>: {m.message}
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Input 
              className="flex-1" 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              placeholder="메시지를 입력하세요" 
            />
            <Button onClick={send}>전송</Button>
          </div>
          <p className="text-xs text-muted-foreground">로그인 후 이용 가능합니다.</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatPage;

