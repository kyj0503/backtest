import React, { useEffect, useRef, useState } from 'react';
import { getAuthToken } from '../services/auth';
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Array<{user:string; message:string; type:string}>>([]);
  const [input, setInput] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const connectedRef = useRef(false);

  const alertedRef = useRef(false);
  useEffect(() => {
    // StrictMode에서 중복 연결 방지
    if (connectedRef.current) {
      return;
    }
    const token = getAuthToken();
    if (!token) {
      // StrictMode 등에서 중복 실행 방지
      if (!alertedRef.current) {
        alertedRef.current = true;
        alert('로그인 후 이용 가능합니다.');
        window.location.href = '/login';
      }
      return undefined;
    }

    let wsUrlBase: string;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    if (
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1'
    ) {
      wsUrlBase = `${protocol}//localhost:8001`;
    } else {
      wsUrlBase = `${protocol}//${window.location.host}`;
    }
    const url = `${wsUrlBase}/api/v1/chat/ws/general?token=${token}`;
    console.log('WebSocket 연결 시도:', url);

    const ws = new WebSocket(url);
    wsRef.current = ws;
    connectedRef.current = true;

    let opened = false;
    ws.onopen = () => {
      opened = true;
      console.log('WebSocket 연결 성공');
    };

    ws.onclose = (event) => {
      console.log('WebSocket 연결 종료:', event.code, event.reason);
      if (event.code === 4001) {
        alert('인증 정보가 유효하지 않거나 세션이 만료되었습니다. 다시 로그인 해주세요.');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.location.href = '/login';
      } else if (opened && event.code !== 1000 && event.code !== 1005) {
        alert('채팅 서버와의 연결이 끊어졌습니다. 잠시 후 다시 시도해 주세요.');
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket 연결 오류:', error);
    };

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        const newMessage = { user: data.user, message: data.message, type: data.type };
        
        // 중복 메시지 방지: 같은 내용의 메시지가 연속으로 오는 경우 무시
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && 
              lastMessage.user === newMessage.user && 
              lastMessage.message === newMessage.message &&
              lastMessage.type === newMessage.type) {
            return prev; // 중복 메시지 무시
          }
          return [...prev, newMessage];
        });
      } catch {
        // ignore non-JSON
      }
    };
    // StrictMode에서 cleanup이 두 번 호출되는 것을 방지: ws가 이미 닫혔으면 close하지 않음
    return () => {
      connectedRef.current = false;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
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
      alert('채팅 서버와의 연결이 아직 완료되지 않았거나 인증에 실패했습니다. 다시 로그인 후 시도해 주세요.');
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
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatPage;

