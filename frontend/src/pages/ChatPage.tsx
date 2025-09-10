import React, { useEffect, useRef, useState } from 'react';
import { getAuthToken } from '../services/auth';

const getApiBase = () => (import.meta as any)?.env?.VITE_API_BASE_URL?.replace(/\/$/, '') || '';

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Array<{user:string; message:string; type:string}>>([]);
  const [input, setInput] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;
    const base = getApiBase();
    const wsUrlBase = base.startsWith('http') ? base.replace('http', 'ws') : '';
    const url = `${wsUrlBase}/api/v1/chat/ws/general?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
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
      <h2 className="text-2xl font-bold mb-6">채팅방</h2>
      <div className="border rounded p-4 h-80 overflow-auto bg-white mb-4">
        {messages.map((m, i) => (
          <div key={i} className="text-sm"><strong>{m.user}</strong>: {m.message}</div>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="flex-1 px-3 py-2 border rounded" value={input} onChange={e => setInput(e.target.value)} placeholder="메시지를 입력하세요" />
        <button className="bg-blue-600 text-white rounded px-4" onClick={send}>전송</button>
      </div>
      <p className="text-xs text-gray-500 mt-2">로그인 후 이용 가능합니다.</p>
    </div>
  );
};

export default ChatPage;

